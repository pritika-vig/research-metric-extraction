# models/extracted_document_data.py

from dataclasses import dataclass, field
from typing import List, Optional

from models.paper_id import PaperId


@dataclass
class ExtractedField:
    name: str
    description: str
    value: Optional[str] = None
    evidence_quote: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class ExtractedDocumentData:
    paper_id: PaperId
    paper_title: str
    paper_gc_uri: str
    source_url: str
    fields: List[ExtractedField] = field(default_factory=list)

    def get_field_value(self, field_name: str) -> Optional[str]:
        for f in self.fields:
            if f.name == field_name:
                return f.value
        return None

    def get_paper_id(self) -> Optional[str]:
        return self.paper_id.get_canonical_id() if self.paper_id else None

    def __repr__(self):
        field_summaries = "\n  ".join(
            f"{f.name}: {f.value or 'N/A'} (Evidence: {f.evidence_quote or 'N/A'}, Page: {f.page_number or 'N/A'})"
            for f in self.fields
        )
        return f"<ExtractedDocumentData for {self.paper_id.get_canonical_id()}>\n  {field_summaries}"
