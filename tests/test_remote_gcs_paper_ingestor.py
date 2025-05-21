from unittest.mock import MagicMock, patch

import pytest

from ingestors.remote_gcs_paper_ingestor import RemoteGCSPaperIngestor
from models.document import Document
from models.paper_metadata import FetchedPaperMetadata

EXPECTED_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


@pytest.fixture
def sample_pdf_paper():
    return FetchedPaperMetadata(
        id="1234.5678",
        title="A Deep Dive into Transformers",
        authors=["Alice Smith", "Bob Jones"],
        url="https://example.com/test.pdf",
        format="pdf",
        metadata={"doi": "10.1000/xyz123", "journal": "Nature AI"},
    )


@pytest.fixture
def sample_html_paper():
    return FetchedPaperMetadata(
        id="4321.8765",
        title="HTML Interfaces for LLMs",
        authors=["Jane Roe"],
        url="https://example.com/test.html",
        format="html",
        metadata={"doi": "10.2000/html567", "journal": "Web Science"},
    )


@patch("ingestors.remote_gcs_paper_ingestor.requests.get")
@patch("ingestors.remote_gcs_paper_ingestor.storage.Client")
def test_ingest_pdf_upload(mock_storage_client, mock_requests_get, sample_pdf_paper):
    """Uploads PDF to GCS and creates Document with metadata."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    mock_pdf_bytes = b"%PDF-1.4 mock content"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.content = mock_pdf_bytes

    ingestor = RemoteGCSPaperIngestor(papers=[sample_pdf_paper])
    documents = ingestor.ingest()

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, Document)
    assert doc.file_bytes == mock_pdf_bytes
    assert doc.gcs_metadata.format == "pdf"

    mock_requests_get.assert_called_with(
        sample_pdf_paper.url,
        headers=EXPECTED_HEADERS,
        timeout=10,
    )


@patch("ingestors.remote_gcs_paper_ingestor.requests.get")
@patch("ingestors.remote_gcs_paper_ingestor.storage.Client")
def test_ingest_html_upload(mock_storage_client, mock_requests_get, sample_html_paper):
    """Uploads HTML to GCS and creates Document with metadata."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    mock_html_text = "<html><body>This is a test HTML document.</body></html>"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.text = mock_html_text

    ingestor = RemoteGCSPaperIngestor(papers=[sample_html_paper])
    documents = ingestor.ingest()

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, Document)
    assert doc.file_bytes is None
    assert doc.gcs_metadata.format == "html"

    mock_requests_get.assert_called_with(
        sample_html_paper.url,
        headers=EXPECTED_HEADERS,
        timeout=10,
    )


@patch("ingestors.remote_gcs_paper_ingestor.requests.get")
@patch("ingestors.remote_gcs_paper_ingestor.storage.Client")
def test_ingest_skips_missing_url(mock_storage_client, mock_requests_get):
    """Skips papers with no URL."""
    paper = FetchedPaperMetadata(
        id="no-url",
        title="No Link Here",
        authors=[],
        url=None,
        format="pdf",
        metadata={"doi": "10.0000/void"},
    )

    ingestor = RemoteGCSPaperIngestor(papers=[paper])
    documents = ingestor.ingest()

    assert documents == []
    mock_requests_get.assert_not_called()
    mock_storage_client.return_value.bucket.return_value.blob.assert_not_called()


@patch(
    "ingestors.remote_gcs_paper_ingestor.requests.get",
    side_effect=Exception("network fail"),
)
@patch("ingestors.remote_gcs_paper_ingestor.storage.Client")
def test_ingest_handles_download_failure(
    mock_storage_client, mock_requests_get, sample_pdf_paper
):
    """Skips paper if download fails and file is not already in GCS."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False  # Not in GCS

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    ingestor = RemoteGCSPaperIngestor(papers=[sample_pdf_paper])
    documents = ingestor.ingest()

    assert documents == []


@patch("ingestors.remote_gcs_paper_ingestor.requests.get")
@patch("ingestors.remote_gcs_paper_ingestor.storage.Client")
def test_ingest_skips_html_upload_if_exists(
    mock_storage_client, mock_requests_get, sample_html_paper
):
    """Skips uploading HTML if already exists in GCS."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True  # Simulate blob already in GCS

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    ingestor = RemoteGCSPaperIngestor(papers=[sample_html_paper])
    documents = ingestor.ingest()

    assert len(documents) == 1
    doc = documents[0]
    assert doc.file_bytes is None
    assert doc.gcs_metadata.format == "html"

    mock_requests_get.assert_not_called()
    mock_blob.upload_from_string.assert_not_called()
