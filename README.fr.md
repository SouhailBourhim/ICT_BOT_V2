# 🎓 Assistant Éducatif RAG - INPT Smart ICT

**Projet Académique - Système de Recherche et Génération Augmentée par Récupération**

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.29.0-red)
![ChromaDB](https://img.shields.io/badge/chromadb-0.4.22-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 📋 Présentation du Projet

Ce projet implémente un **système RAG (Retrieval-Augmented Generation)** intelligent conçu pour assister les étudiants Smart ICT de l'Institut National des Postes et Télécommunications (INPT). Le système combine des techniques avancées de traitement du langage naturel, de recherche vectorielle et de génération de texte pour créer un assistant éducatif capable de répondre aux questions des étudiants en se basant sur leurs documents de cours.

### 🎯 Objectifs Pédagogiques

1. **Apprentissage Personnalisé** : Fournir des réponses contextualisées basées sur le contenu spécifique des cours
2. **Accessibilité** : Permettre aux étudiants d'interroger leurs documents en langage naturel
3. **Traçabilité** : Citer précisément les sources utilisées pour chaque réponse
4. **Multimodalité** : Supporter différents formats de documents (PDF, TXT, MD, DOCX)

---

## 🏗️ Architecture Technique

### Vue d'Ensemble du Système

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
│  (Semantic + BM25) │          │   (Qwen 2.5)      │
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
- **Parser** : Extraction de texte multi-format (PDF, TXT, MD, DOCX)
- **Chunker Sémantique** : Découpage intelligent préservant la cohérence
- **Générateur d'Embeddings** : Vectorisation avec modèles multilingues
- **Extracteur de Métadonnées** : Enrichissement contextuel

#### 2. **Moteur de Recherche Hybride** (`src/retrieval/`)
- **Recherche Sémantique** : Similarité vectorielle avec embeddings
- **Recherche BM25** : Correspondance par mots-clés (TF-IDF amélioré)
- **Fusion de Scores** : Combinaison pondérée des deux approches
- **Re-ranking** : Amélioration de la pertinence des résultats

#### 3. **Couche de Stockage** (`src/storage/`)
- **ChromaDB** : Base de données vectorielle pour embeddings
- **SQLite** : Métadonnées et historique des conversations
- **Modèles de Données** : Structures optimisées pour la recherche

#### 4. **Intégration LLM** (`src/llm/`)
- **Client Ollama** : Interface avec modèles locaux (Qwen 2.5 par défaut)
- **Templates de Prompts** : Prompts optimisés pour l'éducation
- **Générateur de Réponses** : Orchestration RAG complète

#### 5. **Interface Utilisateur** (`app/`)
- **Streamlit** : Interface web moderne et intuitive
- **Chat Interface** : Conversation naturelle avec l'assistant
- **Upload de Documents** : Ingestion en temps réel
- **Analytics** : Métriques et statistiques d'utilisation

---

## 🚀 Installation et Configuration

### Prérequis Système

- **Python 3.11+** (testé avec 3.11.14)
- **Ollama** ([https://ollama.ai](https://ollama.ai))
- **8GB RAM minimum** (16GB recommandé)
- **10GB espace disque** pour modèles et données

### Installation Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/SouhailBourhim/ICT_BOT_V2.git
cd ICT_BOT_V2

# 2. Créer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer Ollama
ollama serve &
ollama pull qwen2.5:3b

# 5. Initialiser la base de données
python scripts/setup_database.py

# 6. Configurer l'environnement
cp .env.example .env
# Éditer .env selon vos besoins
```

### Configuration Avancée

Le fichier `.env` permet de personnaliser le comportement du système :

```bash
# Modèle LLM
OLLAMA_MODEL="qwen2.5:3b"
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

# Embeddings
EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE=32

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

# Vérifier les statistiques
python scripts/ingest_documents.py --stats
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

1. **Page Chat** : Poser des questions en langage naturel
2. **Upload Documents** : Ajouter de nouveaux documents
3. **Analytics** : Consulter les métriques du système

### 4. Exemples de Questions

```
- "Qu'est-ce que le clustering en machine learning ?"
- "Explique-moi l'algorithme K-means"
- "Quelles sont les différences entre apprentissage supervisé et non-supervisé ?"
- "Comment fonctionne la régression linéaire ?"
```

---

## 🔬 Aspects Techniques Avancés

### Algorithmes de Recherche

#### Recherche Sémantique
- **Modèle d'Embeddings** : `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimension des Vecteurs** : 384
- **Métrique de Similarité** : Cosinus
- **Optimisation** : Index HNSW pour recherche rapide

#### Recherche BM25
- **Tokenisation** : NLTK avec support français
- **Paramètres** : k1=1.2, b=0.75 (optimisés pour textes académiques)
- **Préprocessing** : Lemmatisation et suppression des mots vides

#### Fusion de Scores
```python
score_final = (semantic_weight * score_semantic) + (bm25_weight * score_bm25)
```

### Pipeline de Traitement

#### Chunking Sémantique
- **Stratégie** : Préservation des paragraphes et sections
- **Taille** : 1000 caractères avec overlap de 200
- **Métadonnées** : Page, section, type de contenu

#### Génération de Réponses
- **Contexte** : Top-K chunks les plus pertinents
- **Prompt Engineering** : Templates optimisés pour l'éducation
- **Post-processing** : Validation et formatage des réponses

---

## � Structure du Projet

```
inpt-rag-assistant/
├── src/                          # Code source principal
│   ├── config/                   # Configuration système
│   │   └── settings.py          # Paramètres globaux
│   ├── document_processing/      # Pipeline de traitement
│   │   ├── parser.py            # Extraction multi-format
│   │   ├── chunker.py           # Découpage sémantique
│   │   ├── embedding_generator.py # Vectorisation
│   │   └── metadata_extractor.py # Enrichissement
│   ├── storage/                  # Couche de persistance
│   │   ├── vector_store.py      # Interface ChromaDB
│   │   ├── metadata_store.py    # Gestion métadonnées
│   │   └── models.py            # Modèles de données
│   ├── retrieval/                # Moteur de recherche
│   │   ├── hybrid_search.py     # Recherche hybride
│   │   ├── semantic_retriever.py # Recherche vectorielle
│   │   └── bm25_retriever.py    # Recherche BM25
│   ├── llm/                      # Intégration LLM
│   │   ├── ollama_client.py     # Client Ollama
│   │   ├── prompt_templates.py  # Templates de prompts
│   │   └── response_generator.py # Génération RAG
│   ├── conversation/             # Gestion conversations
│   │   ├── manager.py           # Historique et contexte
│   │   └── context_window.py    # Fenêtre contextuelle
│   └── utils/                    # Utilitaires
│       ├── text_processing.py   # Traitement de texte
│       └── logger.py            # Système de logs
├── app/                          # Interface Streamlit
│   ├── chat.py                  # Application principale
│   ├── components/              # Composants UI
│   └── pages/                   # Pages de l'interface
├── scripts/                      # Scripts utilitaires
│   ├── ingest_documents.py      # Ingestion de documents
│   ├── setup_database.py        # Initialisation DB
│   └── benchmark.py             # Tests de performance
├── tests/                        # Tests unitaires
├── docker/                       # Configuration Docker
├── data/                         # Données
│   ├── documents/               # Documents sources
│   └── conversations/           # Historique des chats
├── database/                     # Bases de données
│   └── chroma_db/              # ChromaDB
├── requirements.txt              # Dépendances Python
├── .env.example                 # Configuration exemple
└── README.md                    # Documentation
```

---

## 🧪 Tests et Évaluation

### Tests Unitaires

```bash
# Installer les outils de développement
python -m pip install -r requirements-dev.txt

# Lancer tous les tests
python -m pytest tests/ -v

# Tests avec couverture
python -m pytest tests/ --cov=src --cov-report=html

# Lint CI
python -m ruff check src app tests scripts

# Healthcheck local sans services externes
python scripts/healthcheck.py --skip-streamlit --skip-ollama
```

### Évaluation du Système

Le système inclut des métriques d'évaluation automatiques :

- **Précision de Recherche** : Pertinence des documents récupérés
- **Qualité des Réponses** : Cohérence et exactitude
- **Performance** : Temps de réponse et utilisation mémoire
- **Couverture** : Pourcentage de questions avec réponses satisfaisantes

### Benchmarks de Performance

Sur une machine de référence (i7, 16GB RAM) :
- **Ingestion** : ~50 pages PDF/minute
- **Recherche** : ~100ms par requête
- **Génération** : ~2-5 secondes selon le modèle
- **Embedding** : ~1000 chunks/minute

---

## 🐳 Déploiement Docker

Pour un déploiement simplifié :

```bash
# Déploiement complet
cd docker
docker-compose up -d

# Accès à l'application
open http://localhost:8501
```

Le système Docker inclut :
- **Application principale** avec Streamlit
- **Service Ollama** pour les LLMs
- **Volumes persistants** pour données et modèles
- **Configuration réseau** optimisée

---

## 📈 Métriques et Analytics

### Tableau de Bord Analytics

L'interface inclut un tableau de bord complet avec :

- **Statistiques de Documents** : Nombre, taille, formats
- **Métriques de Recherche** : Requêtes, temps de réponse, pertinence
- **Utilisation LLM** : Tokens générés, modèles utilisés
- **Performance Système** : Mémoire, CPU, stockage

### Logs et Monitoring

```bash
# Consulter les logs
tail -f logs/application.log

# Statistiques de la base vectorielle
python scripts/ingest_documents.py --stats

# Métriques de performance
python scripts/benchmark.py
```

---

## 🔧 Personnalisation et Extension

### Ajout de Nouveaux Formats

Pour supporter un nouveau format de document :

1. Étendre `src/document_processing/parser.py`
2. Ajouter le parser spécifique
3. Mettre à jour `SUPPORTED_FORMATS` dans `settings.py`

### Modification des Prompts

Les templates de prompts sont dans `src/llm/prompt_templates.py` :

```python
RAG_QA = PromptTemplate(
    system="Tu es un assistant éducatif...",
    user="Contexte: {context}\nQuestion: {question}\nRéponse:"
)
```

### Intégration de Nouveaux Modèles

Pour utiliser un autre modèle LLM :

```bash
# Télécharger le modèle
ollama pull mistral:7b

# Modifier la configuration
echo "OLLAMA_MODEL=mistral:7b" >> .env
```

---

## 🎓 Aspects Pédagogiques

### Fonctionnalités Éducatives

1. **Réponses Graduées** : Adaptation au niveau de compréhension
2. **Citations Précises** : Références aux sources avec numéros de page
3. **Questions de Suivi** : Génération automatique pour approfondir
4. **Explications Étape par Étape** : Décomposition des concepts complexes

### Optimisations pour l'Apprentissage

- **Prompts Pédagogiques** : Encouragent la réflexion critique
- **Contexte Préservé** : Maintien de la cohérence conversationnelle
- **Feedback Constructif** : Suggestions d'amélioration
- **Multilingue** : Support français optimisé

---

## 🔒 Sécurité et Confidentialité

### Protection des Données

- **Traitement Local** : Aucune donnée envoyée vers des services externes
- **Chiffrement** : Base de données et communications sécurisées
- **Isolation** : Environnement containerisé avec Docker
- **Logs Anonymisés** : Pas de stockage d'informations personnelles

### Bonnes Pratiques

- Variables d'environnement pour configuration sensible
- Validation des entrées utilisateur
- Gestion sécurisée des fichiers uploadés
- Limitation des ressources système

---

## 📚 Documentation Technique

### Guides Disponibles

- **QUICKSTART.md** : Guide de démarrage rapide
- **DOCKER_GUIDE.md** : Déploiement avec Docker
- **EVALUATION_REPORT.md** : Rapport d'évaluation détaillé
- **MATH_FORMULAS_GUIDE.md** : Support des formules mathématiques

### API et Intégration

Le système expose des interfaces Python pour intégration :

```python
from src.llm.response_generator import ResponseGenerator
from src.retrieval.hybrid_search import HybridSearchEngine

# Initialisation
response_gen = ResponseGenerator(...)

# Génération de réponse
response = response_gen.generate_response(
    question="Qu'est-ce que l'IoT ?",
    conversation_id="user_123"
)
```

---

## 🤝 Contribution et Développement

### Standards de Code

- **PEP 8** : Style de code Python
- **Type Hints** : Annotations de types complètes
- **Docstrings** : Documentation des fonctions
- **Tests** : Couverture minimale de 80%

### Workflow de Développement

1. Fork du repository
2. Création d'une branche feature
3. Développement avec tests
4. Pull request avec review
5. Intégration après validation

---

## 📞 Support et Contact

### Ressources d'Aide

- **Issues GitHub** : Signalement de bugs et demandes de fonctionnalités
- **Documentation** : Guides complets dans le repository
- **Logs** : Diagnostic automatique des problèmes
- **Community** : Forum de discussion pour utilisateurs

### Informations de Contact

- **Repository** : https://github.com/SouhailBourhim/ICT_BOT_V2
- **Auteur** : Étudiant Smart ICT - INPT
- **Encadrement** : Professeurs du département Smart ICT

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

## 🎯 Conclusion

Ce projet démontre l'implémentation pratique d'un système RAG complet, intégrant les dernières avancées en intelligence artificielle pour créer un assistant éducatif performant. Il illustre la maîtrise de technologies modernes (LLMs, bases de données vectorielles, interfaces web) tout en répondant à un besoin pédagogique réel.

Le système est conçu pour être :
- **Extensible** : Architecture modulaire permettant l'ajout de fonctionnalités
- **Performant** : Optimisations pour temps de réponse et utilisation mémoire
- **Robuste** : Gestion d'erreurs et tests automatisés
- **Utilisable** : Interface intuitive et documentation complète

**Version** : 1.0.0  
**Date** : Décembre 2024  
**Statut** : Production Ready ✅

---

*Développé avec ❤️ pour l'excellence académique à l'INPT Smart ICT*
