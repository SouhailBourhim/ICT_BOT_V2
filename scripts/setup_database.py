"""Script de setup des bases de données"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storage import VectorStore, MetadataStore
from config.settings import settings


def setup_databases():
    """Initialise les bases de données"""
    print("Initialisation des bases de données...")
    
    # Créer les répertoires
    settings.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialiser ChromaDB
    print("- ChromaDB...")
    vector_store = VectorStore(
        persist_directory=str(settings.CHROMA_PERSIST_DIR),
        collection_name=settings.CHROMA_COLLECTION_NAME
    )
    print(f"  ✓ Collection '{settings.CHROMA_COLLECTION_NAME}' créée")
    
    # Initialiser SQLite
    print("- SQLite...")
    metadata_store = MetadataStore()
    print(f"  ✓ Base de métadonnées créée")
    
    print("\n✓ Bases de données initialisées avec succès!")


if __name__ == "__main__":
    setup_databases()
