# ingestors/local_pdf_ingestor.py

import logging
from pathlib import Path
from typing import List

import pdfplumber

from ingestors.ingestor import Ingestor
from models.document import Document

logger = logging.getLogger(__name__)


class LocalPDFIngestor(Ingestor):
    """
    Ingest PDFs from a local directory.
    Handles multi-column PDFs such as journal articles.
    """

    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)

    def ingest(self) -> List[Document]:
        if not self.directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory_path}")
        if not self.directory_path.is_dir():
            raise NotADirectoryError(
                f"Specified path is not a directory: {self.directory_path}"
            )

        documents: List[Document] = []

        for file_path in self.directory_path.glob("*.pdf"):
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                parsed_text = self._extract_text_from_pdf(file_path)
                documents.append(
                    Document(
                        file_path=file_path,
                        file_bytes=file_bytes,
                        parsed_text=parsed_text,
                        grobid_response=None,
                    )
                )
                logger.info(f"Successfully ingested {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to ingest {file_path.name}: {e}")

        return documents

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract and reorder text from a PDF file."""
        full_left_text = []
        full_right_text = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                width = page.width
                center_x = width / 2

                words = page.extract_words()
                left_words = [w for w in words if w["x0"] < center_x]
                right_words = [w for w in words if w["x0"] >= center_x]

                full_left_text.extend(self._group_words_into_lines(left_words))
                full_right_text.extend(self._group_words_into_lines(right_words))

        return "\n".join(full_left_text + full_right_text)

    def _group_words_into_lines(self, words: List[dict]) -> List[str]:
        """Group nearby words into lines based on vertical position."""
        lines = []
        current_line = []
        last_top = None

        for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
            if last_top is None or abs(word["top"] - last_top) > 5:
                if current_line:
                    lines.append(" ".join(w["text"] for w in current_line))
                current_line = [word]
                last_top = word["top"]
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(w["text"] for w in current_line))

        return lines
