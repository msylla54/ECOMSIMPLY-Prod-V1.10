#!/usr/bin/env python3
"""
Database Connection Module
Separate module to avoid circular imports
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global database connection
_db_client = None
_db_instance = None

async def get_db():
    """
    Get database instance with lazy initialization
    """
    global _db_client, _db_instance
    
    if _db_instance is None:
        try:
            # Get MongoDB URL from environment
            MONGO_URL = os.getenv("MONGO_URL")
            DB_NAME = os.getenv("DB_NAME", "ecomsimply_production")
            
            if not MONGO_URL:
                raise Exception("MONGO_URL is not set")
            
            # Create connection if not exists
            if _db_client is None:
                _db_client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
                logger.info("MongoDB client initialized")
            
            # Test connection and get database
            await _db_client.admin.command('ping')
            _db_instance = _db_client[DB_NAME]
            
            logger.debug(f"✅ MongoDB connection successful to: {DB_NAME}")
            
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