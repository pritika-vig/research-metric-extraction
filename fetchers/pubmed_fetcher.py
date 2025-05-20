import logging
import xml.etree.ElementTree as ET
from typing import List, Optional

import requests
from Bio import Entrez

from fetchers.fetcher import Fetcher
from models.paper_metadata import PaperMetadata

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PubMedFetcher(Fetcher):
    def __init__(self, email: str, max_results: int = 20, validate_pdf: bool = True):
        Entrez.email = email
        self.max_results = max_results
        self.validate_pdf = validate_pdf

    def fetch(self, query: str) -> List[PaperMetadata]:
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
        """Searches PMC for the query and returns a list of PMC IDs."""
        logger.info(f"Searching PubMed Central for query: '{query}'")
        with Entrez.esearch(db="pmc", term=query, retmax=self.max_results) as handle:
            search_results = Entrez.read(handle)
        pmc_ids = search_results.get("IdList", [])
        logger.info(f"Found {len(pmc_ids)} results")
        return pmc_ids

    def _fetch_metadata(self, pmc_id: str) -> Optional[PaperMetadata]:
        """Fetches metadata and constructs a PaperMetadata object."""
        with Entrez.efetch(db="pmc", id=pmc_id, retmode="xml") as handle:
            xml_data = handle.read()

        root = ET.fromstring(xml_data)

        title = self._extract_title(root)
        authors = self._extract_authors(root)
        pdf_url = self._construct_pdf_url(pmc_id)

        if self.validate_pdf and not self._validate_pdf_url(pdf_url):
            logger.info(f"No valid PDF found for PMC{pmc_id}; skipping.")
            return None

        return PaperMetadata(
            id=pmc_id,
            title=title,
            authors=authors,
            pdf_url=pdf_url,
            metadata={"source": "PubMed", "pmc_id": pmc_id},
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

    def _construct_pdf_url(self, pmc_id: str) -> str:
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"

    def _validate_pdf_url(self, url: str) -> bool:
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            return (
                response.status_code == 200
                and "application/pdf" in response.headers.get("Content-Type", "")
            )
        except requests.RequestException as e:
            logger.warning(f"PDF validation failed for {url}: {e}")
            return False
