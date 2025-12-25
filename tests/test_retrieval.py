"""Tests pour la récupération"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval import BM25Retriever


def test_bm25_retriever():
    """Test du retriever BM25"""
    retriever = BM25Retriever()
    
    documents = [
        {"id": "1", "content": "Machine learning is a subset of AI"},
        {"id": "2", "content": "Deep learning uses neural networks"}
    ]
    
    retriever.index(documents)
    results = retriever.search("machine learning", top_k=1)
    
    assert len(results) > 0
    assert results[0]["id"] == "1"
