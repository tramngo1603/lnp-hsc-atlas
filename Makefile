# ============================================================================
# LNP Research Platform — Makefile
# ============================================================================
# Run `make help` to see all available commands
# Run `make setup` first time to install everything
# ============================================================================

.PHONY: help setup setup-uv setup-python setup-deps setup-env setup-claude-code \
        check-prereqs verify test lint typecheck format clean \
        run-dashboard run-api extract-papers backfill session

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(GREEN)LNP Research Platform$(NC)"
	@echo "=============================="
	@echo ""
	@echo "$(YELLOW)First time setup:$(NC)"
	@echo "  make setup          — Install everything (uv, Python, deps, .env)"
	@echo ""
	@echo "$(YELLOW)Daily workflow:$(NC)"
	@echo "  make session        — Start Claude Code in project directory"
	@echo "  make test           — Run all tests"
	@echo "  make lint           — Run ruff linter"
	@echo "  make typecheck      — Run mypy type checker"
	@echo "  make check          — Run lint + typecheck + test (do before commits)"
	@echo "  make run-dashboard  — Start Streamlit dashboard"
	@echo "  make run-api        — Start FastAPI server"
	@echo ""
	@echo "$(YELLOW)All commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# FIRST TIME SETUP (run once)
# ============================================================================

setup: check-prereqs setup-uv setup-python setup-deps setup-env setup-git ## Full first-time setup (run this first!)
	@echo ""
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env and add your API keys (see instructions below)"
	@echo "  2. Run: make session"
	@echo "  3. In Claude Code, type: Read CLAUDE.md. We're on Session 1."
	@echo ""
	@echo "$(YELLOW)API Keys needed in .env:$(NC)"
	@echo "  ANTHROPIC_API_KEY — Your Claude API key"
	@echo "  NCBI_API_KEY     — Your NCBI/PubMed API key (optional but recommended)"
	@echo ""

check-prereqs: ## Check system prerequisites
	@echo "$(YELLOW)Checking prerequisites...$(NC)"
	@command -v git >/dev/null 2>&1 || { echo "$(RED)❌ git not found. Install git first.$(NC)"; exit 1; }
	@echo "  ✅ git found"
	@command -v curl >/dev/null 2>&1 || { echo "$(RED)❌ curl not found. Install curl first.$(NC)"; exit 1; }
	@echo "  ✅ curl found"
	@echo "  ✅ Prerequisites OK"

setup-uv: ## Install uv (Python package manager)
	@echo "$(YELLOW)Installing uv...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		echo "  ✅ uv already installed ($$(uv --version))"; \
	else \
		echo "  Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "  ✅ uv installed"; \
		echo "  $(YELLOW)⚠️  Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)$(NC)"; \
	fi

setup-python: ## Install Python 3.12 via uv
	@echo "$(YELLOW)Setting up Python 3.12...$(NC)"
	@uv python install 3.12
	@uv python pin 3.12
	@echo "  ✅ Python 3.12 installed and pinned"

setup-deps: ## Install all project dependencies
	@echo "$(YELLOW)Installing project dependencies...$(NC)"
	@uv sync --extra dev
	@echo "  ✅ Dependencies installed"

setup-env: ## Create .env file from template
	@echo "$(YELLOW)Setting up .env file...$(NC)"
	@if [ -f .env ]; then \
		echo "  ⚠️  .env already exists, skipping (delete it to recreate)"; \
	else \
		cp .env.template .env; \
		echo "  ✅ .env created from template"; \
		echo "  $(YELLOW)⚠️  Edit .env and add your API keys!$(NC)"; \
	fi

setup-git: ## Initialize git if needed
	@echo "$(YELLOW)Setting up git...$(NC)"
	@if [ -d .git ]; then \
		echo "  ✅ Git already initialized"; \
	else \
		git init; \
		echo "  ✅ Git initialized"; \
	fi
	@if [ -f .gitignore ]; then \
		echo "  ✅ .gitignore exists"; \
	else \
		echo "  Creating .gitignore..."; \
	fi

setup-claude-code: ## Install Claude Code CLI (requires Node.js 18+)
	@echo "$(YELLOW)Installing Claude Code...$(NC)"
	@if command -v claude >/dev/null 2>&1; then \
		echo "  ✅ Claude Code already installed"; \
	else \
		echo "  Installing Claude Code via npm..."; \
		npm install -g @anthropic-ai/claude-code; \
		echo "  ✅ Claude Code installed"; \
	fi

# ============================================================================
# DAILY WORKFLOW
# ============================================================================

session: ## Start Claude Code session in this project
	@echo "$(GREEN)Starting Claude Code session...$(NC)"
	@echo "Tip: Start with 'Read CLAUDE.md' then reference docs/SESSION_PLAN.md"
	@claude

test: ## Run all tests
	@echo "$(YELLOW)Running tests...$(NC)"
	@uv run pytest -v

test-cov: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	@uv run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "  HTML report: htmlcov/index.html"

test-fast: ## Run tests excluding slow integration tests
	@uv run pytest -v -m "not integration"

lint: ## Run ruff linter
	@echo "$(YELLOW)Running ruff...$(NC)"
	@uv run ruff check .

lint-fix: ## Run ruff with auto-fix
	@uv run ruff check . --fix

typecheck: ## Run mypy type checker
	@echo "$(YELLOW)Running mypy...$(NC)"
	@uv run mypy .

format: ## Format code with ruff
	@uv run ruff format .

check: lint typecheck test ## Run all checks (lint + typecheck + test)
	@echo "$(GREEN)✅ All checks passed!$(NC)"

# ============================================================================
# RUN SERVICES
# ============================================================================

run-dashboard: ## Start Streamlit dashboard
	@echo "$(GREEN)Starting Streamlit dashboard...$(NC)"
	@uv run streamlit run dashboard/app.py

run-api: ## Start FastAPI server
	@echo "$(GREEN)Starting FastAPI server...$(NC)"
	@uv run uvicorn api.main:app --reload --port 8000

# ============================================================================
# DATA PIPELINE
# ============================================================================

extract-papers: ## Run paper extraction on new papers
	@echo "$(YELLOW)Running paper extraction...$(NC)"
	@uv run python -m pubmed_agent.cli extract

backfill: ## Run full backfill of historical papers
	@echo "$(YELLOW)Starting backfill...$(NC)"
	@uv run python -m pubmed_agent.cli backfill

poll: ## Check PubMed for new papers
	@echo "$(YELLOW)Polling PubMed for new papers...$(NC)"
	@uv run python -m pubmed_agent.cli poll

# ============================================================================
# UTILITIES
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning...$(NC)"
	@rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "  ✅ Cleaned"

reset-db: ## Reset the SQLite database (WARNING: deletes all data)
	@echo "$(RED)⚠️  This will delete all extracted data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		rm -f data/lnp_research.db; \
		echo "  ✅ Database reset"; \
	else \
		echo "  Cancelled"; \
	fi

verify: ## Verify the full setup is working
	@echo "$(YELLOW)Verifying setup...$(NC)"
	@echo -n "  uv: " && uv --version
	@echo -n "  Python: " && uv run python --version
	@echo -n "  ruff: " && uv run ruff --version
	@echo "  Checking .env..."
	@if [ -f .env ]; then \
		if grep -q "your-.*-here" .env; then \
			echo "  $(YELLOW)⚠️  .env has placeholder values — update your API keys$(NC)"; \
		else \
			echo "  ✅ .env configured"; \
		fi \
	else \
		echo "  $(RED)❌ .env missing — run: make setup-env$(NC)"; \
	fi
	@echo "  Checking Claude Code..."
	@if command -v claude >/dev/null 2>&1; then \
		echo "  ✅ Claude Code installed"; \
	else \
		echo "  $(YELLOW)⚠️  Claude Code not found — run: make setup-claude-code$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)Verification complete!$(NC)"