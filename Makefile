# Weather Forecast App - Makefile

.PHONY: help init plan apply destroy test clean install-deps

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

# Testing targets
test: test-python test-tf

test-tf:
	terraform test

test-python:
	pytest tests/ -v --cov=src

# Development targets
install-deps:
	pip install -r requirements-dev.txt

format:
	black src/ tests/
	terraform fmt -recursive

lint:
	flake8 src/ tests/
	mypy src/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage