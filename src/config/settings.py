"""
Configuration globale du système RAG INPT
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration principale du système"""
    
    # Informations Projet
    PROJECT_NAME: str = "Assistant Éducatif RAG - INPT Smart ICT"
    VERSION: str = "1.0.0"
    LANGUAGE: str = "fr"
    
    # Chemins
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    DATABASE_DIR: Path = BASE_DIR / "database"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MIN_CHUNK_SIZE: int = 100
    SUPPORTED_FORMATS: List[str] = [".pdf", ".txt", ".md", ".docx"]
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    BATCH_SIZE: int = 32
    
    # ChromaDB
    CHROMA_PERSIST_DIR: Path = DATABASE_DIR / "chroma_db"
    CHROMA_COLLECTION_NAME: str = "inpt_smart_ict_docs"
    
    # SQLite
    SQLITE_DB_PATH: Path = DATABASE_DIR / "metadata.db"
    SQLITE_DB_URL: str = f"sqlite:///{SQLITE_DB_PATH}"
    
    # Retrieval
    TOP_K_RETRIEVAL: int = 5  # Réduit de 10 à 5 pour moins de bruit
    SIMILARITY_THRESHOLD: float = 0.4  # Augmenté de 0.3 à 0.4 pour meilleure qualité
    BM25_WEIGHT: float = 0.3
    SEMANTIC_WEIGHT: float = 0.7
    RERANK_TOP_K: int = 3  # Réduit de 5 à 3 pour réponses plus focalisées
    
    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"  # Modèle par défaut (ou llama3:latest)
    OLLAMA_TIMEOUT: int = 120
    LLM_TEMPERATURE: float = 0.3  # Réduit de 0.7 à 0.3 pour réponses plus focalisées
    LLM_MAX_TOKENS: int = 1000  # Réduit de 2000 à 1000 pour réponses plus concises
    
    # Conversation
    MAX_CONVERSATION_HISTORY: int = 10
    CONTEXT_WINDOW_SIZE: int = 4096
    
    # Query Enhancement
    ENABLE_SPELLING_CORRECTION: bool = True
    ENABLE_QUERY_EXPANSION: bool = True
    
    # Analytics
    ENABLE_TRACKING: bool = True
    ENABLE_METRICS: bool = True
    
    # Streamlit
    STREAMLIT_PAGE_TITLE: str = "Assistant RAG - INPT Smart ICT"
    STREAMLIT_PAGE_ICON: str = "🎓"
    STREAMLIT_LAYOUT: str = "wide"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    
    # Performance
    MAX_WORKERS: int = 4
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # secondes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instance globale
settings = Settings()


# Création des dossiers nécessaires
def setup_directories():
    """Crée tous les dossiers nécessaires"""
    directories = [
        settings.DATA_DIR,
        settings.DOCUMENTS_DIR,
        settings.PROCESSED_DIR,
        settings.DATABASE_DIR,
        settings.LOGS_DIR,
        settings.CHROMA_PERSIST_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Dossiers initialisés dans: {settings.BASE_DIR}")


if __name__ == "__main__":
    setup_directories()
    print(f"Configuration chargée: {settings.PROJECT_NAME} v{settings.VERSION}")