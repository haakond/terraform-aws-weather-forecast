# Weather Forecast App - Makefile

.PHONY: help init plan apply destroy test clean install-deps setup-venv

# Virtual environment settings
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest

# Default target
help:
	@echo "Available targets:"
	@echo "  init         - Initialize Terraform"
	@echo "  plan         - Run Terraform plan"
	@echo "  apply        - Apply Terraform configuration"
	@echo "  destroy      - Destroy Terraform resources"
	@echo "  test         - Run all tests"
	@echo "  test-tf      - Run Terraform tests"
	@echo "  test-python  - Run Python tests"
	@echo "  setup-venv   - Set up Python virtual environment"
	@echo "  clean        - Clean temporary files"
	@echo "  install-deps - Install Python dependencies"
	@echo "  format       - Format code"
	@echo "  lint         - Run linting"

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
test: setup-venv install-deps test-python test-tf

test-tf:
	@echo "Running Terraform tests..."
	cd tests/terraform && terraform test

test-python: setup-venv install-deps
	@echo "Running Python tests in virtual environment..."
	PYTHONPATH=. $(PYTEST) tests/ -v --cov=src

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

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf $(VENV_DIR)