from datetime import datetime
from pathlib import Path
from typing import List

from extraction_configs.patient_engagement_config import build_patient_engagement_config
from extractors.vertex_gemini_extractor import VertexGeminiExtractor
from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from ingestors.remote_gcs_paper_ingestor import RemoteGCSPaperIngestor
from models.extraction_config import ExtractionConfig
from models.paper_metadata import FetchedPaperMetadata
from pipelines.pipeline import Pipeline
from writers.gcs_writer import GCSWriter
from writers.local_file_writer import LocalFileWriter

MAX_PAPERS = 50
LOCAL_WRITE = True  # Write to local directory or gcs.


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
        arxiv_query = (
            '"large language model" OR LLM OR "machine learning" OR AI '
            "AND (patient OR diagnosis OR treatment OR healthcare)"
        )

        arxiv_fetcher = ArxivFetcher(max_results=MAX_PAPERS, validate_pdf=True)
        papers: List[FetchedPaperMetadata] = fetcher.fetch(
            self.query
        ) + arxiv_fetcher.fetch(arxiv_query)

        # Step 2: Ingest to GCS
        ingestor = RemoteGCSPaperIngestor(papers=papers)
        documents = ingestor.ingest()

        if not documents:
            return

        # Step 3: Extract content in batch
        config: ExtractionConfig = build_patient_engagement_config()
        extractor = VertexGeminiExtractor()
        extracted_data_list = extractor.extract(documents, config)

        # Step 4: Save extracted results to documents/extracted_text/pubmed_search + run timestamp
        if LOCAL_WRITE:
            writer = LocalFileWriter(
                base_output_dir="documents/extracted_text/combined_search/"
            )
            writer.write(extracted_data_list)
        else:
            writer = GCSWriter(prefix="extracted_text/pubmed_search")
            writer.write(extracted_data_list)
