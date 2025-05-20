# extractors/extractor.py

from abc import ABC, abstractmethod

from models.document import Document
from models.extracted_document_data import ExtractedDocumentData
from models.extraction_config import ExtractionConfig


class Extractor(ABC):
    @abstractmethod
    def extract(
        self, document: Document, config: ExtractionConfig
    ) -> ExtractedDocumentData:
        """
        Extract structured data from a document according to a config.

        Args:
            document (Document): The source document
            config (ExtractionConfig): Fields to extract and how

        Returns:
            ExtractedDocumentData: Structured output
        """
        pass
