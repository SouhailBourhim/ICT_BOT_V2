"""Tests pour le traitement de documents"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_processing import DocumentParser, SemanticChunker


def test_parser():
    """Test du parser"""
    # À implémenter
    pass


def test_chunker():
    """Test du chunker"""
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    text = "Test " * 50
    chunks = chunker.chunk(text)
    
    assert len(chunks) > 0
    assert all("content" in c for c in chunks)
