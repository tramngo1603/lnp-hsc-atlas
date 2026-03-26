# HSC-LNP Atlas — Makefile
# Run `make update` to rebuild everything from annotations → explorer

.PHONY: help validate build train figures extract patch update test lint check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Pipeline steps (run in order)
validate: ## Validate annotation JSONs
	uv run python scripts/validate_annotations.py

build: validate ## Build feature matrix from annotations
	uv run python scripts/build_feature_matrix.py

train: build ## Train LightGBM + compute SHAP
	uv run python scripts/train_model.py

figures: train ## Generate publication figures
	uv run python scripts/generate_figures.py

extract: train ## Extract data for interactive explorer
	uv run python scripts/extract_explorer_data.py

patch: extract ## Patch explorer JSX with extracted data
	uv run python scripts/patch_explorer.py

update: validate build train figures extract patch ## Run full pipeline
	@echo ""
	@echo "✓ Atlas updated. Review changes, then:"
	@echo "  git add -A && git commit -m 'Update atlas' && git push"

# Development
test: ## Run all tests
	uv run python -m pytest tests/ -q

lint: ## Run ruff + mypy
	uv run ruff check src/ scripts/
	uv run mypy src/ --ignore-missing-imports

check: lint test ## Run all checks

clean: ## Remove generated artifacts
	rm -f data/features/hsc_features.parquet data/features/hsc_features.csv
	rm -f data/models/lgbm_model.pkl data/models/shap_values.csv
	rm -f data/models/lopocv_results.json
	rm -f explorer_data.json
	rm -rf figures/
