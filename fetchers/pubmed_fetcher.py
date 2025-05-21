import logging
import xml.etree.ElementTree as ET
from typing import List, Optional

import requests
from Bio import Entrez

from fetchers.fetcher import Fetcher
from models.paper_metadata import FetchedPaperMetadata

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PubMedFetcher(Fetcher):
    def __init__(self, email: str, max_results: int = 20, validate_pdf: bool = True):
        Entrez.email = email
        self.max_results = max_results
        self.validate_pdf = validate_pdf

    def fetch(self, query: str) -> List[FetchedPaperMetadata]:
        try:
            pmc_ids = self._search_pmc(query)
        except Exception as e:
            logger.warning(f"Entrez search failed: {e}")
            return []

        papers = []
        for pmc_id in pmc_ids:
            try:
                metadata = self._fetch_metadata(pmc_id)
                if metadata:
                    papers.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to process PMC{pmc_id}: {e}")

        return papers

    def _search_pmc(self, query: str) -> List[str]:
        logger.info(f"Searching PubMed Central for query: '{query}'")
        with Entrez.esearch(db="pmc", term=query, retmax=self.max_results) as handle:
            search_results = Entrez.read(handle)
        pmc_ids = search_results.get("IdList", [])
        logger.info(f"Found {len(pmc_ids)} results")
        return pmc_ids

    def _fetch_metadata(self, pmc_id: str) -> Optional[FetchedPaperMetadata]:
        with Entrez.efetch(db="pmc", id=pmc_id, retmode="xml") as handle:
            xml_data = handle.read()

        root = ET.fromstring(xml_data)

        title = self._extract_title(root)
        authors = self._extract_authors(root)

        # Try to find PDF
        pdf_url = self._extract_pdf_url_from_xml(root)
        if pdf_url:
            if not self.validate_pdf or self._validate_pdf_url(pdf_url):
                return self._make_metadata(pmc_id, title, authors, pdf_url, "pdf")
            else:
                logger.info(f"Invalid PDF URL for PMC{pmc_id}, trying HTML instead.")

        # Fallback to HTML
        html_url = self._construct_html_url(pmc_id)
        logger.info(
            f"No PDF found for PMC{pmc_id}, using HTML link instead: {html_url}"
        )

        if not self.validate_pdf or self._validate_html_url(html_url):
            return self._make_metadata(pmc_id, title, authors, html_url, "html")
        else:
            logger.info(f"Invalid HTML URL for PMC{pmc_id}, {html_url}; skipping.")
            return None

    def _make_metadata(
        self,
        pmc_id: str,
        title: str,
        authors: List[str],
        url: str,
        format_type: str,
    ) -> FetchedPaperMetadata:
        return FetchedPaperMetadata(
            id=pmc_id,
            title=title,
            authors=authors,
            url=url,
            format=format_type,
            metadata={
                "source": "pmc",
                "pmc_id": pmc_id,
            },
        )

    def _extract_title(self, root: ET.Element) -> str:
        elem = root.find(".//article-title")
        return elem.text.strip() if elem is not None else "Untitled"

    def _extract_authors(self, root: ET.Element) -> List[str]:
        authors = []
        for contrib in root.findall(".//contrib[@contrib-type='author']"):
            surname = contrib.findtext("name/surname", default="")
            given_names = contrib.findtext("name/given-names", default="")
            full_name = f"{surname}, {given_names}".strip(", ")
            if full_name:
                authors.append(full_name)
        return authors

    def _extract_pdf_url_from_xml(self, root: ET.Element) -> Optional[str]:
        ns = {"xlink": "http://www.w3.org/1999/xlink"}
        for elem in root.findall(".//self-uri", namespaces=ns):
            if elem.attrib.get("content-type") == "pdf":
                href = elem.attrib.get("{http://www.w3.org/1999/xlink}href")
                if href:
                    if href.startswith("/"):
                        return f"https://www.ncbi.nlm.nih.gov{href}"
                    elif href.startswith("http"):
                        return href
        return None

    def _construct_html_url(self, pmc_id: str) -> str:
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/"

    def _validate_pdf_url(self, url: str) -> bool:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=5)
            content_type = response.headers.get("Content-Type", "").lower()
            logger.debug(
                f"GET {url} → {response.status_code}, Content-Type: {content_type}"
            )
            return response.status_code == 200 and "pdf" in content_type
        except requests.RequestException as e:
            logger.warning(f"PDF validation failed for {url}: {e}")
            return False

    def _validate_html_url(self, url: str) -> bool:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=5)
            logger.debug(
                f"GET {url} → {response.status_code}, Content-Type: {response.headers.get('Content-Type')}"
            )
            return (
                response.status_code == 200
                and "html" in response.headers.get("Content-Type", "").lower()
            )
        except requests.RequestException as e:
            logger.warning(f"HTML validation failed for {url}: {e}")
            return False
