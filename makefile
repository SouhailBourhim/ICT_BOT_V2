.PHONY: help install setup run ingest clean test docker-up docker-down

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
STREAMLIT := streamlit
OLLAMA_MODEL := llama3.2:3b

# Couleurs pour l'affichage
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@echo "$(GREEN)Assistant RAG INPT - Commandes disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Installe les dépendances Python
	@echo "$(GREEN)Installation des dépendances...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON) -m spacy download fr_core_news_md
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

setup: install ## Setup complet du projet (install + init)
	@echo "$(GREEN)Initialisation du projet...$(NC)"
	cp .env.example .env
	$(PYTHON) -c "from src.config.settings import setup_directories; setup_directories()"
	@echo "$(GREEN)✅ Projet initialisé$(NC)"
	@echo "$(YELLOW)⚠️  N'oubliez pas de:$(NC)"
	@echo "  1. Éditer le fichier .env"
	@echo "  2. Installer Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
	@echo "  3. Télécharger le modèle: ollama pull $(OLLAMA_MODEL)"

venv: ## Crée un environnement virtuel
	@echo "$(GREEN)Création de l'environnement virtuel...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ Environnement créé$(NC)"
	@echo "$(YELLOW)Activez-le avec: source $(VENV)/bin/activate$(NC)"

run: ## Lance l'application Streamlit
	@echo "$(GREEN)Lancement de l'application...$(NC)"
	$(STREAMLIT) run app/chat.py

ollama-start: ## Démarre Ollama en arrière-plan
	@echo "$(GREEN)Démarrage d'Ollama...$(NC)"
	ollama serve &
	@echo "$(GREEN)✅ Ollama lancé$(NC)"

ollama-pull: ## Télécharge le modèle LLM
	@echo "$(GREEN)Téléchargement du modèle $(OLLAMA_MODEL)...$(NC)"
	ollama pull $(OLLAMA_MODEL)
	@echo "$(GREEN)✅ Modèle téléchargé$(NC)"

ollama-models: ## Liste les modèles disponibles
	@echo "$(GREEN)Modèles Ollama disponibles:$(NC)"
	ollama list

ingest: ## Ingère les documents du dossier data/documents
	@echo "$(GREEN)Ingestion des documents...$(NC)"
	$(PYTHON) scripts/ingest_documents.py data/documents --recursive
	@echo "$(GREEN)✅ Documents ingérés$(NC)"

ingest-file: ## Ingère un fichier unique (usage: make ingest-file FILE=path/to/file)
	@echo "$(GREEN)Ingestion de $(FILE)...$(NC)"
	$(PYTHON) scripts/ingest_documents.py $(FILE)

stats: ## Affiche les statistiques de la base
	@echo "$(GREEN)Statistiques de la base:$(NC)"
	$(PYTHON) scripts/ingest_documents.py --stats

reset-db: ## Réinitialise la base de données (⚠️ DESTRUCTIF)
	@echo "$(YELLOW)⚠️  Cette action va supprimer toutes les données!$(NC)"
	@read -p "Confirmer (oui/non): " confirm && [ "$$confirm" = "oui" ] && \
		$(PYTHON) scripts/ingest_documents.py data/documents --reset || echo "Annulé"

test: ## Lance les tests
	@echo "$(GREEN)Lancement des tests...$(NC)"
	pytest tests/ -v

test-cov: ## Lance les tests avec couverture
	@echo "$(GREEN)Tests avec couverture...$(NC)"
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Rapport disponible dans: htmlcov/index.html$(NC)"

lint: ## Vérifie le code avec flake8
	@echo "$(GREEN)Vérification du code...$(NC)"
	flake8 src/ app/ tests/ --max-line-length=120

format: ## Formate le code avec black
	@echo "$(GREEN)Formatage du code...$(NC)"
	black src/ app/ tests/

clean: ## Nettoie les fichiers temporaires
	@echo "$(GREEN)Nettoyage...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

docker-build: ## Build l'image Docker
	@echo "$(GREEN)Build de l'image Docker...$(NC)"
	cd docker && docker-compose build

docker-up: ## Lance les services Docker
	@echo "$(GREEN)Démarrage des services Docker...$(NC)"
	cd docker && docker-compose up -d
	@echo "$(GREEN)✅ Services lancés$(NC)"
	@echo "$(YELLOW)Application disponible sur: http://localhost:8501$(NC)"
	@echo "$(YELLOW)Analytics disponible sur: http://localhost:8501/analytics$(NC)"

docker-down: ## Arrête les services Docker
	@echo "$(GREEN)Arrêt des services Docker...$(NC)"
	cd docker && docker-compose down

docker-logs: ## Affiche les logs Docker
	cd docker && docker-compose logs -f

docker-restart: docker-down docker-up ## Redémarre les services Docker

docker-prod: ## Lance en mode production
	@echo "$(GREEN)Démarrage en mode production...$(NC)"
	cd docker && docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Services production lancés$(NC)"

docker-ingest: ## Ingère des documents via Docker
	@echo "$(GREEN)Ingestion via Docker...$(NC)"
	cd docker && docker-compose exec rag-app python scripts/ingest_documents.py data/documents --recursive

docker-shell: ## Ouvre un shell dans le container
	cd docker && docker-compose exec rag-app /bin/bash

docker-clean: ## Nettoie les containers et volumes
	@echo "$(YELLOW)⚠️  Suppression des containers et volumes...$(NC)"
	cd docker && docker-compose down -v
	@echo "$(GREEN)✅ Nettoyage Docker terminé$(NC)"

docker-health: ## Vérifie la santé des services Docker
	@echo "$(GREEN)Vérification de la santé des services...$(NC)"
	cd docker && ./docker-health-check.sh

docker-stats: ## Affiche les statistiques des containers
	@echo "$(GREEN)Statistiques des containers:$(NC)"
	docker stats --no-stream

docker-deploy: ## Déploiement rapide avec script
	@echo "$(GREEN)Déploiement avec script...$(NC)"
	cd docker && ./docker-run.sh

logs: ## Affiche les logs de l'application
	tail -f logs/*.log

dev: ## Mode développement (rechargement auto)
	$(STREAMLIT) run app/streamlit_app.py --server.runOnSave=true

all: setup ollama-pull ingest run ## Installation complète et lancement

# Commandes utiles pour le développement
watch-logs: ## Surveille les logs en temps réel
	watch -n 2 'tail -n 50 logs/ingestion_*.log'

check: lint test ## Vérifie le code (lint + tests)

backup-db: ## Sauvegarde la base de données
	@echo "$(GREEN)Sauvegarde de la base...$(NC)"
	tar -czf backup_db_$(shell date +%Y%m%d_%H%M%S).tar.gz database/
	@echo "$(GREEN)✅ Sauvegarde créée$(NC)"

# Infos système
info: ## Affiche les informations système
	@echo "$(GREEN)Informations Système:$(NC)"
	@echo "Python: $$(python --version)"
	@echo "Pip: $$(pip --version)"
	@echo "Ollama: $$(ollama --version 2>/dev/null || echo 'Non installé')"
	@echo "Docker: $$(docker --version 2>/dev/null || echo 'Non installé')"
	@echo ""
	@echo "$(GREEN)Documents:$(NC)"
	@find data/documents -type f 2>/dev/null | wc -l || echo "0"
	@echo ""
	@echo "$(GREEN)Taille base ChromaDB:$(NC)"
	@du -sh database/chroma_db 2>/dev/null || echo "Non initialisée"