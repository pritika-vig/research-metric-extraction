# models/extraction_config.py

from dataclasses import dataclass
from typing import List
from models.extraction_field_spec import ExtractionFieldSpec

@dataclass
class ExtractionConfig:
    name: str  # e.g. "Patient Engagement Paper Extraction"
    fields: List[ExtractionFieldSpec]
