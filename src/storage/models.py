"""Modèles de données"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


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
    # Enhanced fields for contextual headers and structure
    contextual_header: str = ""
    hierarchy_path: List[str] = field(default_factory=list)
    structure_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default values for new fields"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EnhancedChunk(Chunk):
    """Enhanced chunk with contextual information - extends base Chunk for compatibility"""
    
    @classmethod
    def from_chunk(cls, chunk: Chunk, contextual_header: str = "", 
                   hierarchy_path: List[str] = None, 
                   structure_metadata: Dict[str, Any] = None) -> 'EnhancedChunk':
        """Create EnhancedChunk from existing Chunk"""
        return cls(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata or {},
            contextual_header=contextual_header,
            hierarchy_path=hierarchy_path or [],
            structure_metadata=structure_metadata or {}
        )
    
    def to_storage_metadata(self) -> Dict[str, Any]:
        """Convert enhanced chunk to storage-compatible metadata"""
        storage_metadata = dict(self.metadata)
        
        # Add enhanced fields to metadata for storage
        if self.contextual_header:
            storage_metadata['contextual_header'] = self.contextual_header
        
        if self.hierarchy_path:
            # Serialize list as JSON string for ChromaDB compatibility
            storage_metadata['hierarchy_path'] = json.dumps(self.hierarchy_path)
        else:
            storage_metadata['hierarchy_path'] = '[]'
        
        if self.structure_metadata:
            # Serialize dict as JSON string for ChromaDB compatibility
            storage_metadata['structure_metadata'] = json.dumps(self.structure_metadata)
        else:
            storage_metadata['structure_metadata'] = '{}'
        
        # Handle other list/dict fields that might be in metadata
        for key, value in list(storage_metadata.items()):
            if isinstance(value, list):
                # Serialize lists as JSON strings
                storage_metadata[key] = json.dumps(value)
            elif isinstance(value, dict):
                # Serialize all dicts as JSON strings for ChromaDB compatibility
                storage_metadata[key] = json.dumps(value)
            
        return storage_metadata
    
    @classmethod
    def from_storage_metadata(cls, chunk_id: str, document_id: str, 
                             chunk_index: int, content: str, 
                             metadata: Dict[str, Any], 
                             embedding: List[float] = None) -> 'EnhancedChunk':
        """Create EnhancedChunk from storage metadata"""
        # Extract enhanced fields from metadata
        contextual_header = metadata.pop('contextual_header', '')
        
        # Deserialize JSON strings back to Python objects
        hierarchy_path_str = metadata.pop('hierarchy_path', '[]')
        try:
            hierarchy_path = json.loads(hierarchy_path_str) if hierarchy_path_str else []
        except (json.JSONDecodeError, TypeError):
            hierarchy_path = []
        
        structure_metadata_str = metadata.pop('structure_metadata', '{}')
        try:
            structure_metadata = json.loads(structure_metadata_str) if structure_metadata_str else {}
        except (json.JSONDecodeError, TypeError):
            structure_metadata = {}
        
        return cls(
            id=chunk_id,
            document_id=document_id,
            chunk_id=chunk_index,
            content=content,
            embedding=embedding,
            metadata=metadata,
            contextual_header=contextual_header,
            hierarchy_path=hierarchy_path,
            structure_metadata=structure_metadata
        )


def is_enhanced_chunk(metadata: Dict[str, Any]) -> bool:
    """Check if chunk metadata contains enhanced fields"""
    enhanced_fields = ['contextual_header', 'hierarchy_path', 'structure_metadata']
    return any(field in metadata for field in enhanced_fields)


def migrate_chunk_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old chunk metadata to new format with enhanced fields"""
    if is_enhanced_chunk(metadata):
        return metadata  # Already enhanced
    
    # Add default enhanced fields for backward compatibility
    enhanced_metadata = dict(metadata)
    enhanced_metadata.setdefault('contextual_header', '')
    enhanced_metadata.setdefault('hierarchy_path', '[]')  # Store as JSON string
    enhanced_metadata.setdefault('structure_metadata', '{}')  # Store as JSON string
    
    return enhanced_metadata
