import requests
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET
from models.document import Document
from ingestors.ingestor import Ingestor
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GrobidPDFIngestor(Ingestor):
    def __init__(self, grobid_url: str = "http://localhost:8070", verbose: bool = False):
        self.grobid_url = grobid_url.rstrip("/")
        self.verbose = verbose

    def ingest(self, directory_path: str) -> List[Document]:
        extracted_documents = []

        input_dir = Path(directory_path)
        if not input_dir.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")

        for pdf_file in input_dir.glob("*.pdf"):
            try:
                if self.verbose:
                    logger.info(f"Sending {pdf_file.name} to GROBID...")

                with open(pdf_file, "rb") as f:
                    file_bytes = f.read()
                    files = {'input': (pdf_file.name, file_bytes, 'application/pdf')}
                    response = requests.post(f"{self.grobid_url}/api/processFulltextDocument", files=files)

                if response.status_code != 200:
                    raise Exception(f"GROBID error: {response.status_code} - {response.text}")

                parsed_text = self.parse_grobid_response(response.text)

                doc = Document(
                    file_path=pdf_file,
                    file_bytes=file_bytes,
                    grobid_response=response.text,
                    parsed_text=parsed_text
                )
                extracted_documents.append(doc)

                if self.verbose:
                    logger.info(f"Sending {pdf_file.name} to GROBID...")

            except Exception as e:
                logger.info(f"Failed to process {pdf_file.name}: {e}")

        return extracted_documents

    def parse_grobid_response(self, xml_text: str) -> str:
        """
        Extracts the entire body text (excluding references, abstract, and metadata) from GROBID's TEI XML.
        """
        paragraphs = []
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        root = ET.fromstring(xml_text)

        # Select all paragraphs within the main body of the article
        for p in root.findall(".//tei:text/tei:body//tei:p", namespaces=ns):
            paragraph_text = "".join(p.itertext()).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)

        return "\n\n".join(paragraphs)