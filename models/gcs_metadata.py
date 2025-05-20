# models/gcs_metadata.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class GCSMetadata:
    gcs_uri: str
    blob_name: str
    bucket_name: str