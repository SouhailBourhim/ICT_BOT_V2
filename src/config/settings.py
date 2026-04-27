"""
Configuration globale du système RAG INPT
"""
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration principale du système"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
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
    SQLITE_DB_URL: str | None = None
    
    # Retrieval
    TOP_K_RETRIEVAL: int = 7  # Augmenté pour meilleur concept coverage
    SIMILARITY_THRESHOLD: float = 0.4  # Augmenté de 0.3 à 0.4 pour meilleure qualité
    BM25_WEIGHT: float = 0.3
    SEMANTIC_WEIGHT: float = 0.7
    RERANK_TOP_K: int = 3  # Réduit de 5 à 3 pour réponses plus focalisées
    
    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"  # Meilleur pour RAG, moins d'hallucinations
    OLLAMA_TIMEOUT: int = 180  # Plus long pour 3B params
    LLM_TEMPERATURE: float = 0.1  # Légèrement plus créatif que 0.0
    LLM_MAX_TOKENS: int = 500  # Augmenté pour réponses plus complètes
    
    # Conversation
    MAX_CONVERSATION_HISTORY: int = 6  # Réduit de 10 à 6 pour éviter la pollution du contexte
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
    
    @field_validator(
        "CHUNK_SIZE",
        "MIN_CHUNK_SIZE",
        "EMBEDDING_DIMENSION",
        "BATCH_SIZE",
        "TOP_K_RETRIEVAL",
        "RERANK_TOP_K",
        "OLLAMA_TIMEOUT",
        "LLM_MAX_TOKENS",
        "MAX_CONVERSATION_HISTORY",
        "CONTEXT_WINDOW_SIZE",
        "MAX_WORKERS",
        "CACHE_TTL",
    )
    @classmethod
    def _must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value

    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def _chunk_overlap_not_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("must be greater than or equal to 0")
        return value

    @field_validator(
        "SIMILARITY_THRESHOLD",
        "BM25_WEIGHT",
        "SEMANTIC_WEIGHT",
        "LLM_TEMPERATURE",
    )
    @classmethod
    def _must_be_probability(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("must be between 0 and 1")
        return value

    @field_validator("SUPPORTED_FORMATS")
    @classmethod
    def _formats_must_be_extensions(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("must contain at least one extension")
        invalid = [ext for ext in value if not ext.startswith(".")]
        if invalid:
            raise ValueError(f"extensions must start with '.': {invalid}")
        return value

    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def _ollama_base_url_must_be_http(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("must be an absolute http(s) URL")
        return value.rstrip("/")

    @field_validator("LOG_LEVEL")
    @classmethod
    def _log_level_must_be_known(cls, value: str) -> str:
        normalized = value.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in valid_levels:
            raise ValueError(f"must be one of {sorted(valid_levels)}")
        return normalized

    @model_validator(mode="after")
    def _validate_related_settings(self):
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

        if self.MIN_CHUNK_SIZE > self.CHUNK_SIZE:
            raise ValueError("MIN_CHUNK_SIZE must be smaller than or equal to CHUNK_SIZE")

        if abs((self.SEMANTIC_WEIGHT + self.BM25_WEIGHT) - 1.0) > 0.001:
            raise ValueError("SEMANTIC_WEIGHT and BM25_WEIGHT must sum to 1.0")

        if self.RERANK_TOP_K > self.TOP_K_RETRIEVAL:
            raise ValueError("RERANK_TOP_K must be smaller than or equal to TOP_K_RETRIEVAL")

        if not self.SQLITE_DB_URL:
            self.SQLITE_DB_URL = f"sqlite:///{self.SQLITE_DB_PATH}"

        return self


# Instance globale
settings = Settings()


# Création des dossiers nécessaires
def setup_directories():
    """Crée tous les dossiers nécessaires"""
    directories = [
        settings.DATA_DIR,
        settings.DOCUMENTS_DIR,
        settings.DATA_DIR / "conversations",
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
