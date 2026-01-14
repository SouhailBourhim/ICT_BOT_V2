# Codebase Review (Generated from Source Inspection)

## High-level purpose
This repository implements a French-first RAG assistant aimed at Smart ICT coursework. The core runtime is a Streamlit UI that wires together a document ingestion/retrieval pipeline (ChromaDB + BM25) and an Ollama-backed LLM to answer questions from ingested course materials. The pipeline leans heavily on contextual chunk headers to preserve document structure while maintaining backward compatibility with older chunk formats.【F:app/chat.py†L1-L508】【F:src/config/settings.py†L1-L207】【F:src/document_processing/chunker.py†L1-L480】【F:src/storage/compatibility.py†L1-L307】

## Runtime entry points and flows

### Streamlit app (interactive Q&A)
1. **Initialization**: The UI initializes the vector store, embeddings, hybrid search, Ollama client, prompt builder, response generator, and conversation manager with Streamlit caching for reuse across requests.【F:app/chat.py†L70-L167】
2. **Conversation state**: Session state persists the current conversation ID and message history, while the `ConversationManager` persists JSON conversations on disk for recall between sessions.【F:app/chat.py†L196-L330】【F:src/conversation/manager.py†L1-L360】
3. **User query flow**: A new prompt triggers hybrid retrieval, LLM generation, and response persistence with confidence and source metadata rendered in the UI along with math rendering support for LaTeX-like formulas.【F:app/chat.py†L254-L420】【F:src/llm/response_generator.py†L66-L318】【F:app/components/math_renderer.py†L1-L73】

### Document ingestion (offline or batch)
The ingestion script parses documents, chunks them (preferentially with semantic chunking if available), generates embeddings, and stores them in ChromaDB with enhanced metadata and contextual headers. It also provides a migration path for legacy chunks and can refresh the BM25 index from stored documents.【F:scripts/ingest_documents.py†L1-L349】【F:src/document_processing/parser.py†L1-L230】【F:src/document_processing/chunker.py†L1-L480】

## Core data model and storage

### Chunks and compatibility
- **EnhancedChunk** extends the base `Chunk` with contextual headers, hierarchy paths, and structure metadata, but it still serializes in a Chroma-friendly format (JSON strings for lists/dicts).【F:src/storage/models.py†L1-L122】
- **Compatibility layer** normalizes legacy chunks into enhanced format, extracts clean content for retrieval/processing, and generates display titles for UI rendering.【F:src/storage/compatibility.py†L1-L307】

### Vector store
- ChromaDB is the persistent store used for embedding search. Results are normalized by the compatibility layer to ensure the UI and retrieval code can work with both legacy and enhanced chunks uniformly.【F:src/storage/vector_store.py†L1-L272】

## Retrieval and ranking

### Hybrid search
- Combines semantic similarity (Chroma embeddings) with BM25 keyword search via a weighted merge (default 70/30). Scores can be normalized before fusion to balance both ranking signals.【F:src/retrieval/hybrid_search.py†L1-L254】
- The hybrid engine also surfaces clean-content fields to avoid contextual headers polluting BM25 scoring, while still displaying full content in the UI.【F:src/retrieval/hybrid_search.py†L102-L199】

### Prompt and response orchestration
- Prompts enforce strict context-only answers in French and include a conversational variant to leverage recent chat history when a query is detected as follow-up.【F:src/llm/prompt_templates.py†L1-L214】【F:src/llm/response_generator.py†L40-L196】
- The `ResponseGenerator` handles end-to-end response generation: retrieval, confidence filtering, prompt assembly, generation via Ollama, and source extraction with confidence scoring.【F:src/llm/response_generator.py†L66-L316】

## Document parsing and chunking

### Parsing
The parser supports PDF, TXT, Markdown, and DOCX. It extracts raw text plus format-specific metadata (e.g., per-page content for PDFs, heading detection for Markdown).【F:src/document_processing/parser.py†L1-L230】

### Chunking
- Semantic chunking uses LangChain’s `SemanticChunker` when available, falling back to a recursive character splitter or a custom overlap-based chunker when needed.【F:src/document_processing/chunker.py†L1-L339】
- Each chunk is enriched with contextual headers generated from detected document structure (sections/pages) to help the UI and retrieval logic show where chunks came from in the source material.【F:src/document_processing/chunker.py†L116-L480】【F:src/document_processing/contextual_header_generator.py†L1-L190】

## LLM integration
- The Ollama client wraps both generate and chat endpoints, includes connectivity checks, and supports streaming responses (though Streamlit uses non-streaming in the current code path).【F:src/llm/ollama_client.py†L1-L250】【F:src/llm/response_generator.py†L192-L318】

## Conversation persistence
Conversations are stored as JSON on disk and include timestamps and optional metadata for each message. The manager supports listing, searching, exporting, and deleting conversations, and it also maintains a rolling context window for retrieval prompts.【F:src/conversation/manager.py†L1-L359】

## Observability and analytics
The analytics utilities provide basic latency tracking and interaction logging, but they are not wired into the Streamlit UI by default (they are standalone helpers).【F:src/analytics/metrics.py†L1-L44】【F:src/analytics/tracker.py†L1-L44】

## Configuration surface
`Settings` centralizes runtime defaults for chunk sizes, retrieval parameters, Ollama settings, and storage paths, with validation guards for correctness and environment-aware warnings (e.g., Docker vs local).【F:src/config/settings.py†L1-L207】

## Notable implementation details and implications
- **Contextual headers**: The system preserves human-readable provenance in chunk content itself, which improves UI clarity but requires clean-content extraction for lexical scoring and other processing steps.【F:src/document_processing/chunker.py†L212-L339】【F:src/storage/compatibility.py†L171-L269】
- **Confidence gating**: Low-confidence retrieval results are filtered before prompt assembly, providing a conservative answer strategy when the retrieved context is weak.【F:src/llm/response_generator.py†L237-L318】
- **Legacy safety**: The compatibility layer prevents runtime failures when older chunks lack new metadata fields, which is critical during migrations or when reusing existing Chroma stores.【F:src/storage/compatibility.py†L1-L307】

