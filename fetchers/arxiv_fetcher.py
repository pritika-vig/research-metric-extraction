import logging
import xml.etree.ElementTree as ET
from typing import List, Optional

import requests

from fetchers.fetcher import Fetcher
from models.paper_id import PaperId
from models.paper_metadata import FetchedPaperMetadata

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ArxivFetcher(Fetcher):
    def __init__(self, max_results: int = 20, validate_pdf: bool = True):
        self.max_results = max_results
        self.validate_pdf = validate_pdf

    def fetch(self, query: str) -> List[FetchedPaperMetadata]:
        try:
            xml_data = self._search_arxiv(query)
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
            return []

        root = ET.fromstring(xml_data)
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        logger.info(f"Found {len(entries)} entries for query '{query}'")

        papers = []
        for entry in entries:
            try:
                metadata = self._parse_entry(entry)
                if metadata:
                    papers.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to parse arXiv entry: {e}")

        return papers

    def _search_arxiv(self, query: str) -> str:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{query}&start=0&max_results={self.max_results}"
        )
        logger.info(f"Querying arXiv: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def _parse_entry(self, entry: ET.Element) -> Optional[FetchedPaperMetadata]:
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns)
            if name is not None:
                authors.append(name.text.strip())

        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib["href"]
                break

        if pdf_url and (not self.validate_pdf or self._validate_pdf_url(pdf_url)):
            return self._make_metadata(arxiv_id, title, authors, pdf_url, "pdf")

        logger.info(f"No valid PDF for arXiv:{arxiv_id}, skipping.")
        return None

    def _make_metadata(
        self,
        arxiv_id: str,
        title: str,
        authors: List[str],
        url: str,
        format_type: str,
    ) -> FetchedPaperMetadata:
        paper_id = PaperId(arxiv_id=arxiv_id)
        return FetchedPaperMetadata(
            paper_id=paper_id,
            title=title,
            authors=authors,
            url=url,
            format=format_type,
            metadata={"source": "arxiv", "arxiv_id": arxiv_id},
        )

    def _validate_pdf_url(self, url: str) -> bool:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        try:
            response = requests.head(url, headers=headers, timeout=5)
            content_type = response.headers.get("Content-Type", "").lower()
            return response.status_code == 200 and "pdf" in content_type
        except requests.RequestException as e:
            logger.warning(f"PDF validation failed for {url}: {e}")
            return False
