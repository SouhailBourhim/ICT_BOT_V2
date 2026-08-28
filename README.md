# INPT Smart ICT — RAG Study Assistant

A retrieval-augmented generation system that answers students' questions from their own course
material, with page-level citations. Runs entirely on local hardware — no data leaves the machine,
no API keys, no per-query cost.

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![ChromaDB](https://img.shields.io/badge/Vectors-ChromaDB-4B8BBE)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20·%20Qwen2.5-000000)
![License](https://img.shields.io/badge/license-MIT-orange)

**Stack:** Python 3.11 · Streamlit · ChromaDB · Ollama (Qwen 2.5 3B) · Sentence-Transformers ·
BM25 · SQLite · Docker

---

## Why hybrid retrieval

A course corpus is a hard case for pure vector search: students ask about exact terms — `K-means`,
`BM25`, `SVM` — that a 384-dimension multilingual embedding blurs together. Pure keyword search has
the opposite failure, missing paraphrased questions entirely.

This system runs both and fuses the scores:

```
final_score = 0.7 × semantic_similarity + 0.3 × bm25_score
```

Semantic retrieval catches the paraphrase; BM25 anchors the exact term. The weights are
configurable in `.env` — the 70/30 split was chosen against the evaluation set below.

---

## Measured results

Evaluated against a hand-built question set with `tests/evaluate_rag.py`
(qwen2.5:3b, temperature 0.1, top-k 5). Full breakdown in
[`EVALUATION_REPORT.md`](EVALUATION_REPORT.md).

| Metric | Score |
|---|---|
| Overall quality | **77.4 / 100** (grade B) |
| Hallucination rate | **0%** |
| Mean confidence | 98% |
| Keyword coverage | 77% |
| Concept coverage | 56% |
| Mean response time | 7.8 s |

**By question type:**

| Category | Score | n |
|---|---|---|
| Definitions | 84.2 | 4 |
| Characteristics | 75.0 | 1 |
| Explanations | 74.6 | 1 |
| Comparisons | 72.5 | 1 |
| Enumerations | 60.0 | 1 |

Two caveats stated rather than buried. **The set is 8 questions** — enough to catch a category-level
weakness, not enough for a confidence interval. And **enumerations are the known failure**: asked
"what are the types of supervised learning?", the model answers "classification and regression" and
stops, because `LLM_MAX_TOKENS` was tuned for concise definitional answers. The fix is a prompt
change plus a higher token ceiling, and it is not applied yet.

Zero hallucinations across the set is the result worth keeping: every answer stayed inside the
retrieved chunks, which is what the citation guarantee depends on.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                Streamlit interface                  │
│           (chat · upload · analytics)               │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│               Response generator                    │
│      (orchestration: retrieve → LLM → post-proc)    │
└─────┬─────────────────────────────────────┬─────────┘
      │                                     │
┌─────▼──────────────┐          ┌───────────▼───────┐
│   Hybrid search    │          │   Ollama client   │
│  (semantic + BM25) │          │    (Qwen 2.5)     │
└─────┬──────────────┘          └───────────────────┘
      │
┌─────▼──────────────┐
│    Vector store    │
│     (ChromaDB)     │
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Document pipeline  │
│  parse → chunk     │
│    → embed         │
└────────────────────┘
```

| Layer | Responsibility | Code |
|---|---|---|
| Document processing | Multi-format extraction (PDF, TXT, MD, DOCX), semantic chunking, embedding, metadata enrichment | `src/document_processing/` |
| Retrieval | Semantic search, BM25, weighted fusion, re-ranking | `src/retrieval/` |
| Storage | ChromaDB for vectors, SQLite for metadata and conversation history | `src/storage/` |
| LLM | Ollama client, education-tuned prompt templates, RAG orchestration | `src/llm/` |
| Conversation | History and context-window management | `src/conversation/` |
| Interface | Streamlit chat, upload, analytics dashboard | `app/` |

**Retrieval details.** Embeddings are `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, cosine
similarity, HNSW index). BM25 uses NLTK tokenisation with French support, `k1=1.2`, `b=0.75`.
Chunking preserves paragraph and section boundaries at 1000 characters with 200 overlap, carrying
page and section metadata so citations resolve to a location, not just a document.

---

## Quick start

**Requirements:** Python 3.11+, [Ollama](https://ollama.ai), 8 GB RAM (16 GB recommended),
10 GB disk for models and data.

```bash
git clone https://github.com/SouhailBourhim/ICT_BOT_V2.git
cd ICT_BOT_V2

python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

ollama serve &
ollama pull qwen2.5:3b

python scripts/setup_database.py
cp .env.example .env
```

Ingest course material and launch:

```bash
cp ~/courses/*.pdf data/documents/
python scripts/ingest_documents.py data/documents --recursive
streamlit run app/chat.py          # → http://localhost:8501
```

Or with Docker:

```bash
cd docker && docker-compose up -d   # → http://localhost:8501
```

---

## Configuration

All behaviour is driven from `.env`:

```bash
OLLAMA_MODEL="qwen2.5:3b"
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE=32

SEMANTIC_WEIGHT=0.7      # semantic share of the fused score
BM25_WEIGHT=0.3          # keyword share
TOP_K_RETRIEVAL=7

CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

Swapping the model is one line — `ollama pull mistral:7b`, then `OLLAMA_MODEL=mistral:7b`.

---

## Tests

```bash
python -m pytest tests/ -v                          # unit tests
python -m pytest tests/ --cov=src --cov-report=html # with coverage
python -m ruff check src app tests scripts          # lint (runs in CI)
python scripts/healthcheck.py --skip-streamlit --skip-ollama
python tests/evaluate_rag.py                        # regenerate the eval table above
```

Throughput on an i7 / 16 GB reference machine: ~50 PDF pages/min ingested, ~1000 chunks/min
embedded, ~100 ms per retrieval, 2–5 s per generation.

---

## Project layout

```
src/
├── config/                  # global settings
├── document_processing/     # parser · chunker · embedding_generator · metadata_extractor
├── storage/                 # vector_store (ChromaDB) · metadata_store · models
├── retrieval/               # hybrid_search · semantic_retriever · bm25_retriever
├── llm/                     # ollama_client · prompt_templates · response_generator
├── conversation/            # manager · context_window
└── utils/                   # text_processing · logger

app/                         # Streamlit UI — chat.py, components/, pages/
scripts/                     # ingest_documents · setup_database · benchmark · healthcheck
tests/                       # unit tests + evaluate_rag.py and its labeled set
docker/                      # Dockerfile, compose, Caddy reverse proxy
```

---

## Extending it

**New document format** — add a parser in `src/document_processing/parser.py` and register it in
`SUPPORTED_FORMATS` in `settings.py`.

**Different prompts** — templates live in `src/llm/prompt_templates.py`.

**Programmatic use** — the pipeline is importable, not just a UI:

```python
from src.llm.response_generator import ResponseGenerator

response = response_gen.generate_response(
    question="What is IoT?",
    conversation_id="user_123",
)
```

---

## Further documentation

- [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) — full evaluation, per-question results
- [`DOCKER_GUIDE.md`](DOCKER_GUIDE.md) — container deployment
- [`MATH_FORMULAS_GUIDE.md`](MATH_FORMULAS_GUIDE.md) — LaTeX rendering in answers
- [`GUIDE_UTILISATEUR.md`](GUIDE_UTILISATEUR.md) — end-user guide (French)
- [`README.fr.md`](README.fr.md) — this document in French

---

## Context

Built for the Smart ICT programme at INPT (Institut National des Postes et Télécommunications).
The privacy property is the reason for the local-only design: course material and student questions
stay on the machine that runs it.

MIT licensed.
