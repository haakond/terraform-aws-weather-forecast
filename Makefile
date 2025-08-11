# Weather Forecast App - Makefile

.PHONY: help init plan apply destroy test clean install-deps setup-venv

# Virtual environment settings
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest

# Frontend virtual environment settings
FRONTEND_VENV_DIR = .frontend-venv
FRONTEND_NODE_MODULES = $(FRONTEND_VENV_DIR)/node_modules

# Default target
help:
	@echo "Available targets:"
	@echo "  init              - Initialize Terraform"
	@echo "  plan              - Run Terraform plan"
	@echo "  apply             - Apply Terraform configuration"
	@echo "  destroy           - Destroy Terraform resources"
	@echo "  test              - Run all tests (Python, Frontend, Terraform)"
	@echo "  test-tf           - Run Terraform tests"
	@echo "  test-python       - Run Python tests"
	@echo "  test-frontend     - Run frontend tests"
	@echo "  build-frontend    - Build React frontend application"
	@echo "  setup-venv        - Set up Python virtual environment"
	@echo "  setup-frontend-venv - Set up frontend virtual environment"
	@echo "  clean             - Clean temporary files"
	@echo "  clean-frontend    - Clean frontend virtual environment only"
	@echo "  install-deps      - Install Python dependencies"
	@echo "  format            - Format code"
	@echo "  lint              - Run linting"

# Terraform targets
init:
	terraform init

plan:
	terraform plan -var-file="environments/dev.tfvars"

apply:
	terraform apply -var-file="environments/dev.tfvars"

destroy:
	terraform destroy -var-file="environments/dev.tfvars"

# Virtual environment setup
setup-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	fi
	@echo "Virtual environment ready at $(VENV_DIR)"

# Testing targets
test: setup-venv install-deps test-python test-frontend test-tf

test-tf:
	@echo "Running Terraform tests..."
	cd tests/terraform && terraform test

test-python: setup-venv install-deps
	@echo "Running Python tests in virtual environment..."
	PYTHONPATH=. $(PYTEST) tests/ -v --cov=src

test-frontend: setup-frontend-venv
	@echo "Running frontend tests in virtual environment..."
	cd $(FRONTEND_VENV_DIR) && npm test -- --coverage --watchAll=false --verbose

# Development targets
install-deps: setup-venv
	@echo "Installing Python dependencies in virtual environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

format: setup-venv install-deps
	$(VENV_DIR)/bin/black src/ tests/
	terraform fmt -recursive

lint: setup-venv install-deps
	$(VENV_DIR)/bin/flake8 src/ tests/
	$(VENV_DIR)/bin/mypy src/

# Frontend targets
setup-frontend-venv:
	@echo "Setting up frontend virtual environment..."
	@if [ ! -d "$(FRONTEND_VENV_DIR)" ]; then \
		echo "Creating frontend virtual environment..."; \
		mkdir -p $(FRONTEND_VENV_DIR); \
		echo "Copying frontend source files..."; \
		cp -r frontend/src $(FRONTEND_VENV_DIR)/; \
		cp -r frontend/public $(FRONTEND_VENV_DIR)/; \
		cp frontend/package.json $(FRONTEND_VENV_DIR)/; \
		echo "Installing dependencies in virtual environment..."; \
		cd $(FRONTEND_VENV_DIR) && npm install --silent; \
	else \
		echo "Frontend virtual environment already exists"; \
		echo "Syncing frontend code to virtual environment..."; \
		cp -r frontend/src $(FRONTEND_VENV_DIR)/; \
		cp -r frontend/public $(FRONTEND_VENV_DIR)/; \
		cp frontend/package.json $(FRONTEND_VENV_DIR)/; \
		echo "Updating dependencies in virtual environment..."; \
		cd $(FRONTEND_VENV_DIR) && npm install --silent; \
	fi
	@echo "Frontend virtual environment ready at $(FRONTEND_VENV_DIR)"

setup-frontend-env: setup-frontend-venv
	@echo "Frontend environment setup completed (using virtual environment)"

build-frontend: setup-frontend-venv
	@echo "Building frontend application in virtual environment..."
	cd $(FRONTEND_VENV_DIR) && npm run build
	@echo "Frontend build completed"

# Cleanup
clean:
	@echo "Cleaning Python artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf $(VENV_DIR)
	@echo "Cleaning frontend artifacts..."
	rm -rf frontend/build/
	rm -rf frontend/node_modules/
	rm -rf frontend/coverage/
	rm -rf $(FRONTEND_VENV_DIR)
	@echo "Cleanup completed"

clean-frontend:
	@echo "Cleaning frontend virtual environment..."
	rm -rf $(FRONTEND_VENV_DIR)
	@echo "Frontend virtual environment cleaned"