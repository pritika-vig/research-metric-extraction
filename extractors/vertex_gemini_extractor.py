# extractors/vertex_gemini_extractor.py

import logging
import os
from typing import List

from dotenv import load_dotenv
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, Part

from extractors.extractor import Extractor
from models.document import Document
from models.extracted_document_data import ExtractedDocumentData, ExtractedField
from models.extraction_config import ExtractionConfig

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VertexGeminiExtractor(Extractor):
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")
        init(project=self.project_id, location=self.region)
        self.model = GenerativeModel("gemini-2.0-flash")

    def extract(
        self, document: Document, config: ExtractionConfig
    ) -> ExtractedDocumentData:
        if not document.gcs_metadata:
            raise ValueError(
                f"Document {getattr(document.file_path, 'name', 'unknown')} has no gcs_metadata"
            )

        gcs_uri = document.gcs_metadata.gcs_uri
        file_format = document.gcs_metadata.format

        if file_format == "pdf":
            mime_type = "application/pdf"
        elif file_format == "html":
            mime_type = "text/html"
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        prompt = self._build_prompt(config)

        result = self.model.generate_content(
            [
                prompt,
                Part.from_uri(gcs_uri, mime_type=mime_type),
            ],
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 4096,
            },
        )
        response_text = result.text.strip()
        logger.info(f"Gemini raw response:\n{response_text}")
        fields = self._parse_response(response_text, config)
        return ExtractedDocumentData(document=document, fields=fields)

    def _build_prompt(self, config: ExtractionConfig) -> str:
        field_defs = "\n".join(
            [f'- "{f.name}": {f.description}' for f in config.fields]
        )

        output_format = "\n".join(
            [
                f"{f.name}:\n  value: ...\n  evidence_quote: ...\n  page_number: ..."
                for f in config.fields
            ]
        )

        example_block = """
            ### Example:

            Title:
                value: AI for Patient Outcomes
                evidence_quote: "This study, titled 'AI for Patient Outcomes', explores the use of
                artificial intelligence to enhance recovery metrics."
                page_number: 1

            Patient Co-authors:
                value: Yes
                evidence_quote: "The research team included two patient advocates as co-authors
                to ensure relevance and inclusivity."
                page_number: 2

            Type of Engagement (Montreal Model continuum):
                value: Collaboration
                evidence_quote: "Patients collaborated with developers during the design and testing of the AI model."
                page_number: 3

            Impact of Engagement:
                value: Improved system usability
                evidence_quote: "User feedback from patients helped refine the interface
                and increased adoption rates."
                page_number: 4
        """

        return (
            "You are analyzing a scientific research paper related to AI tools in healthcare.\n\n"
            "Your task is to extract information about how patient or public "
            "engagement was reported in the study, "
            "following key principles from the Montreal Model and the Holistic E-Health Framework.\n\n"
            "The evidence will be used by a human reviewer to validate what you extract.\n\n"
            "Extract **each of the following fields**, providing:\n"
            "- The value\n"
            "- A **direct quote** from the paper that supports the value (or 'N/A' if none)\n"
            "- The **page number** where that quote appears (or 'N/A')\n\n"
            "### Example (strict format):\n"
            f"{example_block}\n\n"
            "### Respond using **exactly this format**. Do NOT use JSON or any other format:\n"
            f"{output_format}\n\n"
            "### Field Definitions:\n"
            f"{field_defs}\n\n"
            "Strictly follow the format above. Your output will be parsed by a program. Do not change formatting."
        )

    def _parse_response(
        self, response: str, config: ExtractionConfig
    ) -> List[ExtractedField]:
        extracted_fields = []
        field_map = {f.name.lower(): f for f in config.fields}

        current_field = None
        field_data = {}

        lines = response.splitlines()

        for line in lines:
            if not line.strip():
                continue

            if not line.startswith("  "):  # New field
                if current_field and "value" in field_data:
                    spec = field_map.get(current_field.lower())
                    if spec:
                        extracted_fields.append(
                            ExtractedField(
                                name=spec.name,
                                description=spec.description,
                                value=field_data.get("value"),
                                evidence_quote=field_data.get("evidence_quote"),
                                page_number=int(field_data["page_number"])
                                if field_data.get("page_number")
                                and field_data["page_number"].isdigit()
                                else None,
                            )
                        )
                current_field = line.split(":", 1)[0].strip()
                field_data = {}
            else:
                key_val = line.strip().split(":", 1)
                if len(key_val) == 2:
                    key, val = key_val
                    field_data[key.strip()] = val.strip()

        # Final field
        if current_field and "value" in field_data:
            spec = field_map.get(current_field.lower())
            if spec:
                extracted_fields.append(
                    ExtractedField(
                        name=spec.name,
                        description=spec.description,
                        value=field_data.get("value"),
                        evidence_quote=field_data.get("evidence_quote"),
                        page_number=int(field_data["page_number"])
                        if field_data.get("page_number")
                        and field_data["page_number"].isdigit()
                        else None,
                    )
                )

        # Fill in missing fields
        for spec in config.fields:
            if not any(f.name == spec.name for f in extracted_fields):
                extracted_fields.append(
                    ExtractedField(
                        name=spec.name,
                        description=spec.description,
                        value=None,
                        evidence_quote=None,
                        page_number=None,
                    )
                )

        return extracted_fields
