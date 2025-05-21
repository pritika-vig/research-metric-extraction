from pathlib import Path
from unittest.mock import MagicMock

from extractors.vertex_gemini_extractor import VertexGeminiExtractor
from models.document import Document
from models.extraction_config import ExtractionConfig
from models.extraction_field_spec import ExtractionFieldSpec
from models.gcs_metadata import GCSMetadata
from models.paper_id import PaperId


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

    paper_id = PaperId(pmcid="PMC123")
    document = Document(
        file_path=Path("tests/fake.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake-bucket/fake.pdf",
            blob_name="fake.pdf",
            bucket_name="fake-bucket",
            source_url="https://example.com/fake.pdf",
            format="pdf",
        ),
        paper_id=paper_id,
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

    assert extracted.get_paper_id() == document.paper_id.get_canonical_id()
    assert len(extracted.fields) == 4

    title_field = next(f for f in extracted.fields if f.name == "Title")
    assert title_field.value == "AI for Patient Outcomes"
    assert (
        title_field.evidence_quote
        == "\"This study is titled 'AI for Patient Outcomes'.\""
    )
    assert title_field.page_number == 1


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
            source_url="https://example.com/fake_missing.pdf",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

    title_field = next(f for f in extracted.fields if f.name == "Title")
    patient_field = next(f for f in extracted.fields if f.name == "Patient Co-authors")

    assert title_field.value == "Only this field is here"
    assert title_field.evidence_quote in ["N/A", None]
    assert title_field.page_number is None

    assert patient_field.value is None
    assert patient_field.evidence_quote is None
    assert patient_field.page_number is None


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
            source_url="https://example.com/fake_malformed.pdf",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

    assert extracted.get_field_value("Title") is None
    assert extracted.get_field_value("Patient Co-authors") is None


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
            source_url="https://example.com/fake_empty.pdf",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = ""
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

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
            source_url="https://example.com/missing_evidence.pdf",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

    field = extracted.fields[0]
    assert field.value == "AI for Health"
    assert field.evidence_quote in ["N/A", None]
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
            source_url="https://example.com/html_doc.html",
            format="html",
        ),
    )

    extractor = VertexGeminiExtractor()
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    extracted = extractor.extract([document], config)[0]

    assert extracted.get_field_value("Title") == "HTML Document Test"


def test_extract_handles_unsupported_format_gracefully(caplog):
    config = ExtractionConfig(
        name="Unsupported Format",
        fields=[ExtractionFieldSpec("Title", "Study title")],
    )

    document = Document(
        file_path=Path("tests/fake.txt"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://fake/fake.txt",
            blob_name="fake.txt",
            bucket_name="fake",
            source_url="https://example.com/fake.txt",
            format="txt",  # Unsupported
        ),
    )

    extractor = VertexGeminiExtractor()

    with caplog.at_level("WARNING"):
        results = extractor.extract([document], config)

    assert results == []
    assert any("Unsupported file format" in record.message for record in caplog.records)


def test_batch_extract_with_partial_failure(caplog):
    mock_response = (
        "Title:\n"
        "  value: Clean Paper\n"
        '  evidence_quote: "This is a clean paper."\n'
        "  page_number: 1\n"
    )

    config = ExtractionConfig(
        name="Batch Test",
        fields=[ExtractionFieldSpec("Title", "Study title")],
    )

    good_document = Document(
        file_path=Path("tests/good.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://bucket/good.pdf",
            blob_name="good.pdf",
            bucket_name="bucket",
            source_url="https://example.com/good.pdf",
            format="pdf",
        ),
    )

    bad_document = Document(
        file_path=Path("tests/bad.txt"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://bucket/bad.txt",
            blob_name="bad.txt",
            bucket_name="bucket",
            source_url="https://example.com/bad.txt",
            format="txt",  # Unsupported
        ),
    )

    extractor = VertexGeminiExtractor()

    # Mock only the good document's response
    mock_result = MagicMock()
    mock_result.text = mock_response
    extractor.model.generate_content = MagicMock(return_value=mock_result)

    with caplog.at_level("WARNING"):
        results = extractor.extract([good_document, bad_document], config)

    assert len(results) == 1
    assert results[0].get_field_value("Title") == "Clean Paper"

    # Ensure error was logged for bad document
    assert any("Unsupported file format" in record.message for record in caplog.records)


def test_batch_extract_with_one_network_failure(caplog):
    mock_response = (
        "Title:\n"
        "  value: Good Paper Title\n"
        '  evidence_quote: "The title is Good Paper Title."\n'
        "  page_number: 1\n"
    )

    config = ExtractionConfig(
        name="Partial Failure Test",
        fields=[
            ExtractionFieldSpec("Title", "Study title"),
        ],
    )

    good_document = Document(
        file_path=Path("tests/good_network.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://bucket/good_network.pdf",
            blob_name="good_network.pdf",
            bucket_name="bucket",
            source_url="https://example.com/good_network.pdf",
            format="pdf",
        ),
    )

    failing_document = Document(
        file_path=Path("tests/bad_network.pdf"),
        gcs_metadata=GCSMetadata(
            gcs_uri="gs://bucket/bad_network.pdf",
            blob_name="bad_network.pdf",
            bucket_name="bucket",
            source_url="https://example.com/bad_network.pdf",
            format="pdf",
        ),
    )

    extractor = VertexGeminiExtractor()

    # Configure mock: good doc returns a response, bad doc raises a network error
    def mock_generate_content(parts, generation_config):
        uri_str = str(parts[1])
        if "good_network.pdf" in uri_str:
            mock_result = MagicMock()
            mock_result.text = mock_response
            return mock_result
        else:
            raise RuntimeError("Simulated network failure")

    extractor.model.generate_content = MagicMock(side_effect=mock_generate_content)

    with caplog.at_level("WARNING"):
        results = extractor.extract([good_document, failing_document], config)

    # Only one result (for the good doc)
    assert len(results) == 1
    assert results[0].get_field_value("Title") == "Good Paper Title"

    # Confirm the network error was logged
    assert any("Simulated network failure" in r.message for r in caplog.records)
    assert any("bad_network.pdf" in r.message for r in caplog.records)
