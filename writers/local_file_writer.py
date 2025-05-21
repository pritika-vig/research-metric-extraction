import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

from models.extracted_document_data import ExtractedDocumentData


class LocalFileWriter:
    def __init__(self, base_output_dir: str = "documents/extracted_text/pubmed_search"):
        self.base_output_dir = Path(base_output_dir)

    def write(self, extracted_documents: List[ExtractedDocumentData]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.base_output_dir / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        for extracted_doc in extracted_documents:
            print("DOC TYPE:", type(extracted_doc))
            print("ASDICT OUTPUT:", asdict(extracted_doc))
            paper_id = extracted_doc.paper_id
            if not paper_id:
                print("Skipping document with missing paper_id.")
                continue

            output_path = output_dir / f"{paper_id.get_canonical_id()}.json"

            doc_dict = asdict(
                extracted_doc
            )  # includes nested PaperId and ExtractedField dataclasses

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(doc_dict, f, indent=2)

            print(f"Saved extracted data to: {output_path}")
