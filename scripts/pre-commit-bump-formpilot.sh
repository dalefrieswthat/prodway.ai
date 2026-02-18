#!/usr/bin/env bash
# Bump FormPilot manifest version when apps/formpilot/ is being committed; stage the manifest.
set -e
cd "$(git rev-parse --show-toplevel)"
python3 scripts/bump-formpilot-version.py
git add apps/formpilot/manifest.json 2>/dev/null || true
