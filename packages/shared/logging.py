"""
Structured logging for Prodway apps.

All logs include:
- Timestamp
- Log level
- Context (user_id, org_id, request_id)
- Structured data for searching
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Any
from functools import lru_cache


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "org_id"):
            log_data["org_id"] = record.org_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "data"):
            log_data["data"] = record.data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class PrettyFormatter(logging.Formatter):
    """Human-readable format for development."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now().strftime("%H:%M:%S")

        msg = f"{color}[{timestamp}] {record.levelname:8}{self.RESET} {record.getMessage()}"

        # Add context if present
        context_parts = []
        if hasattr(record, "user_id"):
            context_parts.append(f"user={record.user_id}")
        if hasattr(record, "action"):
            context_parts.append(f"action={record.action}")

        if context_parts:
            msg += f" ({', '.join(context_parts)})"

        return msg


class ContextLogger(logging.Logger):
    """Logger with context binding support."""

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs) -> "ContextLogger":
        """Bind context that will be included in all logs."""
        self._context.update(kwargs)
        return self

    def _log(self, level, msg, args, exc_info=None, extra=None, **kwargs):
        if extra is None:
            extra = {}
        extra.update(self._context)
        extra.update(kwargs)
        super()._log(level, msg, args, exc_info, extra)


@lru_cache
def get_logger(name: str = "prodway") -> ContextLogger:
    """Get a configured logger."""

    # Use JSON in production, pretty in development
    is_production = os.environ.get("APP_ENV") == "production"

    logging.setLoggerClass(ContextLogger)
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if is_production:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(PrettyFormatter())

        logger.addHandler(handler)
        logger.setLevel(
            getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper())
        )

    return logger


# Audit logging for SOC2 compliance
class AuditLogger:
    """
    Audit logger for compliance-sensitive actions.

    Records:
    - Who did what
    - When
    - What data was accessed/modified
    - Result (success/failure)
    """

    def __init__(self):
        self.logger = get_logger("prodway.audit")

    def log_action(
        self,
        action: str,
        user_id: str | None,
        org_id: str | None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        result: str = "success",
    ):
        """Log an auditable action."""
        self.logger.info(
            f"AUDIT: {action}",
            extra={
                "action": action,
                "user_id": user_id,
                "org_id": org_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "result": result,
                "audit": True,
            }
        )

    def log_sow_generated(self, user_id: str, sow_title: str, pricing: int):
        self.log_action(
            action="sow_generated",
            user_id=user_id,
            org_id=None,
            resource_type="sow",
            details={"title": sow_title, "pricing": pricing},
        )

    def log_sow_sent(self, user_id: str, sow_id: str, client_email: str):
        self.log_action(
            action="sow_sent",
            user_id=user_id,
            org_id=None,
            resource_type="sow",
            resource_id=sow_id,
            details={"client_email_hash": hash(client_email)},  # Don't log PII
        )

    def log_payment_created(self, user_id: str, amount: int, invoice_id: str):
        self.log_action(
            action="payment_created",
            user_id=user_id,
            org_id=None,
            resource_type="payment",
            resource_id=invoice_id,
            details={"amount": amount},
        )


# Global audit logger
audit = AuditLogger()
