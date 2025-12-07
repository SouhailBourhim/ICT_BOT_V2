# 🎓 Assistant Éducatif RAG - INPT Smart ICT

Assistant intelligent basé sur RAG (Retrieval-Augmented Generation) conçu spécifiquement pour les étudiants Smart ICT de l'Institut National des Postes et Télécommunications (INPT).

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Table des Matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du Projet](#-structure-du-projet)
- [Développement](#-développement)
- [FAQ](#-faq)

## ✨ Fonctionnalités

### 🔍 Recherche Avancée
- **Recherche hybride** : Combine recherche sémantique (embeddings) et recherche par mots-clés (BM25)
- **Multi-format** : Support de PDF, TXT, MD, DOCX
- **Chunking intelligent** : Découpage sémantique préservant la structure des documents
- **Re-ranking** : Amélioration de la pertinence des résultats

### 💬 Chat Intelligent
- **Conversation contextuelle** : Maintien du contexte sur plusieurs échanges
- **Citations précises** : Références aux sources avec numéros de page
- **Confiance** : Indicateur de confiance pour chaque réponse
- **Multilingue** : Optimisé pour le français

### 📚 Gestion Documentaire
- **Ingestion automatique** : Pipeline de traitement de documents
- **Métadonnées** : Extraction et indexation des métadonnées
- **Versioning** : Suivi des versions de documents
- **Stockage vectoriel** : ChromaDB pour recherche rapide

### 🎯 Pédagogique
- **Explications progressives** : Adaptation au niveau de l'étudiant
- **Questions de suivi** : Génération automatique de questions
- **Exercices** : Création d'exercices pratiques
- **Feedback** : Évaluation constructive des réponses

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Interface Streamlit                │
│              (Chat + Upload + Analytics)            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Response Generator                     │
│    (Orchestration: Recherche + LLM + Post-proc)    │
└─────┬─────────────────────────────────────┬────────┘
      │                                     │
┌─────▼──────────────┐          ┌─────────▼─────────┐
│  Hybrid Search     │          │   Ollama Client   │
│  (Semantic + BM25) │          │   (Llama 3.2)     │
└─────┬──────────────┘          └───────────────────┘
      │
┌─────▼──────────────┐
│   Vector Store     │
│    (ChromaDB)      │
└────────────────────┘
      │
┌─────▼──────────────┐
│  Document Pipeline │
│ Parser → Chunker   │
│    → Embedder      │
└────────────────────┘
```

### Composants Principaux

1. **Document Processing** : Parsing, chunking sémantique, génération d'embeddings
2. **Storage Layer** : ChromaDB (vecteurs) + SQLite (métadonnées)
3. **Retrieval Engine** : Recherche hybride avec re-ranking
4. **LLM Integration** : Ollama pour génération locale
5. **Conversation Manager** : Gestion de l'historique et du contexte
6. **Web Interface** : Streamlit pour l'UI

## 🚀 Installation

### Prérequis

- Python 3.9+
- Ollama installé et en cours d'exécution
- 8GB RAM minimum (16GB recommandé)
- GPU optionnel mais recommandé

### Installation Rapide

```bash
# 1. Cloner le repository
git clone https://github.com/votre-repo/inpt-rag-assistant.git
cd inpt-rag-assistant

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer spaCy français
python -m spacy download fr_core_news_md

# 5. Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 6. Télécharger le modèle LLM
ollama pull llama3.2:3b

# 7. Copier et configurer .env
cp .env.example .env
# Éditer .env selon vos besoins

# 8. Initialiser les dossiers
python -c "from src.config.settings import setup_directories; setup_directories()"
```

## ⚙️ Configuration

### Variables d'Environnement

Éditez le fichier `.env` :

```bash
# Modèle LLM (choisir selon vos ressources)
OLLAMA_MODEL="llama3.2:3b"  # Léger, rapide (3GB RAM)
# OLLAMA_MODEL="mistral:7b"  # Meilleur qualité (8GB RAM)

# Embeddings
EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"

# Recherche
SEMANTIC_WEIGHT=0.7  # Poids recherche sémantique
BM25_WEIGHT=0.3      # Poids recherche mots-clés
```

### Modèles Recommandés

**LLM (Ollama):**
- `llama3.2:3b` - Léger et rapide (3GB)
- `llama3.2:7b` - Équilibré (7GB)
- `mistral:7b` - Excellente qualité (8GB)

**Embeddings:**
- `paraphrase-multilingual-MiniLM-L12-v2` - Rapide, 384 dim
- `paraphrase-multilingual-mpnet-base-v2` - Meilleure qualité, 768 dim

## 📖 Utilisation

### 1. Ingestion de Documents

```bash
# Lancer Ollama en arrière-plan
ollama serve &

# Ingérer un dossier complet
python scripts/ingest_documents.py data/documents --recursive

# Ingérer un fichier unique
python scripts/ingest_documents.py data/documents/cours_iot.pdf

# Réinitialiser et réingérer
python scripts/ingest_documents.py data/documents --reset --recursive

# Voir les statistiques
python scripts/ingest_documents.py --stats
```

### 2. Lancer l'Application

```bash
# Lancer Streamlit
streamlit run app/streamlit_app.py

# Ou avec configuration personnalisée
streamlit run app/streamlit_app.py --server.port 8501
```

L'application sera accessible sur `http://localhost:8501`

### 3. Utilisation via Python

```python
from src.config.settings import settings
from src.storage.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.llm.ollama_client import OllamaClient
from src.llm.response_generator import ResponseGenerator
from src.llm.prompt_templates import PromptBuilder

# Initialisation
vector_store = VectorStore(
    persist_directory=str(settings.CHROMA_PERSIST_DIR),
    collection_name=settings.CHROMA_COLLECTION_NAME
)

hybrid_search = HybridSearchEngine(vector_store=vector_store)
ollama = OllamaClient(model=settings.OLLAMA_MODEL)
prompt_builder = PromptBuilder()

response_gen = ResponseGenerator(
    hybrid_search=hybrid_search,
    ollama_client=ollama,
    prompt_builder=prompt_builder
)

# Poser une question
response = response_gen.generate_response(
    question="Qu'est-ce que l'IoT ?",
    temperature=0.7
)

print(response.answer)
print(f"Confiance: {response.confidence:.2%}")
print(f"Sources: {len(response.sources)}")
```

## 📁 Structure du Projet

```
inpt-rag-assistant/
├── src/                          # Code source
│   ├── config/                   # Configuration
│   │   └── settings.py
│   ├── document_processing/      # Traitement documents
│   │   ├── parser.py
│   │   ├── chunker.py
│   │   ├── metadata_extractor.py
│   │   └── embedding_generator.py
│   ├── storage/                  # Couche stockage
│   │   ├── vector_store.py
│   │   ├── metadata_store.py
│   │   └── models.py
│   ├── retrieval/                # Moteur de recherche
│   │   ├── hybrid_search.py
│   │   ├── bm25_retriever.py
│   │   └── reranker.py
│   ├── llm/                      # Intégration LLM
│   │   ├── ollama_client.py
│   │   ├── prompt_templates.py
│   │   └── response_generator.py
│   ├── conversation/             # Gestion conversations
│   │   ├── manager.py
│   │   └── context_window.py
│   ├── utils/                    # Utilitaires
│   │   ├── query_enhancement.py
│   │   ├── text_processing.py
│   │   └── logger.py
│   └── analytics/                # Analytics
│       ├── tracker.py
│       └── metrics.py
├── app/                          # Application Streamlit
│   ├── streamlit_app.py
│   └── pages/
│       ├── chat.py
│       ├── upload.py
│       └── analytics.py
├── data/                         # Données
│   ├── documents/                # Documents sources
│   └── processed/                # Documents traités
├── database/                     # Bases de données
│   ├── chroma_db/               # ChromaDB
│   └── metadata.db              # SQLite
├── scripts/                      # Scripts utilitaires
│   ├── ingest_documents.py
│   ├── setup_database.py
│   └── benchmark.py
├── tests/                        # Tests
├── logs/                         # Logs
├── requirements.txt              # Dépendances
├── .env.example                  # Config exemple
└── README.md                     # Documentation
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/

# Tests avec couverture
pytest tests/ --cov=src --cov-report=html

# Test d'un composant spécifique
pytest tests/test_document_processing.py -v
```

## 🛠️ Développement

### Ajout d'un Nouveau Format de Document

1. Modifier `src/document_processing/parser.py`
2. Ajouter le parser spécifique
3. Mettre à jour `SUPPORTED_FORMATS` dans `settings.py`

### Changement de Modèle LLM

```bash
# Télécharger un nouveau modèle
ollama pull mistral:7b

# Mettre à jour .env
OLLAMA_MODEL="mistral:7b"

# Redémarrer l'application
```

### Personnalisation des Prompts

Éditer `src/llm/prompt_templates.py` pour modifier les templates de prompts selon vos besoins.

## 📊 Performances

### Benchmarks (Machine de référence: i7, 16GB RAM)

- **Ingestion**: ~50 pages PDF/minute
- **Recherche**: ~100ms par requête
- **Génération**: ~2-5 secondes (selon modèle)
- **Embedding**: ~1000 chunks/minute

### Optimisations

```python
# Augmenter le batch size pour l'ingestion
BATCH_SIZE=64

# Réduire le nombre de résultats de recherche
TOP_K_RETRIEVAL=5

# Utiliser un modèle plus léger
OLLAMA_MODEL="llama3.2:3b"
```

## ❓ FAQ

**Q: Ollama ne se connecte pas**  
A: Vérifiez que le service est lancé: `ollama serve`

**Q: Erreur "Out of memory"**  
A: Utilisez un modèle plus léger ou réduisez `BATCH_SIZE`

**Q: Les réponses sont lentes**  
A: Utilisez un GPU ou un modèle plus petit (llama3.2:3b)

**Q: Comment ajouter des documents en cours d'exécution?**  
A: Utilisez le script d'ingestion pendant que l'app tourne, ou uploadez via l'interface (à implémenter)

**Q: Les embeddings sont lents**  
A: Utilisez un GPU ou réduisez `BATCH_SIZE`

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE)

## 👥 Auteurs

- Développé pour l'INPT Smart ICT
- Propulsé par Ollama, ChromaDB, Streamlit

## 📧 Support

Pour toute question ou problème:
- Ouvrir une issue sur GitHub
- Contacter: support@inpt.ac.ma

---

**Version**: 1.0.0  
**Dernière mise à jour**: Décembre 2024