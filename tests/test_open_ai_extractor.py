# tests/test_open_ai_extractor.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from extractors.open_ai_extractor import OpenAIExtractor
from models.document import Document
from models.extracted_document_data import ExtractedField

class TestOpenAIExtractor(unittest.TestCase):

    @patch("extractors.open_ai_extractor.openai.ChatCompletion.create")
    def test_extraction_from_mocked_openai(self, mock_openai_create):
        # Mocked OpenAI JSON response as if returned by the LLM
        mock_response_content = {
            "research_methodology": "Prospective clinical trial",
            "auc_score": "0.91",
            "target_disease": "Breast cancer",
            "model_type": "Random Forest"
        }

        mock_choice = MagicMock()
        mock_choice.message.content = str(mock_response_content).replace("'", '"')  # simulate JSON string

        mock_openai_create.return_value = MagicMock(choices=[mock_choice])

        # Create a dummy Document
        doc = Document(
            file_path=Path("sample.pdf"),
            parsed_text="This study used a prospective clinical trial to evaluate a random forest model..."
        )

        extractor = OpenAIExtractor(openai_api_key="test-key", model="gpt-4")
        result = extractor.extract(doc)

        # Assertions
        self.assertEqual(result.document.file_path.name, "sample.pdf")
        field_map = {f.name: f.value for f in result.fields}

        self.assertEqual(field_map["research_methodology"], "Prospective clinical trial")
        self.assertEqual(field_map["auc_score"], "0.91")
        self.assertEqual(field_map["target_disease"], "Breast cancer")
        self.assertEqual(field_map["model_type"], "Random Forest")

    @patch("extractors.open_ai_extractor.openai.ChatCompletion.create")
    def test_extraction_from_custom_fields(self, mock_openai_create):
        mock_response_content = {
            "intervention": "Dietary counseling",
            "population": "Adults with type 2 diabetes"}

        mock_choice = MagicMock()
        mock_choice.message.content = str(mock_response_content).replace("'", '"')
        mock_openai_create.return_value = MagicMock(choices=[mock_choice])

        fields = [
            ExtractedField("intervention", "The treatment or intervention used"),
            ExtractedField("population", "The group of people studied"),
        ]

        doc = Document(file_path=Path("sample.pdf"), parsed_text="dummy content")
        extractor = OpenAIExtractor(openai_api_key="test-key", fields_to_extract=fields)
        result = extractor.extract(doc)

        field_map = {f.name: f.value for f in result.fields}
        self.assertEqual(field_map["intervention"], "Dietary counseling")
        self.assertEqual(field_map["population"], "Adults with type 2 diabetes")

if __name__ == "__main__":
    unittest.main()