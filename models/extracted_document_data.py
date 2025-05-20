# models/extracted_document_data.py

from dataclasses import dataclass
from models.document import Document
from typing import Optional, List

@dataclass
@dataclass
class ExtractedField:
    name: str
    description: str
    value: Optional[str] = None
    evidence_quote: Optional[str] = None
    page_number: Optional[int] = None

class ExtractedDocumentData:
    def __init__(self, document: Document, fields: List[ExtractedField]):
        self.document = document
        self.fields = fields

    def get_field_value(self, field_name: str) -> Optional[str]:
        for field in self.fields:
            if field.name == field_name:
                return field.value
        return None

    def __repr__(self):
        field_summaries = "\n  ".join(
            f"{f.name}: {f.value or 'N/A'} (Evidence: {f.evidence_quote or 'N/A'}, Page: {f.page_number or 'N/A'})"
            for f in self.fields
        )
        return f"<ExtractedDocumentData for {self.document.file_path.name}>\n  {field_summaries}"
