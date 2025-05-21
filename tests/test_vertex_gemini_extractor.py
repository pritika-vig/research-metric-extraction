# tests/test_vertex_gemini_extractor.py

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from extractors.vertex_gemini_extractor import VertexGeminiExtractor
from models.document import Document
from models.extraction_config import ExtractionConfig
from models.extraction_field_spec import ExtractionFieldSpec
from models.gcs_metadata import GCSMetadata


# Test that well-formed Gemini responses are parsed correctly
# into ExtractedField objects
def test_extract_parses_mock_response_correctly():
    mock_response = (
        "Title:\n"
        "  value: AI for Patient Outcomes\n"
        "  evidence_quote: \"This study is titled 'AI for Patient Outcomes'.\"\n"
        "  page_number: 1\n"
        "Patient Co-authors:\n"
        "  value: Yes\n"
        '  evidence_quote: "Co-authored by patients as part of the collaboration."\n'
        "  page_number: 2\n"
        "Type of Engagement:\n"
        "  value: Collaboration\n"
        '  evidence_quote: "The project was a collaboration."\n'
        "  page_number: 2\n"
        "Impact of Engagement:\n"
        "  value: Patients influenced study design\n"
        '  evidence_quote: "Patients helped shape the study design."\n'
        "  page_number: 3\n"
    )

    config = ExtractionConfig(
        name="Test Config",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
            ExtractionFieldSpec("Patient Co-authors", "Were patients co-authors?"),
            ExtractionFieldSpec("Type of Engagement", "Montreal Model classification"),
            ExtractionFieldSpec(
                "Impact of Engagement", "What was the effect of engagement?"
            ),
        ],
    )

    document = Document(
        file_path=Path("tests/fake.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake-bucket/fake.pdf",
            blob_name="fake.pdf",
            bucket_name="fake-bucket",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    assert extracted.document == document
    assert len(extracted.fields) == 4

    title_field = next(f for f in extracted.fields if f.name == "Title")
    assert title_field.value == "AI for Patient Outcomes"
    assert (
        title_field.evidence_quote
        == "\"This study is titled 'AI for Patient Outcomes'.\""
    )
    assert title_field.page_number == 1


# Test that missing fields in the Gemini response are
# handled gracefully with None/defaults
def test_extract_handles_missing_fields_gracefully():
    mock_response = (
        "Title:\n"
        "  value: Only this field is here\n"
        "  evidence_quote: N/A\n"
        "  page_number: N/A\n"
    )

    config = ExtractionConfig(
        name="Test Missing Fields",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
            ExtractionFieldSpec("Patient Co-authors", "Were patients co-authors?"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake_missing.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/fake_missing.pdf",
            blob_name="fake_missing.pdf",
            bucket_name="fake",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    title_field = next(f for f in extracted.fields if f.name == "Title")
    patient_field = next(f for f in extracted.fields if f.name == "Patient Co-authors")

    assert title_field.value == "Only this field is here"
    assert title_field.evidence_quote == "N/A" or title_field.evidence_quote is None
    assert title_field.page_number is None

    assert patient_field.value is None
    assert patient_field.evidence_quote is None
    assert patient_field.page_number is None


# Test that malformed output (no colons or structured format)
# results in empty values but no crash
def test_extract_handles_malformed_text():
    mock_response = (
        "This document contains a paragraph, not fields.\n"
        "Patients were included. There were many authors."
    )

    config = ExtractionConfig(
        name="Test Malformed",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
            ExtractionFieldSpec("Patient Co-authors", "Were patients co-authors?"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake_malformed.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/fake_malformed.pdf",
            blob_name="fake_malformed.pdf",
            bucket_name="fake",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    assert extracted.get_field_value("Title") is None
    assert extracted.get_field_value("Patient Co-authors") is None


# Test that an empty string response from Gemini is handled safely
# with all fields set to None
def test_extract_handles_empty_response():
    config = ExtractionConfig(
        name="Test Empty Response",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake_empty.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/fake_empty.pdf",
            blob_name="fake_empty.pdf",
            bucket_name="fake",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = ""
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    assert extracted.get_field_value("Title") is None


def test_extract_handles_missing_evidence_and_page():
    mock_response = (
        "Title:\n"
        "  value: AI for Health\n"
        "  evidence_quote: N/A\n"
        "  page_number: N/A\n"
    )

    config = ExtractionConfig(
        name="Test Missing Evidence",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake_missing_evidence.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/missing_evidence.pdf",
            blob_name="missing_evidence.pdf",
            bucket_name="fake",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    field = extracted.fields[0]
    assert field.value == "AI for Health"
    assert field.evidence_quote == "N/A" or field.evidence_quote is None
    assert field.page_number is None


def test_extract_handles_html_document():
    mock_response = (
        "Title:\n"
        "  value: HTML Document Test\n"
        '  evidence_quote: "Found in HTML body."\n'
        "  page_number: 1\n"
    )

    config = ExtractionConfig(
        name="HTML Format Test",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake.html"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/html_doc.html",
            blob_name="html_doc.html",
            bucket_name="fake",
            format="html",  # ✅ HTML format triggers correct MIME
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract(document, config)

    assert extracted.get_field_value("Title") == "HTML Document Test"


def test_extract_raises_on_unsupported_format():
    config = ExtractionConfig(
        name="Unsupported Format",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
        ],
    )

    document = Document(
        file_path=Path("tests/fake.txt"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/fake.txt",
            blob_name="fake.txt",
            bucket_name="fake",
            format="txt",
        ),
    )

    extractor = VertexGeminiExtractor()

    with pytest.raises(ValueError, match="Unsupported file format"):
        extractor.extract(document, config)
