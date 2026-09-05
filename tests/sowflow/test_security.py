"""Tests for SowFlow security: encryption, audit logging."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet


class TestEncryption:
    """API key encryption at rest."""

    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEY", key)

        import importlib
        import sowflow_main as mod
        mod.ENCRYPTION_KEY = key

        plaintext = "pw_test_secret_key_12345"
        encrypted = mod._encrypt_api_key(plaintext)
        assert encrypted != plaintext
        decrypted = mod._decrypt_api_key(encrypted)
        assert decrypted == plaintext

    def test_decrypt_handles_plaintext_gracefully(self, monkeypatch):
        monkeypatch.setenv("ENCRYPTION_KEY", "")
        import sowflow_main as mod
        mod.ENCRYPTION_KEY = ""

        result = mod._decrypt_api_key("pw_plaintext_key")
        assert result == "pw_plaintext_key"

    def test_decrypt_empty_returns_empty(self):
        from sowflow_main import _decrypt_api_key
        assert _decrypt_api_key("") == ""

    def test_no_encryption_key_returns_plaintext(self, monkeypatch):
        monkeypatch.setenv("ENCRYPTION_KEY", "")
        import sowflow_main as mod
        mod.ENCRYPTION_KEY = ""

        result = mod._encrypt_api_key("test_key")
        assert result == "test_key"


class TestAuditLogging:
    """Append-only audit log."""

    def test_writes_audit_entry(self, tmp_data_dir):
        audit_dir = tmp_data_dir / "audit"
        audit_dir.mkdir(exist_ok=True)

        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import _audit_log

            _audit_log("T001", "U001", "api_key_generated", {"key_prefix": "pw_abc"})

            log_file = audit_dir / "T001.jsonl"
            assert log_file.exists()

            lines = log_file.read_text().strip().split("\n")
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["team_id"] == "T001"
            assert entry["user_id"] == "U001"
            assert entry["action"] == "api_key_generated"
            assert "timestamp" in entry

    def test_audit_appends(self, tmp_data_dir):
        audit_dir = tmp_data_dir / "audit"
        audit_dir.mkdir(exist_ok=True)

        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import _audit_log

            _audit_log("T002", "U001", "action_one", {})
            _audit_log("T002", "U002", "action_two", {})

            log_file = audit_dir / "T002.jsonl"
            lines = log_file.read_text().strip().split("\n")
            assert len(lines) == 2
