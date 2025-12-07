"""
Interface ChromaDB pour stockage vectoriel
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    # Fallback to chromadb-client
    import chromadb
    Settings = chromadb.Settings if hasattr(chromadb, 'Settings') else None
    embedding_functions = chromadb.utils.embedding_functions if hasattr(chromadb, 'utils') else None
from loguru import logger
import numpy as np


class VectorStore:
    """
    Gestionnaire de base vectorielle avec ChromaDB
    Permet stockage, recherche et gestion d'embeddings
    """
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "documents",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialise le vector store
        
        Args:
            persist_directory: Chemin de persistance
            collection_name: Nom de la collection
            embedding_function: Fonction d'embedding (optionnel)
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Création du dossier si nécessaire
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialisation ChromaDB: {persist_directory}")
        
        # Configuration ChromaDB
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Fonction d'embedding par défaut (multilingual)
            if embedding_function is None:
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="paraphrase-multilingual-MiniLM-L12-v2"
                )
            else:
                self.embedding_function = embedding_function
            
            # Créer ou récupérer la collection
            self.collection = self._get_or_create_collection()
            
            logger.success(f"✅ Collection '{collection_name}' prête ({self.collection.count()} documents)")
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation ChromaDB: {e}")
            raise
    
    def _get_or_create_collection(self):
        """Récupère ou crée la collection"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Collection '{self.collection_name}' récupérée")
        except:
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "INPT Smart ICT Documents"}
            )
            logger.info(f"Collection '{self.collection_name}' créée")
        
        return collection
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Ajoute des documents à la collection
        
        Args:
            texts: Liste de textes
            metadatas: Liste de métadonnées
            ids: IDs personnalisés (optionnel)
            embeddings: Embeddings pré-calculés (optionnel)
            
        Returns:
            Liste des IDs ajoutés
        """
        if not texts:
            logger.warning("Aucun texte à ajouter")
            return []
        
        # Génération d'IDs si non fournis
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        try:
            logger.info(f"Ajout de {len(texts)} documents...")
            
            if embeddings is not None:
                # Avec embeddings pré-calculés
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                # Embeddings auto-générés par ChromaDB
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.success(f"✅ {len(texts)} documents ajoutés")
            return ids
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout: {e}")
            raise
    
    def search(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Recherche sémantique dans la collection
        
        Args:
            query_text: Texte de la requête
            n_results: Nombre de résultats
            where: Filtres sur métadonnées
            where_document: Filtres sur documents
            
        Returns:
            Dictionnaire avec ids, documents, metadatas, distances
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            # Reformater les résultats
            formatted_results = {
                'ids': results['ids'][0] if results['ids'] else [],
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else []
            }
            
            logger.info(f"Recherche: {len(formatted_results['ids'])} résultats trouvés")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            raise
    
    def search_by_embedding(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Recherche par vecteur d'embedding directement
        
        Args:
            query_embedding: Vecteur d'embedding
            n_results: Nombre de résultats
            where: Filtres sur métadonnées
            
        Returns:
            Dictionnaire avec résultats
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            formatted_results = {
                'ids': results['ids'][0] if results['ids'] else [],
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else []
            }
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par embedding: {e}")
            raise
    
    def get_by_ids(self, ids: List[str]) -> Dict:
        """Récupère des documents par leurs IDs"""
        try:
            results = self.collection.get(ids=ids)
            return results
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            raise
    
    def update_documents(
        self,
        ids: List[str],
        texts: Optional[List[str]] = None,
        metadatas: Optional[List[Dict]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """Met à jour des documents existants"""
        try:
            update_params = {'ids': ids}
            
            if texts is not None:
                update_params['documents'] = texts
            if metadatas is not None:
                update_params['metadatas'] = metadatas
            if embeddings is not None:
                update_params['embeddings'] = embeddings
            
            self.collection.update(**update_params)
            logger.info(f"✅ {len(ids)} documents mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour: {e}")
            raise
    
    def delete_documents(self, ids: List[str]):
        """Supprime des documents"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"✅ {len(ids)} documents supprimés")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            raise
    
    def delete_by_filter(self, where: Dict):
        """Supprime des documents selon un filtre"""
        try:
            self.collection.delete(where=where)
            logger.info(f"Documents supprimés avec filtre: {where}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            raise
    
    def count(self) -> int:
        """Retourne le nombre de documents"""
        return self.collection.count()
    
    def peek(self, limit: int = 10) -> Dict:
        """Aperçu des premiers documents"""
        try:
            return self.collection.peek(limit=limit)
        except Exception as e:
            logger.error(f"Erreur lors du peek: {e}")
            raise
    
    def reset(self):
        """Réinitialise la collection (ATTENTION: supprime tout)"""
        logger.warning("⚠️ Réinitialisation de la collection...")
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.success("✅ Collection réinitialisée")
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            raise
    
    def get_collection_stats(self) -> Dict:
        """Statistiques de la collection"""
        return {
            'name': self.collection_name,
            'count': self.count(),
            'persist_directory': str(self.persist_directory)
        }


# Test du VectorStore
if __name__ == "__main__":
    # Initialisation
    vector_store = VectorStore(
        persist_directory="./test_db",
        collection_name="test_collection"
    )
    
    # Ajout de documents
    texts = [
        "L'IoT révolutionne l'industrie 4.0",
        "Les capteurs intelligents collectent des données",
        "La sécurité des réseaux est cruciale",
        "Le cloud computing facilite le stockage"
    ]
    
    metadatas = [
        {'source': 'cours_iot.pdf', 'page': 1},
        {'source': 'cours_iot.pdf', 'page': 2},
        {'source': 'cours_secu.pdf', 'page': 5},
        {'source': 'cours_cloud.pdf', 'page': 3}
    ]
    
    ids = vector_store.add_documents(texts, metadatas)
    print(f"✅ Documents ajoutés: {ids}")
    
    # Recherche
    results = vector_store.search("Comment sécuriser un réseau ?", n_results=2)
    
    print("\n🔍 Résultats de recherche:")
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results['distances']
    )):
        print(f"{i+1}. [{dist:.3f}] {doc}")
        print(f"   Source: {meta['source']}, Page: {meta['page']}")
    
    # Stats
    print(f"\n📊 Stats: {vector_store.get_collection_stats()}")