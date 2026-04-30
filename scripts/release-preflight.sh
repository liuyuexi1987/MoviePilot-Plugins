#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/2] repo hygiene"
bash scripts/repo-hygiene.sh

echo "[2/2] pre-release check"
bash scripts/pre-release-check.sh
