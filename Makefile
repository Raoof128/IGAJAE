.PHONY: install run-backend run-frontend test lint format clean help

help:
	@echo "Available commands:"
	@echo "  install       Install backend dependencies"
	@echo "  run-backend   Run the FastAPI backend"
	@echo "  run-frontend  Run the React frontend"
	@echo "  test          Run backend tests"
	@echo "  lint          Run linting (flake8, mypy)"
	@echo "  format        Format code (black)"
	@echo "  clean         Remove build artifacts and cache"

install:
	pip install -e .[dev]
	cd frontend && npm install

run-backend:
	python3 -m backend.main

run-frontend:
	cd frontend && npm run dev

test:
	pytest

lint:
	flake8 backend connectors tests
	mypy backend connectors tests

format:
	black backend connectors tests

clean:
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
