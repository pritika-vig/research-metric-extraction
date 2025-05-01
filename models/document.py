from pathlib import Path
from typing import Optional

class Document:
    def __init__(
        self, 
        file_path: Path, 
        file_bytes: Optional[bytes] = None,
        grobid_response: Optional[str] = None,
        parsed_text: Optional[str] = None
    ):
        self.file_path = file_path
        self.file_bytes = file_bytes
        self.grobid_response = grobid_response
        self.parsed_text = parsed_text

    def __repr__(self):
        return f"<Document {self.file_path.name}>"