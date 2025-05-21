# tests/test_pubmed_fetcher.py
from unittest.mock import MagicMock, patch

from fetchers.pubmed_fetcher import PubMedFetcher

# XML string for efetch (PMC article metadata)
EFETCH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
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
    <self-uri content-type="pdf" xlink:href="/pmc/articles/PMC123456/pdf/nihms123456.pdf" />
</article>
"""


@patch("fetchers.pubmed_fetcher.requests.get")
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
    assert (
        results[0].url
        == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/nihms123456.pdf"
    )
    assert results[0].format == "pdf"


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
    assert results[0].format == "pdf"


@patch("fetchers.pubmed_fetcher.Entrez.esearch", side_effect=Exception("Entrez failed"))
def test_entrez_failure(mock_esearch):
    """Handles Entrez failure gracefully by returning empty list."""
    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("failure case")
    assert results == []


@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_missing_pdf_link_uses_html_fallback(mock_esearch, mock_efetch, mock_read):
    """Falls back to HTML article link if PDF self-uri is not found in XML."""
    no_pdf_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <article>
        <front>
            <article-meta>
                <title-group>
                    <article-title>No PDF Paper</article-title>
                </title-group>
                <contrib-group>
                    <contrib contrib-type="author">
                        <name>
                            <surname>Smith</surname>
                            <given-names>Jane</given-names>
                        </name>
                    </contrib>
                </contrib-group>
            </article-meta>
        </front>
    </article>"""

    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["654321"]}
    mock_efetch.return_value.__enter__.return_value.read.return_value = no_pdf_xml

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=False)
    results = fetcher.fetch("no-pdf")

    assert len(results) == 1
    assert results[0].title == "No PDF Paper"
    assert results[0].authors == ["Smith, Jane"]
    assert results[0].url == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC654321/"
    assert results[0].format == "html"


@patch("fetchers.pubmed_fetcher.requests.get")
@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_fallback_to_valid_html_when_pdf_invalid(
    mock_esearch, mock_efetch, mock_read, mock_head
):
    """Falls back to HTML if PDF is invalid but HTML is valid."""
    no_pdf_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <article xmlns:xlink="http://www.w3.org/1999/xlink">
        <front>
            <article-meta>
                <title-group>
                    <article-title>Fallback HTML Paper</article-title>
                </title-group>
                <contrib-group>
                    <contrib contrib-type="author">
                        <name>
                            <surname>Lee</surname>
                            <given-names>Ada</given-names>
                        </name>
                    </contrib>
                </contrib-group>
            </article-meta>
        </front>
        <self-uri content-type="pdf" xlink:href="/pmc/articles/PMC789012/pdf/nihms789012.pdf" />
    </article>"""

    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["789012"]}
    mock_efetch.return_value.__enter__.return_value.read.return_value = no_pdf_xml

    def mock_head_side_effect(url, *args, **kwargs):
        mock_resp = MagicMock()
        if url.endswith(".pdf"):
            mock_resp.status_code = 404
            mock_resp.headers = {"Content-Type": "text/html"}
        else:
            mock_resp.status_code = 200
            mock_resp.headers = {"Content-Type": "text/html"}
        return mock_resp

    mock_head.side_effect = mock_head_side_effect

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("fallback-html")

    assert len(results) == 1
    paper = results[0]
    assert paper.title == "Fallback HTML Paper"
    assert paper.authors == ["Lee, Ada"]
    assert paper.url == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC789012/"
    assert paper.format == "html"


@patch("fetchers.pubmed_fetcher.requests.get")
@patch("fetchers.pubmed_fetcher.Entrez.read")
@patch("fetchers.pubmed_fetcher.Entrez.efetch")
@patch("fetchers.pubmed_fetcher.Entrez.esearch")
def test_skip_if_both_pdf_and_html_invalid(
    mock_esearch, mock_efetch, mock_read, mock_head
):
    """Skips document if both PDF and HTML are invalid/unreachable."""
    no_pdf_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <article xmlns:xlink="http://www.w3.org/1999/xlink">
        <front>
            <article-meta>
                <title-group>
                    <article-title>Unreachable Paper</article-title>
                </title-group>
                <contrib-group>
                    <contrib contrib-type="author">
                        <name>
                            <surname>Nguyen</surname>
                            <given-names>Pat</given-names>
                        </name>
                    </contrib>
                </contrib-group>
            </article-meta>
        </front>
        <self-uri content-type="pdf" xlink:href="/pmc/articles/PMC111222/pdf/bad.pdf" />
    </article>"""

    mock_esearch.return_value.__enter__.return_value = MagicMock()
    mock_read.return_value = {"IdList": ["111222"]}
    mock_efetch.return_value.__enter__.return_value.read.return_value = no_pdf_xml

    # Both PDF and HTML return bad headers
    def mock_head_side_effect(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.headers = {"Content-Type": "text/html"}
        return mock_resp

    mock_head.side_effect = mock_head_side_effect

    fetcher = PubMedFetcher(email="test@example.com", validate_pdf=True)
    results = fetcher.fetch("fail-both")

    assert results == []
