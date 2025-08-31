"""
ECOMSIMPLY Security Module
Centralizes all security-related functions for better maintainability
"""

import os
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Setup logger
logger = logging.getLogger("ecomsimply.security")

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET') or secrets.token_urlsafe(32)
if not os.environ.get('JWT_SECRET'):
    logger.warning("⚠️ JWT_SECRET not set in environment. Using generated secret.")
    logger.info(f"🔐 Add this to your environment: JWT_SECRET={JWT_SECRET}")
    
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(days=30)

class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt with salt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its bcrypt hash with legacy support"""
        try:
            return pwd_context.verify(password, hashed)
        except Exception as e:
            logger.debug(f"Password verification error: {e}")
            # Handle potential legacy SHA256 hashes during migration
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            if legacy_hash == hashed:
                logger.warning(f"⚠️ Legacy SHA256 password detected - should be migrated to bcrypt")
                return True
            return False
    
    @staticmethod
    def create_jwt_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create a JWT token for user authentication"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + JWT_EXPIRATION_DELTA,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        if additional_claims:
            payload.update(additional_claims)
            
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    @staticmethod
    def generate_secure_secret(length: int = 32) -> str:
        """Generate a cryptographically secure secret"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def is_password_strong(password: str) -> tuple[bool, list[str]]:
        """Check if password meets security requirements"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
            
        return len(issues) == 0, issues
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Basic input sanitization"""
        if not isinstance(input_string, str):
            return ""
        
        # Remove potential dangerous characters
        sanitized = input_string.replace('<', '&lt;').replace('>', '&gt;')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized.strip()

# Global security manager instance
security_manager = SecurityManager()

# Convenience functions for backward compatibility
def hash_password(password: str) -> str:
    return security_manager.hash_password(password)

def verify_password(password: str, hashed: str) -> bool:
    return security_manager.verify_password(password, hashed)

def create_jwt_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    return security_manager.create_jwt_token(user_id, additional_claims)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    return security_manager.verify_jwt_token(token)

# FastAPI Dependencies for Authentication
security = HTTPBearer()

async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency function to get current user from JWT token
    Returns user data as dict including image management preferences
    """
    try:
        # Verify the JWT token
        payload = verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide - user_id manquant"
            )
            
        # Import here to avoid circular imports
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        # Get MongoDB connection
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
        db = client[db_name]
        
        # Fetch user data from database
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        # Return user data including image management fields
        return {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "subscription_plan": user_data.get("subscription_plan", "gratuit"),
            "is_admin": user_data.get("is_admin", False),
            "language": user_data.get("language", "fr"),
            "generate_images": user_data.get("generate_images", True),
            "include_images_manual": user_data.get("include_images_manual", True)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user_from_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification"
        )