"""
Backward compatibility layer for handling existing chunks without contextual headers
"""
from typing import List, Dict, Any, Optional, Union
from loguru import logger
import json

from .models import Chunk, EnhancedChunk, is_enhanced_chunk, migrate_chunk_metadata


class ChunkCompatibilityLayer:
    """
    Compatibility layer for handling both old and new chunk formats
    
    This class provides seamless handling of:
    - Legacy chunks without contextual headers
    - New enhanced chunks with contextual headers
    - Mixed format scenarios during transition
    """
    
    def __init__(self):
        """Initialize the compatibility layer"""
        self.legacy_chunk_count = 0
        self.enhanced_chunk_count = 0
        logger.info("Chunk compatibility layer initialized")
    
    def detect_chunk_format(self, metadata: Dict[str, Any]) -> str:
        """
        Detect whether a chunk uses old or new format
        
        Args:
            metadata: Chunk metadata dictionary
            
        Returns:
            'enhanced' if chunk has contextual headers, 'legacy' otherwise
        """
        if is_enhanced_chunk(metadata):
            return 'enhanced'
        return 'legacy'
    
    def normalize_chunk_data(
        self, 
        chunk_id: str, 
        document_id: str, 
        chunk_index: int, 
        content: str, 
        metadata: Dict[str, Any], 
        embedding: Optional[List[float]] = None
    ) -> EnhancedChunk:
        """
        Normalize chunk data to EnhancedChunk format regardless of source format
        
        Args:
            chunk_id: Unique chunk identifier
            document_id: Document identifier
            chunk_index: Chunk index within document
            content: Chunk text content
            metadata: Chunk metadata
            embedding: Optional embedding vector
            
        Returns:
            EnhancedChunk instance with proper format
        """
        chunk_format = self.detect_chunk_format(metadata)
        
        if chunk_format == 'enhanced':
            # Already enhanced format
            self.enhanced_chunk_count += 1
            return EnhancedChunk.from_storage_metadata(
                chunk_id, document_id, chunk_index, content, metadata, embedding
            )
        else:
            # Legacy format - needs migration
            self.legacy_chunk_count += 1
            migrated_metadata = migrate_chunk_metadata(metadata)
            
            # Create enhanced chunk from legacy data
            enhanced_chunk = EnhancedChunk.from_storage_metadata(
                chunk_id, document_id, chunk_index, content, migrated_metadata, embedding
            )
            
            # Log migration for debugging
            logger.debug(f"Migrated legacy chunk {chunk_id} to enhanced format")
            
            return enhanced_chunk
    
    def prepare_chunk_for_storage(self, chunk: Union[Chunk, EnhancedChunk]) -> Dict[str, Any]:
        """
        Prepare chunk for storage in vector database
        
        Args:
            chunk: Chunk instance (legacy or enhanced)
            
        Returns:
            Storage-compatible metadata dictionary
        """
        if isinstance(chunk, EnhancedChunk):
            # Enhanced chunk - use its storage method
            return chunk.to_storage_metadata()
        else:
            # Legacy chunk - migrate and prepare
            migrated_metadata = migrate_chunk_metadata(chunk.metadata or {})
            
            # Create temporary enhanced chunk for storage preparation
            temp_enhanced = EnhancedChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                embedding=chunk.embedding,
                metadata=migrated_metadata,
                contextual_header="",  # No header for legacy chunks
                hierarchy_path=[],
                structure_metadata={}
            )
            
            return temp_enhanced.to_storage_metadata()
    
    def format_chunk_for_display(self, chunk: Union[Chunk, EnhancedChunk]) -> Dict[str, Any]:
        """
        Format chunk for display in UI components
        
        Args:
            chunk: Chunk instance (legacy or enhanced)
            
        Returns:
            Display-formatted dictionary
        """
        # Base display format
        display_data = {
            'id': chunk.id,
            'content': chunk.content,
            'metadata': chunk.metadata or {},
            'has_contextual_header': False,
            'contextual_header': '',
            'hierarchy_path': [],
            'display_title': self._generate_display_title(chunk)
        }
        
        # Enhanced format specific fields
        if isinstance(chunk, EnhancedChunk):
            display_data.update({
                'has_contextual_header': bool(chunk.contextual_header),
                'contextual_header': chunk.contextual_header,
                'hierarchy_path': chunk.hierarchy_path,
                'structure_metadata': chunk.structure_metadata
            })
            
            # Use contextual header for display if available
            if chunk.contextual_header:
                display_data['display_title'] = chunk.contextual_header
        
        return display_data
    
    def _generate_display_title(self, chunk: Union[Chunk, EnhancedChunk]) -> str:
        """
        Generate a display title for chunks without contextual headers
        
        Args:
            chunk: Chunk instance
            
        Returns:
            Generated display title
        """
        metadata = chunk.metadata or {}
        
        # Try to build title from available metadata
        title_parts = []
        
        # Add filename if available
        filename = metadata.get('filename') or metadata.get('source')
        if filename:
            title_parts.append(f"File: {filename}")
        
        # Add page number if available
        page_num = metadata.get('page_number') or metadata.get('page')
        if page_num:
            title_parts.append(f"Page: {page_num}")
        
        # Add section if available
        section = metadata.get('section')
        if section:
            title_parts.append(f"Section: {section}")
        
        # Add chunk index as fallback
        if not title_parts:
            chunk_idx = getattr(chunk, 'chunk_id', 0)
            title_parts.append(f"Chunk: {chunk_idx + 1}")
        
        return " > ".join(title_parts)
    
    def extract_clean_content(self, chunk: Union[Chunk, EnhancedChunk]) -> str:
        """
        Extract clean content without contextual headers for processing
        
        Args:
            chunk: Chunk instance
            
        Returns:
            Clean content text without contextual headers
        """
        content = chunk.content
        
        # For enhanced chunks, try to extract original content
        if isinstance(chunk, EnhancedChunk) and chunk.contextual_header:
            # Remove contextual header from content if present
            if content.startswith(chunk.contextual_header):
                # Remove header and any following newlines
                clean_content = content[len(chunk.contextual_header):].lstrip('\n')
                return clean_content
        
        # Check metadata for original text
        if hasattr(chunk, 'metadata') and chunk.metadata:
            original_text = chunk.metadata.get('original_text')
            if original_text:
                return original_text
        
        # Return content as-is for legacy chunks
        return content
    
    def get_compatibility_stats(self) -> Dict[str, Any]:
        """
        Get statistics about chunk format compatibility
        
        Returns:
            Dictionary with compatibility statistics
        """
        total_chunks = self.legacy_chunk_count + self.enhanced_chunk_count
        
        return {
            'total_chunks_processed': total_chunks,
            'legacy_chunks': self.legacy_chunk_count,
            'enhanced_chunks': self.enhanced_chunk_count,
            'legacy_percentage': (self.legacy_chunk_count / total_chunks * 100) if total_chunks > 0 else 0,
            'enhanced_percentage': (self.enhanced_chunk_count / total_chunks * 100) if total_chunks > 0 else 0
        }
    
    def batch_normalize_chunks(
        self, 
        raw_chunks: List[Dict[str, Any]]
    ) -> List[EnhancedChunk]:
        """
        Batch normalize multiple chunks to EnhancedChunk format
        
        Args:
            raw_chunks: List of raw chunk data dictionaries
            
        Returns:
            List of normalized EnhancedChunk instances
        """
        normalized_chunks = []
        
        for raw_chunk in raw_chunks:
            try:
                # Extract required fields
                chunk_id = raw_chunk.get('id', '')
                document_id = raw_chunk.get('document_id', '')
                chunk_index = raw_chunk.get('chunk_id', 0)
                content = raw_chunk.get('content', '')
                metadata = raw_chunk.get('metadata', {})
                embedding = raw_chunk.get('embedding')
                
                # Normalize to enhanced format
                enhanced_chunk = self.normalize_chunk_data(
                    chunk_id, document_id, chunk_index, content, metadata, embedding
                )
                
                normalized_chunks.append(enhanced_chunk)
                
            except Exception as e:
                logger.error(f"Failed to normalize chunk {raw_chunk.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Normalized {len(normalized_chunks)} chunks to enhanced format")
        return normalized_chunks
    
    def handle_mixed_search_results(
        self, 
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Handle search results that may contain mixed chunk formats
        
        Args:
            search_results: Raw search results from vector store
            
        Returns:
            Normalized search results with consistent format
        """
        normalized_results = []
        
        for result in search_results:
            try:
                # Extract metadata
                metadata = result.get('metadata', {})
                content = result.get('content', '')
                
                # Detect format and normalize display
                chunk_format = self.detect_chunk_format(metadata)
                
                # Create a temporary chunk for formatting
                if chunk_format == 'enhanced':
                    temp_chunk = EnhancedChunk.from_storage_metadata(
                        result.get('id', ''),
                        metadata.get('document_id', ''),
                        metadata.get('chunk_id', 0),
                        content,
                        metadata
                    )
                else:
                    # Legacy chunk
                    temp_chunk = Chunk(
                        id=result.get('id', ''),
                        document_id=metadata.get('document_id', ''),
                        chunk_id=metadata.get('chunk_id', 0),
                        content=content,
                        metadata=metadata,
                        embedding=None
                    )
                
                # Format for display
                display_data = self.format_chunk_for_display(temp_chunk)
                
                # Preserve original search result fields
                normalized_result = {
                    **result,  # Keep original fields like score, distance
                    **display_data,  # Add normalized display fields
                    'chunk_format': chunk_format,
                    'clean_content': self.extract_clean_content(temp_chunk)
                }
                
                normalized_results.append(normalized_result)
                
            except Exception as e:
                logger.error(f"Failed to normalize search result {result.get('id', 'unknown')}: {e}")
                # Include original result as fallback
                normalized_results.append({
                    **result,
                    'chunk_format': 'unknown',
                    'has_contextual_header': False,
                    'display_title': 'Unknown Document',
                    'clean_content': result.get('content', '')
                })
        
        return normalized_results


# Global compatibility layer instance
compatibility_layer = ChunkCompatibilityLayer()