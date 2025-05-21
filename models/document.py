from pathlib import Path
from typing import Optional

from models.gcs_metadata import GCSMetadata
from models.paper_id import PaperId


class Document:
    def __init__(
        self,
        file_path: Path,
        file_bytes: Optional[bytes] = None,
        grobid_response: Optional[str] = None,
        parsed_text: Optional[str] = None,
        gcs_metadata: Optional[GCSMetadata] = None,
        paper_id: Optional[PaperId] = None,
    ):
        self.paper_id = paper_id
        self.file_path = file_path

        # Field specific to GROBID ingestor
        self.grobid_response = grobid_response
        self.file_bytes = file_bytes
        self.parsed_text = parsed_text

        # Metadata specific to Google Cloud Storage
        self.gcs_metadata = gcs_metadata

    def __repr__(self):
        base = f"<Document {self.file_path.name}"
        if self.paper_id:
            try:
                base += f" ({self.paper_id.get_canonical_id()})"
            except ValueError:
                pass
        return base + ">"
