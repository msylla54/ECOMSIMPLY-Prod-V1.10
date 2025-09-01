#!/usr/bin/env python3
"""
Database Connection Module - URI EXCLUSIVE
Force utilisation exclusivement de MONGO_URL avec DB explicite
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Global database connection
_db_client = None
_db_instance = None

def _extract_db_from_uri(mongo_url: str) -> str:
    """
    Extract database name from MongoDB URI
    Returns database name or raises exception if not found
    """
    try:
        parsed = urlparse(mongo_url)
        db_name = parsed.path.lstrip('/')
        if not db_name:
            raise ValueError("No database specified in MONGO_URL path")
        
        # Remove query parameters if present
        db_name = db_name.split('?')[0]
        return db_name
    except Exception as e:
        raise ValueError(f"Failed to extract database from URI: {e}")

async def get_db():
    """
    Get database instance with URI-ONLY initialization
    IGNORE DB_NAME env var - use only MONGO_URL database specification
    """
    global _db_client, _db_instance
    
    if _db_instance is None:
        try:
            # Get MongoDB URL from environment - MANDATORY
            MONGO_URL = os.getenv("MONGO_URL")
            
            if not MONGO_URL:
                raise Exception("MONGO_URL is not set")
            
            # Extract database name FROM URI ONLY
            database_name = _extract_db_from_uri(MONGO_URL)
            
            # Log startup info
            parsed_url = urlparse(MONGO_URL)
            host_info = f"{parsed_url.hostname}:{parsed_url.port or 27017}"
            
            logger.info(f"🔗 MongoDB Host: {host_info}")
            logger.info(f"📊 Database from URI: {database_name}")
            
            # Check for conflicting ENV vars and warn
            env_db_name = os.getenv("DB_NAME")
            if env_db_name:
                logger.warning(f"⚠️ DB_NAME env var detected ({env_db_name}) but IGNORED - using URI database: {database_name}")
            
            # Create connection if not exists
            if _db_client is None:
                _db_client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
                logger.info("✅ MongoDB client initialized from URI")
            
            # Test connection and get database FROM URI
            await _db_client.admin.command('ping')
            _db_instance = _db_client[database_name]
            
            # Verify actual database name
            actual_db_name = _db_instance.name
            logger.info(f"✅ MongoDB connected - Actual DB: {actual_db_name}")
            
            if actual_db_name != database_name:
                logger.error(f"❌ Database mismatch! Expected: {database_name}, Got: {actual_db_name}")
                
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection timeout: {str(e)}")
            raise Exception(f"Database connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {str(e)}")
            raise Exception(f"Database connection failed: {str(e)}")
            
    return _db_instance

async def close_db():
    """
    Close database connection
    """
    global _db_client, _db_instance
    
    if _db_client:
        _db_client.close()
        _db_client = None
        _db_instance = None
        logger.info("✅ MongoDB connection closed")