"""
Configuration globale du système RAG INPT
"""
from pathlib import Path
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator
import os
import logging


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
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @field_validator('OLLAMA_BASE_URL')
    @classmethod
    def validate_ollama_url(cls, v):
        """Validate Ollama URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('OLLAMA_BASE_URL must start with http:// or https://')
        return v

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {valid_levels}')
        return v.upper()

    @field_validator('EMBEDDING_DIMENSION')
    @classmethod
    def validate_embedding_dimension(cls, v):
        """Validate embedding dimension is positive"""
        if v <= 0:
            raise ValueError('EMBEDDING_DIMENSION must be positive')
        return v

    @field_validator('CHUNK_SIZE')
    @classmethod
    def validate_chunk_size(cls, v):
        """Validate chunk size is reasonable"""
        if v < 100 or v > 10000:
            raise ValueError('CHUNK_SIZE must be between 100 and 10000')
        return v


# Instance globale
settings = Settings()


def validate_environment_configuration() -> Dict[str, Any]:
    """
    Validate environment configuration and detect Docker environment
    Returns validation results and environment information
    """
    validation_results = {
        "is_docker": False,
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "environment_type": "local"
    }
    
    # Detect Docker environment
    docker_indicators = [
        os.path.exists('/.dockerenv'),
        os.environ.get('PYTHONUNBUFFERED') == '1',
        'docker' in os.environ.get('HOSTNAME', '').lower(),
        settings.OLLAMA_BASE_URL.startswith('http://ollama:')
    ]
    
    if any(docker_indicators):
        validation_results["is_docker"] = True
        validation_results["environment_type"] = "docker"
    
    # Validate required directories exist or can be created
    required_dirs = [
        settings.DATA_DIR,
        settings.DOCUMENTS_DIR,
        settings.PROCESSED_DIR,
        settings.DATABASE_DIR,
        settings.LOGS_DIR
    ]
    
    for directory in required_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            validation_results["errors"].append(f"Cannot create directory {directory}: {e}")
            validation_results["is_valid"] = False
    
    # Validate Ollama configuration
    if validation_results["is_docker"]:
        if not settings.OLLAMA_BASE_URL.startswith('http://ollama:'):
            validation_results["warnings"].append(
                "In Docker environment, OLLAMA_BASE_URL should use service name 'ollama'"
            )
    else:
        if not settings.OLLAMA_BASE_URL.startswith('http://localhost:'):
            validation_results["warnings"].append(
                "In local environment, OLLAMA_BASE_URL should use 'localhost'"
            )
    
    # Validate file paths for Docker
    if validation_results["is_docker"]:
        container_paths = ['/app/data', '/app/database', '/app/logs']
        for path in container_paths:
            if not os.path.exists(path):
                validation_results["warnings"].append(f"Docker volume path {path} not found")
    
    # Validate model configuration
    if not settings.OLLAMA_MODEL:
        validation_results["errors"].append("OLLAMA_MODEL is required")
        validation_results["is_valid"] = False
    
    # Validate embedding model
    if not settings.EMBEDDING_MODEL:
        validation_results["errors"].append("EMBEDDING_MODEL is required")
        validation_results["is_valid"] = False
    
    return validation_results


def log_environment_validation():
    """Log environment validation results"""
    results = validate_environment_configuration()
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"Environment type: {results['environment_type']}")
    logger.info(f"Docker environment: {results['is_docker']}")
    logger.info(f"Configuration valid: {results['is_valid']}")
    
    for error in results["errors"]:
        logger.error(f"Configuration error: {error}")
    
    for warning in results["warnings"]:
        logger.warning(f"Configuration warning: {warning}")
    
    return results


# Création des dossiers nécessaires
def setup_directories():
    """Crée tous les dossiers nécessaires et valide la configuration"""
    # Validate environment first
    validation_results = validate_environment_configuration()
    
    if not validation_results["is_valid"]:
        print("❌ Configuration validation failed:")
        for error in validation_results["errors"]:
            print(f"  - {error}")
        return False
    
    # Log warnings if any
    if validation_results["warnings"]:
        print("⚠️  Configuration warnings:")
        for warning in validation_results["warnings"]:
            print(f"  - {warning}")
    
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
    
    env_type = "🐳 Docker" if validation_results["is_docker"] else "💻 Local"
    print(f"✅ Dossiers initialisés dans: {settings.BASE_DIR} ({env_type})")
    return True


if __name__ == "__main__":
    if setup_directories():
        print(f"Configuration chargée: {settings.PROJECT_NAME} v{settings.VERSION}")
        
        # Log detailed validation results
        validation_results = log_environment_validation()
        
        if validation_results["is_docker"]:
            print("🐳 Running in Docker environment")
        else:
            print("💻 Running in local environment")
    else:
        print("❌ Setup failed due to configuration errors")
        exit(1)