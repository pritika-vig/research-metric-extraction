# tests/local_pdf_ingestor_test.py

import os
import tempfile
import unittest

import fitz  # PyMuPDF

from ingestors.local_pdf_ingestor import LocalPDFIngestor


class TestLocalPDFIngestor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def _create_pdf(self, filename, left_texts, right_texts=None):
        """Helper to create a simple single or two-column PDF."""
        path = os.path.join(self.test_dir.name, filename)
        doc = fitz.open()
        page = doc.new_page()

        y = 72  # start at 1 inch down

        # Left column
        for text in left_texts:
            page.insert_text((72, y), text)
            y += 20

        if right_texts:
            y = 72
            for text in right_texts:
                page.insert_text((300, y), text)
                y += 20

        doc.save(path)
        doc.close()
        return path

    def _get_document_text(self, docs, filename):
        """Helper to find a Document by filename and return its parsed_text."""
        for doc in docs:
            if doc.file_path.name == filename:
                return doc.parsed_text
        raise AssertionError(f"Document {filename} not found in results")

    def test_ingest_single_column_pdf(self):
        self._create_pdf("single_column.pdf", ["Line 1", "Line 2", "Line 3"])

        ingestor = LocalPDFIngestor()
        result = ingestor.ingest(self.test_dir.name)

        text = self._get_document_text(result, "single_column.pdf")
        self.assertIn("Line 1", text)
        self.assertIn("Line 2", text)
        self.assertIn("Line 3", text)

    def test_ingest_two_column_pdf(self):
        self._create_pdf(
            "two_column.pdf",
            left_texts=["Left 1", "Left 2"],
            right_texts=["Right 1", "Right 2"],
        )

        ingestor = LocalPDFIngestor()
        result = ingestor.ingest(self.test_dir.name)

        text = self._get_document_text(result, "two_column.pdf")
        self.assertIn("Left 1", text)
        self.assertIn("Left 2", text)
        self.assertIn("Right 1", text)
        self.assertIn("Right 2", text)

        left_index = text.find("Left 1")
        right_index = text.find("Right 1")
        self.assertLess(
            left_index, right_index, "Left column should come before right column"
        )

    def test_ingest_mixed_column_pdf(self):
        self._create_pdf(
            "mixed_column.pdf",
            left_texts=["Intro Paragraph", "Left Body"],
            right_texts=["Right Body"],
        )

        ingestor = LocalPDFIngestor()
        result = ingestor.ingest(self.test_dir.name)

        text = self._get_document_text(result, "mixed_column.pdf")
        self.assertIn("Intro Paragraph", text)
        self.assertIn("Left Body", text)
        self.assertIn("Right Body", text)

        intro_index = text.find("Intro Paragraph")
        left_index = text.find("Left Body")
        right_index = text.find("Right Body")

        self.assertLess(intro_index, left_index)
        self.assertLess(left_index, right_index)


if __name__ == "__main__":
    unittest.main()
