# 📝 Changelog - Assistant RAG INPT

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/lang/fr/).

## [Non publié]

### À venir
- Support de nouveaux formats de documents (PPTX, XLSX)
- API REST pour intégration externe
- Re-ranking avec modèles cross-encoder
- Interface multi-utilisateurs
- Métriques avancées et analytics

## [1.0.0] - 2024-12-28

### 🎉 Version Initiale - Production Ready

#### Ajouté
- **Architecture RAG Complète**
  - Pipeline de traitement de documents multi-format (PDF, TXT, MD, DOCX)
  - Moteur de recherche hybride (sémantique + BM25)
  - Intégration LLM avec Ollama (Qwen2.5:3b par défaut)
  - Interface conversationnelle Streamlit

- **Traitement de Documents Avancé**
  - Parser universel avec support multi-format
  - Chunking sémantique intelligent
  - Génération d'en-têtes contextuels automatiques
  - Extraction de métadonnées enrichies
  - Support de la structure des pages pour PDFs

- **Recherche Hybride Optimisée**
  - Recherche sémantique avec embeddings multilingues
  - Recherche BM25 avec tokenisation française
  - Fusion de scores pondérée et configurable
  - Normalisation automatique des scores
  - Support de filtres sur métadonnées

- **Stockage et Persistance**
  - ChromaDB pour stockage vectoriel
  - SQLite pour métadonnées et conversations
  - Modèles de données avec support de migration
  - Couche de compatibilité pour formats anciens/nouveaux
  - Sérialisation JSON pour métadonnées complexes

- **Interface Utilisateur Moderne**
  - Interface Streamlit responsive et intuitive
  - Chat conversationnel avec historique persistant
  - Gestion des conversations (création, chargement, suppression)
  - Affichage des sources avec niveaux de confiance
  - Rendu mathématique LaTeX intégré
  - Paramètres configurables (température, nombre de sources)

- **Génération de Réponses Intelligente**
  - Détection automatique de questions de suivi
  - Contexte conversationnel adaptatif
  - Post-traitement et validation des réponses
  - Extraction automatique de sources
  - Calcul de confiance basé sur scores multiples

- **Configuration Docker Complète**
  - Images Docker optimisées multi-stage
  - Docker Compose pour développement et production
  - Script d'initialisation robuste avec retry automatique
  - Gestion automatique des modèles Ollama
  - Volumes persistants pour données et modèles
  - Health checks intégrés

- **Outils et Scripts**
  - Script d'ingestion avec support de migration
  - Makefile complet pour toutes les opérations
  - Scripts de sauvegarde et restauration
  - Tests d'intégration Docker
  - Outils de diagnostic et monitoring

- **Documentation Complète**
  - Guide d'installation détaillé
  - Documentation d'architecture technique
  - Guide Docker avec configurations production
  - Documentation API complète
  - Guide de dépannage exhaustif
  - README avec exemples d'utilisation

#### Fonctionnalités Techniques

- **Compatibilité et Migration**
  - Support transparent des formats de chunks anciens et nouveaux
  - Migration automatique des métadonnées
  - Détection de format avec fallback gracieux
  - Validation de données avec correction automatique

- **Performance et Optimisation**
  - Cache Streamlit pour composants lourds
  - Traitement par batch optimisé pour embeddings
  - Index HNSW pour recherche vectorielle rapide
  - Lazy loading des modèles
  - Connection pooling pour Ollama

- **Sécurité et Robustesse**
  - Traitement local sans envoi de données externes
  - Validation des entrées utilisateur
  - Gestion d'erreurs avec retry automatique
  - Logs structurés avec niveaux configurables
  - Configuration via variables d'environnement

- **Monitoring et Observabilité**
  - Logs détaillés avec rotation automatique
  - Métriques de performance intégrées
  - Health checks pour tous les services
  - Scripts de diagnostic automatique
  - Monitoring des ressources système

#### Configuration par Défaut

- **Modèles**
  - LLM : Qwen2.5:3b (équilibré performance/qualité)
  - Embeddings : paraphrase-multilingual-MiniLM-L12-v2 (384 dim)
  - Recherche : 70% sémantique + 30% BM25

- **Paramètres Optimisés**
  - Chunk size : 1000 caractères avec overlap 200
  - Top-K retrieval : 7 documents
  - Seuil de similarité : 0.4
  - Température LLM : 0.1 (précis)
  - Max tokens : 500

- **Environnement**
  - Support Python 3.11+
  - Compatible Linux, macOS, Windows
  - Docker avec orchestration complète
  - Configuration adaptative local/Docker

#### Tests et Qualité

- **Tests Unitaires**
  - Couverture des composants principaux
  - Tests de parsing multi-format
  - Tests de recherche hybride
  - Tests d'intégration ChromaDB

- **Tests Docker**
  - Tests d'intégration complète
  - Tests de santé des services
  - Tests de persistance des données
  - Tests de communication inter-services

- **Qualité de Code**
  - Formatage automatique avec Black
  - Linting avec Ruff
  - Type hints complets
  - Documentation des fonctions

#### Déploiement

- **Environnements Supportés**
  - Développement local avec environnement virtuel
  - Docker Compose pour développement
  - Docker production avec Nginx
  - Déploiement serveur avec systemd

- **Scalabilité**
  - Configuration des ressources Docker
  - Limitation mémoire et CPU
  - Optimisation pour différentes tailles de modèles
  - Support de déploiement multi-instance

### Métadonnées de Version

- **Taille du Projet** : ~50 fichiers Python, ~5000 lignes de code
- **Dépendances** : 25+ packages Python optimisés
- **Formats Supportés** : PDF, TXT, Markdown, DOCX
- **Langues** : Français (optimisé), support multilingue
- **Modèles** : Compatible Ollama (Qwen, Llama, Mistral)
- **Base de Données** : ChromaDB + SQLite
- **Interface** : Streamlit web moderne

### Notes de Migration

Cette version 1.0.0 établit l'architecture de base stable. Les versions futures maintiendront la compatibilité ascendante pour :
- Formats de données existants
- Configuration utilisateur
- API interne principale
- Structure des documents

### Problèmes Connus

- **Performance** : Première génération peut être lente (téléchargement modèles)
- **Mémoire** : Modèles 7B+ nécessitent 16GB+ RAM
- **Docker** : Premier démarrage long (téléchargement images et modèles)

### Remerciements

Version développée pour l'INPT Smart ICT avec contributions de :
- Équipe de développement étudiante
- Encadrement pédagogique département Smart ICT
- Communauté open source (Streamlit, ChromaDB, Ollama)

---

## Format des Versions Futures

### [X.Y.Z] - YYYY-MM-DD

#### Ajouté
- Nouvelles fonctionnalités

#### Modifié
- Changements dans les fonctionnalités existantes

#### Déprécié
- Fonctionnalités qui seront supprimées

#### Supprimé
- Fonctionnalités supprimées

#### Corrigé
- Corrections de bugs

#### Sécurité
- Corrections de vulnérabilités

---

## Conventions de Versioning

- **Version Majeure (X.0.0)** : Changements incompatibles
- **Version Mineure (X.Y.0)** : Nouvelles fonctionnalités compatibles
- **Version Patch (X.Y.Z)** : Corrections de bugs compatibles

## Liens Utiles

- [Repository GitHub](https://github.com/votre-org/inpt-rag-assistant)
- [Documentation](./README.md)
- [Guide d'Installation](./INSTALLATION.md)
- [Guide Docker](./DOCKER_GUIDE.md)
- [Dépannage](./TROUBLESHOOTING.md)