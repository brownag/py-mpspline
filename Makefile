.PHONY: help install test lint lint-fix format docs clean build all
.DEFAULT_GOAL := help

all: clean install lint-fix test build ## Run full build pipeline (clean, install, lint-fix, test, build)

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  %%-15s %%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install the package in development mode
	pip install -e ".[dev,spc,docs]"

install-prod: ## Install only production dependencies
	pip install -e .

test: ## Run the test suite
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=mpspline --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	ruff check src/ tests/
	mypy src/mpspline --ignore-missing-imports

lint-fix: ## Run linting checks and auto-fix issues
	ruff check --fix src/ tests/
	ruff format src/ tests/
	mypy src/mpspline --ignore-missing-imports

format: ## Format code
	ruff format src/ tests/

format-check: ## Check code formatting without making changes
	ruff format --check src/ tests/

security: ## Run security checks
	bandit -r src/
	safety check

docs: ## Build documentation (Sphinx)
	pip install -e ".[docs]"
	cd docs && make html

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

examples: ## Run basic functionality check
	@echo "Testing basic functionality..."
	@python -c "import mpspline; print('Package imports successfully')"
	@python -c "from mpspline import mpspline; res = mpspline({'horizons': [{'hzname': 'A', 'upper': 0, 'lower': 10, 'sand': 50}]}); print('Basic calc success')"
	@echo "Basic checks completed"
