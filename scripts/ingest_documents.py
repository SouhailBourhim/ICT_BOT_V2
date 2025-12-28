"""
Script d'ingestion de documents dans le système RAG
Traite PDF, TXT, MD, DOCX et les indexe dans ChromaDB
"""
from pathlib import Path
import sys
from typing import List
from tqdm import tqdm
from loguru import logger

# Ajout du path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.document_processing.parser import DocumentParser
from src.document_processing.chunker import SemanticChunker
from src.document_processing.embedding_generator import EmbeddingGenerator
from src.storage.vector_store import VectorStore
from src.storage.models import EnhancedChunk, is_enhanced_chunk, migrate_chunk_metadata
from src.retrieval.hybrid_search import HybridSearchEngine


class DocumentIngestion:
    """Pipeline d'ingestion de documents"""
    
    def __init__(self):
        """Initialise le pipeline d'ingestion"""
        logger.info("🚀 Initialisation du pipeline d'ingestion")
        
        # 1. Parser
        self.parser = DocumentParser()
        
        # 2. Chunker
        self.chunker = SemanticChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            min_chunk_size=settings.MIN_CHUNK_SIZE
        )
        
        # 3. Embedding Generator
        self.embedder = EmbeddingGenerator(
            model_name=settings.EMBEDDING_MODEL,
            batch_size=settings.BATCH_SIZE
        )
        
        # 4. Vector Store
        self.vector_store = VectorStore(
            persist_directory=str(settings.CHROMA_PERSIST_DIR),
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        # 5. Hybrid Search (pour BM25)
        self.hybrid_search = HybridSearchEngine(
            vector_store=self.vector_store,
            semantic_weight=settings.SEMANTIC_WEIGHT,
            bm25_weight=settings.BM25_WEIGHT
        )
        
        logger.success("✅ Pipeline initialisé")
    
    def ingest_document(self, file_path: Path) -> int:
        """
        Ingère un document unique
        
        Args:
            file_path: Chemin vers le document
            
        Returns:
            Nombre de chunks créés
        """
        logger.info(f"📄 Traitement de: {file_path.name}")
        
        try:
            # 1. Parsing
            parsed_doc = self.parser.parse(file_path)
            logger.info(f"  ✓ Parsing: {len(parsed_doc.content)} caractères")
            
            # 2. Chunking
            if parsed_doc.pages:
                # Pour les PDFs avec structure de pages
                chunks = self.chunker.chunk_with_pages(
                    pages_data=parsed_doc.pages,
                    doc_metadata=parsed_doc.metadata
                )
            else:
                # Pour les autres formats
                chunks = self.chunker.chunk_text(
                    text=parsed_doc.content,
                    doc_metadata=parsed_doc.metadata,
                    preserve_structure=True
                )
            
            logger.info(f"  ✓ Chunking: {len(chunks)} chunks créés")
            
            if not chunks:
                logger.warning(f"  ⚠️ Aucun chunk créé pour {file_path.name}")
                return 0
            
            # 3. Génération d'embeddings
            texts = []
            for chunk in chunks:
                # Extract text from chunk (handle both old and new formats)
                if hasattr(chunk, 'content'):
                    texts.append(chunk.content)  # EnhancedChunk format
                elif hasattr(chunk, 'text'):
                    texts.append(chunk.text)     # Legacy Chunk format
                else:
                    logger.warning(f"Unknown chunk format for chunk {i}")
                    continue
                    
            embeddings = self.embedder.generate_embeddings_batch(
                texts=texts,
                show_progress=True
            )
            logger.info(f"  ✓ Embeddings: {len(embeddings)} générés")
            
            # 4. Préparation des métadonnées
            metadatas = []
            ids = []
            
            # Generate unique IDs
            import uuid
            for i, chunk in enumerate(chunks):
                # Create unique ID using filename and index
                unique_id = f"{file_path.stem}_{i}_{uuid.uuid4().hex[:8]}"
                
                # Use enhanced chunk's storage metadata method if available
                if hasattr(chunk, 'to_storage_metadata'):
                    storage_metadata = chunk.to_storage_metadata()
                else:
                    # Fallback for legacy chunks
                    storage_metadata = chunk.metadata.copy() if hasattr(chunk, 'metadata') else {}
                
                # Ensure required fields are present
                storage_metadata.update({
                    'chunk_id': unique_id,
                    'filename': chunk.metadata.get('filename') if hasattr(chunk, 'metadata') else parsed_doc.metadata.get('filename'),
                    'filepath': chunk.metadata.get('filepath') if hasattr(chunk, 'metadata') else parsed_doc.metadata.get('filepath'),
                    'page_number': chunk.metadata.get('page_number', '') if hasattr(chunk, 'metadata') else '',
                    'section': chunk.metadata.get('section', '') if hasattr(chunk, 'metadata') else '',
                    'format': chunk.metadata.get('format') if hasattr(chunk, 'metadata') else parsed_doc.metadata.get('format'),
                })
                
                # Add statistical fields if not already present
                chunk_text = chunk.content if hasattr(chunk, 'content') else chunk.text
                if 'char_count' not in storage_metadata:
                    storage_metadata['char_count'] = len(chunk_text)
                if 'word_count' not in storage_metadata:
                    storage_metadata['word_count'] = len(chunk_text.split())
                if 'token_count' not in storage_metadata:
                    storage_metadata['token_count'] = len(chunk_text) // 4
                
                metadatas.append(storage_metadata)
                ids.append(unique_id)
            
            # 5. Ajout au vector store
            self.vector_store.add_documents(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings.tolist()
            )
            logger.info(f"  ✓ Stockage: {len(texts)} chunks ajoutés à ChromaDB")
            
            # 6. Indexation BM25
            documents_for_bm25 = []
            for chunk_id, text, meta in zip(ids, texts, metadatas):
                documents_for_bm25.append({
                    'id': chunk_id,
                    'text': text,
                    'metadata': meta
                })
            
            # Note: On devrait accumuler tous les documents puis indexer BM25 à la fin
            # Pour l'instant, on peut sauter cette étape et l'indexer lors du premier usage
            
            logger.success(f"✅ {file_path.name}: {len(chunks)} chunks ingérés")
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de {file_path.name}: {e}")
            return 0
    
    def ingest_directory(self, directory: Path, recursive: bool = True) -> dict:
        """
        Ingère tous les documents d'un répertoire
        
        Args:
            directory: Répertoire source
            recursive: Parcours récursif des sous-dossiers
            
        Returns:
            Statistiques d'ingestion
        """
        logger.info(f"📁 Ingestion du répertoire: {directory}")
        
        # Collecter les fichiers
        files = []
        for ext in settings.SUPPORTED_FORMATS:
            if recursive:
                files.extend(directory.rglob(f"*{ext}"))
            else:
                files.extend(directory.glob(f"*{ext}"))
        
        logger.info(f"📊 {len(files)} fichiers trouvés")
        
        if not files:
            logger.warning("Aucun fichier à traiter")
            return {'total': 0, 'success': 0, 'failed': 0, 'chunks': 0}
        
        # Ingestion avec barre de progression
        stats = {
            'total': len(files),
            'success': 0,
            'failed': 0,
            'chunks': 0
        }
        
        for file_path in tqdm(files, desc="Ingestion"):
            try:
                num_chunks = self.ingest_document(file_path)
                if num_chunks > 0:
                    stats['success'] += 1
                    stats['chunks'] += num_chunks
                else:
                    stats['failed'] += 1
            except Exception as e:
                logger.error(f"Erreur: {e}")
                stats['failed'] += 1
        
        # Indexation BM25 finale
        logger.info("🔍 Indexation BM25...")
        self._index_bm25()
        
        # Rapport final
        logger.info("=" * 60)
        logger.info("📊 RAPPORT D'INGESTION")
        logger.info("=" * 60)
        logger.info(f"Fichiers traités: {stats['total']}")
        logger.info(f"  ✅ Succès: {stats['success']}")
        logger.info(f"  ❌ Échecs: {stats['failed']}")
        logger.info(f"  📦 Chunks créés: {stats['chunks']}")
        logger.info(f"  💾 Total en base: {self.vector_store.count()}")
        logger.info("=" * 60)
        
        return stats
    
    def _index_bm25(self):
        """Indexe tous les documents pour BM25"""
        try:
            # Récupérer tous les documents
            all_docs = self.vector_store.peek(limit=self.vector_store.count())
            
            if not all_docs or not all_docs.get('documents'):
                logger.warning("Aucun document à indexer pour BM25")
                return
            
            # Préparer les documents pour BM25
            documents = []
            for doc_id, text, metadata in zip(
                all_docs['ids'],
                all_docs['documents'],
                all_docs['metadatas']
            ):
                documents.append({
                    'id': doc_id,
                    'text': text,
                    'metadata': metadata
                })
            
            # Indexation
            self.hybrid_search.index_documents(documents)
            logger.success(f"✅ {len(documents)} documents indexés pour BM25")
            
        except Exception as e:
            logger.error(f"Erreur indexation BM25: {e}")
    
    def reset_database(self):
        """Réinitialise complètement la base de données"""
        logger.warning("⚠️ RÉINITIALISATION DE LA BASE")
        confirmation = input("Confirmer la suppression de tous les documents? (oui/non): ")
        
        if confirmation.lower() == 'oui':
            self.vector_store.reset()
            logger.success("✅ Base réinitialisée")
        else:
            logger.info("Opération annulée")
    
    def migrate_existing_chunks(self):
        """Migrate existing chunks to enhanced format with backward compatibility"""
        logger.info("🔄 Checking for chunks that need migration to enhanced format")
        
        try:
            # Get all existing documents
            all_docs = self.vector_store.peek(limit=self.vector_store.count())
            
            if not all_docs or not all_docs.get('documents'):
                logger.info("No existing chunks found to migrate")
                return
            
            migration_count = 0
            
            for doc_id, text, metadata in zip(
                all_docs['ids'],
                all_docs['documents'], 
                all_docs['metadatas']
            ):
                # Check if chunk needs migration
                if not is_enhanced_chunk(metadata):
                    # Migrate metadata to enhanced format
                    enhanced_metadata = migrate_chunk_metadata(metadata)
                    
                    # Update the chunk in vector store
                    self.vector_store.update_metadata(doc_id, enhanced_metadata)
                    migration_count += 1
            
            if migration_count > 0:
                logger.success(f"✅ Migrated {migration_count} chunks to enhanced format")
            else:
                logger.info("All chunks are already in enhanced format")
                
        except Exception as e:
            logger.error(f"Error during chunk migration: {e}")
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de la base"""
        return {
            'total_documents': self.vector_store.count(),
            'collection_name': settings.CHROMA_COLLECTION_NAME,
            'embedding_model': settings.EMBEDDING_MODEL,
            'embedding_dimension': settings.EMBEDDING_DIMENSION,
            'chunk_size': settings.CHUNK_SIZE,
            'chunk_overlap': settings.CHUNK_OVERLAP
        }


def main():
    """Fonction principale CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ingestion de documents dans le système RAG INPT"
    )
    
    parser.add_argument(
        'path',
        type=str,
        help='Chemin vers un fichier ou dossier à ingérer'
    )
    
    parser.add_argument(
        '--recursive',
        '-r',
        action='store_true',
        help='Parcours récursif des sous-dossiers'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Réinitialiser la base avant ingestion'
    )
    
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate existing chunks to enhanced format'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Afficher les statistiques uniquement'
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    logger.add(
        "logs/ingestion_{time}.log",
        rotation="10 MB",
        level="INFO"
    )
    
    # Initialisation
    ingestion = DocumentIngestion()
    
    # Migration if requested
    if args.migrate:
        ingestion.migrate_existing_chunks()
        return
    
    # Stats uniquement
    if args.stats:
        stats = ingestion.get_stats()
        print("\n📊 STATISTIQUES DE LA BASE")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("=" * 50)
        return
    
    # Reset si demandé
    if args.reset:
        ingestion.reset_database()
    
    # Vérification du path
    path = Path(args.path)
    
    if not path.exists():
        logger.error(f"❌ Chemin introuvable: {path}")
        sys.exit(1)
    
    # Ingestion
    if path.is_file():
        logger.info("Mode: Fichier unique")
        num_chunks = ingestion.ingest_document(path)
        logger.info(f"✅ Terminé: {num_chunks} chunks créés")
        
    elif path.is_dir():
        logger.info("Mode: Répertoire")
        stats = ingestion.ingest_directory(path, recursive=args.recursive)
        
    else:
        logger.error("❌ Type de chemin non supporté")
        sys.exit(1)
    
    # Stats finales
    final_stats = ingestion.get_stats()
    logger.info(f"\n💾 Total en base: {final_stats['total_documents']} chunks")


if __name__ == "__main__":
    # Exemples d'utilisation:
    # python scripts/ingest_documents.py data/documents
    # python scripts/ingest_documents.py data/documents --recursive
    # python scripts/ingest_documents.py data/documents/cours_iot.pdf
    # python scripts/ingest_documents.py --stats
    # python scripts/ingest_documents.py --migrate
    # python scripts/ingest_documents.py data/documents --reset
    
    main()