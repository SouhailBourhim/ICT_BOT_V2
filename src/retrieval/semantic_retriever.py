"""Retriever sémantique basé sur les embeddings"""
from typing import List, Dict, Any


class SemanticRetriever:
    """Recherche sémantique par similarité vectorielle"""
    
    def __init__(self, vector_store, embedding_generator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recherche sémantique"""
        # Générer l'embedding de la requête
        query_embedding = self.embedding_generator.generate(query)
        
        # Rechercher dans ChromaDB
        results = self.vector_store.query(query_embedding, n_results=top_k)
        
        # Formater les résultats
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "score": 1 - results["distances"][0][i],  # Convertir distance en similarité
                "metadata": results["metadatas"][0][i]
            })
        
        return formatted_results
