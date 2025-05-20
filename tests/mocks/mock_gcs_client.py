# tests/mocks/mock_gcs_client.py

from pathlib import Path
from typing import Dict

class MockBlob:
    def __init__(self, name):
        self.name = name
        self._uploaded = False

    def exists(self):
        return self._uploaded

    def upload_from_filename(self, filename):
        self._uploaded = True

    def delete(self):
        self._uploaded = False

class MockBucket:
    def __init__(self):
        self._blobs: Dict[str, MockBlob] = {}

    def blob(self, name):
        if name not in self._blobs:
            self._blobs[name] = MockBlob(name)
        return self._blobs[name]

class MockStorageClient:
    def __init__(self):
        self._buckets: Dict[str, MockBucket] = {}

    def bucket(self, name):
        if name not in self._buckets:
            self._buckets[name] = MockBucket()
        return self._buckets[name]