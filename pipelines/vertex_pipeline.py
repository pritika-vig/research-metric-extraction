# pipeline/vertex_pipeline.py

import json
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

from pipelines.pipeline import Pipeline
from models.extraction_config import ExtractionConfig
from models.extraction_field_spec import ExtractionFieldSpec
from ingestors.vertex_gcs_pdf_ingestor import VertexGcsPDFIngestor
from extractors.vertex_gemini_extractor import VertexGeminiExtractor

class VertexPipeline(Pipeline):
    def build_config(self) -> ExtractionConfig:
        return ExtractionConfig(
            name="Patient Engagement Paper Analysis",
            fields = [
                ExtractionFieldSpec("Title", "Full title of the study as stated in the paper"),
                ExtractionFieldSpec("Author(s)", "List of all authors involved in the paper, in order of appearance"),
                ExtractionFieldSpec("Patient Co-authors", "Were any co-authors identified as patients or caregivers?"),
                ExtractionFieldSpec("Journal", "Name of the journal where the study was published"),
                ExtractionFieldSpec("Publication Stage", "Indicate if the paper is peer-reviewed, a preprint, or another stage"),
                ExtractionFieldSpec("Publication Date", "Official date the paper was published"),
                ExtractionFieldSpec("Field of Study", "Disciplinary or clinical field, such as primary care, oncology, or public health"),
                ExtractionFieldSpec("Country", "Country or countries where the study was conducted or primarily situated"),
                ExtractionFieldSpec("Type of Article", "Classify the article: original research, protocol, review, commentary, etc."),
                ExtractionFieldSpec("Aim of Study", "State the main purpose or objective of the study as described by the authors"),
                ExtractionFieldSpec("Key Findings", "Summarize the main results or conclusions of the study"),
                ExtractionFieldSpec("Patient/Public Engagement (Y/N)",
                                    "Does the study report any involvement of patients or the public? This includes participation, feedback, consultation, or co-design."),
                ExtractionFieldSpec("Type of Engagement (Montreal Model continuum)",
                                    "Categorize engagement based on the Montreal Model: Information, Consultation, Collaboration, or Partnership."),
                ExtractionFieldSpec("Evaluation of Impact (Y/N)",
                                    "Did the study evaluate or measure the effect of patient/public engagement?"),
                ExtractionFieldSpec("Type of Evaluation",
                                    "What type of method or framework was used to evaluate the impact of engagement (e.g., metrics, qualitative feedback, evaluation framework)?"),
                ExtractionFieldSpec("Impact of Engagement",
                                    "Describe any outcomes or changes attributed to patient/public engagement (e.g., design changes, improved recruitment, insights)."),
                ExtractionFieldSpec("Participatory Process",
                                    "Did the study include a participatory design process such as workshops, co-design, or stakeholder sessions?"),
                ExtractionFieldSpec("Continuous Evaluation Cycles",
                                    "Was engagement conducted iteratively or cyclically, with feedback loops or repeated interaction?"),
                ExtractionFieldSpec("Implementation",
                                    "Did patient/public engagement influence the implementation strategy or process of the research?"),
                ExtractionFieldSpec("Organization of Health Care",
                                    "Did engagement lead to reported changes in health care delivery, systems design, or institutional practice?"),
                ExtractionFieldSpec("Persuasive Design Techniques",
                                    "Were behavior-change strategies or persuasive technologies mentioned (e.g., nudges, gamification, reminders)?"),
                ExtractionFieldSpec("Assess Impact",
                                    "Did the study measure outcomes or success metrics related specifically to engagement efforts?"),
                ExtractionFieldSpec("Information",
                                    "Was information passively provided to patients or the public without requesting feedback or participation?"),
                ExtractionFieldSpec("Consultation",
                                    "Was patient or public input sought (e.g., through interviews, surveys, focus groups), without involving them in decision-making?"),
                ExtractionFieldSpec("Collaboration",
                                    "Was there shared decision-making or co-design between researchers and participants in any phase of the study?"),
                ExtractionFieldSpec("Partnership",
                                    "Were patients/public involved across all stages with formal roles (e.g., co-authors, advisory board, project governance)?"),
            ]
        )

    def run(self) -> None:
        input_dir = Path("documents/")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"documents/extracted_text/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)

        config = self.build_config()
        ingestor = VertexGcsPDFIngestor()
        extractor = VertexGeminiExtractor()

        documents = ingestor.ingest(str(input_dir))

        for doc in documents:
            print(f"🔍 Extracting fields from: {doc.file_path.name}")
            extracted_data = extractor.extract(doc, config)
            print(f"✅ Extracted {len(extracted_data.fields)} fields from: {doc.file_path.name}")
            for f in extracted_data.fields:
                print(f"  - {f.name}: {f.value} \n {f.evidence_quote} (Page {f.page_number})")

            output_path = output_dir / f"{doc.file_path.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "source_file": str(doc.file_path),
                    "fields": [asdict(field) for field in extracted_data.fields]
                    }, f, indent=2)

            print(f"✅ Saved extracted data to: {output_path}")