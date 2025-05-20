from abc import ABC, abstractmethod
from typing import List

from models.document import Document


class Ingestor(ABC):
    @abstractmethod
    def ingest(self) -> List[Document]:
        """Run ingestion and return a list of Documents."""
        pass
