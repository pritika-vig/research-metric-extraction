# verify_gcs_bucket.py

import os

from dotenv import load_dotenv
from google.api_core.exceptions import Forbidden, NotFound
from google.cloud import storage

# Load .env variables
load_dotenv()

bucket_name = os.getenv("GCS_BUCKET")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not bucket_name or not credentials_path:
    print("ERROR: GCS_BUCKET or GOOGLE_APPLICATION_CREDENTIALS not set in .env")
    exit(1)

try:
    # Initialize GCS client (automatically picks up credentials from env var)
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    print(f"Bucket '{bucket_name}' exists and is accessible.")

    # Test upload
    test_blob = bucket.blob("test_gcs_upload.txt")
    test_blob.upload_from_string("This is a test file.")
    print("Test file uploaded successfully.")

    # Optionally delete the test file
    test_blob.delete()
    print("🧹 Cleaned up test file.")

except NotFound:
    print(f"ERROR: Bucket '{bucket_name}' was not found.")
except Forbidden:
    print(
        f"ERROR: Access to bucket '{bucket_name}' is forbidden. "
        "Check your service account permissions."
    )
except Exception as e:
    print(f"ERROR: {str(e)}")
