# Research Metric Extraction with Vertex AI

This project is an **initial exploration** into using **large language models (LLMs)** to extract structured metrics from scientific research papers — particularly those describing patient engagement in AI-driven healthcare studies.

The goal is to assess how well frameworks such as the **Montreal Model** and **Holistic E-Health principles** are being reported and implemented in academic literature.

## Overview

The current pipeline operates **offline** and is designed to process PDF files stored in a local directory.

### Pipeline Steps

1. **Input**  
   Place your research paper PDFs in the `documents/` directory.

2. **Upload**  
   Each PDF is uploaded to a configured **Google Cloud Storage bucket** using a Vertex AI-compatible ingestion flow.

3. **LLM-Based Extraction**  
   The PDFs are processed through **Vertex AI's Gemini model**, which extracts a set of predefined research engagement metrics.

4. **Output**  
   - Output is written to: `documents/extracted_text/<timestamp>/`
   - Each file will have the same name as the original PDF but with a `.json` extension.
   - Each JSON file contains structured output for all extracted metrics, including:
     - Extracted value
     - Supporting evidence quote
     - Page number (when available)

## Example Output Structure

```
documents/
├── mhealth-2021-6-e27102.pdf
└── extracted_text/
    └── 20240519_103212/
        └── mhealth-2021-6-e27102.json
```

Example content of a JSON file:

```json
{
  "source_file": "documents/mhealth-2021-6-e27102.pdf",
  "fields": [
    {
      "name": "Title",
      "description": "Full title of the study",
      "value": "Considerations for the Design and Implementation of COVID-19 Contact Tracing Apps",
      "evidence_quote": "\"This study, titled...\"",
      "page_number": 1
    }
    // Additional fields...
  ]
}
```

## Configuration

- All field definitions are defined using `ExtractionFieldSpec` objects.
- The project uses Google Cloud credentials (via a `.env` file) and Vertex AI’s Python SDK. See the .env.example.

## Status

This is a **work-in-progress prototype** to evaluate feasibility, output quality, and LLM behavior in the context of extracting nuanced engagement-related metrics from academic publications.

Further work may include:
- Evaluation metrics
- Improved model prompting
- Active learning or feedback loops
- Web-based interfaces or batch jobs

## Contact

For questions or collaboration, please reach out to `pritika.vig@example.com` or open an issue in this repository.
