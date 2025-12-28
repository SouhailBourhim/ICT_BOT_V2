# 📚 Documentation API - Assistant RAG INPT

## Vue d'Ensemble

Cette documentation détaille l'API interne de l'Assistant RAG INPT, les interfaces de programmation disponibles, et les méthodes d'intégration avec le système.

## 🏗️ Architecture API

### Structure Modulaire

```python
src/
├── config/           # Configuration et paramètres
├── document_processing/  # Pipeline de traitement
├── storage/          # Couche de persistance
├── retrieval/        # Moteurs de recherche
├── llm/             # Intégration LLM
└── conversation/    # Gestion des conversations
```

## 🔧 APIs Principales

### 1. Configuration (`src/config/settings.py`)

#### Classe Settings
```python
from src.config.settings import settings

# Accès aux paramètres globaux
print(settings.PROJECT_NAME)
print(settings.OLLAMA_MODEL)
print(settings.CHUNK_SIZE)

# Validation de l'environnement
from src.config.settings import validate_environment_configuration
validation_results = validate_environment_configuration()
```

**Paramètres Disponibles :**
```python
class Settings(BaseSettings):
    # Projet
    PROJECT_NAME: str = "Assistant Éducatif RAG - INPT Smart ICT"
    VERSION: str = "1.0.0"
    LANGUAGE: str = "fr"
    
    # Chemins
    BASE_DIR: Path
    DATA_DIR: Path
    DOCUMENTS_DIR: Path
    DATABASE_DIR: Path
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    SUPPORTED_FORMATS: List[str] = [".pdf", ".txt", ".md", ".docx"]
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Retrieval
    TOP_K_RETRIEVAL: int = 7
    SIMILARITY_THRESHOLD: float = 0.4
    SEMANTIC_WEIGHT: float = 0.7
    BM25_WEIGHT: float = 0.3
    
    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    LLM_TEMPERATURE: float = 0.1
```

### 2. Traitement de Documents (`src/document_processing/`)

#### Parser de Documents
```python
from src.document_processing.parser import DocumentParser
from pathlib import Path

# Initialisation
parser = DocumentParser()

# Parser un document
doc_path = Path("data/documents/cours.pdf")
parsed_doc = parser.parse(doc_path)

print(f"Contenu: {len(parsed_doc.content)} caractères")
print(f"Métadonnées: {parsed_doc.metadata}")
print(f"Pages: {len(parsed_doc.pages) if parsed_doc.pages else 'N/A'}")

# Parser plusieurs documents
docs = parser.batch_parse([Path("doc1.pdf"), Path("doc2.txt")])
```

**Formats Supportés :**
- **PDF** : Extraction avec pypdf, métadonnées par page
- **TXT** : Détection automatique d'encodage (UTF-8, latin-1)
- **Markdown** : Conversion HTML → texte, extraction des titres
- **DOCX** : Extraction paragraphes et tableaux

#### Chunker Sémantique
```python
from src.document_processing.chunker import SemanticChunker

# Initialisation
chunker = SemanticChunker(
    chunk_size=1000,
    chunk_overlap=200,
    min_chunk_size=100
)

# Chunking standard
chunks = chunker.chunk_text(
    text=parsed_doc.content,
    doc_metadata=parsed_doc.metadata,
    preserve_structure=True
)

# Chunking avec pages (pour PDFs)
if parsed_doc.pages:
    chunks = chunker.chunk_with_pages(
        pages_data=parsed_doc.pages,
        doc_metadata=parsed_doc.metadata
    )

# Accès aux chunks enrichis
for chunk in chunks:
    print(f"ID: {chunk.id}")
    print(f"Contenu: {chunk.content[:100]}...")
    print(f"En-tête contextuel: {chunk.contextual_header}")
    print(f"Hiérarchie: {chunk.hierarchy_path}")
```

#### Générateur d'Embeddings
```python
from src.document_processing.embedding_generator import EmbeddingGenerator

# Initialisation
embedder = EmbeddingGenerator(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    batch_size=32
)

# Génération d'embeddings
texts = ["Texte 1", "Texte 2", "Texte 3"]
embeddings = embedder.generate_embeddings_batch(texts, show_progress=True)

print(f"Shape: {embeddings.shape}")  # (3, 384)
print(f"Type: {embeddings.dtype}")   # float32

# Embedding unique
single_embedding = embedder.generate_embedding("Texte unique")
```

### 3. Stockage (`src/storage/`)

#### Vector Store
```python
from src.storage.vector_store import VectorStore

# Initialisation
vector_store = VectorStore(
    persist_directory="./database/chroma_db",
    collection_name="inpt_smart_ict_docs"
)

# Ajout de documents
texts = ["Document 1", "Document 2"]
metadatas = [{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
ids = ["doc1_chunk1", "doc2_chunk1"]

vector_store.add_documents(
    texts=texts,
    metadatas=metadatas,
    ids=ids,
    embeddings=embeddings.tolist()
)

# Recherche
results = vector_store.search(
    query_text="Qu'est-ce que l'IoT ?",
    n_results=5,
    where={"source": "cours_iot.pdf"}
)

print(f"IDs: {results['ids']}")
print(f"Documents: {results['documents']}")
print(f"Métadonnées: {results['metadatas']}")
print(f"Distances: {results['distances']}")

# Statistiques
print(f"Nombre de documents: {vector_store.count()}")

# Récupération par IDs
docs = vector_store.get_by_ids(["doc1_chunk1", "doc2_chunk1"])
```

#### Modèles de Données
```python
from src.storage.models import Document, EnhancedChunk
from datetime import datetime

# Création d'un document
doc = Document(
    id="doc_123",
    filename="cours_iot.pdf",
    filepath="/path/to/cours_iot.pdf",
    format="pdf",
    size=1024000,
    created_at=datetime.now(),
    modified_at=datetime.now(),
    processed_at=datetime.now(),
    metadata={"pages": 50, "author": "Prof. Dupont"}
)

# Création d'un chunk enrichi
chunk = EnhancedChunk(
    id="chunk_456",
    document_id="doc_123",
    chunk_id=1,
    content="L'Internet des Objets (IoT) est...",
    contextual_header="Chapitre 1: Introduction à l'IoT",
    hierarchy_path=["Chapitre 1", "Section 1.1", "Introduction"],
    structure_metadata={
        "document_type": "academic_paper",
        "has_sections": True,
        "confidence_score": 0.95
    }
)

# Conversion pour stockage
storage_metadata = chunk.to_storage_metadata()
```

### 4. Recherche (`src/retrieval/`)

#### Recherche Hybride
```python
from src.retrieval.hybrid_search import HybridSearchEngine

# Initialisation
hybrid_search = HybridSearchEngine(
    vector_store=vector_store,
    semantic_weight=0.7,
    bm25_weight=0.3,
    normalize_scores=True
)

# Indexation pour BM25
documents = [
    {"id": "doc1", "text": "Texte du document 1", "metadata": {}},
    {"id": "doc2", "text": "Texte du document 2", "metadata": {}}
]
hybrid_search.index_documents(documents)

# Recherche hybride
results = hybrid_search.search(
    query="Comment fonctionne l'IoT ?",
    top_k=5,
    filters={"source": "cours_iot.pdf"}
)

for result in results:
    print(f"ID: {result.doc_id}")
    print(f"Score total: {result.score:.3f}")
    print(f"Score sémantique: {result.semantic_score:.3f}")
    print(f"Score BM25: {result.bm25_score:.3f}")
    print(f"Texte: {result.text[:100]}...")
    print("---")

# Recherche avec re-ranking
results = hybrid_search.search_with_reranking(
    query="IoT sécurité",
    top_k=3,
    initial_k=20
)
```

### 5. LLM et Génération (`src/llm/`)

#### Client Ollama
```python
from src.llm.ollama_client import OllamaClient

# Initialisation
ollama = OllamaClient(
    base_url="http://localhost:11434",
    model="qwen2.5:3b",
    timeout=180
)

# Vérification de connexion
if ollama._check_connection():
    print("Ollama connecté ✅")

# Génération simple
response = ollama.generate(
    prompt="Qu'est-ce que l'Internet des Objets ?",
    temperature=0.1,
    max_tokens=500
)
print(response)

# Génération avec système
response = ollama.generate(
    prompt="Explique l'IoT simplement",
    system="Tu es un assistant éducatif pour étudiants Smart ICT",
    temperature=0.2
)

# Génération streaming
for chunk in ollama.generate_stream(
    prompt="Décris les protocoles IoT",
    temperature=0.1
):
    print(chunk, end="", flush=True)
```

#### Générateur de Réponses RAG
```python
from src.llm.response_generator import ResponseGenerator
from src.llm.prompt_templates import PromptBuilder

# Initialisation
prompt_builder = PromptBuilder()
response_gen = ResponseGenerator(
    hybrid_search=hybrid_search,
    ollama_client=ollama,
    prompt_builder=prompt_builder,
    min_confidence=0.4,
    max_sources=3,
    top_k_retrieval=7
)

# Génération de réponse RAG
response = response_gen.generate_response(
    question="Comment sécuriser un réseau IoT ?",
    conversation_history=None,
    filters={"source": "cours_securite.pdf"},
    temperature=0.1
)

print(f"Réponse: {response.answer}")
print(f"Confiance: {response.confidence:.2%}")
print(f"Sources: {len(response.sources)}")

for i, source in enumerate(response.sources, 1):
    print(f"  [{i}] {source['name']} - Score: {source['score']:.3f}")

# Génération avec historique conversationnel
conversation_history = [
    {"role": "user", "content": "Qu'est-ce que l'IoT ?"},
    {"role": "assistant", "content": "L'IoT est..."},
    {"role": "user", "content": "Et la sécurité ?"}
]

response = response_gen.generate_response(
    question="Comment la protéger ?",
    conversation_history=conversation_history
)
```

### 6. Gestion des Conversations (`src/conversation/`)

#### Manager de Conversations
```python
from src.conversation.manager import ConversationManager

# Initialisation
conv_manager = ConversationManager(
    storage_dir="./data/conversations",
    max_history_length=10
)

# Créer une nouvelle conversation
conversation = conv_manager.create_conversation(
    title="Discussion sur l'IoT"
)
print(f"ID conversation: {conversation.id}")

# Ajouter des messages
conv_manager.add_message(
    role="user",
    content="Qu'est-ce que l'IoT ?",
    conversation_id=conversation.id
)

conv_manager.add_message(
    role="assistant",
    content="L'Internet des Objets (IoT) est...",
    metadata={"confidence": 0.85, "sources": ["cours_iot.pdf"]},
    conversation_id=conversation.id
)

# Charger une conversation
loaded_conv = conv_manager.load_conversation(conversation.id)
print(f"Messages: {len(loaded_conv.messages)}")

# Lister les conversations
conversations = conv_manager.list_conversations(limit=10)
for conv in conversations:
    print(f"- {conv['title']} ({conv['created_at']})")

# Obtenir le contexte pour RAG
context = conv_manager.get_context_window(
    conversation_id=conversation.id,
    max_messages=6
)
```

## 🔌 Intégration et Utilisation

### 1. Pipeline Complet d'Ingestion

```python
from pathlib import Path
from src.document_processing.parser import DocumentParser
from src.document_processing.chunker import SemanticChunker
from src.document_processing.embedding_generator import EmbeddingGenerator
from src.storage.vector_store import VectorStore

def ingest_document(file_path: Path):
    """Pipeline complet d'ingestion d'un document"""
    
    # 1. Parsing
    parser = DocumentParser()
    parsed_doc = parser.parse(file_path)
    
    # 2. Chunking
    chunker = SemanticChunker()
    chunks = chunker.chunk_text(
        text=parsed_doc.content,
        doc_metadata=parsed_doc.metadata
    )
    
    # 3. Embeddings
    embedder = EmbeddingGenerator()
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.generate_embeddings_batch(texts)
    
    # 4. Stockage
    vector_store = VectorStore()
    
    # Préparation des métadonnées
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{file_path.stem}_{i}"
        metadata = chunk.to_storage_metadata()
        
        metadatas.append(metadata)
        ids.append(chunk_id)
    
    # Ajout au vector store
    vector_store.add_documents(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings.tolist()
    )
    
    return len(chunks)

# Utilisation
num_chunks = ingest_document(Path("data/documents/cours_iot.pdf"))
print(f"Document ingéré: {num_chunks} chunks créés")
```

### 2. Système RAG Complet

```python
def create_rag_system():
    """Initialise un système RAG complet"""
    
    # Configuration
    from src.config.settings import settings
    
    # Composants de stockage
    vector_store = VectorStore(
        persist_directory=str(settings.CHROMA_PERSIST_DIR),
        collection_name=settings.CHROMA_COLLECTION_NAME
    )
    
    # Recherche hybride
    hybrid_search = HybridSearchEngine(
        vector_store=vector_store,
        semantic_weight=settings.SEMANTIC_WEIGHT,
        bm25_weight=settings.BM25_WEIGHT
    )
    
    # Client LLM
    ollama = OllamaClient(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL
    )
    
    # Générateur de réponses
    prompt_builder = PromptBuilder()
    response_gen = ResponseGenerator(
        hybrid_search=hybrid_search,
        ollama_client=ollama,
        prompt_builder=prompt_builder
    )
    
    # Manager de conversations
    conv_manager = ConversationManager()
    
    return {
        'vector_store': vector_store,
        'hybrid_search': hybrid_search,
        'ollama': ollama,
        'response_gen': response_gen,
        'conv_manager': conv_manager
    }

def ask_question(system, question: str, conversation_id: str = None):
    """Pose une question au système RAG"""
    
    # Récupérer l'historique si conversation existante
    history = None
    if conversation_id:
        history = system['conv_manager'].get_context_window(conversation_id)
    
    # Générer la réponse
    response = system['response_gen'].generate_response(
        question=question,
        conversation_history=history
    )
    
    # Sauvegarder dans l'historique
    if conversation_id:
        system['conv_manager'].add_message(
            role="user",
            content=question,
            conversation_id=conversation_id
        )
        
        system['conv_manager'].add_message(
            role="assistant",
            content=response.answer,
            metadata={
                'confidence': response.confidence,
                'num_sources': len(response.sources)
            },
            conversation_id=conversation_id
        )
    
    return response

# Utilisation
rag_system = create_rag_system()

# Créer une conversation
conv = rag_system['conv_manager'].create_conversation()

# Poser des questions
response1 = ask_question(
    rag_system, 
    "Qu'est-ce que l'Internet des Objets ?", 
    conv.id
)

response2 = ask_question(
    rag_system, 
    "Quels sont les protocoles utilisés ?", 
    conv.id
)

print(f"Réponse 1: {response1.answer}")
print(f"Réponse 2: {response2.answer}")
```

### 3. API REST (Extension)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="INPT RAG API", version="1.0.0")

# Modèles de requête
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    temperature: Optional[float] = 0.1
    max_sources: Optional[int] = 3

class DocumentUploadRequest(BaseModel):
    file_path: str
    metadata: Optional[dict] = {}

# Initialisation du système
rag_system = create_rag_system()

@app.post("/ask")
async def ask_question_api(request: QuestionRequest):
    """Endpoint pour poser une question"""
    try:
        response = ask_question(
            rag_system,
            request.question,
            request.conversation_id
        )
        
        return {
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "metadata": response.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_document_api(request: DocumentUploadRequest):
    """Endpoint pour ingérer un document"""
    try:
        num_chunks = ingest_document(Path(request.file_path))
        return {"message": f"Document ingéré: {num_chunks} chunks créés"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations")
async def list_conversations():
    """Liste les conversations"""
    conversations = rag_system['conv_manager'].list_conversations()
    return {"conversations": conversations}

@app.get("/stats")
async def get_stats():
    """Statistiques du système"""
    return {
        "total_documents": rag_system['vector_store'].count(),
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.OLLAMA_MODEL
    }

# Lancement: uvicorn api:app --reload
```

## 🧪 Tests et Validation

### Tests Unitaires

```python
import pytest
from src.document_processing.parser import DocumentParser
from pathlib import Path

def test_pdf_parsing():
    """Test du parsing PDF"""
    parser = DocumentParser()
    
    # Créer un fichier de test
    test_file = Path("test_document.pdf")
    
    # Parser le document
    parsed_doc = parser.parse(test_file)
    
    # Assertions
    assert parsed_doc.content is not None
    assert len(parsed_doc.content) > 0
    assert parsed_doc.metadata['format'] == 'pdf'
    assert 'filename' in parsed_doc.metadata

def test_embedding_generation():
    """Test de génération d'embeddings"""
    from src.document_processing.embedding_generator import EmbeddingGenerator
    
    embedder = EmbeddingGenerator()
    
    # Test embedding unique
    text = "Ceci est un test"
    embedding = embedder.generate_embedding(text)
    
    assert embedding.shape == (384,)  # Dimension attendue
    assert embedding.dtype == 'float32'
    
    # Test batch
    texts = ["Texte 1", "Texte 2"]
    embeddings = embedder.generate_embeddings_batch(texts)
    
    assert embeddings.shape == (2, 384)

def test_hybrid_search():
    """Test de recherche hybride"""
    # Setup minimal pour test
    # ... (configuration de test)
    
    results = hybrid_search.search("test query", top_k=3)
    
    assert len(results) <= 3
    assert all(hasattr(r, 'score') for r in results)
    assert all(hasattr(r, 'semantic_score') for r in results)
    assert all(hasattr(r, 'bm25_score') for r in results)
```

Cette documentation API complète permet une intégration facile et une extension du système RAG INPT selon les besoins spécifiques.