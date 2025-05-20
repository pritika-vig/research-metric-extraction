from pathlib import Path
from typing import Optional
from models.gcs_metadata import GCSMetadata

class Document:
    def __init__(
        self, 
        file_path: Path, 
        file_bytes: Optional[bytes] = None,
        grobid_response: Optional[str] = None,
        parsed_text: Optional[str] = None,
        gcs_metadata: Optional[GCSMetadata] = None 
    ):
        self.file_path = file_path

        # Field specific to GROBID ingestor
        self.grobid_response = grobid_response
        self.file_bytes = file_bytes
        self.parsed_text = parsed_text

        # Field specific to GCS ingestor
        self.gcs_metadata = gcs_metadata

    def __repr__(self):
        return f"<Document {self.file_path.name}>"