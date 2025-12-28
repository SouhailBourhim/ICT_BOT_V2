.PHONY: help install setup run ingest clean test lint format check docker-up docker-down docs migrate validate dev-setup dev-up dev-down dev-logs dev-shell dev-test dev-format dev-lint dev-tools

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
STREAMLIT := streamlit
OLLAMA_MODEL := qwen2.5:3b

# Couleurs pour l'affichage
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@echo "$(GREEN)🎓 Assistant RAG INPT - Commandes disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)📚 Documentation disponible:$(NC)"
	@echo "  $(CYAN)README.md$(NC)           - Documentation principale"
	@echo "  $(CYAN)INSTALLATION.md$(NC)     - Guide d'installation détaillé"
	@echo "  $(CYAN)DOCKER_GUIDE.md$(NC)     - Guide Docker complet"
	@echo "  $(CYAN)ARCHITECTURE.md$(NC)     - Documentation technique"
	@echo "  $(CYAN)API_DOCUMENTATION.md$(NC) - Documentation API"
	@echo "  $(CYAN)TROUBLESHOOTING.md$(NC)  - Guide de dépannage"
	@echo "  $(CYAN)CHANGELOG.md$(NC)        - Historique des versions"
	@echo ""

# === INSTALLATION ET CONFIGURATION ===

install: ## Installe les dépendances Python
	@echo "$(GREEN)📦 Installation des dépendances...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(YELLOW)📥 Téléchargement des modèles spaCy...$(NC)"
	$(PYTHON) -m spacy download fr_core_news_md || echo "$(YELLOW)⚠️ Modèle spaCy optionnel non installé$(NC)"
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

setup: install ## Setup complet du projet (install + init)
	@echo "$(GREEN)🚀 Initialisation du projet...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)📝 Fichier .env créé depuis .env.example$(NC)"; fi
	$(PYTHON) -c "from src.config.settings import setup_directories; setup_directories()"
	@echo "$(GREEN)✅ Projet initialisé$(NC)"
	@echo ""
	@echo "$(PURPLE)📋 Prochaines étapes:$(NC)"
	@echo "  1. $(CYAN)Éditer le fichier .env selon vos besoins$(NC)"
	@echo "  2. $(CYAN)Installer Ollama: curl -fsSL https://ollama.ai/install.sh | sh$(NC)"
	@echo "  3. $(CYAN)Télécharger le modèle: make ollama-pull$(NC)"
	@echo "  4. $(CYAN)Ingérer des documents: make ingest$(NC)"
	@echo "  5. $(CYAN)Lancer l'application: make run$(NC)"

venv: ## Crée un environnement virtuel
	@echo "$(GREEN)🐍 Création de l'environnement virtuel...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ Environnement créé$(NC)"
	@echo "$(YELLOW)💡 Activez-le avec: source $(VENV)/bin/activate$(NC)"

validate: ## Valide la configuration du système
	@echo "$(GREEN)🔍 Validation de la configuration...$(NC)"
	@$(PYTHON) -c "from src.config.settings import validate_environment_configuration, log_environment_validation; log_environment_validation()"

# === OLLAMA ET MODÈLES ===

ollama-start: ## Démarre Ollama en arrière-plan
	@echo "$(GREEN)🚀 Démarrage d'Ollama...$(NC)"
	@if pgrep -f "ollama serve" > /dev/null; then \
		echo "$(YELLOW)⚠️ Ollama est déjà en cours d'exécution$(NC)"; \
	else \
		ollama serve & \
		echo "$(GREEN)✅ Ollama lancé en arrière-plan$(NC)"; \
	fi

ollama-pull: ## Télécharge le modèle LLM
	@echo "$(GREEN)📥 Téléchargement du modèle $(OLLAMA_MODEL)...$(NC)"
	@echo "$(YELLOW)⏳ Cela peut prendre plusieurs minutes...$(NC)"
	ollama pull $(OLLAMA_MODEL)
	@echo "$(GREEN)✅ Modèle $(OLLAMA_MODEL) téléchargé$(NC)"

ollama-models: ## Liste les modèles Ollama disponibles
	@echo "$(GREEN)📋 Modèles Ollama disponibles:$(NC)"
	@ollama list || echo "$(RED)❌ Ollama non accessible$(NC)"

ollama-status: ## Vérifie le statut d'Ollama
	@echo "$(GREEN)🔍 Statut d'Ollama:$(NC)"
	@if pgrep -f "ollama serve" > /dev/null; then \
		echo "$(GREEN)✅ Service Ollama actif$(NC)"; \
		curl -s http://localhost:11434/api/tags > /dev/null && echo "$(GREEN)✅ API Ollama accessible$(NC)" || echo "$(RED)❌ API Ollama non accessible$(NC)"; \
	else \
		echo "$(RED)❌ Service Ollama non actif$(NC)"; \
	fi

# === APPLICATION ===

run: ## Lance l'application Streamlit
	@echo "$(GREEN)🚀 Lancement de l'application...$(NC)"
	@echo "$(BLUE)🌐 Application disponible sur: http://localhost:8501$(NC)"
	$(STREAMLIT) run app/chat.py

dev: ## Mode développement avec rechargement automatique
	@echo "$(GREEN)🔧 Mode développement (rechargement auto)...$(NC)"
	$(STREAMLIT) run app/chat.py --server.runOnSave=true

# === GESTION DES DOCUMENTS ===

ingest: ## Ingère les documents du dossier data/documents
	@echo "$(GREEN)📚 Ingestion des documents...$(NC)"
	@if [ ! -d "data/documents" ] || [ -z "$$(ls -A data/documents 2>/dev/null)" ]; then \
		echo "$(YELLOW)⚠️ Aucun document trouvé dans data/documents/$(NC)"; \
		echo "$(BLUE)💡 Ajoutez des fichiers PDF, TXT, MD ou DOCX dans ce dossier$(NC)"; \
	else \
		$(PYTHON) scripts/ingest_documents.py data/documents --recursive; \
		echo "$(GREEN)✅ Documents ingérés$(NC)"; \
	fi

ingest-file: ## Ingère un fichier unique (usage: make ingest-file FILE=path/to/file)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)❌ Usage: make ingest-file FILE=path/to/file$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)📄 Ingestion de $(FILE)...$(NC)"
	$(PYTHON) scripts/ingest_documents.py "$(FILE)"

migrate: ## Migre les chunks existants vers le nouveau format
	@echo "$(GREEN)🔄 Migration des chunks vers le format enrichi...$(NC)"
	$(PYTHON) scripts/ingest_documents.py --migrate
	@echo "$(GREEN)✅ Migration terminée$(NC)"

stats: ## Affiche les statistiques de la base de données
	@echo "$(GREEN)📊 Statistiques de la base de données:$(NC)"
	$(PYTHON) scripts/ingest_documents.py --stats

reset-db: ## Réinitialise la base de données (⚠️ DESTRUCTIF)
	@echo "$(RED)⚠️ ATTENTION: Cette action va supprimer toutes les données!$(NC)"
	@read -p "Confirmer la suppression (tapez 'oui' pour confirmer): " confirm && \
	if [ "$$confirm" = "oui" ]; then \
		$(PYTHON) scripts/ingest_documents.py --reset; \
		echo "$(GREEN)✅ Base de données réinitialisée$(NC)"; \
	else \
		echo "$(YELLOW)❌ Opération annulée$(NC)"; \
	fi

# === TESTS ET QUALITÉ ===

test: ## Lance les tests unitaires
	@echo "$(GREEN)🧪 Lancement des tests...$(NC)"
	pytest tests/ -v --tb=short

test-cov: ## Lance les tests avec rapport de couverture
	@echo "$(GREEN)📊 Tests avec couverture de code...$(NC)"
	pytest tests/ --cov=src --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(BLUE)📋 Rapport HTML disponible dans: htmlcov/index.html$(NC)"

test-docker: ## Lance les tests Docker spécifiques
	@echo "$(GREEN)🐳 Tests d'intégration Docker...$(NC)"
	pytest tests/test_docker_*.py -v

lint: ## Vérifie le code avec ruff et flake8
	@echo "$(GREEN)🔍 Vérification du code...$(NC)"
	@echo "$(BLUE)📝 Ruff...$(NC)"
	ruff check src/ app/ tests/ || true
	@echo "$(BLUE)📝 Flake8...$(NC)"
	flake8 src/ app/ tests/ --max-line-length=100 --extend-ignore=E203,W503 || true

format: ## Formate le code avec black
	@echo "$(GREEN)✨ Formatage du code...$(NC)"
	black src/ app/ tests/ --line-length=100
	@echo "$(GREEN)✅ Code formaté$(NC)"

check: lint test ## Vérifie le code et lance les tests
	@echo "$(GREEN)✅ Vérification complète terminée$(NC)"

# === DOCKER ===

docker-build: ## Construit l'image Docker
	@echo "$(GREEN)🔨 Construction de l'image Docker...$(NC)"
	cd docker && docker-compose build --no-cache

docker-up: ## Lance les services Docker
	@echo "$(GREEN)🐳 Démarrage des services Docker...$(NC)"
	cd docker && docker-compose up -d
	@echo "$(GREEN)✅ Services lancés$(NC)"
	@echo "$(BLUE)🌐 Application: http://localhost:8501$(NC)"
	@echo "$(BLUE)🤖 Ollama API: http://localhost:11434$(NC)"

docker-down: ## Arrête les services Docker
	@echo "$(GREEN)🛑 Arrêt des services Docker...$(NC)"
	cd docker && docker-compose down

docker-logs: ## Affiche les logs Docker en temps réel
	@echo "$(GREEN)📋 Logs Docker (Ctrl+C pour quitter):$(NC)"
	cd docker && docker-compose logs -f

docker-restart: docker-down docker-up ## Redémarre les services Docker

docker-prod: ## Lance en mode production
	@echo "$(GREEN)🚀 Démarrage en mode production...$(NC)"
	cd docker && docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Services production lancés$(NC)"

docker-ingest: ## Ingère des documents via Docker
	@echo "$(GREEN)📚 Ingestion via Docker...$(NC)"
	cd docker && docker-compose exec rag-app python scripts/ingest_documents.py data/documents --recursive

docker-shell: ## Ouvre un shell dans le conteneur
	@echo "$(GREEN)🐚 Ouverture du shell dans le conteneur...$(NC)"
	cd docker && docker-compose exec rag-app /bin/bash

docker-clean: ## Nettoie les conteneurs et volumes Docker
	@echo "$(YELLOW)🧹 Nettoyage Docker (containers et volumes)...$(NC)"
	@read -p "Confirmer la suppression des volumes (tapez 'oui'): " confirm && \
	if [ "$$confirm" = "oui" ]; then \
		cd docker && docker-compose down -v; \
		docker system prune -f; \
		echo "$(GREEN)✅ Nettoyage Docker terminé$(NC)"; \
	else \
		echo "$(YELLOW)❌ Nettoyage annulé$(NC)"; \
	fi

docker-health: ## Vérifie la santé des services Docker
	@echo "$(GREEN)🏥 Vérification de la santé des services...$(NC)"
	cd docker && ./docker-health-check.sh

docker-stats: ## Affiche les statistiques des conteneurs
	@echo "$(GREEN)📊 Statistiques des conteneurs:$(NC)"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# === DÉVELOPPEMENT DOCKER ===

dev-setup: ## 🛠️  Configure l'environnement de développement
	@echo "$(BLUE)🛠️  Configuration de l'environnement de développement...$(NC)"
	@cd docker && ./docker-dev-setup.sh
	@echo "$(GREEN)✅ Environnement de développement prêt!$(NC)"
	@echo "$(YELLOW)💡 Utilisez 'make dev-up' pour démarrer$(NC)"

dev-up: ## 🚀 Lance le stack de développement avec hot reload
	@echo "$(BLUE)🚀 Démarrage du stack de développement...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Stack de développement démarré!$(NC)"
	@echo "$(CYAN)📱 App: http://localhost:8501$(NC)"
	@echo "$(CYAN)🐛 Debug: localhost:5678$(NC)"

dev-down: ## 🛑 Arrête le stack de développement
	@echo "$(BLUE)🛑 Arrêt du stack de développement...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Stack de développement arrêté$(NC)"

dev-logs: ## 📋 Affiche les logs de développement
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

dev-shell: ## 🐚 Ouvre un shell dans le conteneur de développement
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec rag-app bash

dev-test: ## 🧪 Lance les tests dans l'environnement de développement
	@echo "$(BLUE)🧪 Lancement des tests en développement...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools exec dev-tools pytest -v
	@echo "$(GREEN)✅ Tests terminés$(NC)"

dev-format: ## 🎨 Formate le code avec Black
	@echo "$(BLUE)🎨 Formatage du code...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools exec dev-tools black .
	@echo "$(GREEN)✅ Code formaté$(NC)"

dev-lint: ## 🔍 Analyse le code avec flake8
	@echo "$(BLUE)🔍 Analyse du code...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools exec dev-tools flake8 .
	@echo "$(GREEN)✅ Analyse terminée$(NC)"

dev-tools: ## 🔧 Lance le développement avec tous les outils
	@echo "$(BLUE)🔧 Démarrage avec tous les outils de développement...$(NC)"
	@cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools --profile db-admin up -d
	@echo "$(GREEN)✅ Environnement de développement complet démarré!$(NC)"
	@echo "$(CYAN)📱 App: http://localhost:8501$(NC)"
	@echo "$(CYAN)🗄️  Admin DB: http://localhost:8080$(NC)"
	@echo "$(CYAN)🐛 Debug: localhost:5678$(NC)"

# === MAINTENANCE ET MONITORING ===

logs: ## Affiche les logs de l'application
	@echo "$(GREEN)📋 Logs de l'application:$(NC)"
	@if [ -d "logs" ] && [ -n "$$(ls logs/*.log 2>/dev/null)" ]; then \
		tail -f logs/*.log; \
	else \
		echo "$(YELLOW)⚠️ Aucun fichier de log trouvé dans logs/$(NC)"; \
	fi

watch-logs: ## Surveille les logs en temps réel
	@echo "$(GREEN)👀 Surveillance des logs (Ctrl+C pour quitter):$(NC)"
	watch -n 2 'find logs/ -name "*.log" -exec tail -n 10 {} \; 2>/dev/null || echo "Aucun log trouvé"'

backup-db: ## Sauvegarde la base de données
	@echo "$(GREEN)💾 Sauvegarde de la base de données...$(NC)"
	@BACKUP_NAME="backup_db_$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	tar -czf "$$BACKUP_NAME" database/ data/conversations/ 2>/dev/null || true; \
	echo "$(GREEN)✅ Sauvegarde créée: $$BACKUP_NAME$(NC)"

clean: ## Nettoie les fichiers temporaires
	@echo "$(GREEN)🧹 Nettoyage des fichiers temporaires...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage .coverage.* 2>/dev/null || true
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

# === INFORMATIONS SYSTÈME ===

info: ## Affiche les informations système
	@echo "$(GREEN)ℹ️  Informations Système:$(NC)"
	@echo "$(BLUE)🐍 Python:$(NC) $$(python3 --version 2>/dev/null || echo 'Non installé')"
	@echo "$(BLUE)📦 Pip:$(NC) $$(pip3 --version 2>/dev/null | cut -d' ' -f2 || echo 'Non installé')"
	@echo "$(BLUE)🤖 Ollama:$(NC) $$(ollama --version 2>/dev/null || echo 'Non installé')"
	@echo "$(BLUE)🐳 Docker:$(NC) $$(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo 'Non installé')"
	@echo "$(BLUE)🎯 Streamlit:$(NC) $$(streamlit --version 2>/dev/null | cut -d' ' -f2 || echo 'Non installé')"
	@echo ""
	@echo "$(GREEN)📊 Statistiques du projet:$(NC)"
	@echo "$(BLUE)📄 Documents:$(NC) $$(find data/documents -type f 2>/dev/null | wc -l || echo '0') fichiers"
	@echo "$(BLUE)💬 Conversations:$(NC) $$(find data/conversations -name "*.json" 2>/dev/null | wc -l || echo '0') conversations"
	@echo "$(BLUE)💾 Base ChromaDB:$(NC) $$(du -sh database/chroma_db 2>/dev/null | cut -f1 || echo 'Non initialisée')"
	@echo "$(BLUE)📋 Logs:$(NC) $$(find logs -name "*.log" 2>/dev/null | wc -l || echo '0') fichiers"

status: ## Affiche le statut complet du système
	@echo "$(GREEN)🔍 Statut du système RAG INPT:$(NC)"
	@echo ""
	@make --no-print-directory ollama-status
	@echo ""
	@echo "$(GREEN)📊 Base de données:$(NC)"
	@if [ -d "database/chroma_db" ]; then \
		echo "$(GREEN)✅ ChromaDB initialisée$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ ChromaDB non initialisée$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)📁 Répertoires:$(NC)"
	@for dir in data/documents data/conversations database logs; do \
		if [ -d "$$dir" ]; then \
			echo "$(GREEN)✅ $$dir$(NC)"; \
		else \
			echo "$(YELLOW)⚠️ $$dir manquant$(NC)"; \
		fi; \
	done

# === RACCOURCIS UTILES ===

all: setup ollama-pull ingest run ## Installation complète et lancement

quick-start: setup ollama-start ollama-pull ## Démarrage rapide (sans ingestion)
	@echo "$(GREEN)🎉 Système prêt! Ajoutez des documents avec 'make ingest' puis lancez avec 'make run'$(NC)"

dev-setup: setup ollama-start ollama-pull ingest ## Configuration complète pour développement
	@echo "$(GREEN)🎉 Environnement de développement prêt!$(NC)"
	@echo "$(BLUE)💡 Lancez l'application avec: make run$(NC)"

# === DOCUMENTATION ===

docs: ## Ouvre la documentation dans le navigateur
	@echo "$(GREEN)📚 Ouverture de la documentation...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open README.md; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open README.md; \
	else \
		echo "$(BLUE)📖 Consultez README.md pour la documentation complète$(NC)"; \
	fi

# === DIAGNOSTIC ===

diagnose: ## Lance un diagnostic complet du système
	@echo "$(GREEN)🔍 Diagnostic complet du système...$(NC)"
	@echo ""
	@make --no-print-directory info
	@echo ""
	@make --no-print-directory status
	@echo ""
	@echo "$(GREEN)🧪 Test des composants:$(NC)"
	@$(PYTHON) -c "
try:
    from src.config.settings import settings
    print('$(GREEN)✅ Configuration chargée$(NC)')
    print(f'$(BLUE)📋 Projet: {settings.PROJECT_NAME}$(NC)')
    print(f'$(BLUE)🔢 Version: {settings.VERSION}$(NC)')
except Exception as e:
    print(f'$(RED)❌ Erreur configuration: {e}$(NC)')

try:
    import streamlit, chromadb, sentence_transformers
    print('$(GREEN)✅ Modules principaux disponibles$(NC)')
except ImportError as e:
    print(f'$(RED)❌ Module manquant: {e}$(NC)')
"
	@echo ""
	@echo "$(GREEN)✅ Diagnostic terminé$(NC)"