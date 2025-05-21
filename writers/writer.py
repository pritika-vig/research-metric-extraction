from abc import ABC, abstractmethod
from typing import List

from models.extracted_document_data import ExtractedDocumentData


class Writer(ABC):
    @abstractmethod
    def write(self, documents: List[ExtractedDocumentData]) -> None:
        pass
