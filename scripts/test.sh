#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_background.cjs
node --check extension/background.js
node --check extension/management.js
for task_script in scripts/*.sh alternative/*.sh; do bash -n "$task_script"; done
python3 scripts/build.py
