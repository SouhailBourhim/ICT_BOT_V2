"""
Générateur d'embeddings avec support multilingue (français)
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
import torch


class EmbeddingGenerator:
    """
    Générateur d'embeddings vectoriels pour textes
    Utilise SentenceTransformers avec support du français
    """
    
    # Modèles recommandés pour le français
    FRENCH_MODELS = {
        'multilingual_mini': 'paraphrase-multilingual-MiniLM-L12-v2',  # Rapide, 384 dim
        'multilingual_mpnet': 'paraphrase-multilingual-mpnet-base-v2',  # Meilleur qualité, 768 dim
        'camembert': 'dangvantuan/sentence-camembert-large',  # Spécifique français
    }
    
    def __init__(
        self,
        model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        device: str = None,
        batch_size: int = 32
    ):
        """
        Initialise le générateur d'embeddings
        
        Args:
            model_name: Nom du modèle SentenceTransformer
            device: 'cuda', 'cpu' ou None (auto-détection)
            batch_size: Taille des batchs pour l'encodage
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Détection automatique du device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Chargement du modèle: {model_name} sur {self.device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            logger.success(f"✅ Modèle chargé: {self.embedding_dimension} dimensions")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Génère un embedding pour un texte unique
        
        Args:
            text: Texte à encoder
            
        Returns:
            Vecteur numpy de dimensions [embedding_dimension]
        """
        if not text or not text.strip():
            logger.warning("Texte vide, retour d'un vecteur nul")
            return np.zeros(self.embedding_dimension)
        
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True  # Normalisation L2 pour similarité cosinus
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embedding: {e}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str],
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Génère des embeddings pour plusieurs textes (plus efficace)
        
        Args:
            texts: Liste de textes à encoder
            show_progress: Afficher la barre de progression
            
        Returns:
            Matrice numpy de dimensions [len(texts), embedding_dimension]
        """
        if not texts:
            logger.warning("Liste de textes vide")
            return np.array([])
        
        # Filtrer les textes vides
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        logger.info(f"Génération de {len(valid_texts)} embeddings (batch_size={self.batch_size})")
        
        try:
            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                normalize_embeddings=True
            )
            
            logger.success(f"✅ {len(embeddings)} embeddings générés")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération batch: {e}")
            raise
    
    def compute_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier vecteur
            embedding2: Second vecteur
            
        Returns:
            Score de similarité [0, 1]
        """
        # Produit scalaire (les embeddings sont déjà normalisés)
        similarity = np.dot(embedding1, embedding2)
        
        return float(similarity)
    
    def compute_similarity_matrix(
        self, 
        embeddings1: np.ndarray, 
        embeddings2: np.ndarray
    ) -> np.ndarray:
        """
        Calcule la matrice de similarité entre deux ensembles d'embeddings
        
        Args:
            embeddings1: Matrice [N, dim]
            embeddings2: Matrice [M, dim]
            
        Returns:
            Matrice de similarité [N, M]
        """
        # Produit matriciel pour toutes les paires
        similarity_matrix = np.dot(embeddings1, embeddings2.T)
        
        return similarity_matrix
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        corpus_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Trouve les K embeddings les plus similaires dans un corpus
        
        Args:
            query_embedding: Embedding de la requête [dim]
            corpus_embeddings: Embeddings du corpus [N, dim]
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (index, score) triés par similarité décroissante
        """
        # Calcul des similarités
        similarities = np.dot(corpus_embeddings, query_embedding)
        
        # Top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Résultats avec scores
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        
        return results
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str):
        """Sauvegarde des embeddings sur disque"""
        try:
            np.save(filepath, embeddings)
            logger.info(f"Embeddings sauvegardés: {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise
    
    def load_embeddings(self, filepath: str) -> np.ndarray:
        """Charge des embeddings depuis le disque"""
        try:
            embeddings = np.load(filepath)
            logger.info(f"Embeddings chargés: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            raise
    
    def get_model_info(self) -> dict:
        """Retourne les informations sur le modèle"""
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'device': self.device,
            'batch_size': self.batch_size,
            'max_seq_length': self.model.max_seq_length
        }


# Test du générateur
if __name__ == "__main__":
    # Initialisation
    embedder = EmbeddingGenerator()
    
    # Textes de test en français
    texts = [
        "L'Internet des Objets transforme notre quotidien.",
        "Les capteurs IoT collectent des données en temps réel.",
        "La cybersécurité est essentielle pour protéger les systèmes.",
        "Le machine learning permet d'analyser les données IoT."
    ]
    
    # Génération d'embeddings
    print("\n📊 Génération d'embeddings...")
    embeddings = embedder.generate_embeddings_batch(texts)
    print(f"Shape: {embeddings.shape}")
    
    # Test de similarité
    query = "Comment sécuriser un réseau IoT ?"
    query_emb = embedder.generate_embedding(query)
    
    print(f"\n🔍 Requête: {query}")
    results = embedder.find_most_similar(query_emb, embeddings, top_k=3)
    
    print("\nRésultats les plus similaires:")
    for idx, score in results:
        print(f"  [{score:.3f}] {texts[idx]}")
    
    # Informations modèle
    print(f"\n📋 Info modèle: {embedder.get_model_info()}")