# models/gcs_metadata.py

from dataclasses import dataclass


@dataclass
class GCSMetadata:
    gcs_uri: str
    blob_name: str
    bucket_name: str
    format: str  # e.g. "pdf", "html"
