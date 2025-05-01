# extractors/open_ai_extractor.py

import openai
from typing import List, Optional
from extractors.extractor import Extractor
from models.document import Document
from models.extracted_document_data import ExtractedDocumentData, ExtractedField

class OpenAIExtractor(Extractor):
    def __init__(
        self,
        openai_api_key: str,
        fields_to_extract: Optional[List[ExtractedField]] = None,
        model: str = "gpt-4"
    ):
        openai.api_key = openai_api_key
        self.model = model

        # Default fields if none provided
        self.fields_to_extract = fields_to_extract or [
            ExtractedField("research_methodology", "The research methodology used in the paper"),
            ExtractedField("auc_score", "The reported AUC score or other evaluation metric"),
            ExtractedField("target_disease", "The disease or medical condition being studied"),
            ExtractedField("model_type", "The type of model or algorithm used")
        ]

    def extract(self, document: Document) -> ExtractedDocumentData:
        prompt = self._build_prompt(document.parsed_text)
        response = self._call_openai(prompt)
        extracted_fields = self._parse_response(response)
        return ExtractedDocumentData(document=document, fields=extracted_fields)

    def _build_prompt(self, text: str) -> str:
        field_list = "\n".join(
            f"- {field.name}: {field.description}" for field in self.fields_to_extract
        )

        return (
            "You are a scientific document parser. Given the following research paper text, "
            "extract the following fields and return them in JSON format:\n\n"
            f"{field_list}\n\n"
            "Text:\n"
            f"{text[:8000]}"
        )

    def _call_openai(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for extracting structured data from research papers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()

    def _parse_response(self, response: str) -> List[ExtractedField]:
        import json
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = {}

        return [
            ExtractedField(f.name, f.description, value=data.get(f.name))
            for f in self.fields_to_extract
        ]