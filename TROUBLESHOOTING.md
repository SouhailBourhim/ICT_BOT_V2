# 🔧 Guide de Dépannage - Assistant RAG INPT

## Vue d'Ensemble

Ce guide détaille les problèmes courants rencontrés avec l'Assistant RAG INPT et leurs solutions. Il couvre les environnements locaux, Docker, et les déploiements en production.

## 🚨 Problèmes Courants et Solutions

### 1. Problèmes d'Installation

#### Python et Dépendances

**Erreur : `ModuleNotFoundError: No module named 'src'`**
```bash
# Solution 1: Vérifier le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Solution 2: Installation en mode développement
pip install -e .

# Solution 3: Utiliser le chemin absolu
python -c "import sys; sys.path.append('/path/to/inpt-rag-assistant'); from src.config.settings import settings"
```

**Erreur : `ImportError: cannot import name 'DocxDocument'`**
```bash
# Installation de python-docx manquante
pip install python-docx

# Vérification
python -c "from docx import Document; print('DOCX support OK')"
```

**Erreur : `SSL: CERTIFICATE_VERIFY_FAILED`**
```bash
# Mise à jour des certificats (macOS)
/Applications/Python\ 3.11/Install\ Certificates.command

# Alternative avec pip
pip install --trusted-host pypi.org --trusted-host pypi.python.org --upgrade pip

# Configuration permanente
pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org"
```

#### Problèmes de Modèles

**Erreur : `spacy.util.OSError: [E050] Can't find model 'fr_core_news_md'`**
```bash
# Télécharger le modèle spaCy français
python -m spacy download fr_core_news_md

# Vérification
python -c "import spacy; nlp = spacy.load('fr_core_news_md'); print('spaCy OK')"

# Alternative si échec
pip install https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.7.0/fr_core_news_md-3.7.0-py3-none-any.whl
```

**Erreur : `sentence_transformers` modèle non trouvé**
```bash
# Téléchargement manuel du modèle
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print('Modèle téléchargé avec succès')
"

# Vérifier l'espace disque
df -h ~/.cache/torch/sentence_transformers/
```

### 2. Problèmes Ollama

#### Service Ollama

**Erreur : `Connection refused to localhost:11434`**
```bash
# Vérifier si Ollama est installé
ollama --version

# Démarrer le service
ollama serve &

# Vérifier le processus
ps aux | grep ollama
netstat -tlnp | grep 11434

# Test de connectivité
curl http://localhost:11434/api/tags
```

**Erreur : `Model 'qwen2.5:3b' not found`**
```bash
# Lister les modèles disponibles
ollama list

# Télécharger le modèle
ollama pull qwen2.5:3b

# Vérifier l'espace disque (modèles ~2-4GB)
df -h ~/.ollama/

# Alternative avec modèle plus petit
ollama pull qwen2.5:1.5b
```

**Erreur : `Ollama timeout after 180 seconds`**
```bash
# Augmenter le timeout dans .env
OLLAMA_TIMEOUT=300

# Vérifier les ressources système
free -h
top -p $(pgrep ollama)

# Redémarrer Ollama
pkill ollama
ollama serve &
```

#### Performance Ollama

**Problème : Génération très lente**
```bash
# Vérifier l'utilisation CPU/RAM
htop

# Optimiser la configuration Ollama
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1

# Utiliser un modèle plus petit
export OLLAMA_MODEL="qwen2.5:1.5b"

# Vérifier si GPU disponible (optionnel)
nvidia-smi  # Pour NVIDIA
```

### 3. Problèmes ChromaDB

#### Base de Données

**Erreur : `chromadb.errors.InvalidDimensionException`**
```bash
# Vérifier la dimension des embeddings
python -c "
from src.document_processing.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()
emb = gen.generate_embedding('test')
print(f'Dimension: {emb.shape[0]}')
"

# Réinitialiser la base si nécessaire
rm -rf database/chroma_db/
python -c "from src.config.settings import setup_directories; setup_directories()"
```

**Erreur : `sqlite3.OperationalError: database is locked`**
```bash
# Vérifier les processus utilisant la base
lsof database/chroma_db/chroma.sqlite3

# Arrêter l'application proprement
pkill -f streamlit
pkill -f python

# Redémarrer
streamlit run app/chat.py
```

**Problème : Base de données corrompue**
```bash
# Sauvegarder les données si possible
cp -r database/chroma_db database/chroma_db.backup

# Réinitialiser la base
python scripts/ingest_documents.py --reset

# Ré-ingérer les documents
python scripts/ingest_documents.py data/documents --recursive
```

### 4. Problèmes Streamlit

#### Interface Web

**Erreur : `streamlit: command not found`**
```bash
# Vérifier l'installation
pip list | grep streamlit

# Réinstaller si nécessaire
pip install --upgrade streamlit

# Vérifier le PATH
which python
which streamlit
```

**Problème : Page blanche ou erreur 404**
```bash
# Vérifier le port
netstat -tlnp | grep 8501

# Redémarrer avec port différent
streamlit run app/chat.py --server.port=8502

# Vérifier les logs
streamlit run app/chat.py --logger.level=debug
```

**Erreur : `ModuleNotFoundError` dans Streamlit**
```bash
# Vérifier le working directory
pwd
ls -la src/

# Lancer depuis le bon répertoire
cd /path/to/inpt-rag-assistant
streamlit run app/chat.py

# Ou utiliser le Makefile
make run
```

#### Performance Interface

**Problème : Interface très lente**
```bash
# Vérifier la mémoire
free -h

# Réduire la taille des batches
export BATCH_SIZE=8
export MAX_WORKERS=2

# Nettoyer le cache Streamlit
rm -rf ~/.streamlit/
```

### 5. Problèmes Docker

#### Services Docker

**Erreur : `docker-compose: command not found`**
```bash
# Installer Docker Compose
sudo apt install docker-compose-plugin

# Ou utiliser docker compose (v2)
docker compose up -d

# Vérifier la version
docker compose version
```

**Erreur : `Cannot connect to the Docker daemon`**
```bash
# Démarrer Docker
sudo systemctl start docker

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Vérifier
docker ps
```

**Problème : Services qui ne démarrent pas**
```bash
# Vérifier les logs
docker-compose logs ollama
docker-compose logs rag-app

# Vérifier les ressources
docker stats
df -h

# Redémarrer proprement
docker-compose down
docker-compose up -d
```

#### Réseau Docker

**Erreur : `Connection refused` entre services**
```bash
# Vérifier le réseau Docker
docker network ls
docker network inspect docker_default

# Tester la connectivité
docker-compose exec rag-app ping ollama
docker-compose exec rag-app curl http://ollama:11434/api/tags

# Recréer le réseau
docker-compose down
docker network prune
docker-compose up -d
```

#### Volumes Docker

**Problème : Données perdues après redémarrage**
```bash
# Vérifier les volumes
docker volume ls
docker volume inspect inpt-rag_ollama_data

# Vérifier les montages
docker-compose exec rag-app ls -la /app/data
docker-compose exec rag-app ls -la /app/database

# Corriger les permissions
sudo chown -R $USER:$USER data/ database/ logs/
```

### 6. Problèmes de Performance

#### Mémoire

**Erreur : `Out of Memory` ou `Killed`**
```bash
# Vérifier l'utilisation mémoire
free -h
ps aux --sort=-%mem | head -10

# Réduire l'utilisation mémoire
export BATCH_SIZE=8
export MAX_WORKERS=2
export OLLAMA_MAX_LOADED_MODELS=1

# Utiliser un modèle plus petit
export OLLAMA_MODEL="qwen2.5:1.5b"

# Augmenter le swap (temporaire)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Stockage

**Erreur : `No space left on device`**
```bash
# Vérifier l'espace disque
df -h

# Nettoyer les données temporaires
docker system prune -f
rm -rf ~/.cache/torch/
rm -rf ~/.cache/huggingface/

# Nettoyer les logs
find logs/ -name "*.log" -mtime +7 -delete

# Compresser les anciennes données
tar -czf backup_$(date +%Y%m%d).tar.gz database/
```

#### CPU

**Problème : CPU à 100%**
```bash
# Identifier les processus gourmands
top -o %CPU
htop

# Limiter les workers
export MAX_WORKERS=2
export BATCH_SIZE=16

# Utiliser nice pour réduire la priorité
nice -n 10 streamlit run app/chat.py
```

## 🔍 Diagnostic Avancé

### 1. Scripts de Diagnostic

#### Test Complet du Système
```bash
#!/bin/bash
# diagnostic.sh - Test complet du système

echo "🔍 Diagnostic Assistant RAG INPT"
echo "================================"

# Test Python
echo "1. Test Python..."
python --version || echo "❌ Python non trouvé"

# Test des modules
echo "2. Test des modules Python..."
python -c "
try:
    import streamlit, chromadb, sentence_transformers, ollama
    print('✅ Modules principaux OK')
except ImportError as e:
    print(f'❌ Module manquant: {e}')
"

# Test Ollama
echo "3. Test Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama accessible"
    ollama list | head -5
else
    echo "❌ Ollama non accessible"
fi

# Test ChromaDB
echo "4. Test ChromaDB..."
if [ -d "database/chroma_db" ]; then
    echo "✅ Base ChromaDB trouvée"
    ls -la database/chroma_db/
else
    echo "⚠️ Base ChromaDB non initialisée"
fi

# Test des ressources
echo "5. Ressources système..."
echo "RAM: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "Disque: $(df -h . | tail -1 | awk '{print $3"/"$2" ("$5")"}')"

# Test de configuration
echo "6. Configuration..."
python -c "
from src.config.settings import settings
print(f'Modèle LLM: {settings.OLLAMA_MODEL}')
print(f'Modèle embeddings: {settings.EMBEDDING_MODEL}')
print(f'Chunk size: {settings.CHUNK_SIZE}')
"

echo "================================"
echo "Diagnostic terminé"
```

#### Test de Performance
```bash
#!/bin/bash
# benchmark.sh - Test de performance

echo "📊 Benchmark Assistant RAG INPT"

# Test d'ingestion
echo "Test d'ingestion..."
time python scripts/ingest_documents.py data/documents/test.pdf

# Test de recherche
echo "Test de recherche..."
time python -c "
from src.retrieval.hybrid_search import HybridSearchEngine
from src.storage.vector_store import VectorStore

vs = VectorStore()
hs = HybridSearchEngine(vs)
results = hs.search('test query', top_k=5)
print(f'Résultats: {len(results)}')
"

# Test de génération
echo "Test de génération LLM..."
time python -c "
from src.llm.ollama_client import OllamaClient
client = OllamaClient()
response = client.generate('Qu\'est-ce que l\'IoT ?', max_tokens=100)
print(f'Réponse: {len(response)} caractères')
"
```

### 2. Logs de Debug

#### Configuration des Logs
```python
# Configuration debug dans .env
LOG_LEVEL=DEBUG
LOG_FORMAT="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Logs détaillés pour composants spécifiques
import logging
logging.getLogger("chromadb").setLevel(logging.DEBUG)
logging.getLogger("sentence_transformers").setLevel(logging.DEBUG)
```

#### Analyse des Logs
```bash
# Logs d'erreur récents
grep -i error logs/*.log | tail -20

# Logs par composant
grep "ollama_client" logs/*.log
grep "vector_store" logs/*.log
grep "hybrid_search" logs/*.log

# Analyse des performances
grep "duration\|time\|ms" logs/*.log | tail -10

# Erreurs de mémoire
grep -i "memory\|oom\|killed" logs/*.log
```

### 3. Monitoring en Temps Réel

#### Surveillance Système
```bash
# Monitoring continu
watch -n 2 '
echo "=== Processus ==="
ps aux | grep -E "(streamlit|ollama|python)" | grep -v grep
echo "=== Mémoire ==="
free -h
echo "=== Réseau ==="
netstat -tlnp | grep -E "(8501|11434)"
'

# Logs en temps réel
tail -f logs/*.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

#### Métriques Docker
```bash
# Stats des conteneurs
docker stats --no-stream

# Logs en temps réel
docker-compose logs -f --tail=50

# Santé des services
docker-compose ps
```

## 🛠️ Solutions Spécialisées

### 1. Migration de Données

#### Migration ChromaDB
```python
# Script de migration de base
from src.storage.models import migrate_chunk_metadata, is_enhanced_chunk
from src.storage.vector_store import VectorStore

def migrate_database():
    """Migre la base vers le nouveau format"""
    vs = VectorStore()
    
    # Récupérer tous les documents
    all_docs = vs.peek(limit=vs.count())
    
    migration_count = 0
    for doc_id, text, metadata in zip(
        all_docs['ids'], all_docs['documents'], all_docs['metadatas']
    ):
        if not is_enhanced_chunk(metadata):
            # Migrer les métadonnées
            enhanced_metadata = migrate_chunk_metadata(metadata)
            vs.update_metadata(doc_id, enhanced_metadata)
            migration_count += 1
    
    print(f"Migration terminée: {migration_count} chunks migrés")

# Exécution
migrate_database()
```

### 2. Récupération d'Urgence

#### Sauvegarde d'Urgence
```bash
#!/bin/bash
# emergency_backup.sh

BACKUP_DIR="emergency_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "🚨 Sauvegarde d'urgence en cours..."

# Arrêter les services
docker-compose down 2>/dev/null || pkill -f streamlit

# Sauvegarder les données critiques
cp -r database/ $BACKUP_DIR/
cp -r data/conversations/ $BACKUP_DIR/
cp .env $BACKUP_DIR/
cp -r logs/ $BACKUP_DIR/

# Créer une archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/
rm -rf $BACKUP_DIR/

echo "✅ Sauvegarde créée: $BACKUP_DIR.tar.gz"
```

#### Restauration d'Urgence
```bash
#!/bin/bash
# emergency_restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

echo "🔄 Restauration d'urgence depuis $BACKUP_FILE"

# Arrêter les services
docker-compose down 2>/dev/null || pkill -f streamlit

# Sauvegarder l'état actuel
mv database database.old.$(date +%Y%m%d_%H%M%S) 2>/dev/null
mv data/conversations data/conversations.old.$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Extraire la sauvegarde
tar -xzf $BACKUP_FILE

# Restaurer les données
BACKUP_DIR=$(basename $BACKUP_FILE .tar.gz)
cp -r $BACKUP_DIR/database/ .
cp -r $BACKUP_DIR/conversations/ data/
cp $BACKUP_DIR/.env .

# Nettoyer
rm -rf $BACKUP_DIR/

echo "✅ Restauration terminée"
echo "Redémarrez le système avec: make run ou docker-compose up -d"
```

## 📞 Support et Escalade

### Niveaux de Support

#### Niveau 1 : Auto-diagnostic
1. Consulter ce guide de dépannage
2. Vérifier les logs d'erreur
3. Exécuter les scripts de diagnostic
4. Tenter les solutions courantes

#### Niveau 2 : Support Communautaire
1. Rechercher dans les issues GitHub
2. Consulter la documentation complète
3. Poser une question avec logs détaillés

#### Niveau 3 : Support Technique
1. Créer un rapport de bug détaillé
2. Inclure les logs complets
3. Fournir les informations système
4. Décrire les étapes de reproduction

### Informations à Fournir

#### Rapport de Bug Complet
```bash
# Générer un rapport automatique
cat > bug_report.txt << EOF
=== RAPPORT DE BUG ASSISTANT RAG INPT ===
Date: $(date)
Système: $(uname -a)
Python: $(python --version)
Docker: $(docker --version 2>/dev/null || echo "Non installé")

=== CONFIGURATION ===
$(cat .env | grep -v "PASSWORD\|SECRET\|KEY" || echo "Fichier .env non trouvé")

=== LOGS D'ERREUR ===
$(tail -50 logs/*.log 2>/dev/null || echo "Pas de logs trouvés")

=== PROCESSUS ===
$(ps aux | grep -E "(streamlit|ollama|python)" | grep -v grep)

=== RESSOURCES ===
Mémoire: $(free -h | grep Mem)
Disque: $(df -h . | tail -1)

=== DESCRIPTION DU PROBLÈME ===
[Décrire le problème ici]

=== ÉTAPES DE REPRODUCTION ===
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]

=== COMPORTEMENT ATTENDU ===
[Décrire ce qui devrait se passer]

=== COMPORTEMENT OBSERVÉ ===
[Décrire ce qui se passe réellement]
EOF

echo "Rapport généré dans bug_report.txt"
```

Ce guide de dépannage couvre la majorité des problèmes rencontrés avec l'Assistant RAG INPT. Pour des problèmes spécifiques non couverts, n'hésitez pas à consulter la documentation complète ou à créer un rapport de bug détaillé.