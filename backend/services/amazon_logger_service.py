"""
Amazon SP-API Logger Service
Service centralisé pour logs Amazon avec MongoDB comme source unique
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

logger = logging.getLogger(__name__)

class AmazonLoggerService:
    """Service de logging centralisé pour Amazon SP-API"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["amazon_logs"]
        
    async def log_api_call(
        self,
        user_id: str,
        endpoint: str,
        method: str = "GET",
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[float] = None
    ):
        """Log d'un appel API Amazon SP-API"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "user_id": user_id,
                "service_type": "amazon_spapi",
                "endpoint": endpoint,
                "method": method,
                "request_data": request_data or {},
                "response_data": response_data or {},
                "status_code": status_code,
                "success": status_code < 400,
                "error_message": error_message,
                "execution_time_ms": execution_time_ms,
                "environment": os.environ.get("NODE_ENV", "development")
            }
            
            await self.collection.insert_one(log_entry)
            
            # Log console pour développement
            log_level = logging.INFO if status_code < 400 else logging.ERROR
            console_msg = f"Amazon API {method} {endpoint} → {status_code}"
            if execution_time_ms:
                console_msg += f" ({execution_time_ms}ms)"
            if error_message:
                console_msg += f" | Error: {error_message}"
                
            logger.log(log_level, console_msg)
            
        except Exception as e:
            logger.error(f"Failed to log Amazon API call: {e}")
    
    async def log_oauth_event(
        self,
        user_id: str,
        event_type: str,  # connect, refresh, disconnect, error
        marketplace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log d'un événement OAuth Amazon"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "user_id": user_id,
                "service_type": "amazon_oauth",
                "event_type": event_type,
                "marketplace_id": marketplace_id,
                "details": details or {},
                "success": success,
                "error_message": error_message,
                "environment": os.environ.get("NODE_ENV", "development")
            }
            
            await self.collection.insert_one(log_entry)
            
            # Log console
            status = "✅" if success else "❌"
            console_msg = f"{status} Amazon OAuth {event_type}"
            if marketplace_id:
                console_msg += f" (marketplace: {marketplace_id})"
            if error_message:
                console_msg += f" | Error: {error_message}"
                
            logger.info(console_msg)
            
        except Exception as e:
            logger.error(f"Failed to log Amazon OAuth event: {e}")

# Instance globale pour réutilisation
amazon_logger = None

async def get_amazon_logger(db: AsyncIOMotorDatabase) -> AmazonLoggerService:
    """Factory pour obtenir l'instance du logger Amazon"""
    global amazon_logger
    if not amazon_logger:
        amazon_logger = AmazonLoggerService(db)
        
        # Créer les index MongoDB pour performance
        try:
            await db["amazon_logs"].create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ])
            await db["amazon_logs"].create_index([
                ("service_type", 1),
                ("timestamp", -1)
            ])
            logger.info("✅ Amazon logs indexes created")
        except Exception as e:
            logger.warning(f"Failed to create Amazon logs indexes: {e}")
    
    return amazon_logger