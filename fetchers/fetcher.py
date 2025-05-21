from abc import ABC, abstractmethod
from typing import List

from models.paper_metadata import FetchedPaperMetadata


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, query: str) -> List[FetchedPaperMetadata]:
        """Fetch paper metadata based on a search query."""
        pass
