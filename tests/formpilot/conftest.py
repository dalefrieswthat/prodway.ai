"""FormPilot-specific conftest."""
import os
import sys
import importlib.util
from pathlib import Path

_formpilot_path = Path(__file__).resolve().parent.parent.parent / "apps" / "formpilot-api" / "main.py"
spec = importlib.util.spec_from_file_location("formpilot_main", str(_formpilot_path))
formpilot_main = importlib.util.module_from_spec(spec)
sys.modules["formpilot_main"] = formpilot_main

_formpilot_dir = str(_formpilot_path.parent)
if _formpilot_dir not in sys.path:
    sys.path.insert(0, _formpilot_dir)

spec.loader.exec_module(formpilot_main)
