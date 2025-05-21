# extractors/extractor.py

from abc import ABC, abstractmethod
from typing import List

from models.document import Document
from models.extracted_document_data import ExtractedDocumentData
from models.extraction_config import ExtractionConfig


class Extractor(ABC):
    @abstractmethod
    def extract(
        self, documents: List[Document], config: ExtractionConfig
    ) -> List[ExtractedDocumentData]:
        """
        Extract structured data from a list of documents according to a config.

        Args:
            documents (List[Document]): Source documents
            config (ExtractionConfig): Fields to extract and how

        Returns:
            List[ExtractedDocumentData]: Structured output
        """
        pass
