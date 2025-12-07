"""Amélioration des requêtes utilisateur"""
from typing import List


class QueryEnhancer:
    """Amélioration et expansion des requêtes"""
    
    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client
    
    def enhance(self, query: str) -> str:
        """Améliore une requête"""
        # Nettoyage basique
        enhanced = query.strip()
        
        # Expansion avec LLM si disponible
        if self.ollama_client:
            from ..llm.prompt_templates import PromptTemplates
            prompt = PromptTemplates.format_query_enhancement(query)
            enhanced = self.ollama_client.generate(prompt)
        
        return enhanced
    
    def extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés d'une requête"""
        # Simple extraction par mots
        words = query.lower().split()
        # Filtrer les mots courts
        keywords = [w for w in words if len(w) > 3]
        return keywords
