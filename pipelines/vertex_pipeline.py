# pipeline/vertex_pipeline.py

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from extraction_configs.patient_engagement_config import build_patient_engagement_config
from extractors.vertex_gemini_extractor import VertexGeminiExtractor
from ingestors.vertex_gcs_pdf_ingestor import VertexGcsPDFIngestor
from pipelines.pipeline import Pipeline


class VertexPipeline(Pipeline):
    def run(self) -> None:
        input_dir = Path("documents/")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"documents/extracted_text/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)

        config = build_patient_engagement_config()
        ingestor = VertexGcsPDFIngestor(str(input_dir))
        extractor = VertexGeminiExtractor()

        documents = ingestor.ingest()

        for doc in documents:
            extracted_data = extractor.extract(doc, config)
            print(
                f"Extracted {len(extracted_data.fields)} fields from: {extracted_data.get_paper_id()}"
            )
            for f in extracted_data.fields:
                print(
                    f"  - {f.name}: {f.value} \n {f.evidence_quote} (Page {f.page_number})"
                )

            output_path = output_dir / f"{extracted_data.get_paper_id()}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "document_id": str(extracted_data.get_paper_id()),
                        "fields": [asdict(field) for field in extracted_data.fields],
                    },
                    f,
                    indent=2,
                )

            print(f"Saved extracted data to: {output_path}")
