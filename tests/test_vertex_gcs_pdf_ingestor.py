# tests/test_vertex_gcs_pdf_ingestor.py

import uuid

from google.cloud import storage

from ingestors.vertex_gcs_pdf_ingestor import VertexGcsPDFIngestor


def test_pdf_upload_and_cleanup(temp_test_dir, test_pdf_file):
    ingestor = VertexGcsPDFIngestor()

    # Ingest the file
    documents = ingestor.ingest(str(temp_test_dir))
    assert len(documents) == 1

    doc = documents[0]
    blob = (
        storage.Client().bucket(ingestor.bucket_name).blob(doc.gcs_metadata.blob_name)
    )

    assert blob.exists()
    blob.delete()


def test_skip_existing_blob(temp_test_dir):
    ingestor = VertexGcsPDFIngestor()

    # Create a file manually
    test_pdf = temp_test_dir / f"skip_test_{uuid.uuid4().hex}.pdf"
    test_pdf.write_text("Skip test PDF upload.", encoding="utf-8")

    blob_name = f"uploads/{test_pdf.name}"
    bucket = storage.Client().bucket(ingestor.bucket_name)
    blob = bucket.blob(blob_name)

    # Upload it manually first
    blob.upload_from_filename(str(test_pdf))
    assert blob.exists()

    upload_attempted = {"count": 0}

    def wrapped_upload(file, blob_name):
        if not storage.Client().bucket(ingestor.bucket_name).blob(blob_name).exists():
            upload_attempted["count"] += 1
        return ingestor.upload_to_gcs.__wrapped__(file, blob_name)

    original_upload = ingestor.upload_to_gcs
    wrapped_upload.__wrapped__ = original_upload
    ingestor.upload_to_gcs = wrapped_upload

    # Should skip upload
    ingestor.ingest(str(temp_test_dir))
    assert upload_attempted["count"] == 0

    blob.delete()
