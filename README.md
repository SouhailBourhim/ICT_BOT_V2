# 🎓 Assistant Éducatif RAG - INPT Smart ICT

**Système de Recherche et Génération Augmentée par Récupération pour l'Éducation**

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.29.0-red)
![ChromaDB](https://img.shields.io/badge/chromadb-0.4.22-green)
![Ollama](https://img.shields.io/badge/ollama-qwen2.5:3b-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 📋 Vue d'Ensemble

Ce projet implémente un **système RAG (Retrieval-Augmented Generation)** intelligent conçu pour assister les étudiants Smart ICT de l'Institut National des Postes et Télécommunications (INPT). Le système combine des techniques avancées de traitement du langage naturel, de recherche vectorielle hybride et de génération de texte pour créer un assistant éducatif capable de répondre aux questions des étudiants en se basant sur leurs documents de cours.

### 🎯 Fonctionnalités Principales

- **Recherche Hybride** : Combine recherche sémantique (embeddings) et recherche par mots-clés (BM25)
- **Support Multi-Format** : PDF, TXT, MD, DOCX avec extraction intelligente
- **LLM Local** : Utilise Ollama avec modèles comme Qwen2.5:3b pour la génération
- **Interface Intuitive** : Interface web Streamlit avec chat conversationnel
- **Gestion de Conversations** : Historique persistant et détection intelligente de questions de suivi
- **Déploiement Docker** : Configuration complète pour développement et production
- **Compatibilité Avancée** : Support des formats de chunks anciens et nouveaux

---

## 🏗️ Architecture Technique

### Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────┐
│                Interface Streamlit                  │
│         (Chat + Upload + Analytics)                 │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Response Generator                     │
│    (Orchestration: Recherche + LLM + Post-proc)    │
└─────┬─────────────────────────────────────┬────────┘
      │                                     │
┌─────▼──────────────┐          ┌─────────▼─────────┐
│  Hybrid Search     │          │   Ollama Client   │
│  (Semantic + BM25) │          │   (Qwen2.5:3b)    │
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

### 🔧 Composants Principaux

#### 1. **Pipeline de Traitement de Documents** (`src/document_processing/`)

**Parser** (`parser.py`)
- Support multi-format : PDF (pypdf), TXT, Markdown, DOCX
- Extraction de métadonnées enrichies (pages, structure, encodage)
- Gestion robuste des erreurs d'encodage et formats corrompus

**Chunker Sémantique** (`chunker.py`)
- Découpage intelligent préservant la cohérence sémantique
- Support des structures de pages pour PDFs
- Génération d'en-têtes contextuels pour améliorer la recherche
- Métadonnées de hiérarchie et structure

**Générateur d'Embeddings** (`embedding_generator.py`)
- Modèle par défaut : `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions)
- Traitement par batch optimisé
- Support multilingue avec focus français

#### 2. **Moteur de Recherche Hybride** (`src/retrieval/`)

**Recherche Hybride** (`hybrid_search.py`)
- **Recherche Sémantique** : Similarité cosinus sur embeddings (70% par défaut)
- **Recherche BM25** : Correspondance par mots-clés avec tokenisation française (30% par défaut)
- **Fusion de Scores** : Combinaison pondérée avec normalisation
- **Compatibilité** : Support des formats de chunks anciens et nouveaux

#### 3. **Couche de Stockage** (`src/storage/`)

**Vector Store** (`vector_store.py`)
- ChromaDB pour stockage vectoriel avec persistance
- Métadonnées enrichies avec support de migration
- Opérations CRUD optimisées

**Modèles de Données** (`models.py`)
- `EnhancedChunk` : Format enrichi avec en-têtes contextuels
- Compatibilité avec anciens formats via `migrate_chunk_metadata`
- Sérialisation JSON pour métadonnées complexes

#### 4. **Intégration LLM** (`src/llm/`)

**Client Ollama** (`ollama_client.py`)
- Interface avec modèles locaux (Qwen2.5:3b par défaut)
- Gestion des timeouts et reconnexions
- Support streaming pour réponses en temps réel

**Générateur de Réponses** (`response_generator.py`)
- Détection intelligente de questions de suivi
- Orchestration complète du pipeline RAG
- Post-traitement et extraction de sources
- Calcul de confiance basé sur scores de recherche

#### 5. **Interface Utilisateur** (`app/`)

**Application Principale** (`chat.py`)
- Interface Streamlit moderne avec chat conversationnel
- Gestion des conversations persistantes
- Rendu mathématique LaTeX intégré
- Affichage des sources avec niveaux de confiance

---

## 🚀 Installation et Configuration

### Prérequis Système

- **Python 3.11+** (testé avec 3.11.14)
- **Ollama** ([https://ollama.ai](https://ollama.ai))
- **8GB RAM minimum** (16GB recommandé pour modèles 7B+)
- **10GB espace disque** pour modèles et données

### Installation Rapide

```bash
# 1. Cloner le projet
git clone <repository-url>
cd inpt-rag-assistant

# 2. Créer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer Ollama
ollama serve &
ollama pull qwen2.5:3b

# 5. Initialiser la configuration
cp .env.example .env
# Éditer .env selon vos besoins

# 6. Initialiser les répertoires
python -c "from src.config.settings import setup_directories; setup_directories()"
```

### Configuration avec Makefile

Le projet inclut un Makefile complet pour simplifier les opérations :

```bash
# Installation complète
make setup

# Lancement de l'application
make run

# Ingestion de documents
make ingest

# Tests et qualité de code
make test
make lint
make format

# Docker
make docker-up
make docker-down
```

### Configuration Avancée

Le fichier `.env` permet de personnaliser le comportement :

```bash
# Modèle LLM
OLLAMA_MODEL="qwen2.5:3b"
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

# Embeddings
EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION=384

# Recherche Hybride
SEMANTIC_WEIGHT=0.7  # 70% recherche sémantique
BM25_WEIGHT=0.3      # 30% recherche par mots-clés
TOP_K_RETRIEVAL=7

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## 📚 Utilisation du Système

### 1. Ingestion de Documents

```bash
# Ajouter des documents au dossier
cp ~/cours/*.pdf data/documents/

# Ingérer tous les documents
python scripts/ingest_documents.py data/documents --recursive

# Ingérer un fichier unique
python scripts/ingest_documents.py data/documents/cours_iot.pdf

# Vérifier les statistiques
python scripts/ingest_documents.py --stats

# Migration des chunks existants (si nécessaire)
python scripts/ingest_documents.py --migrate
```

### 2. Lancement de l'Application

```bash
# Démarrer Ollama (si pas déjà fait)
ollama serve &

# Lancer l'interface Streamlit
streamlit run app/chat.py
```

L'application sera accessible sur `http://localhost:8501`

### 3. Utilisation via Interface Web

1. **Page Chat** : Interface conversationnelle principale
2. **Gestion des Conversations** : Création, chargement et suppression
3. **Paramètres** : Ajustement de la température et nombre de sources
4. **Sources** : Affichage détaillé avec niveaux de confiance

### 4. Exemples de Questions

```
- "Qu'est-ce que l'Internet des Objets ?"
- "Explique-moi les protocoles de sécurité IoT"
- "Comment fonctionne l'algorithme K-means ?"
- "Quelles sont les différences entre TCP et UDP ?"
```

---

## 🐳 Déploiement Docker

### Configuration Docker Complète

Le projet inclut une configuration Docker optimisée pour production :

```bash
# Déploiement complet
cd docker
docker-compose up -d

# Vérification de l'état
docker-compose ps

# Logs en temps réel
docker-compose logs -f

# Ingestion de documents via Docker
docker-compose exec rag-app python scripts/ingest_documents.py data/documents --recursive
```

### Services Docker

- **ollama** : Service LLM avec modèles persistants
- **rag-app** : Application principale avec Streamlit
- **Volumes** : Persistance des données, modèles et logs

### Configuration Production

```yaml
# docker-compose.prod.yml
services:
  rag-app:
    environment:
      - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

---

## 🔧 Aspects Techniques Avancés

### Recherche Hybride

**Algorithme de Fusion**
```python
score_final = (semantic_weight * score_semantic) + (bm25_weight * score_bm25)
```

**Optimisations**
- Index HNSW pour recherche vectorielle rapide
- Tokenisation française optimisée pour BM25
- Normalisation des scores avant fusion
- Cache des embeddings pour performance

### Pipeline de Traitement

**Chunking Sémantique**
- Préservation des paragraphes et sections
- Génération d'en-têtes contextuels automatiques
- Métadonnées de hiérarchie pour navigation
- Support de migration entre formats

**Génération de Réponses**
- Détection intelligente de questions de suivi via patterns regex
- Contexte conversationnel adaptatif
- Post-traitement avec validation LaTeX
- Extraction automatique de sources avec scores

### Compatibilité et Migration

Le système supporte une migration transparente entre formats de chunks :

```python
# Migration automatique des métadonnées
enhanced_metadata = migrate_chunk_metadata(legacy_metadata)

# Support des deux formats simultanément
if is_enhanced_chunk(metadata):
    # Utiliser le nouveau format
else:
    # Compatibilité avec l'ancien format
```

---

## 📊 Structure du Projet

```
inpt-rag-assistant/
├── src/                          # Code source principal
│   ├── config/                   # Configuration système
│   │   └── settings.py          # Paramètres globaux avec validation
│   ├── document_processing/      # Pipeline de traitement
│   │   ├── parser.py            # Extraction multi-format
│   │   ├── chunker.py           # Découpage sémantique
│   │   ├── embedding_generator.py # Vectorisation
│   │   └── contextual_header_generator.py # En-têtes contextuels
│   ├── storage/                  # Couche de persistance
│   │   ├── vector_store.py      # Interface ChromaDB
│   │   ├── models.py            # Modèles de données avec migration
│   │   └── compatibility.py     # Couche de compatibilité
│   ├── retrieval/                # Moteur de recherche
│   │   ├── hybrid_search.py     # Recherche hybride
│   │   ├── semantic_retriever.py # Recherche vectorielle
│   │   └── bm25_retriever.py    # Recherche BM25
│   ├── llm/                      # Intégration LLM
│   │   ├── ollama_client.py     # Client Ollama
│   │   ├── prompt_templates.py  # Templates de prompts
│   │   └── response_generator.py # Génération RAG
│   └── conversation/             # Gestion conversations
│       ├── manager.py           # Historique et contexte
│       └── context_window.py    # Fenêtre contextuelle
├── app/                          # Interface Streamlit
│   ├── chat.py                  # Application principale
│   └── components/              # Composants UI réutilisables
├── scripts/                      # Scripts utilitaires
│   ├── ingest_documents.py      # Ingestion avec migration
│   └── setup_database.py        # Initialisation DB
├── docker/                       # Configuration Docker
│   ├── Dockerfile               # Image optimisée
│   ├── docker-compose.yml       # Services complets
│   └── entrypoint.sh           # Script d'initialisation
├── tests/                        # Tests unitaires et intégration
├── data/                         # Données
│   ├── documents/               # Documents sources
│   └── conversations/           # Historique des chats
├── database/                     # Bases de données
│   └── chroma_db/              # ChromaDB persistante
├── requirements.txt              # Dépendances Python
├── makefile                     # Commandes automatisées
└── .env.example                 # Configuration exemple
```

---

## 🧪 Tests et Qualité

### Tests Unitaires

```bash
# Lancer tous les tests
pytest tests/ -v

# Tests avec couverture
pytest tests/ --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_document_processing.py -v
pytest tests/test_retrieval.py -v
```

### Tests Docker

Le projet inclut des tests complets pour l'environnement Docker :

```bash
# Tests d'intégration Docker
pytest tests/test_docker_integration.py -v

# Tests de santé des services
pytest tests/test_docker_health_check.py -v

# Tests de persistance des données
pytest tests/test_docker_data_persistence.py -v
```

### Qualité de Code

```bash
# Formatage automatique
make format

# Vérification du style
make lint

# Vérification complète
make check
```

---

## 📈 Performance et Optimisations

### Métriques de Performance

Sur une machine de référence (i7, 16GB RAM) :
- **Ingestion** : ~50 pages PDF/minute
- **Recherche** : ~100ms par requête
- **Génération** : ~2-5 secondes selon le modèle
- **Embedding** : ~1000 chunks/minute

### Optimisations Implémentées

- **Cache Streamlit** : Mise en cache des composants lourds
- **Batch Processing** : Traitement par lots pour embeddings
- **Index HNSW** : Recherche vectorielle optimisée
- **Lazy Loading** : Chargement à la demande des modèles
- **Connection Pooling** : Réutilisation des connexions Ollama

---

## 🔒 Sécurité et Confidentialité

### Protection des Données

- **Traitement Local** : Aucune donnée envoyée vers des services externes
- **Chiffrement** : Base de données et communications sécurisées
- **Isolation** : Environnement containerisé avec Docker
- **Logs Anonymisés** : Pas de stockage d'informations personnelles

### Configuration Sécurisée

```bash
# Variables d'environnement pour configuration sensible
OLLAMA_BASE_URL="http://localhost:11434"
LOG_LEVEL="INFO"  # Éviter DEBUG en production

# Validation des entrées utilisateur
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
```

---

## 🤝 Développement et Contribution

### Standards de Code

- **PEP 8** : Style de code Python avec Black
- **Type Hints** : Annotations de types complètes
- **Docstrings** : Documentation des fonctions
- **Tests** : Couverture minimale de 80%

### Workflow de Développement

```bash
# Setup environnement de développement
make setup

# Formatage et vérification
make format
make lint

# Tests avant commit
make test

# Nettoyage
make clean
```

### Architecture Extensible

Le système est conçu pour être facilement extensible :

- **Nouveaux Formats** : Ajouter des parsers dans `document_processing/`
- **Nouveaux Modèles** : Configuration via variables d'environnement
- **Nouvelles Interfaces** : Composants Streamlit modulaires
- **Nouveaux Stockages** : Interface abstraite pour vector stores

---

## 📞 Support et Maintenance

### Logs et Monitoring

```bash
# Consulter les logs
tail -f logs/application.log

# Logs Docker
docker-compose logs -f rag-app

# Statistiques de la base
python scripts/ingest_documents.py --stats

# Santé des services Docker
docker/docker-health-check.sh
```

### Dépannage Courant

**Ollama non accessible**
```bash
# Vérifier le service
ollama serve

# Télécharger le modèle
ollama pull qwen2.5:3b

# Vérifier la connectivité
curl http://localhost:11434/api/tags
```

**Problèmes de mémoire**
```bash
# Réduire la taille des batches
export BATCH_SIZE=16

# Utiliser un modèle plus petit
export OLLAMA_MODEL="qwen2.5:1.5b"
```

---

## 📝 Licence et Crédits

### Licence

Ce projet est distribué sous licence MIT, permettant :
- Utilisation libre pour l'éducation et la recherche
- Modification et redistribution
- Usage commercial avec attribution

### Technologies Utilisées

- **Python 3.11** : Langage principal
- **Streamlit** : Interface utilisateur web
- **ChromaDB** : Base de données vectorielle
- **Ollama** : Orchestration de modèles LLM
- **Sentence Transformers** : Génération d'embeddings
- **NLTK** : Traitement du langage naturel
- **Docker** : Containerisation et déploiement

### Remerciements

- **INPT** : Institut National des Postes et Télécommunications
- **Département Smart ICT** : Encadrement pédagogique
- **Communauté Open Source** : Outils et bibliothèques utilisés

---

## 🎯 Roadmap et Évolutions

### Version Actuelle (1.0.0)
- ✅ Recherche hybride sémantique + BM25
- ✅ Support multi-format de documents
- ✅ Interface conversationnelle Streamlit
- ✅ Déploiement Docker complet
- ✅ Compatibilité et migration de données

### Prochaines Versions

**Version 1.1.0**
- 🔄 Re-ranking avec modèles cross-encoder
- 🔄 Support de nouveaux formats (PPTX, XLSX)
- 🔄 API REST pour intégration externe
- 🔄 Métriques avancées et analytics

**Version 1.2.0**
- 🔄 Support multi-utilisateurs
- 🔄 Personnalisation par profil étudiant
- 🔄 Intégration avec systèmes LMS
- 🔄 Mode hors-ligne complet

---

**Version** : 1.0.0  
**Date** : Décembre 2024  
**Statut** : Production Ready ✅

*Développé avec ❤️ pour l'excellence académique à l'INPT Smart ICT*