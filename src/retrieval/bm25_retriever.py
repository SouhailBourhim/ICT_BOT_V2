"""Retriever BM25 pour la recherche par mots-clés"""
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize


class BM25Retriever:
    """Recherche BM25 pour les mots-clés"""
    
    def __init__(self):
        self.corpus = []
        self.documents = []
        self.bm25 = None
        
        # Télécharger les ressources NLTK si nécessaire
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
    
    def index(self, documents: List[Dict[str, Any]]):
        """Indexe les documents pour BM25"""
        self.documents = documents
        self.corpus = [self._tokenize(doc["content"]) for doc in documents]
        self.bm25 = BM25Okapi(self.corpus)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recherche par BM25"""
        if not self.bm25:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Trier par score
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            result = self.documents[idx].copy()
            result["score"] = float(scores[idx])
            results.append(result)
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize le texte"""
        return word_tokenize(text.lower())
