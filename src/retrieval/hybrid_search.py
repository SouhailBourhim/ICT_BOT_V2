"""
Système de recherche hybride: Sémantique (embeddings) + Keyword (BM25)
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
from loguru import logger


@dataclass
class SearchResult:
    """Résultat de recherche unifié"""
    doc_id: str
    text: str
    metadata: Dict
    score: float
    semantic_score: float = 0.0
    bm25_score: float = 0.0
    rank: int = 0


class HybridSearchEngine:
    """
    Moteur de recherche hybride combinant:
    - Recherche sémantique (similarité cosinus sur embeddings)
    - Recherche par mots-clés (BM25)
    """
    
    def __init__(
        self,
        vector_store,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        normalize_scores: bool = True
    ):
        """
        Initialise le moteur de recherche hybride
        
        Args:
            vector_store: Instance de VectorStore
            semantic_weight: Poids de la recherche sémantique [0, 1]
            bm25_weight: Poids de la recherche BM25 [0, 1]
            normalize_scores: Normaliser les scores avant fusion
        """
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        self.normalize_scores = normalize_scores
        
        # Vérification des poids
        assert abs(semantic_weight + bm25_weight - 1.0) < 0.01, \
            "Les poids doivent sommer à 1.0"
        
        # Index BM25 (sera construit lors de l'indexation)
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_documents: List[Dict] = []
        
        logger.info(f"Recherche hybride: {semantic_weight:.1%} sémantique + {bm25_weight:.1%} BM25")
    
    def index_documents(self, documents: List[Dict]):
        """
        Indexe les documents pour BM25
        
        Args:
            documents: Liste de dicts avec 'id', 'text', 'metadata'
        """
        if not documents:
            logger.warning("Aucun document à indexer")
            return
        
        logger.info(f"Indexation de {len(documents)} documents pour BM25...")
        
        # Stockage des documents
        self.bm25_documents = documents
        
        # Tokenisation pour BM25
        tokenized_corpus = [
            self._tokenize(doc['text']) 
            for doc in documents
        ]
        
        # Construction de l'index BM25
        self.bm25_index = BM25Okapi(tokenized_corpus)
        
        logger.success(f"✅ Index BM25 construit: {len(documents)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisation simple pour BM25
        Peut être amélioré avec spaCy pour le français
        """
        # Conversion en minuscules
        text = text.lower()
        
        # Tokenisation basique
        tokens = text.split()
        
        # Nettoyage basique
        tokens = [t.strip('.,!?;:()[]{}') for t in tokens]
        tokens = [t for t in tokens if len(t) > 2]  # Filtrer mots courts
        
        return tokens
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        return_details: bool = True
    ) -> List[SearchResult]:
        """
        Recherche hybride principale
        
        Args:
            query: Requête de l'utilisateur
            top_k: Nombre de résultats à retourner
            filters: Filtres sur métadonnées (pour recherche sémantique)
            return_details: Inclure les scores détaillés
            
        Returns:
            Liste de SearchResult triés par pertinence
        """
        logger.info(f"🔍 Recherche: '{query}' (top_k={top_k})")
        
        # 1. Recherche sémantique
        semantic_results = self._semantic_search(query, top_k * 2, filters)
        
        # 2. Recherche BM25
        bm25_results = self._bm25_search(query, top_k * 2)
        
        # 3. Fusion des résultats
        fused_results = self._fuse_results(
            semantic_results,
            bm25_results,
            top_k
        )
        
        logger.info(f"✅ {len(fused_results)} résultats retournés")
        
        return fused_results
    
    def _semantic_search(
        self,
        query: str,
        n_results: int,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Recherche sémantique via vector store"""
        try:
            results = self.vector_store.search(
                query_text=query,
                n_results=n_results,
                where=filters
            )
            
            # Conversion en SearchResult
            search_results = []
            for i, (doc_id, text, metadata, distance) in enumerate(zip(
                results['ids'],
                results['documents'],
                results['metadatas'],
                results['distances']
            )):
                # Conversion distance -> similarité [0, 1]
                similarity = 1 / (1 + distance)
                
                search_results.append(SearchResult(
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata,
                    score=similarity,
                    semantic_score=similarity,
                    rank=i + 1
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Erreur recherche sémantique: {e}")
            return []
    
    def _bm25_search(self, query: str, n_results: int) -> List[SearchResult]:
        """Recherche BM25 par mots-clés"""
        if self.bm25_index is None or not self.bm25_documents:
            logger.warning("Index BM25 non initialisé")
            return []
        
        try:
            # Tokenisation de la requête
            query_tokens = self._tokenize(query)
            
            # Calcul des scores BM25
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Tri des résultats
            top_indices = np.argsort(scores)[::-1][:n_results]
            
            # Conversion en SearchResult
            search_results = []
            for rank, idx in enumerate(top_indices, 1):
                if scores[idx] > 0:  # Filtrer scores nuls
                    doc = self.bm25_documents[idx]
                    
                    search_results.append(SearchResult(
                        doc_id=doc['id'],
                        text=doc['text'],
                        metadata=doc.get('metadata', {}),
                        score=float(scores[idx]),
                        bm25_score=float(scores[idx]),
                        rank=rank
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Erreur recherche BM25: {e}")
            return []
    
    def _fuse_results(
        self,
        semantic_results: List[SearchResult],
        bm25_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        Fusionne les résultats des deux méthodes
        Utilise la méthode RRF (Reciprocal Rank Fusion) ou score pondéré
        """
        # Créer un dictionnaire unifié des résultats
        results_dict: Dict[str, SearchResult] = {}
        
        # Normalisation des scores si nécessaire
        if self.normalize_scores:
            semantic_results = self._normalize_scores(semantic_results)
            bm25_results = self._normalize_scores(bm25_results)
        
        # Fusion des résultats sémantiques
        for result in semantic_results:
            if result.doc_id not in results_dict:
                results_dict[result.doc_id] = result
                results_dict[result.doc_id].score = result.semantic_score * self.semantic_weight
            else:
                results_dict[result.doc_id].semantic_score = result.semantic_score
                results_dict[result.doc_id].score += result.semantic_score * self.semantic_weight
        
        # Fusion des résultats BM25
        for result in bm25_results:
            if result.doc_id not in results_dict:
                results_dict[result.doc_id] = result
                results_dict[result.doc_id].score = result.bm25_score * self.bm25_weight
            else:
                results_dict[result.doc_id].bm25_score = result.bm25_score
                results_dict[result.doc_id].score += result.bm25_score * self.bm25_weight
        
        # Tri par score combiné
        fused_results = sorted(
            results_dict.values(),
            key=lambda x: x.score,
            reverse=True
        )[:top_k]
        
        # Mise à jour des rangs
        for rank, result in enumerate(fused_results, 1):
            result.rank = rank
        
        return fused_results
    
    def _normalize_scores(self, results: List[SearchResult]) -> List[SearchResult]:
        """Normalise les scores entre 0 et 1"""
        if not results:
            return results
        
        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score - min_score > 0:
            for result in results:
                result.score = (result.score - min_score) / (max_score - min_score)
        
        return results
    
    def search_with_reranking(
        self,
        query: str,
        top_k: int = 10,
        initial_k: int = 50,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Recherche avec re-ranking
        1. Récupère initial_k résultats
        2. Re-rank avec un modèle plus sophistiqué
        3. Retourne top_k
        """
        # Recherche initiale large
        initial_results = self.search(query, top_k=initial_k, filters=filters)
        
        # TODO: Implémenter re-ranking avec un modèle cross-encoder
        # Pour l'instant, retourne simplement les top_k
        
        return initial_results[:top_k]
    
    def get_similar_documents(
        self,
        doc_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Trouve les documents similaires à un document donné
        """
        # Récupérer le document source
        source_docs = self.vector_store.get_by_ids([doc_id])
        
        if not source_docs['documents']:
            logger.warning(f"Document {doc_id} introuvable")
            return []
        
        source_text = source_docs['documents'][0]
        
        # Recherche sémantique basée sur le texte du document
        return self.search(source_text, top_k=top_k + 1)[1:]  # Exclure le doc lui-même


# Test du système hybride
if __name__ == "__main__":
    from vector_store import VectorStore
    
    # Setup
    vector_store = VectorStore(
        persist_directory="./test_db",
        collection_name="test_collection"
    )
    
    # Documents de test
    documents = [
        {
            'id': 'doc1',
            'text': "L'Internet des Objets (IoT) révolutionne l'industrie avec des capteurs intelligents",
            'metadata': {'source': 'cours_iot.pdf'}
        },
        {
            'id': 'doc2',
            'text': "Les protocoles de sécurité sont essentiels pour protéger les réseaux IoT",
            'metadata': {'source': 'cours_secu.pdf'}
        },
        {
            'id': 'doc3',
            'text': "Le cloud computing offre des solutions de stockage et de calcul distribué",
            'metadata': {'source': 'cours_cloud.pdf'}
        }
    ]
    
    # Initialisation recherche hybride
    hybrid_search = HybridSearchEngine(
        vector_store=vector_store,
        semantic_weight=0.7,
        bm25_weight=0.3
    )
    
    # Indexation
    hybrid_search.index_documents(documents)
    
    # Recherche
    query = "Comment sécuriser un réseau IoT ?"
    results = hybrid_search.search(query, top_k=3)
    
    print(f"\n🔍 Requête: {query}\n")
    for result in results:
        print(f"Rang {result.rank}: [Score: {result.score:.3f}]")
        print(f"  Sémantique: {result.semantic_score:.3f} | BM25: {result.bm25_score:.3f}")
        print(f"  Texte: {result.text[:100]}...")
        print()