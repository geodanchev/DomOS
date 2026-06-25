"""Application configuration.

SECURITY: This module validates critical security settings at startup.
In production mode (DEBUG=False), weak or default secrets are rejected.
"""

import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


# List of known weak/default secret keys that must never be used in production
_WEAK_SECRET_KEYS = {
    "change-me-in-production-use-long-random-string",
    "change-me-in-production-use-long-random-string-at-least-32-chars",
    "secret",
    "secret-key",
    "changeme",
    "change-me",
    "your-secret-key",
    "your-secret-key-here",
    "development-secret",
    "dev-secret",
    "test-secret",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    SECURITY NOTES:
    - SECRET_KEY must be unique and at least 32 characters in production
    - DEBUG must be False in production
    - INIT_DEMO_DATA should be False in production
    """
    
    # App info
    APP_NAME: str = "DomOS Cashier MVP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/domos_cashier"
    
    # Security
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Demo data initialization control
    # SECURITY: Set to False in production to prevent demo user creation
    INIT_DEMO_DATA: bool = True
    
    # Demo user passwords (only used when INIT_DEMO_DATA=true)
    # SECURITY: These should not be used in production
    DEMO_ADMIN_PASSWORD: str | None = None
    DEMO_CASHIER_PASSWORD: str | None = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY security requirements.
        
        In production (when DEBUG env var is not 'true'), requires:
        - At least 32 characters
        - Not a known weak/default value
        """
        # Check if we're in production mode
        debug_env = os.getenv('DEBUG', 'true').lower()
        is_production = debug_env not in ('true', '1', 'yes')
        
        if is_production:
            # Check for weak/default keys
            if v.lower() in _WEAK_SECRET_KEYS or v.lower().strip() in _WEAK_SECRET_KEYS:
                raise ValueError(
                    "SECURITY ERROR: SECRET_KEY is set to a known weak/default value. "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            
            # Check minimum length
            if len(v) < 32:
                raise ValueError(
                    f"SECURITY ERROR: SECRET_KEY must be at least 32 characters in production. "
                    f"Current length: {len(v)}. "
                    f"Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
        
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Validates all security settings on first access.
    Raises ValueError if security requirements are not met in production.
    """
    return Settings()


settings = get_settings()


def generate_secure_secret_key() -> str:
    """Generate a cryptographically secure secret key.
    
    Use this to generate a production-ready SECRET_KEY:
        python -c "from app.core.config import generate_secure_secret_key; print(generate_secure_secret_key())"
    """
    return secrets.token_urlsafe(32)
