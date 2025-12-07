"""Modèles de données"""
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime


@dataclass
class Document:
    """Modèle de document"""
    id: str
    filename: str
    filepath: str
    format: str
    size: int
    created_at: datetime
    modified_at: datetime
    processed_at: datetime
    metadata: Dict[str, Any] = None


@dataclass
class Chunk:
    """Modèle de chunk"""
    id: str
    document_id: str
    chunk_id: int
    content: str
    embedding: List[float] = None
    metadata: Dict[str, Any] = None
