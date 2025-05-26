import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import List

from google.cloud import storage

from models.extracted_document_data import ExtractedDocumentData


class GCSWriter:
    def __init__(self, prefix: str = "extracted_text/pubmed_search"):
        self.bucket_name = os.getenv("GCS_BUCKET")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")

        if not self.bucket_name or not self.project_id:
            raise ValueError(
                "GCS_BUCKET and GCP_PROJECT_ID must be set in environment variables."
            )

        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_prefix = f"{prefix}/{timestamp}"

    def write(self, extracted_documents: List[ExtractedDocumentData]) -> None:
        for extracted_doc in extracted_documents:
            paper_id = extracted_doc.get_paper_id()
            if not paper_id:
                print("Skipping document with missing paper_id.")
                continue

            blob_name = f"{self.output_prefix}/{paper_id}.json"
            doc_dict = asdict(extracted_doc)
            json_str = json.dumps(doc_dict, indent=2)

            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(json_str, content_type="application/json")

            print(f"Uploaded extracted data to: gs://{self.bucket_name}/{blob_name}")
