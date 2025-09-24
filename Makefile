.PHONY: help install install-dev format lint type-check test clean run setup-hooks

help:  ## Mostra esta mensagem de ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Instala dependências de produção
	pip install -e .

install-dev:  ## Instala dependências de desenvolvimento
	pip install -e ".[dev]"

setup-hooks:  ## Configura pre-commit hooks
	pre-commit install

format:  ## Formata o código com black e isort
	black .
	isort .

lint:  ## Executa linting com flake8
	flake8 .

type-check:  ## Executa verificação de tipos com mypy
	mypy .

check: format lint type-check  ## Executa todas as verificações

test:  ## Executa testes
	python -m pytest tests/

clean:  ## Limpa arquivos temporários
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

run:  ## Executa o sistema principal
	python main.py

run-test:  ## Executa teste do sistema
	python main.py --test

run-channels:  ## Lista canais autorizados
	python main.py --list-channels
