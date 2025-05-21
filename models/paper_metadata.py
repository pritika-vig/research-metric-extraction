from dataclasses import dataclass
from typing import Any, Dict, List

from models.paper_id import PaperId


# Metadata model for found papers
@dataclass
class FetchedPaperMetadata:
    paper_id: PaperId
    title: str
    authors: List[str]
    url: str  # This can be either a PDF or HTML article URL
    format: str  # 'pdf' or 'html'
    metadata: Dict[str, Any]  # Additional info like journal, date, etc.
