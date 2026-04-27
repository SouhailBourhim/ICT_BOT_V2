from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_search import HybridSearchEngine, SearchResult


def test_bm25_retriever_returns_best_keyword_match():
    retriever = BM25Retriever()
    documents = [
        {"id": "1", "content": "Machine learning is a subset of AI"},
        {"id": "2", "content": "Deep learning uses neural networks"},
    ]

    retriever.index(documents)
    results = retriever.search("machine learning", top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "1"


def test_hybrid_fusion_combines_semantic_and_bm25_scores():
    engine = HybridSearchEngine(
        vector_store=object(),
        semantic_weight=0.7,
        bm25_weight=0.3,
        normalize_scores=False,
    )

    results = engine._fuse_results(
        semantic_results=[
            SearchResult("doc-a", "semantic only", {}, score=0.8, semantic_score=0.8),
            SearchResult("doc-b", "both", {}, score=0.6, semantic_score=0.6),
        ],
        bm25_results=[
            SearchResult("doc-b", "both", {}, score=1.0, bm25_score=1.0),
            SearchResult("doc-c", "keyword only", {}, score=0.9, bm25_score=0.9),
        ],
        top_k=3,
    )

    assert [result.doc_id for result in results] == ["doc-b", "doc-a", "doc-c"]
    assert results[0].score == 0.72
