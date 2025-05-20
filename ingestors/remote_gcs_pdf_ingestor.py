# ingestors/remote_gcs_pdf_ingestor.py
import logging
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from google.cloud import storage

from ingestors.ingestor import Ingestor
from models.document import Document
from models.gcs_metadata import GCSMetadata
from models.paper_metadata import PaperMetadata

load_dotenv()

logger = logging.getLogger(__name__)


class RemoteGCSPDFIngestor(Ingestor):
    """
    Ingests academic papers from a list of PaperMetadata objects.

    For each paper:
    - Downloads the PDF from the provided `pdf_url`
    - Uploads the file to a Google Cloud Storage bucket (under `uploads/`)
    - Skips the upload if the file already exists in the bucket
    - Constructs a Document object containing GCS metadata and PDF content

    Environment Variables Required:
        - GCS_BUCKET: Name of the target GCS bucket
        - GCP_PROJECT_ID: Google Cloud project ID
        - GCP_REGION (optional): Defaults to "us-central1"

    Raises:
        - ValueError: If required environment variables are missing
        - requests.RequestException: If a PDF download fails
    """

    def __init__(self, papers: List[PaperMetadata]):
        self.papers = papers
        self.bucket_name = os.getenv("GCS_BUCKET")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")

        if not self.bucket_name or not self.project_id:
            raise ValueError(
                "Missing GCS_BUCKET or GCP_PROJECT_ID environment variable"
            )

        self.gcs_client = storage.Client()

    def ingest(self) -> List[Document]:
        documents = []

        for paper in self.papers:
            if not paper.pdf_url:
                logger.warning(f"Paper has no url: {paper.id}")
                continue
            blob_name = self._make_blob_name(paper)
            blob = self.gcs_client.bucket(self.bucket_name).blob(blob_name)
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            file_bytes: Optional[bytes] = None

            try:
                if blob.exists():
                    print(f"✅ Skipping {blob_name}, already exists.")
                else:
                    print(f"⬇️  Downloading {paper.pdf_url}")
                    response = requests.get(paper.pdf_url, timeout=10)
                    response.raise_for_status()
                    file_bytes = response.content
                    blob.upload_from_string(file_bytes, content_type="application/pdf")
                    print(f"⬆️  Uploaded {blob_name}")

                gcs_metadata = GCSMetadata(
                    gcs_uri=gcs_uri,
                    blob_name=blob_name,
                    bucket_name=self.bucket_name,
                )

                documents.append(
                    Document(
                        file_path=None,
                        file_bytes=file_bytes,
                        gcs_metadata=gcs_metadata,
                        parsed_text=None,
                        grobid_response=None,
                        paper_metadata=paper,
                    )
                )

            except Exception as e:
                logger.warning(f"⚠️ Failed to process {paper.id}: {e}")

        return documents

    def _make_blob_name(self, paper: PaperMetadata) -> str:
        doi = paper.metadata.get("doi")
        if doi:
            base_name = doi.replace("/", "_")
        else:
            base_name = paper.title.lower().replace(" ", "_")[:100]

        return f"uploads/{base_name}.pdf"
