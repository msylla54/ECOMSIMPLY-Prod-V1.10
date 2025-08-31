"""
Initialisation des services de monitoring Amazon - Phase 5
"""
import asyncio
import logging
from services.amazon_monitoring_service import monitoring_service
from amazon.monitoring.orchestrator import monitoring_orchestrator

logger = logging.getLogger(__name__)

async def initialize_monitoring_services():
    """Initialiser tous les services de monitoring Amazon"""
    try:
        logger.info("🚀 Initializing Amazon Monitoring Services (Phase 5)...")
        
        # 1. Créer les indexes MongoDB
        await monitoring_service.create_indexes()
        
        # 2. Initialiser l'orchestrateur
        await monitoring_orchestrator.initialize()
        
        logger.info("✅ Amazon Monitoring Services initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing monitoring services: {str(e)}")
        return False

async def shutdown_monitoring_services():
    """Arrêt propre des services de monitoring"""
    try:
        logger.info("🛑 Shutting down Amazon Monitoring Services...")
        
        await monitoring_orchestrator.shutdown()
        
        logger.info("✅ Amazon Monitoring Services shut down successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

if __name__ == "__main__":
    asyncio.run(initialize_monitoring_services())