"""Retriever sémantique basé sur les embeddings"""
from typing import List, Dict, Any

# Import compatibility layer
from ..storage.compatibility import compatibility_layer


class SemanticRetriever:
    """Recherche sémantique par similarité vectorielle avec support de compatibilité"""
    
    def __init__(self, vector_store, embedding_generator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche sémantique avec support de compatibilité pour les formats de chunks
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de résultats formatés avec support de compatibilité
        """
        # Générer l'embedding de la requête
        query_embedding = self.embedding_generator.generate(query)
        
        # Rechercher dans ChromaDB
        results = self.vector_store.query(query_embedding, n_results=top_k)
        
        # Use compatibility layer if normalized results are available
        if isinstance(results, dict) and 'normalized_results' in results:
            # Use enhanced results from compatibility layer
            normalized_results = results['normalized_results']
            
            formatted_results = []
            for result in normalized_results:
                # Convert distance to similarity score
                distance = result.get('distance', 0.0)
                similarity_score = 1 - distance if distance <= 1.0 else 1 / (1 + distance)
                
                formatted_results.append({
                    "id": result.get('id', ''),
                    "content": result.get('content', ''),
                    "score": similarity_score,
                    "metadata": result.get('metadata', {}),
                    # Enhanced compatibility fields
                    "chunk_format": result.get('chunk_format', 'unknown'),
                    "has_contextual_header": result.get('has_contextual_header', False),
                    "contextual_header": result.get('contextual_header', ''),
                    "display_title": result.get('display_title', ''),
                    "clean_content": result.get('clean_content', result.get('content', '')),
                    "hierarchy_path": result.get('hierarchy_path', []),
                    "structure_metadata": result.get('structure_metadata', {})
                })
            
            return formatted_results
        
        else:
            # Fallback to original format handling
            formatted_results = []
            
            # Handle both old and new result formats
            if isinstance(results, dict):
                ids = results.get("ids", [[]])[0] if results.get("ids") else []
                documents = results.get("documents", [[]])[0] if results.get("documents") else []
                distances = results.get("distances", [[]])[0] if results.get("distances") else []
                metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            else:
                # Handle list format
                ids = []
                documents = []
                distances = []
                metadatas = []
            
            # Process results through compatibility layer
            raw_results = []
            for i in range(len(ids)):
                raw_results.append({
                    'id': ids[i] if i < len(ids) else '',
                    'content': documents[i] if i < len(documents) else '',
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'distance': distances[i] if i < len(distances) else 0.0
                })
            
            # Normalize through compatibility layer
            normalized_results = compatibility_layer.handle_mixed_search_results(raw_results)
            
            # Format for return
            for result in normalized_results:
                distance = result.get('distance', 0.0)
                similarity_score = 1 - distance if distance <= 1.0 else 1 / (1 + distance)
                
                formatted_results.append({
                    "id": result.get('id', ''),
                    "content": result.get('content', ''),
                    "score": similarity_score,
                    "metadata": result.get('metadata', {}),
                    # Enhanced compatibility fields
                    "chunk_format": result.get('chunk_format', 'unknown'),
                    "has_contextual_header": result.get('has_contextual_header', False),
                    "contextual_header": result.get('contextual_header', ''),
                    "display_title": result.get('display_title', ''),
                    "clean_content": result.get('clean_content', result.get('content', '')),
                    "hierarchy_path": result.get('hierarchy_path', []),
                    "structure_metadata": result.get('structure_metadata', {})
                })
            
            return formatted_results
