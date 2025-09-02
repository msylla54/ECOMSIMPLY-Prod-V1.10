# ================================================================================
# ECOMSIMPLY - CONFIGURATION CENTRALISÉE ENV-FIRST (STAFF LEVEL)
# ================================================================================

import os
import logging
from typing import Optional, List
from pydantic import BaseSettings, validator

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Configuration centralisée ENV-first
    AUCUNE valeur sensible hardcodée - Tout vient de l'environnement
    """
    
    # ================================================================================
    # CORE APPLICATION
    # ================================================================================
    APP_NAME: str = "ECOMSIMPLY API"
    APP_VERSION: str = "1.6.0"
    APP_DESCRIPTION: str = "AI-powered SaaS for e-commerce product sheet generation"
    
    # Environment
    NODE_ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 2
    
    # ================================================================================
    # DATABASE - PROD ONLY
    # ================================================================================
    MONGO_URL: str
    DB_NAME: Optional[str] = None  # Extracted from MONGO_URL if not provided
    
    @validator('MONGO_URL')
    def validate_mongo_url(cls, v):
        if not v:
            raise ValueError("MONGO_URL is required for production")
        if not v.startswith(('mongodb://', 'mongodb+srv://')):
            raise ValueError("MONGO_URL must be a valid MongoDB connection string")
        return v
    
    # ================================================================================
    # SECURITY & AUTH
    # ================================================================================
    JWT_SECRET: str
    ENCRYPTION_KEY: str
    
    # Admin Bootstrap
    ADMIN_EMAIL: str
    ADMIN_PASSWORD_HASH: str
    ADMIN_BOOTSTRAP_TOKEN: str
    
    @validator('JWT_SECRET', 'ENCRYPTION_KEY')
    def validate_secrets(cls, v):
        if not v or len(v) < 32:
            raise ValueError("Security keys must be at least 32 characters long")
        return v
    
    # ================================================================================
    # STRIPE CONFIGURATION - ENV ONLY
    # ================================================================================
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_PREMIUM: Optional[str] = None
    
    # Billing URLs
    BILLING_SUCCESS_URL: Optional[str] = None
    BILLING_CANCEL_URL: Optional[str] = None
    
    @validator('STRIPE_SECRET_KEY')
    def validate_stripe_secret(cls, v):
        if v and not v.startswith('sk_'):
            raise ValueError("STRIPE_SECRET_KEY must start with 'sk_'")
        return v
    
    @validator('STRIPE_WEBHOOK_SECRET')
    def validate_webhook_secret(cls, v):
        if v and not v.startswith('whsec_'):
            raise ValueError("STRIPE_WEBHOOK_SECRET must start with 'whsec_'")
        return v
    
    @validator('STRIPE_PRICE_PREMIUM')
    def validate_price_id(cls, v):
        if v and not v.startswith('price_'):
            raise ValueError("STRIPE_PRICE_PREMIUM must start with 'price_'")
        return v
    
    # ================================================================================
    # CORS & NETWORKING
    # ================================================================================
    APP_BASE_URL: str
    ADDITIONAL_ALLOWED_ORIGINS: Optional[str] = None
    
    @validator('APP_BASE_URL')
    def validate_base_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError("APP_BASE_URL must use HTTPS in production")
        return v
    
    def get_allowed_origins(self) -> List[str]:
        """Get list of allowed CORS origins"""
        origins = [self.APP_BASE_URL]
        
        if self.ADDITIONAL_ALLOWED_ORIGINS:
            additional = [origin.strip() for origin in self.ADDITIONAL_ALLOWED_ORIGINS.split(',')]
            origins.extend(additional)
        
        return origins
    
    # ================================================================================
    # AMAZON SP-API (Optional)
    # ================================================================================
    AMAZON_LWA_CLIENT_ID: Optional[str] = None
    AMAZON_LWA_CLIENT_SECRET: Optional[str] = None
    AWS_ROLE_ARN: Optional[str] = None
    AWS_REGION: str = "eu-west-1"
    
    # ================================================================================
    # SCHEDULER & FEATURES
    # ================================================================================
    ENABLE_SCHEDULER: bool = False
    
    # ================================================================================
    # VALIDATION & GUARDS
    # ================================================================================
    
    def validate_stripe_config(self) -> bool:
        """Validate Stripe configuration is complete"""
        if not all([self.STRIPE_SECRET_KEY, self.STRIPE_WEBHOOK_SECRET, self.STRIPE_PRICE_PREMIUM]):
            logger.warning("Stripe configuration incomplete - billing features will be disabled")
            return False
        return True
    
    def get_database_name(self) -> str:
        """Extract database name from MONGO_URL"""
        if self.DB_NAME:
            return self.DB_NAME
            
        # Extract from URL path
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.MONGO_URL)
            db_name = parsed.path.lstrip('/').split('?')[0]
            return db_name if db_name else 'ecomsimply_production'
        except Exception:
            return 'ecomsimply_production'
    
    def get_stripe_config(self) -> dict:
        """Get Stripe configuration dict"""
        return {
            "secret_key": self.STRIPE_SECRET_KEY,
            "webhook_secret": self.STRIPE_WEBHOOK_SECRET,
            "price_premium": self.STRIPE_PRICE_PREMIUM,
            "success_url": self.BILLING_SUCCESS_URL,
            "cancel_url": self.BILLING_CANCEL_URL,
            "enabled": self.validate_stripe_config()
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# ================================================================================
# GLOBAL CONFIGURATION INSTANCE
# ================================================================================

def load_settings() -> Settings:
    """Load settings with validation and error handling"""
    try:
        settings = Settings()
        
        # Log configuration status (without secrets)
        logger.info(f"✅ Configuration loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"📊 Database: {settings.get_database_name()}")
        logger.info(f"🔐 Stripe enabled: {settings.validate_stripe_config()}")
        logger.info(f"🌐 CORS origins: {len(settings.get_allowed_origins())}")
        
        return settings
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        raise RuntimeError(f"Failed to load configuration: {e}")

# Global settings instance
settings = load_settings()

# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

def require_stripe() -> dict:
    """Require Stripe configuration or raise error"""
    stripe_config = settings.get_stripe_config()
    if not stripe_config["enabled"]:
        raise RuntimeError(
            "Stripe configuration required but not complete. "
            "Please set STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, and STRIPE_PRICE_PREMIUM"
        )
    return stripe_config

def get_database_url() -> str:
    """Get database URL with validation"""
    if not settings.MONGO_URL:
        raise RuntimeError("MONGO_URL environment variable is required")
    return settings.MONGO_URL

def is_production() -> bool:
    """Check if running in production"""
    return settings.NODE_ENV.lower() == "production"

def get_cors_origins() -> List[str]:
    """Get CORS origins with emergency defaults"""
    origins = settings.get_allowed_origins()
    
    # Add emergent.sh domain if missing
    emergent_domain = "https://ecom-api-fixes.emergent.host"
    if emergent_domain not in origins:
        origins.append(emergent_domain)
    
    return origins