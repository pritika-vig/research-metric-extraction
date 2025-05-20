# ingestors/vertex_gcs_pdf_ingestor.py

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from google.cloud import storage

from ingestors.ingestor import Ingestor
from models.document import Document
from models.gcs_metadata import GCSMetadata

load_dotenv()


class VertexGcsPDFIngestor(Ingestor):
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        self.bucket_name = os.getenv("GCS_BUCKET")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")

        if not self.bucket_name or not self.project_id:
            raise ValueError(
                "Missing GCS_BUCKET or GCP_PROJECT_ID in environment variables"
            )

        self.gcs_client = storage.Client()

    def upload_to_gcs(self, local_file: Path, destination_blob: str) -> str:
        bucket = self.gcs_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob)

        if blob.exists():
            print(f"Skipping upload — blob already exists: {destination_blob}")
        else:
            blob.upload_from_filename(str(local_file))
            print(f"Uploaded file to: {destination_blob}")

        return f"gs://{self.bucket_name}/{destination_blob}"

    def ingest(self) -> List[Document]:
        documents: List[Document] = []

        for pdf_file in self.directory_path.glob("*.pdf"):
            print(f"Processing: {pdf_file.name}")
            blob_name = f"uploads/{pdf_file.name}"
            gcs_uri = self.upload_to_gcs(pdf_file, blob_name)

            gcs_metadata = GCSMetadata(
                gcs_uri=gcs_uri,
                blob_name=blob_name,
                bucket_name=self.bucket_name,
            )

            doc = Document(
                file_path=pdf_file, parsed_text=None, gcs_metadata=gcs_metadata
            )
            documents.append(doc)

        return documents
