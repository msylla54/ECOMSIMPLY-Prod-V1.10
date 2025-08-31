"""
ECOMSIMPLY Health Check Module
Centralized health monitoring and metrics collection
"""

import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("ecomsimply.health")

class HealthMonitor:
    """Centralized health monitoring system"""
    
    def __init__(self, db: AsyncIOMotorDatabase, scheduler=None):
        self.db = db
        self.scheduler = scheduler
        self.application_start_time = time.time()
        
    async def get_database_health(self) -> tuple[str, Optional[str]]:
        """Check database health"""
        try:
            # Use a simple operation to test connectivity
            await self.db.users.count_documents({})
            return "healthy", None
        except Exception as e:
            error_msg = f"MongoDB health check failed: {e}"
            logger.error(error_msg)
            return "unhealthy", error_msg
    
    def get_scheduler_health(self) -> str:
        """Check scheduler health"""
        if self.scheduler and hasattr(self.scheduler, 'running') and self.scheduler.running:
            return "healthy"
        return "stopped"
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": time.time() - psutil.boot_time(),
                "application_uptime": time.time() - self.application_start_time
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_usage": 0,
                "uptime": 0,
                "application_uptime": time.time() - self.application_start_time
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        db_status, db_error = await self.get_database_health()
        scheduler_status = self.get_scheduler_health()
        system_metrics = self.get_system_metrics()
        
        overall_status = "healthy" if db_status == "healthy" else "degraded"
        
        health_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "database": db_status,
                "scheduler": scheduler_status
            },
            "system": system_metrics
        }
        
        if db_error:
            health_data["errors"] = {"database": db_error}
            
        return health_data
    
    async def get_readiness_status(self) -> tuple[bool, str]:
        """Check if service is ready to accept requests"""
        try:
            # Test database connection and basic operations
            await self.db.users.count_documents({})
            return True, "ready"
        except Exception as e:
            error_msg = f"Service not ready: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """Simple liveness check"""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - self.application_start_time
        }
    
    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed application metrics"""
        try:
            # Database metrics
            db_stats = await self.db.command("dbStats")
            users_count = await self.db.users.count_documents({})
            sheets_count = await self.db.product_sheets.count_documents({})
            
            # System metrics
            system_metrics = self.get_system_metrics()
            
            return {
                "database": {
                    "collections": db_stats.get("collections", 0),
                    "objects": db_stats.get("objects", 0),
                    "dataSize": db_stats.get("dataSize", 0),
                    "indexSize": db_stats.get("indexSize", 0),
                    "avgObjSize": db_stats.get("avgObjSize", 0)
                },
                "application": {
                    "total_users": users_count,
                    "total_sheets": sheets_count,
                    "uptime": time.time() - self.application_start_time,
                    "start_time": datetime.fromtimestamp(self.application_start_time).isoformat()
                },
                "system": system_metrics,
                "performance": {
                    "requests_per_second": 0,  # Would need to implement request counting
                    "avg_response_time": 0,    # Would need to implement timing
                    "error_rate": 0            # Would need to implement error tracking
                }
            }
        except Exception as e:
            logger.error(f"Error collecting detailed metrics: {e}")
            raise
    
    def log_health_event(self, event_type: str, details: str, level: str = "info"):
        """Log health-related events"""
        log_method = getattr(logger, level, logger.info)
        log_method(f"Health Event [{event_type}]: {details}")

# Utility functions for common health checks
async def check_database_connectivity(db: AsyncIOMotorDatabase) -> bool:
    """Simple database connectivity check"""
    try:
        await db.admin.command('ping')
        return True
    except Exception:
        return False

def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "< 1m"