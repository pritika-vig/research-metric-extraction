# tests/conftest.py

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def temp_test_dir():
    """Create a unique temp directory and clean it up after the test."""
    dir_path = Path(f"tests/temp/test_{uuid.uuid4().hex}")
    dir_path.mkdir(parents=True, exist_ok=True)
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def test_pdf_file(temp_test_dir):
    """Create a dummy PDF in the temp directory."""
    pdf_path = temp_test_dir / "test.pdf"
    pdf_path.write_text("This is a test PDF.", encoding="utf-8")
    return pdf_path
