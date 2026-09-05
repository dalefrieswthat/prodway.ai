"""SowFlow-specific conftest."""
import os
import sys
import importlib.util
import tempfile
from pathlib import Path

_test_data = tempfile.mkdtemp(prefix="sowflow_test_")
os.environ.setdefault("DATA_DIR", _test_data)
os.environ.setdefault("SLACK_CLIENT_ID", "test-client-id")
os.environ.setdefault("SLACK_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test-signing-secret")
os.environ.setdefault("STRIPE_PRICE_BASE_ID", "price_test_base")
os.environ.setdefault("STRIPE_PRICE_USAGE_ID", "price_test_usage")

_sowflow_path = Path(__file__).resolve().parent.parent.parent / "apps" / "sowflow" / "main.py"
spec = importlib.util.spec_from_file_location("sowflow_main", str(_sowflow_path))
sowflow_main = importlib.util.module_from_spec(spec)
sys.modules["sowflow_main"] = sowflow_main
spec.loader.exec_module(sowflow_main)
