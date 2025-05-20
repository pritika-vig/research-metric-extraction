# extractors/vertex_gemini_extractor.py

import os
from typing import List
from dotenv import load_dotenv

from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, Part

from models.document import Document
from models.extracted_document_data import ExtractedField, ExtractedDocumentData
from models.extraction_config import ExtractionConfig
from models.extraction_field_spec import ExtractionFieldSpec
from extractors.extractor import Extractor

load_dotenv()


class VertexGeminiExtractor(Extractor):
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")
        init(project=self.project_id, location=self.region)
        self.model = GenerativeModel("gemini-2.0-flash")

    def extract(self, document: Document, config: ExtractionConfig) -> ExtractedDocumentData:
        if not document.gcs_metadata:
            raise ValueError(f"Document {document.file_path.name} has no gcs_metadata")

        gcs_uri = document.gcs_metadata.gcs_uri
        prompt = self._build_prompt(config)

        result = self.model.generate_content(
            [
                prompt,
                Part.from_uri(gcs_uri, mime_type="application/pdf"),
            ],
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 4096,
            }
        )

        response_text = result.text.strip()
        fields = self._parse_response(response_text, config)
        return ExtractedDocumentData(document=document, fields=fields)

    def _build_prompt(self, config: ExtractionConfig) -> str:
        field_list = "\n".join(f"- {f.name}" for f in config.fields)

        field_defs = "\n".join([
            f'- "{f.name}": {f.description}'
            for f in config.fields
        ])

        output_format = "\n".join([
            f"{f.name}:\n  value: ...\n  evidence_quote: ...\n  page_number: ..."
            for f in config.fields
        ])

        return (
        "You are analyzing a scientific research paper related to AI tools in healthcare.\n\n"
        "Your task is to extract structured information about how patient or public engagement was reported in the study, "
        "following key principles from the Montreal Model and the Holistic E-Health Framework.\n\n"
        "Extract **each of the following fields**, providing:\n"
        "  - The value\n"
        "  - A **direct quote** from the paper that supports the value (or 'N/A' if none)\n"
        "  - The **page number** where that quote appears (or 'N/A')\n\n"
        "Please return data in this format:\n"
        f"{output_format}\n\n"
        "### Field Definitions:\n"
        f"{field_defs}\n\n"
        "Use your best judgment to locate implicit as well as explicit evidence.\n"
        "Be concise and accurate, and assume the audience is evaluating use of engagement frameworks in applied research."
        )

    def _parse_response(self, response: str, config: ExtractionConfig) -> List[ExtractedField]:
        extracted_fields = []
        field_map = {f.name.lower(): f for f in config.fields}

        current_field = None
        field_data = {}

        lines = response.splitlines()

        for line in lines:
            if not line.strip():
                continue

            if not line.startswith("  "):  # New field
                if current_field and 'value' in field_data:
                    spec = field_map.get(current_field.lower())
                    if spec:
                        extracted_fields.append(ExtractedField(
                            name=spec.name,
                            description=spec.description,
                            value=field_data.get('value'),
                            evidence_quote=field_data.get('evidence_quote'),
                            page_number=int(field_data['page_number']) if field_data.get('page_number') and field_data['page_number'].isdigit() else None
                        ))
                current_field = line.split(":", 1)[0].strip()
                field_data = {}
            else:
                key_val = line.strip().split(":", 1)
                if len(key_val) == 2:
                    key, val = key_val
                    field_data[key.strip()] = val.strip()

        # Final field
        if current_field and 'value' in field_data:
            spec = field_map.get(current_field.lower())
            if spec:
                extracted_fields.append(ExtractedField(
                    name=spec.name,
                    description=spec.description,
                    value=field_data.get('value'),
                    evidence_quote=field_data.get('evidence_quote'),
                    page_number=int(field_data['page_number']) if field_data.get('page_number') and field_data['page_number'].isdigit() else None
                ))

        # Fill in missing fields
        for spec in config.fields:
            if not any(f.name == spec.name for f in extracted_fields):
                extracted_fields.append(ExtractedField(
                    name=spec.name,
                    description=spec.description,
                    value=None,
                    evidence_quote=None,
                    page_number=None
                ))

        return extracted_fields
