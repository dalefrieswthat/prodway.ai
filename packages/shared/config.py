"""
Centralized configuration for Prodway.

Validates all required environment variables on startup.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from packages.shared.security import (
    is_valid_slack_token,
    is_valid_anthropic_key,
    is_valid_stripe_key,
    mask_token,
)
from packages.shared.logging import get_logger

logger = get_logger("config")


@dataclass
class Config:
    """Application configuration."""
    
    # Environment
    app_env: str
    log_level: str
    
    # Required: AI
    anthropic_api_key: str
    
    # Required: Slack
    slack_bot_token: str
    slack_app_token: str
    slack_signing_secret: str
    
    # Optional: DocuSign
    docusign_integration_key: str | None
    docusign_secret_key: str | None
    docusign_account_id: str | None
    docusign_access_token: str | None
    
    # Optional: Stripe
    stripe_secret_key: str | None
    stripe_webhook_secret: str | None
    
    # Optional: Database
    database_url: str | None
    
    # Optional: Vector store
    pinecone_api_key: str | None
    pinecone_index: str | None
    
    # Security
    encryption_key: str | None
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def has_docusign(self) -> bool:
        return bool(self.docusign_access_token and self.docusign_account_id)
    
    @property
    def has_stripe(self) -> bool:
        return bool(self.stripe_secret_key)
    
    @property
    def has_database(self) -> bool:
        return bool(self.database_url)
    
    def validate(self) -> list[str]:
        """Validate configuration, return list of errors."""
        errors = []
        
        # Required
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        elif not is_valid_anthropic_key(self.anthropic_api_key):
            errors.append("ANTHROPIC_API_KEY format is invalid")
        
        if not self.slack_bot_token:
            errors.append("SLACK_BOT_TOKEN is required")
        elif not is_valid_slack_token(self.slack_bot_token):
            errors.append("SLACK_BOT_TOKEN format is invalid (should start with xoxb-)")
        
        if not self.slack_app_token:
            errors.append("SLACK_APP_TOKEN is required")
        elif not self.slack_app_token.startswith("xapp-"):
            errors.append("SLACK_APP_TOKEN format is invalid (should start with xapp-)")
        
        # Optional validations
        if self.stripe_secret_key and not is_valid_stripe_key(self.stripe_secret_key):
            errors.append("STRIPE_SECRET_KEY format is invalid")
        
        # Production requirements
        if self.is_production:
            if not self.encryption_key:
                errors.append("ENCRYPTION_KEY is required in production")
            if not self.database_url:
                errors.append("DATABASE_URL is required in production")
        
        return errors
    
    def log_status(self):
        """Log configuration status (without secrets)."""
        logger.info("Configuration loaded", extra={
            "data": {
                "env": self.app_env,
                "anthropic": "✓" if self.anthropic_api_key else "✗",
                "slack": "✓" if self.slack_bot_token else "✗",
                "docusign": "✓" if self.has_docusign else "○",
                "stripe": "✓" if self.has_stripe else "○",
                "database": "✓" if self.has_database else "○",
            }
        })


@lru_cache
def get_config() -> Config:
    """Load and validate configuration from environment."""
    
    config = Config(
        # Environment
        app_env=os.environ.get("APP_ENV", "development"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        
        # AI
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        
        # Slack
        slack_bot_token=os.environ.get("SLACK_BOT_TOKEN", ""),
        slack_app_token=os.environ.get("SLACK_APP_TOKEN", ""),
        slack_signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
        
        # DocuSign
        docusign_integration_key=os.environ.get("DOCUSIGN_INTEGRATION_KEY"),
        docusign_secret_key=os.environ.get("DOCUSIGN_SECRET_KEY"),
        docusign_account_id=os.environ.get("DOCUSIGN_ACCOUNT_ID"),
        docusign_access_token=os.environ.get("DOCUSIGN_ACCESS_TOKEN"),
        
        # Stripe
        stripe_secret_key=os.environ.get("STRIPE_SECRET_KEY"),
        stripe_webhook_secret=os.environ.get("STRIPE_WEBHOOK_SECRET"),
        
        # Database
        database_url=os.environ.get("DATABASE_URL"),
        
        # Vector store
        pinecone_api_key=os.environ.get("PINECONE_API_KEY"),
        pinecone_index=os.environ.get("PINECONE_INDEX"),
        
        # Security
        encryption_key=os.environ.get("ENCRYPTION_KEY"),
    )
    
    # Validate
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Config error: {error}")
        
        if config.is_production:
            raise ValueError(f"Configuration errors: {errors}")
    
    config.log_status()
    return config


def require_config(*required_fields: str) -> Config:
    """Get config and ensure specific fields are present."""
    config = get_config()
    
    missing = []
    for field in required_fields:
        if not getattr(config, field, None):
            missing.append(field)
    
    if missing:
        raise ValueError(f"Missing required configuration: {missing}")
    
    return config
