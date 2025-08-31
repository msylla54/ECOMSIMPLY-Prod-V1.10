"""
Initialisation des index MongoDB pour Phase 4 - Amazon Pricing
"""
import asyncio
import logging
from backend.services.amazon_pricing_rules_service import pricing_rules_service

logger = logging.getLogger(__name__)

async def initialize_pricing_indexes():
    """Initialiser les index MongoDB pour les collections de pricing"""
    try:
        logger.info("Initializing MongoDB indexes for Amazon Pricing (Phase 4)...")
        
        await pricing_rules_service.create_indexes()
        
        logger.info("✅ Amazon Pricing MongoDB indexes initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing pricing indexes: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_pricing_indexes())