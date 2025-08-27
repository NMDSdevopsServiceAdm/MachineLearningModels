#!/usr/bin/env bash

echo "Running pytest..."
pipenv run pytest -vrrP --cov || exit 1

echo "Running mypy..."
pipenv run mypy --follow-untyped-imports utilities || exit 1

echo "Running black..."
pipenv run black . --check || exit 1

echo "Running pydoclint..."
pipenv run pydoclint --style=google --quiet . || exit 1

echo "Running pip-audit..."
pipenv run pip-audit || exit 1

echo "Running bandit..."
pipenv run bandit -c bandit.yaml -r utilities || exit 1

echo "Running terraform linting check..."
terraform fmt -recursive || exit 1

echo "Linting ok, running validation..."
cd terraform && terraform validate || exit 1

echo "All pre-checks passed successfully!"