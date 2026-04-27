# 🚀 Guide d'Installation - Assistant RAG INPT

## Installation Rapide (5 minutes)

### Prérequis
- Python 3.11+ installé
- 8GB RAM minimum
- 10GB espace disque libre

### Étapes d'Installation

#### 1. Préparation de l'Environnement
```bash
# Naviguer vers le projet
cd inpt-rag-assistant

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate     # Windows
```

#### 2. Installation des Dépendances
```bash
# Installer les packages Python
pip install -r requirements.txt

# Télécharger les données NLTK
python -c "import nltk; nltk.download('punkt')"
```

#### 3. Installation d'Ollama
```bash
# Installer Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Démarrer le service
ollama serve &

# Télécharger le modèle LLM
ollama pull qwen2.5:3b
```

#### 4. Initialisation du Système
```bash
# Créer les bases de données
python scripts/setup_database.py

# Configurer l'environnement
cp .env.example .env
```

#### 5. Test de l'Installation
```bash
# Lancer l'application
streamlit run app/chat.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`

## Installation avec Docker (Alternative)

Si vous préférez Docker :

```bash
# Naviguer vers le dossier Docker
cd docker

# Lancer tous les services
docker-compose up -d

# Accéder à l'application
open http://localhost:8501
```

## Premier Usage

### 1. Ajouter des Documents
```bash
# Copier vos documents PDF/TXT dans le dossier
cp ~/mes-cours/*.pdf data/documents/

# Ingérer les documents
python scripts/ingest_documents.py data/documents --recursive
```

### 2. Tester le Système
1. Aller sur `http://localhost:8501`
2. Naviguer vers la page "💬 Chat"
3. Poser une question : "Qu'est-ce que le machine learning ?"

## Résolution de Problèmes

### Erreur "Module not found"
```bash
# Vérifier l'environnement virtuel
source venv/bin/activate
pip install -r requirements.txt
```

### Erreur "Ollama connection"
```bash
# Vérifier qu'Ollama fonctionne
curl http://localhost:11434/api/tags

# Si pas de réponse, redémarrer
ollama serve
```

### Erreur "Out of memory"
```bash
# Utiliser un modèle plus léger
ollama pull llama3.2:1b

# Modifier .env
echo "OLLAMA_MODEL=llama3.2:1b" >> .env
```

## Configuration Personnalisée

Éditez le fichier `.env` pour personnaliser :

```bash
# Modèle LLM (choisir selon vos ressources)
OLLAMA_MODEL="qwen2.5:3b"   # Recommandé pour le RAG
# OLLAMA_MODEL="llama3.2:3b" # Alternative plus légère
# OLLAMA_MODEL="mistral:7b"   # Plus performant

# Paramètres de recherche
TOP_K_RETRIEVAL=7
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3

# Paramètres de génération
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500
```

## Vérification de l'Installation

### Commandes de Test
```bash
# Vérifier Python
python --version  # Doit être 3.11+

# Vérifier les packages
pip list | grep streamlit
pip list | grep chromadb

# Vérifier Ollama
ollama list

# Vérifier la base de données
python scripts/ingest_documents.py --stats
```

### Indicateurs de Succès
- ✅ Streamlit démarre sans erreur
- ✅ Page web accessible sur localhost:8501
- ✅ Ollama répond aux requêtes
- ✅ Base de données initialisée
- ✅ Documents ingérés avec succès

## Support

En cas de problème :
1. Vérifiez les logs dans `logs/`
2. Consultez `GUIDE_UTILISATEUR.md`
3. Redémarrez tous les services
4. Réinitialisez la base de données si nécessaire

---

**Installation terminée !** Vous pouvez maintenant utiliser votre assistant RAG. 🎉
