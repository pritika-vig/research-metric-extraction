# tests/test_remote_gcs_pdf_ingestor.py

from unittest.mock import MagicMock, patch

import pytest

from ingestors.remote_gcs_pdf_ingestor import RemoteGCSPDFIngestor
from models.document import Document
from models.paper_metadata import PaperMetadata


@pytest.fixture
def sample_paper():
    return PaperMetadata(
        id="1234.5678",
        title="A Deep Dive into Transformers",
        authors=["Alice Smith", "Bob Jones"],
        pdf_url="https://example.com/test.pdf",
        metadata={"doi": "10.1000/xyz123", "journal": "Nature AI"},
    )


@patch("ingestors.remote_gcs_pdf_ingestor.requests.get")
@patch("ingestors.remote_gcs_pdf_ingestor.storage.Client")
def test_ingest_pdf_upload_and_skip(
    mock_storage_client, mock_requests_get, sample_paper
):
    """Should upload the PDF if not present, skip if already uploaded."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.side_effect = [False, True]  # First upload, then skip

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    # Mock PDF response
    mock_pdf_bytes = b"%PDF-1.4 mock content"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.content = mock_pdf_bytes

    ingestor = RemoteGCSPDFIngestor(papers=[sample_paper])
    documents = ingestor.ingest()

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, Document)
    assert doc.file_bytes == mock_pdf_bytes
    assert doc.gcs_metadata is not None
    assert doc.gcs_metadata.blob_name.endswith(".pdf")

    # Second call: should skip upload
    documents_again = ingestor.ingest()
    assert len(documents_again) == 1
    mock_blob.upload_from_string.assert_called_once()  # only uploaded once


@patch("ingestors.remote_gcs_pdf_ingestor.requests.get")
@patch("ingestors.remote_gcs_pdf_ingestor.storage.Client")
def test_ingest_skips_missing_pdf_url(mock_storage_client, mock_requests_get):
    """Should skip papers that have no PDF URL."""
    paper_missing_url = PaperMetadata(
        id="9999.8888",
        title="No PDF here",
        authors=[],
        pdf_url=None,
        metadata={"doi": "10.0000/missing"},
    )

    ingestor = RemoteGCSPDFIngestor(papers=[paper_missing_url])
    documents = ingestor.ingest()

    assert documents == []
    mock_requests_get.assert_not_called()
    mock_storage_client.return_value.bucket.return_value.blob.assert_not_called()


@patch(
    "ingestors.remote_gcs_pdf_ingestor.requests.get",
    side_effect=Exception("network fail"),
)
@patch("ingestors.remote_gcs_pdf_ingestor.storage.Client")
def test_ingest_handles_download_failure(
    mock_storage_client, mock_requests_get, sample_paper
):
    """Should skip document if download fails and file is not already in GCS."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False  # Simulate blob not in GCS

    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    ingestor = RemoteGCSPDFIngestor(papers=[sample_paper])
    documents = ingestor.ingest()

    assert documents == []  # Should not emit Document if both download & upload fail
