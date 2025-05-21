from dataclasses import dataclass
from typing import Any, Dict, List


# Metadata model for found papers
@dataclass
class PaperMetadata:
    id: str
    title: str
    authors: List[str]
    url: str  # This can be either a PDF or HTML article URL
    format: str  # 'pdf' or 'html'
    metadata: Dict[str, Any]  # Additional info like journal, date, etc.
