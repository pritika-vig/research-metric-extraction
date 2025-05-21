import logging
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from google.cloud import storage

from ingestors.ingestor import Ingestor
from models.document import Document
from models.gcs_metadata import GCSMetadata
from models.paper_metadata import FetchedPaperMetadata

load_dotenv()
logger = logging.getLogger(__name__)


class RemoteGCSPaperIngestor(Ingestor):
    """
    Ingests academic papers (PDF or HTML) from a list of FetchedPaperMetadata objects.

    For each paper:
    - Downloads the document from the provided `url`
    - Uploads the file to a Google Cloud Storage bucket (under `uploads/`)
    - Skips upload if the file already exists
    - Constructs a Document object containing GCS metadata and content reference

    Environment Variables Required:
        - GCS_BUCKET: Name of the GCS bucket
        - GCP_PROJECT_ID: Google Cloud project ID
        - GCP_REGION (optional): Defaults to "us-central1"
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, papers: List[FetchedPaperMetadata]):
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
            if not paper.url:
                logger.warning(f"Paper has no URL: {paper.paper_id.get_canonical_id()}")
                continue

            try:
                if paper.format == "pdf":
                    doc = self._handle_pdf(paper)
                elif paper.format == "html":
                    doc = self._handle_html(paper)
                else:
                    logger.warning(
                        f"Unsupported format '{paper.format}' for {paper.id}"
                    )
                    continue

                if doc:
                    documents.append(doc)

            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to process {paper.paper_id.get_canonical_id()}: {e}"
                )

        return documents

    def _handle_pdf(self, paper: FetchedPaperMetadata) -> Optional[Document]:
        blob_name = self._make_blob_name(paper, extension="pdf")
        blob = self.gcs_client.bucket(self.bucket_name).blob(blob_name)
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
        file_bytes: Optional[bytes] = None

        if not blob.exists():
            logger.info(f"⬇️  Downloading PDF: {paper.url}")
            response = requests.get(paper.url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            file_bytes = response.content
            blob.upload_from_string(file_bytes, content_type="application/pdf")
            logger.info(f"⬆️  Uploaded PDF to {gcs_uri}")
        else:
            logger.info(f"✅ PDF already exists in GCS: {gcs_uri}")

        return Document(
            file_path=None,
            file_bytes=file_bytes,
            gcs_metadata=GCSMetadata(
                gcs_uri=gcs_uri,
                blob_name=blob_name,
                bucket_name=self.bucket_name,
                source_url=paper.url,
                format="pdf",
            ),
            paper_id=paper.paper_id,
        )

    def _handle_html(self, paper: FetchedPaperMetadata) -> Optional[Document]:
        blob_name = self._make_blob_name(paper, extension="html")
        blob = self.gcs_client.bucket(self.bucket_name).blob(blob_name)
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

        if not blob.exists():
            logger.info(f"⬇️  Downloading HTML: {paper.url}")
            response = requests.get(paper.url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            blob.upload_from_string(response.text, content_type="text/html")
            logger.info(f"⬆️  Uploaded HTML to {gcs_uri}")
        else:
            logger.info(f"HTML already exists in GCS: {gcs_uri}")

        return Document(
            file_path=None,
            file_bytes=None,
            gcs_metadata=GCSMetadata(
                gcs_uri=gcs_uri,
                blob_name=blob_name,
                bucket_name=self.bucket_name,
                source_url=paper.url,
                format="html",
            ),
            paper_id=paper.paper_id,
        )

    def _make_blob_name(self, paper: FetchedPaperMetadata, extension: str) -> str:
        doi = paper.metadata.get("doi")
        if doi:
            base_name = doi.replace("/", "_")
        else:
            base_name = paper.title.lower().replace(" ", "_").replace("/", "_")[:100]

        return f"uploads/{base_name}.{extension}"
