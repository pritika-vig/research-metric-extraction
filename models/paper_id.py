from dataclasses import dataclass
from typing import Optional


@dataclass
class PaperId:
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmcid: Optional[str] = None
    pmid: Optional[str] = None

    def get_canonical_id(self) -> str:
        """Returns the preferred unique identifier, prioritizing DOI > arXiv > PMCID > PMID."""
        if self.doi:
            return self.doi
        if self.arxiv_id:
            return f"arXiv:{self.arxiv_id}"
        if self.pmcid:
            return self.pmcid
        if self.pmid:
            return f"PMID:{self.pmid}"
        raise ValueError("No valid paper identifier available.")
