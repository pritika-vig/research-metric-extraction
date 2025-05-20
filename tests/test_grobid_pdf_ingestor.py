# tests/test_grobid_pdf_ingestor.py

import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from ingestors.grobid_pdf_ingestor import GrobidPDFIngestor
from models.document import Document


class TestGrobidPDFIngestor(unittest.TestCase):
    @patch("ingestors.grobid_pdf_ingestor.Path.is_dir", return_value=False)
    def test_invalid_directory_raises(self, mock_is_dir):
        ingestor = GrobidPDFIngestor("/invalid/path")
        with self.assertRaises(ValueError):
            ingestor.ingest()

    @patch("ingestors.grobid_pdf_ingestor.Path.glob")
    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4")
    @patch("requests.post")
    @patch("ingestors.grobid_pdf_ingestor.Path.is_dir", return_value=True)
    def test_successful_ingestion(
        self, mock_is_dir, mock_requests_post, mock_open_file, mock_glob
    ):
        # ✅ Realistic mock TEI XML from GROBID
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Sample Research Paper</title>
                        <author><persName><forename>Jane</forename><surname>Doe</surname></persName></author>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
            <text>
                <front>
                    <abstract>
                        <p>This paper investigates something important.</p>
                    </abstract>
                </front>
                <body>
                    <div>
                        <head>Introduction</head>
                        <p>Deep learning methods have revolutionized NLP.</p>
                    </div>
                    <div>
                        <head>Methodology</head>
                        <p>We use a convolutional architecture on top of embeddings.</p>
                    </div>
                </body>
                <back>
                    <div type="references">
                        <listBibl>
                            <biblStruct>
                                <monogr>
                                    <title>NeurIPS 2020</title>
                                </monogr>
                            </biblStruct>
                        </listBibl>
                    </div>
                </back>
            </text>
        </TEI>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sample_xml
        mock_requests_post.return_value = mock_response

        mock_pdf_path = MagicMock(spec=Path)
        mock_pdf_path.name = "test.pdf"
        mock_glob.return_value = [mock_pdf_path]

        ingestor = GrobidPDFIngestor("/some/valid/path")
        documents = ingestor.ingest()

        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], Document)
        parsed_text = documents[0].parsed_text
        self.assertIn("Deep learning methods have revolutionized NLP.", parsed_text)
        self.assertIn("We use a convolutional architecture", parsed_text)
        self.assertNotIn("abstract", parsed_text.lower())
        self.assertNotIn("NeurIPS", parsed_text)  # references should be excluded

    @patch("ingestors.grobid_pdf_ingestor.Path.glob")
    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4")
    @patch("requests.post")
    @patch("ingestors.grobid_pdf_ingestor.Path.is_dir", return_value=True)
    def test_grobid_error_handling(
        self, mock_is_dir, mock_requests_post, mock_open_file, mock_glob
    ):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests_post.return_value = mock_response

        mock_pdf_path = MagicMock(spec=Path)
        mock_pdf_path.name = "test_error.pdf"
        mock_glob.return_value = [mock_pdf_path]

        ingestor = GrobidPDFIngestor("/some/valid/path")
        documents = ingestor.ingest()

        self.assertEqual(len(documents), 0)


if __name__ == "__main__":
    unittest.main()
