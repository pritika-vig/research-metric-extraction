import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

from extraction_configs.patient_engagement_config import build_patient_engagement_config
from extractors.vertex_gemini_extractor import VertexGeminiExtractor
from fetchers.pubmed_fetcher import PubMedFetcher
from ingestors.remote_gcs_paper_ingestor import RemoteGCSPaperIngestor
from models.extraction_config import ExtractionConfig
from models.paper_metadata import FetchedPaperMetadata
from pipelines.pipeline import Pipeline

# Set a cap on the number of PDFs processed per run
MAX_PAPERS = 10


class PubMedPipeline(Pipeline):
    def __init__(self, query: str, email: str):
        self.query = query
        self.email = email

    def run(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"documents/extracted_text/pubmed_search/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Fetch papers
        fetcher = PubMedFetcher(
            email=self.email, max_results=MAX_PAPERS, validate_pdf=True
        )
        papers: List[FetchedPaperMetadata] = fetcher.fetch(self.query)

        # Step 2: Ingest to GCS
        ingestor = RemoteGCSPaperIngestor(papers=papers)
        documents = ingestor.ingest()

        # Step 3: Extract content
        config: ExtractionConfig = build_patient_engagement_config()
        extractor = VertexGeminiExtractor()

        for doc in documents:
            extracted_data = extractor.extract(doc, config)

            # Step 4: Save extracted results
            safe_stem = extracted_data.get_paper_id()
            output_path = output_dir / f"{safe_stem}.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "paper_id": extracted_data.get_paper_id(),
                        "title": extracted_data.paper_title,
                        "source_pdf": extracted_data.paper_gc_uri,
                        "source_url": extracted_data.source_url,
                        "fields": [asdict(field) for field in extracted_data.fields],
                    },
                    f,
                    indent=2,
                )

            print(f"\nSaved extracted data to: {output_path}\n")
