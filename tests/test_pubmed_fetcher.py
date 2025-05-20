# tests/test_pubmed_fetcher.py
from unittest.mock import MagicMock, patch

from fetchers.pubmed_fetcher import PubMedFetcher

# XML string for efetch (PMC article metadata)
EFETCH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<article>
    <front>
        <article-meta>
            <title-group>
                <article-title>Test Paper Title</article-title>
            </title-group>
            <contrib-group>
                <contrib contrib-type="author">
                    <name>
                        <surname>Doe</surname>
                        <given-names>John</given-names>
                    </name>
                </contrib>
            </contrib-group>
        </article-meta>
    </front>
</article>
"""


@patch("fetchers.pubmed_fetcher.requests.head")
@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_fetch_valid_query(mock_esearch, mock_efetch, mock_read, mock_head):
    """Returns one paper with valid metadata and PDF URL."""
    # Mock esearch and Entrez.read
    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["123456"]}

    # Mock efetch returning XML string
    mock_efetch.return_value.__enter__.return_value.read.return_value = EFETCH_XML

    # Mock PDF HEAD response
    mock_head.return_value.status_code = 200
    mock_head.return_value.headers = {"Content-Type": "application/pdf"}

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("cancer")

    assert len(results) == 1
    assert results[0].title == "Test Paper Title"
    assert results[0].authors == ["Doe, John"]
    assert results[0].pdf_url.endswith("PMC123456/pdf/")


@patch("fetchers.pubmed_fetcher.requests.head")
@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_invalid_pdf_skipped(mock_esearch, mock_efetch, mock_read, mock_head):
    """Skips paper when PDF URL is invalid (404 or wrong content-type)."""
    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["123456"]}
    mock_efetch.return_value.__enter__.return_value.read.return_value = EFETCH_XML

    mock_head.return_value.status_code = 404
    mock_head.return_value.headers = {"Content-Type": "text/html"}

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("cancer")

    assert results == []


@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_no_pdf_validation(mock_esearch, mock_efetch, mock_read):
    """Returns paper even if PDF is unreachable, when validate_pdf=False."""
    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["123456"]}
    mock_efetch.return_value.__enter__.return_value.read.return_value = EFETCH_XML

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=False)
    results = fetcher.fetch("cancer")

    assert len(results) == 1
    assert results[0].title == "Test Paper Title"


@patch("fetchers.pubmed_fetcher.Entrez.esearch", side_effect=Exception("Entrez failed"))
def test_entrez_failure(mock_esearch):
    """Handles Entrez failure gracefully by returning empty list."""
    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("failure case")
    assert results == []
