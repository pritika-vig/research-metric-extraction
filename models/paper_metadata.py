from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# Metadata model for found papers
@dataclass
class PaperMetadata:
    id: str
    title: str
    authors: List[str]
    pdf_url: Optional[str]
    metadata: Dict[str, Any]  # Additional info like journal, date, etc.
