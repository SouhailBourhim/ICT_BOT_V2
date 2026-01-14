"""Amélioration des requêtes utilisateur"""
from typing import List
import re


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
            templates = PromptTemplates()
            system, user = templates.QUERY_REFINEMENT.format(query=query)
            response = self.ollama_client.generate(
                prompt=user,
                system=system,
                temperature=0.2,
                max_tokens=200
            )
            variants = self._extract_variants(response)
            if variants:
                enhanced = variants[0]
        
        return enhanced
    
    def extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés d'une requête"""
        # Simple extraction par mots
        words = query.lower().split()
        # Filtrer les mots courts
        keywords = [w for w in words if len(w) > 3]
        return keywords

    def _extract_variants(self, response: str) -> List[str]:
        """Extrait des variantes depuis une réponse numérotée."""
        matches = re.findall(r'^\s*\d+\.\s*(.+)$', response, flags=re.MULTILINE)
        cleaned = [m.strip() for m in matches if m.strip()]
        if cleaned:
            return cleaned
        return [response.strip()] if response.strip() else []
