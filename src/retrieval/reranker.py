"""Re-ranking des résultats de recherche"""
from typing import List, Dict, Any


class Reranker:
    """Re-ranking des résultats"""
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Re-rank les résultats en combinant les scores"""
        for result in results:
            bm25_score = result.get("bm25_score", 0)
            semantic_score = result.get("semantic_score", 0)
            
            # Score combiné (moyenne pondérée)
            result["combined_score"] = 0.4 * bm25_score + 0.6 * semantic_score
        
        # Trier par score combiné
        return sorted(results, key=lambda x: x.get("combined_score", 0), reverse=True)
