#!/bin/bash

echo ""

# Show full structure, only exclude build artifacts and dependencies
tree -I 'node_modules|.git|dist|build|.next|coverage|.turbo|env|__pycache__|*.pyc|.venv|venv|lib|lib64|include|share|bin|pyvenv.cfg' --dirsfirst -a > repo_structure.md

echo "📂 Repository Structure saved to file: repo_structure.md"

echo ""
# Alternative if tree not installed:
# find . -type d \
#   -not -path '*/node_modules/*' \
#   -not -path '*/.git/*' \
#   -not -path '*/dist/*' \
#   -not -path '*/build/*' \
#   -not -path '*/__pycache__/*' \
#   -not -path '*/.venv/*' \
#   -not -path '*/lib/*' \
#   | sort