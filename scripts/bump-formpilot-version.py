#!/usr/bin/env python3
"""Bump FormPilot manifest.json patch version. Only bumps if not already ahead of HEAD."""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "apps" / "formpilot" / "manifest.json"


def get_version_from_manifest(path):
    data = json.loads(path.read_text())
    return data.get("version")


def get_head_version():
    try:
        out = subprocess.run(
            ["git", "show", "HEAD:apps/formpilot/manifest.json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return None
        data = json.loads(out.stdout)
        return data.get("version")
    except Exception:
        return None


def parse_semver(v):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        raise ValueError("Invalid semver")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def main():
    if not MANIFEST_PATH.exists():
        return 0
    current = get_version_from_manifest(MANIFEST_PATH)
    if not current:
        return 0
    head_ver = get_head_version()
    if head_ver:
        try:
            c = parse_semver(current)
            h = parse_semver(head_ver)
            if c > h:
                return 0
        except ValueError:
            pass
    try:
        major, minor, patch = parse_semver(current)
    except ValueError:
        return 0
    new_version = f"{major}.{minor}.{patch + 1}"
    data = json.loads(MANIFEST_PATH.read_text())
    data["version"] = new_version
    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"FormPilot version {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
