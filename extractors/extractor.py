from abc import ABC, abstractmethod
from models.document import Document
from models.extracted_document_data import ExtractedDocumentData

class Extractor(ABC):
    @abstractmethod
    def extract(self, document: Document) -> ExtractedDocumentData:
        """
        Extract structured properties from a document.

        Args:
            document (Document): The parsed PDF document.

        Returns:
            ExtractedDocumentData: Extracted information about the paper.
        """
        pass
