"""Interface SQLite pour les métadonnées"""
import sqlite3
from typing import List, Dict, Any
try:
    from ..config.settings import settings
except ImportError:
    from config.settings import settings


class MetadataStore:
    """Gestion des métadonnées avec SQLite"""
    
    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialise la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT,
                    filepath TEXT,
                    format TEXT,
                    size INTEGER,
                    created_at TEXT,
                    modified_at TEXT,
                    processed_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    chunk_id INTEGER,
                    content TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """)
    
    def add_document(self, doc_id: str, metadata: Dict[str, Any]):
        """Ajoute un document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, filename, filepath, format, size, created_at, modified_at, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                metadata.get("filename"),
                metadata.get("filepath"),
                metadata.get("format"),
                metadata.get("size"),
                metadata.get("created_at"),
                metadata.get("modified_at"),
                metadata.get("processed_at")
            ))
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Récupère un document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """Liste tous les documents"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM documents")
            return [dict(row) for row in cursor.fetchall()]
