from pipelines.pubmed_pipeline import PubMedPipeline

SEARCH_QUERY = """
(("machine learning"[All Fields] OR "artificial intelligence"[All Fields] OR "AI"[All Fields]
OR "deep learning"[All Fields])
AND
("chatbot"[All Fields] OR "conversational agent"[All Fields] OR "virtual assistant"[All Fields]
OR "mobile app"[All Fields]
OR "digital health"[All Fields])
AND
("patient-facing"[All Fields] OR "patient care"[All Fields] OR "healthcare"[All Fields])
AND
(clinical trial[Publication Type] OR evaluation studies[Publication Type] OR
intervention[Title/Abstract]))
AND
("2019/01/01"[PDAT] : "3000"[PDAT])
""".replace(
    "\n", " "
)

if __name__ == "__main__":
    pipeline = PubMedPipeline(
        query=SEARCH_QUERY,  # Search term for PubMed.
        email="pritikav@mit.edu",  # required for PubMed API
    )
    pipeline.run()
