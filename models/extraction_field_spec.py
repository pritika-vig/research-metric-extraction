# models/extraction_field_spec.py

from dataclasses import dataclass

@dataclass
class ExtractionFieldSpec:
    name: str
    description: str
    required: bool = False