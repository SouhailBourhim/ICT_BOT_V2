# 🚀 Guide d'Installation - Assistant RAG INPT

## Vue d'Ensemble

Ce guide détaille l'installation complète de l'Assistant RAG INPT dans différents environnements : développement local, production Docker, et déploiement sur serveur.

## 📋 Prérequis Système

### Configuration Minimale
- **OS** : Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10/11
- **Python** : 3.11+ (recommandé 3.11.14)
- **RAM** : 8GB minimum (16GB recommandé)
- **Stockage** : 10GB libres (modèles + données)
- **Réseau** : Connexion internet pour téléchargement initial

### Configuration Recommandée
- **CPU** : 8 cœurs ou plus
- **RAM** : 32GB pour modèles 7B+
- **GPU** : Optionnel (NVIDIA avec CUDA pour accélération)
- **SSD** : Recommandé pour performance ChromaDB

## 🛠️ Installation Locale (Développement)

### 1. Préparation de l'Environnement

#### Installation de Python 3.11
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS (avec Homebrew)
brew install python@3.11

# Windows
# Télécharger depuis python.org ou utiliser Microsoft Store
```

#### Installation d'Ollama
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Télécharger depuis https://ollama.ai/download/windows
```

#### Dépendances Système
```bash
# Ubuntu/Debian
sudo apt install -y build-essential curl git poppler-utils tesseract-ocr tesseract-ocr-fra

# macOS
brew install poppler tesseract tesseract-lang

# Windows (avec Chocolatey)
choco install git poppler tesseract
```

### 2. Configuration du Projet

#### Clonage et Setup Initial
```bash
# Cloner le repository
git clone <repository-url>
cd inpt-rag-assistant

# Créer l'environnement virtuel
python3.11 -m venv venv

# Activation (Linux/macOS)
source venv/bin/activate

# Activation (Windows)
venv\Scripts\activate
```

#### Installation des Dépendances
```bash
# Mise à jour de pip
pip install --upgrade pip

# Installation des dépendances
pip install -r requirements.txt

# Téléchargement des données NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Téléchargement du modèle spaCy français (optionnel)
python -m spacy download fr_core_news_md
```

### 3. Configuration Ollama

#### Démarrage du Service
```bash
# Démarrer Ollama en arrière-plan
ollama serve &

# Vérifier que le service fonctionne
curl http://localhost:11434/api/tags
```

#### Téléchargement du Modèle
```bash
# Modèle recommandé (3B paramètres, équilibré)
ollama pull qwen2.5:3b

# Alternatives selon vos ressources
ollama pull qwen2.5:1.5b  # Plus léger
ollama pull llama3.2:3b   # Alternative
ollama pull mistral:7b    # Plus performant (nécessite plus de RAM)

# Vérifier les modèles installés
ollama list
```

### 4. Configuration de l'Application

#### Fichier de Configuration
```bash
# Copier le template de configuration
cp .env.example .env

# Éditer la configuration
nano .env  # ou votre éditeur préféré
```

#### Configuration Recommandée (.env)
```bash
# === Configuration Locale ===
PROJECT_NAME="Assistant Éducatif RAG - INPT Smart ICT"
VERSION="1.0.0"
LANGUAGE="fr"

# === Chemins Locaux ===
BASE_DIR="."
DATA_DIR="./data"
DOCUMENTS_DIR="./data/documents"
DATABASE_DIR="./database"
LOGS_DIR="./logs"

# === Ollama Local ===
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:3b"
OLLAMA_TIMEOUT=180
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

# === Embeddings ===
EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION=384
BATCH_SIZE=32

# === Recherche ===
TOP_K_RETRIEVAL=7
SIMILARITY_THRESHOLD=0.4
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3

# === Performance ===
MAX_WORKERS=4
CACHE_ENABLED=true
LOG_LEVEL="INFO"
```

#### Initialisation des Répertoires
```bash
# Utiliser le script Python
python -c "from src.config.settings import setup_directories; setup_directories()"

# Ou utiliser le Makefile
make setup
```

### 5. Test de l'Installation

#### Vérification des Composants
```bash
# Test de la configuration
python -c "from src.config.settings import settings; print(f'Configuration OK: {settings.PROJECT_NAME}')"

# Test d'Ollama
python -c "from src.llm.ollama_client import OllamaClient; client = OllamaClient(); print('Ollama:', client._check_connection())"

# Test des embeddings
python -c "from src.document_processing.embedding_generator import EmbeddingGenerator; gen = EmbeddingGenerator(); print('Embeddings OK')"
```

#### Premier Lancement
```bash
# Lancer l'application
streamlit run app/chat.py

# Ou utiliser le Makefile
make run
```

L'application devrait être accessible sur `http://localhost:8501`

## 🐳 Installation Docker (Production)

### 1. Prérequis Docker

#### Installation Docker
```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS
brew install docker docker-compose

# Windows
# Installer Docker Desktop depuis docker.com
```

#### Vérification Docker
```bash
docker --version
docker-compose --version
```

### 2. Configuration Docker

#### Structure des Fichiers
```
docker/
├── Dockerfile              # Image de l'application
├── docker-compose.yml      # Services de développement
├── docker-compose.prod.yml # Configuration production
├── entrypoint.sh          # Script d'initialisation
└── nginx.conf             # Configuration Nginx (prod)
```

#### Variables d'Environnement Docker
```bash
# Créer le fichier .env pour Docker
cat > docker/.env << EOF
# === Configuration Docker ===
COMPOSE_PROJECT_NAME=inpt-rag
COMPOSE_FILE=docker-compose.yml

# === Ollama Configuration ===
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=1

# === Application Configuration ===
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# === Volumes ===
DATA_VOLUME=./data
DATABASE_VOLUME=./database
LOGS_VOLUME=./logs
EOF
```

### 3. Déploiement Docker

#### Développement
```bash
# Aller dans le répertoire Docker
cd docker

# Construire et lancer les services
docker-compose up -d

# Vérifier l'état des services
docker-compose ps

# Voir les logs
docker-compose logs -f
```

#### Production
```bash
# Utiliser la configuration production
docker-compose -f docker-compose.prod.yml up -d

# Ou utiliser le Makefile
make docker-prod
```

### 4. Configuration Post-Déploiement

#### Téléchargement du Modèle
```bash
# Attendre que les services soient prêts
docker-compose exec ollama ollama pull qwen2.5:3b

# Vérifier les modèles
docker-compose exec ollama ollama list
```

#### Ingestion de Documents
```bash
# Copier des documents dans le volume
cp ~/documents/*.pdf data/documents/

# Lancer l'ingestion
docker-compose exec rag-app python scripts/ingest_documents.py data/documents --recursive
```

#### Vérification de Santé
```bash
# Script de vérification automatique
./docker-health-check.sh

# Ou vérification manuelle
curl -f http://localhost:8501/_stcore/health
curl -f http://localhost:11434/api/tags
```

## 🖥️ Installation Serveur (Production)

### 1. Configuration Serveur

#### Prérequis Serveur
```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation des outils de base
sudo apt install -y curl wget git htop nginx certbot

# Configuration du firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

#### Utilisateur Dédié
```bash
# Créer un utilisateur pour l'application
sudo adduser inpt-rag
sudo usermod -aG docker inpt-rag
sudo su - inpt-rag
```

### 2. Déploiement avec Nginx

#### Configuration Nginx
```nginx
# /etc/nginx/sites-available/inpt-rag
server {
    listen 80;
    server_name votre-domaine.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

#### Activation du Site
```bash
# Activer la configuration
sudo ln -s /etc/nginx/sites-available/inpt-rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL avec Let's Encrypt
```bash
# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com

# Vérifier le renouvellement automatique
sudo certbot renew --dry-run
```

### 3. Service Systemd

#### Fichier de Service
```ini
# /etc/systemd/system/inpt-rag.service
[Unit]
Description=INPT RAG Assistant
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/inpt-rag/inpt-rag-assistant/docker
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=inpt-rag
Group=inpt-rag

[Install]
WantedBy=multi-user.target
```

#### Activation du Service
```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer le service
sudo systemctl enable inpt-rag
sudo systemctl start inpt-rag

# Vérifier l'état
sudo systemctl status inpt-rag
```

## 🔧 Configuration Avancée

### 1. Optimisation des Performances

#### Configuration Système
```bash
# Augmenter les limites de fichiers ouverts
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimisation mémoire virtuelle
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### Configuration Docker
```yaml
# docker-compose.prod.yml - Optimisations
services:
  rag-app:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    environment:
      - MAX_WORKERS=4
      - BATCH_SIZE=16
      - CACHE_TTL=7200
```

### 2. Monitoring et Logs

#### Configuration des Logs
```bash
# Rotation des logs
sudo tee /etc/logrotate.d/inpt-rag << EOF
/home/inpt-rag/inpt-rag-assistant/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 inpt-rag inpt-rag
}
EOF
```

#### Monitoring avec Prometheus (Optionnel)
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Sauvegarde et Récupération

#### Script de Sauvegarde
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/inpt-rag"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarder la base de données
tar -czf $BACKUP_DIR/database_$DATE.tar.gz database/

# Sauvegarder les conversations
tar -czf $BACKUP_DIR/conversations_$DATE.tar.gz data/conversations/

# Nettoyer les anciennes sauvegardes (garder 30 jours)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### Automatisation avec Cron
```bash
# Ajouter au crontab
crontab -e

# Sauvegarde quotidienne à 2h du matin
0 2 * * * /home/inpt-rag/backup.sh
```

## 🔍 Dépannage

### Problèmes Courants

#### Ollama ne démarre pas
```bash
# Vérifier les logs
journalctl -u ollama -f

# Redémarrer le service
sudo systemctl restart ollama

# Vérifier les ports
netstat -tlnp | grep 11434
```

#### Problèmes de mémoire
```bash
# Vérifier l'utilisation mémoire
free -h
docker stats

# Réduire la taille des batches
export BATCH_SIZE=8
export MAX_WORKERS=2
```

#### Erreurs de permissions
```bash
# Corriger les permissions
sudo chown -R inpt-rag:inpt-rag /home/inpt-rag/inpt-rag-assistant/
chmod -R 755 data/ database/ logs/
```

### Logs de Diagnostic

#### Localisation des Logs
```bash
# Logs de l'application
tail -f logs/application.log

# Logs Docker
docker-compose logs -f rag-app

# Logs système
journalctl -u inpt-rag -f
```

#### Niveaux de Debug
```bash
# Activer le debug
export LOG_LEVEL="DEBUG"

# Redémarrer avec debug
docker-compose restart rag-app
```

## ✅ Validation de l'Installation

### Tests Automatisés
```bash
# Tests unitaires
pytest tests/ -v

# Tests d'intégration Docker
pytest tests/test_docker_integration.py -v

# Test de bout en bout
python scripts/test_system.py
```

### Checklist de Validation

- [ ] Python 3.11+ installé et fonctionnel
- [ ] Ollama installé et modèle téléchargé
- [ ] Dépendances Python installées sans erreur
- [ ] Configuration .env correcte
- [ ] Répertoires initialisés
- [ ] Application accessible sur port 8501
- [ ] Ingestion de documents fonctionnelle
- [ ] Génération de réponses opérationnelle
- [ ] Logs sans erreurs critiques

### Test de Performance
```bash
# Benchmark du système
python scripts/benchmark.py

# Test de charge (optionnel)
# Utiliser des outils comme Apache Bench ou wrk
```

Cette installation complète vous permettra d'avoir un système RAG INPT pleinement fonctionnel, que ce soit pour le développement local ou le déploiement en production.