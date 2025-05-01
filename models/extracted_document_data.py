# models/extracted_document_data.py

from models.document import Document
from typing import Optional, List

class ExtractedField:
    def __init__(self, name: str, description: str, value: Optional[str] = None):
        self.name = name
        self.description = description
        self.value = value

    def __repr__(self):
        return f"{self.name}: {self.value or 'N/A'}"

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
        return f"<ExtractedDocumentData for {self.document.file_path.name}>"