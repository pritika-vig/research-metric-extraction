import os
from pathlib import Path
from ingestors.grobid_pdf_ingestor import GrobidPDFIngestor

def main():
    input_dir = Path("/Users/pritikavig/Documents/python/lab/documents")
    output_dir = input_dir
    grobid_url = "http://localhost:8070"

    print(f"\n🔎 Searching for PDFs inside {input_dir}...\n")

    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print("⚠️  No PDF files found.")
        return

    print(f"📄 Found {len(pdf_files)} PDF file(s). Starting ingestion...\n")

    ingestor = GrobidPDFIngestor(grobid_url=grobid_url, verbose=True)

    documents = ingestor.ingest(input_dir)

    if not documents:
        print("⚠️  No documents were successfully ingested.")
        return

    for doc in documents:
        # 🛠 Debugging output
        print(f"\n🛠 Debugging Document for {doc.file_path.name}:")
      #  print(f"- PDF Size: {len(doc.pdf_bytes)} bytes")
        print(f"- GROBID Response Length: {len(doc.grobid_response)} characters")
        print(f"- Parsed Text Length: {len(doc.parsed_text)} characters\n")

        # 🧪 Save the raw GROBID XML response for manual inspection
        xml_output_file = output_dir / f"{doc.file_path.stem}_grobid.xml"
        with open(xml_output_file, "w", encoding="utf-8") as f:
            f.write(doc.grobid_response)
        print(f"🧪 Written GROBID XML to {xml_output_file}")
        output_file = output_dir / f"{doc.file_path.stem}.txt"

        try:
            paragraphs = doc.parsed_text.split("\n\n") if doc.parsed_text else []

            with open(output_file, "w", encoding="utf-8") as f:
                for i, paragraph in enumerate(paragraphs, 1):
                    f.write(f"# Paragraph {i}\n")
                    f.write(paragraph.strip() + "\n\n")

            print(f"✅ Written extracted text to {output_file.name}")

        except Exception as e:
            print(f"❌ Failed to write {output_file.name}: {e}")

if __name__ == "__main__":
    main()