# Design Document

## Overview

This design refactors the existing ingestion pipeline to replace the custom SemanticChunker with LangChain's SemanticChunker implementation while adding contextual headers to improve retrieval accuracy. The solution maintains backward compatibility with existing indexed documents and preserves all current functionality while leveraging LangChain's robust text splitting capabilities.

## Architecture

The refactored system maintains the existing pipeline architecture with these key changes:

```
Document Input → Parser → LangChain SemanticChunker → Contextual Header Generator → Embedding Generator → Vector Store
```

### Component Interactions

1. **Document Parser**: Remains unchanged, continues to extract text and metadata
2. **LangChain SemanticChunker**: Replaces custom chunker, provides semantic-aware text splitting
3. **Contextual Header Generator**: New component that analyzes document structure and generates hierarchical headers
4. **Embedding Generator**: Remains unchanged, processes chunks with contextual headers
5. **Vector Store**: Remains unchanged, stores enhanced chunks with backward compatibility

## Components and Interfaces

### LangChainSemanticChunker

```python
class LangChainSemanticChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Initialize with LangChain's SemanticChunker"""
        
    def chunk_text(
        self, 
        text: str, 
        doc_metadata: Dict,
        preserve_structure: bool = True
    ) -> List[Chunk]:
        """Chunk text using LangChain's semantic approach"""
        
    def chunk_with_pages(
        self, 
        pages_data: List[Dict], 
        doc_metadata: Dict
    ) -> List[Chunk]:
        """Handle paginated documents with contextual headers"""
```

### ContextualHeaderGenerator

```python
class ContextualHeaderGenerator:
    def __init__(self):
        """Initialize structure detection patterns"""
        
    def generate_header(
        self, 
        chunk_text: str, 
        doc_metadata: Dict, 
        structure_info: Dict
    ) -> str:
        """Generate contextual header for a chunk"""
        
    def detect_structure(
        self, 
        text: str, 
        doc_type: str
    ) -> Dict:
        """Detect document structure (sections, pages, etc.)"""
        
    def extract_section_hierarchy(
        self, 
        text: str, 
        chunk_position: int
    ) -> Dict:
        """Extract hierarchical position of chunk within document"""
```

### Enhanced Chunk Model

```python
@dataclass
class EnhancedChunk(Chunk):
    """Extended chunk with contextual information"""
    contextual_header: str
    hierarchy_path: List[str]
    structure_metadata: Dict
```

## Data Models

### Chunk Structure with Contextual Headers

```python
{
    "text": "File: networking.pdf > Section: Subnetting\n\nSubnetting is the practice of dividing...",
    "metadata": {
        "chunk_id": "networking_pdf_section_2_chunk_1",
        "filename": "networking.pdf",
        "filepath": "/data/documents/networking.pdf",
        "page_number": 15,
        "section": "Subnetting",
        "section_hierarchy": ["Chapter 2: Network Design", "2.3 Subnetting"],
        "contextual_header": "File: networking.pdf > Section: Subnetting",
        "char_count": 850,
        "word_count": 142,
        "token_count": 213,
        "format": "pdf",
        "chunk_type": "semantic",
        "structure_confidence": 0.85
    },
    "chunk_id": "networking_pdf_section_2_chunk_1",
    "start_char": 12450,
    "end_char": 13300,
    "token_count": 213
}
```

### Structure Detection Schema

```python
{
    "document_type": "pdf",
    "has_sections": true,
    "has_pages": true,
    "section_hierarchy": [
        {
            "level": 1,
            "title": "Chapter 2: Network Design",
            "start_char": 10000,
            "end_char": 25000
        },
        {
            "level": 2,
            "title": "2.3 Subnetting",
            "start_char": 12000,
            "end_char": 18000,
            "parent": "Chapter 2: Network Design"
        }
    ],
    "page_breaks": [0, 2500, 5000, 7500, 10000, 12500, 15000],
    "confidence_score": 0.85
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all properties identified in the prework, several can be consolidated to eliminate redundancy:

- Properties 1.2, 3.5 (metadata compatibility) can be combined into one comprehensive metadata preservation property
- Properties 2.2, 2.3, 2.4, 2.5 (header formats) can be combined into one comprehensive header format property
- Properties 3.1, 3.3, 3.4 (backward compatibility) can be combined into one comprehensive compatibility property
- Properties 4.1, 4.2, 4.3 (structure detection) can be combined into one comprehensive structure detection property

Property 1: LangChain chunker integration
*For any* document processed by the ingestion pipeline, the system should use LangChain's SemanticChunker and produce chunks with semantic boundaries rather than fixed-size boundaries
**Validates: Requirements 1.1**

Property 2: Metadata structure preservation
*For any* chunk created by the new system, the metadata should contain all required fields in the expected format, maintaining compatibility with existing chunk metadata structure
**Validates: Requirements 1.2, 3.5**

Property 3: Document format compatibility
*For any* supported document format (PDF, TXT, MD, DOCX), the new chunker should successfully process the document and create valid chunks
**Validates: Requirements 1.4**

Property 4: Configuration parameter compliance
*For any* valid configuration settings (chunk_size, chunk_overlap, min_chunk_size), the resulting chunks should respect these constraints within reasonable semantic boundaries
**Validates: Requirements 1.5**

Property 5: Contextual header presence
*For any* chunk created from a document, the chunk text should begin with a properly formatted contextual header
**Validates: Requirements 2.1**

Property 6: Contextual header format compliance
*For any* document with detectable structure, the contextual header should follow the appropriate format based on available hierarchical information (sections, pages, or fallback)
**Validates: Requirements 2.2, 2.3, 2.4, 2.5**

Property 7: Backward compatibility preservation
*For any* query against the vector store containing both old and new chunk formats, the system should handle retrieval, display, and metadata access seamlessly
**Validates: Requirements 3.1, 3.3, 3.4**

Property 8: New document enhancement
*For any* newly ingested document, the resulting chunks should include contextual headers while maintaining all existing functionality
**Validates: Requirements 3.2**

Property 9: Document structure detection
*For any* document with identifiable structure (PDF sections, Markdown headers, numbered sections), the system should correctly detect and extract hierarchical information for contextual headers
**Validates: Requirements 4.1, 4.2, 4.3**

Property 10: Structure detection fallback
*For any* document without clear structure, the system should fall back to position-based or page-based context and prioritize the most specific available information
**Validates: Requirements 4.4, 4.5**

Property 11: Error resilience
*For any* document that fails to chunk or generate contextual headers, the system should continue processing other documents and provide appropriate fallback behavior
**Validates: Requirements 5.2, 5.3**

Property 12: Diagnostic capabilities
*For any* unexpected chunking results or invalid configurations, the system should provide detailed diagnostic information and helpful error messages
**Validates: Requirements 5.4, 5.5**

## Error Handling

### Dependency Management
- Graceful handling of missing LangChain dependencies with clear installation instructions
- Fallback to custom chunker if LangChain components are unavailable
- Version compatibility checks for LangChain components

### Chunking Failures
- Document-level error isolation to prevent pipeline failures
- Detailed logging of chunking errors with document context
- Fallback to basic text splitting when semantic chunking fails

### Structure Detection Failures
- Graceful degradation when structure detection fails
- Fallback to simple contextual headers (filename + chunk index)
- Confidence scoring for structure detection results

### Backward Compatibility
- Seamless handling of existing chunks without contextual headers
- Metadata field validation and migration support
- Query result formatting that works with both old and new formats

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific functionality with property-based tests for comprehensive validation:

**Unit Tests:**
- Test specific document format processing (PDF, MD, TXT, DOCX)
- Test contextual header generation for known document structures
- Test error handling scenarios with malformed documents
- Test configuration validation with specific parameter sets
- Test backward compatibility with existing chunk samples

**Property-Based Tests:**
- Use Hypothesis for Python property-based testing framework
- Configure each property-based test to run a minimum of 100 iterations
- Each property-based test must be tagged with a comment referencing the design document property
- Tag format: `# Feature: semantic-chunking-refactor, Property {number}: {property_text}`

**Property-Based Test Requirements:**
- Property 1: Generate random documents and verify LangChain chunker usage and semantic boundaries
- Property 2: Generate random chunks and verify metadata structure compliance
- Property 3: Test all supported formats with various document structures
- Property 4: Test various configuration parameter combinations within valid ranges
- Property 5: Verify contextual header presence across all generated chunks
- Property 6: Test header format compliance with various document structures
- Property 7: Test mixed old/new chunk scenarios for compatibility
- Property 8: Verify new document processing includes contextual headers
- Property 9: Test structure detection across various document types
- Property 10: Test fallback behavior with unstructured documents
- Property 11: Test error resilience with intentionally problematic documents
- Property 12: Test diagnostic output with various error scenarios

### Integration Testing
- End-to-end pipeline testing with real documents
- Performance comparison between old and new chunking approaches
- Vector store compatibility testing with mixed chunk formats
- Search quality evaluation with contextual headers

### Test Data Requirements
- Sample documents of each supported format with known structures
- Malformed documents for error handling tests
- Large documents for performance testing
- Documents without clear structure for fallback testing