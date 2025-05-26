import unittest
from unittest.mock import MagicMock, patch

from fetchers.arxiv_fetcher import ArxivFetcher
from models.paper_metadata import FetchedPaperMetadata

SAMPLE_ARXIV_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1234.56789v1</id>
    <title> Sample Title </title>
    <author>
      <name>John Doe</name>
    </author>
    <author>
      <name>Jane Smith</name>
    </author>
    <link rel="alternate" type="text/html" href="http://arxiv.org/abs/1234.56789v1"/>
    <link title="pdf" rel="related" type="application/pdf" href="http://arxiv.org/pdf/1234.56789v1"/>
  </entry>
</feed>
"""


class TestArxivFetcher(unittest.TestCase):
    @patch("fetchers.arxiv_fetcher.requests.get")
    @patch.object(ArxivFetcher, "_validate_pdf_url", return_value=True)
    def test_fetch_successful(self, mock_validate_pdf, mock_requests_get):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_ARXIV_RESPONSE
        mock_requests_get.return_value = mock_response

        fetcher = ArxivFetcher(validate_pdf=True)

        # Act
        results = fetcher.fetch("quantum computing")

        # Assert
        self.assertEqual(len(results), 1)
        paper = results[0]
        self.assertIsInstance(paper, FetchedPaperMetadata)
        self.assertEqual(paper.title, "Sample Title")
        self.assertIn("John Doe", paper.authors)
        self.assertIn("Jane Smith", paper.authors)
        self.assertEqual(paper.url, "http://arxiv.org/pdf/1234.56789v1")
        self.assertEqual(paper.format, "pdf")
        self.assertEqual(paper.paper_id.arxiv_id, "1234.56789v1")

        # Ensure the validator was called
        mock_validate_pdf.assert_called_once_with("http://arxiv.org/pdf/1234.56789v1")


if __name__ == "__main__":
    unittest.main()
