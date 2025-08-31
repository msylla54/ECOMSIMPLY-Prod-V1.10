"""
ECOMSIMPLY Configuration Module
Centralized application configuration management
"""

import os
import secrets
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger("ecomsimply.config")

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._load_config()
        self._validate_critical_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        
        # Database Configuration
        self.MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.DB_NAME = os.environ.get('DB_NAME', 'ecomsimply_production')
        
        # Security Configuration
        self.JWT_SECRET = os.environ.get('JWT_SECRET')
        if not self.JWT_SECRET:
            self.JWT_SECRET = secrets.token_urlsafe(32)
            logger.warning("⚠️ JWT_SECRET not set in environment. Using generated secret.")
            logger.info(f"🔐 Add this to your environment: JWT_SECRET={self.JWT_SECRET}")
        
        self.ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = Fernet.generate_key().decode()
            logger.warning("⚠️ ENCRYPTION_KEY not set in environment. Using generated key.")
            logger.info(f"🔐 Add this to your environment: ENCRYPTION_KEY={self.ENCRYPTION_KEY}")
        
        # API Keys
        self.OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        self.STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
        self.FAL_KEY = os.environ.get('FAL_KEY')
        
        # Application Configuration
        self.ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
        self.DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
        
        # Redis Configuration
        self.REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        
        # Rate Limiting
        self.RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.environ.get('RATE_LIMIT_REQUESTS_PER_MINUTE', '100'))
        
        # Backup Configuration
        self.BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'false').lower() == 'true'
        self.BACKUP_INTERVAL = os.environ.get('BACKUP_INTERVAL', 'daily')
        self.BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
        
        # Email Configuration (if needed)
        self.SMTP_HOST = os.environ.get('SMTP_HOST')
        self.SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
        self.SMTP_USER = os.environ.get('SMTP_USER')
        self.SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
        
        # Monitoring
        self.MONITORING_ENDPOINT = os.environ.get('MONITORING_ENDPOINT')
        
        # Application Settings
        self.MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '10485760'))  # 10MB
        self.SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', '3600'))  # 1 hour
        
        # Feature Flags
        self.FEATURE_AI_ENABLED = os.environ.get('FEATURE_AI_ENABLED', 'true').lower() == 'true'
        self.FEATURE_SCRAPING_ENABLED = os.environ.get('FEATURE_SCRAPING_ENABLED', 'true').lower() == 'true'
        self.FEATURE_AFFILIATE_ENABLED = os.environ.get('FEATURE_AFFILIATE_ENABLED', 'true').lower() == 'true'
        
    def _validate_critical_config(self):
        """Validate critical configuration values"""
        critical_issues = []
        
        # Check for production-critical configurations
        if self.ENVIRONMENT == 'production':
            if not self.OPENAI_API_KEY:
                critical_issues.append("OPENAI_API_KEY not set for production")
            if not self.STRIPE_API_KEY:
                critical_issues.append("STRIPE_API_KEY not set for production")
            if self.JWT_SECRET == "your-secret-key-change-in-production":
                critical_issues.append("JWT_SECRET still using default value in production")
            if self.DB_NAME == "test_database":
                critical_issues.append("Database still using test_database name in production")
        
        if critical_issues:
            logger.error("❌ Critical configuration issues found:")
            for issue in critical_issues:
                logger.error(f"  - {issue}")
            if self.ENVIRONMENT == 'production':
                raise ValueError("Critical configuration issues prevent production startup")
        
        logger.info("✅ Configuration validation passed")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": self.MONGO_URL,
            "database_name": self.DB_NAME,
            "connection_options": {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "maxPoolSize": 10,
                "retryWrites": True
            }
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "jwt_secret": self.JWT_SECRET,
            "encryption_key": self.ENCRYPTION_KEY,
            "session_timeout": self.SESSION_TIMEOUT,
            "max_upload_size": self.MAX_UPLOAD_SIZE
        }
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys configuration"""
        return {
            "openai": self.OPENAI_API_KEY,
            "stripe": self.STRIPE_API_KEY,
            "fal": self.FAL_KEY
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return {
            "ai_enabled": self.FEATURE_AI_ENABLED,
            "scraping_enabled": self.FEATURE_SCRAPING_ENABLED,
            "affiliate_enabled": self.FEATURE_AFFILIATE_ENABLED,
            "rate_limiting": self.RATE_LIMIT_ENABLED,
            "backup": self.BACKUP_ENABLED
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == 'development'
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": self.LOG_LEVEL,
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "handlers": ["console", "file"] if self.is_production() else ["console"]
        }
    
    def __repr__(self) -> str:
        """String representation (safe - no secrets)"""
        return f"Config(environment={self.ENVIRONMENT}, db_name={self.DB_NAME}, debug={self.DEBUG})"

# Global configuration instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get global configuration instance"""
    return config

def is_production() -> bool:
    """Check if running in production"""
    return config.is_production()

def is_development() -> bool:
    """Check if running in development"""
    return config.is_development()

def get_database_url() -> str:
    """Get database URL"""
    return config.MONGO_URL

def get_database_name() -> str:
    """Get database name"""
    return config.DB_NAME