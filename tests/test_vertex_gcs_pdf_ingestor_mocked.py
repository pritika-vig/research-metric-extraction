# tests/test_vertex_gcs_pdf_ingestor_mocked.py

# Mocked test. Does not hit live gcp buckets.

import uuid

from ingestors.vertex_gcs_pdf_ingestor import VertexGcsPDFIngestor
from tests.mocks.mock_gcs_client import MockStorageClient


def test_mocked_upload_and_skip(temp_test_dir):
    test_pdf = temp_test_dir / f"mock_test_{uuid.uuid4().hex}.pdf"
    test_pdf.write_text("Mock test PDF", encoding="utf-8")

    # Replace the real client with mock
    ingestor = VertexGcsPDFIngestor()
    ingestor.gcs_client = MockStorageClient()

    # First upload should succeed
    docs = ingestor.ingest(str(temp_test_dir))
    assert len(docs) == 1
    blob_name = docs[0].gcs_metadata.blob_name

    bucket = ingestor.gcs_client.bucket(ingestor.bucket_name)
    blob = bucket.blob(blob_name)

    assert blob.exists()

    # Second upload should skip
    docs2 = ingestor.ingest(str(temp_test_dir))
    assert len(docs2) == 1
    assert docs2[0].gcs_metadata.blob_name == blob_name
