from abc import ABC, abstractmethod
from typing import List
from models.document import Document

class Ingestor(ABC):
    @abstractmethod
    def ingest(self, directory_path: str) -> List[Document]:
        """
        Ingest documents from a directory.

        Args:
            directory_path (str): Path to the directory containing files.

        Returns:
            List[Document]: A list of Document objects.
        """
        pass