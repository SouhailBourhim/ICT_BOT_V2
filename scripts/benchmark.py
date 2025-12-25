"""Script de benchmark de performance"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval import HybridSearch
from storage import VectorStore
from document_processing import EmbeddingGenerator


def benchmark_retrieval():
    """Benchmark de la récupération"""
    print("Benchmark de récupération...")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    hybrid_search = HybridSearch(vector_store, embedding_gen)
    
    test_queries = [
        "Qu'est-ce que le machine learning?",
        "Comment fonctionne un réseau de neurones?",
        "Expliquez l'algorithme de gradient descent"
    ]
    
    for query in test_queries:
        start = time.time()
        results = hybrid_search.search(query, top_k=5)
        duration = time.time() - start
        
        print(f"\nQuery: {query}")
        print(f"Temps: {duration:.3f}s")
        print(f"Résultats: {len(results)}")


if __name__ == "__main__":
    benchmark_retrieval()
