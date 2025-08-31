#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Startup Script
Optimisé pour déploiement emergent.sh production
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Configuration logging pour production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ecomsimply.startup")

def validate_environment():
    """Valide les variables d'environnement critiques"""
    required_vars = [
        'MONGO_URL',
        'JWT_SECRET', 
        'ENCRYPTION_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {missing_vars}")
        return False
    
    logger.info("✅ Variables d'environnement validées")
    return True

async def test_database_connection():
    """Test de connexion MongoDB avec timeout"""
    try:
        from database import get_db
        db = await asyncio.wait_for(get_db(), timeout=10.0)
        await asyncio.wait_for(db.command("ping"), timeout=5.0)
        logger.info("✅ Connexion MongoDB validée")
        return True
    except asyncio.TimeoutError:
        logger.warning("⚠️ MongoDB timeout - continuera avec fallback")
        return False
    except Exception as e:
        logger.warning(f"⚠️ MongoDB indisponible: {e} - continuera avec fallback")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("🚀 Démarrage ECOMSIMPLY Backend")
    logger.info(f"Environment: {os.getenv('NODE_ENV', 'development')}")
    logger.info(f"Port: {os.getenv('PORT', '8001')}")
    
    # Validation environnement
    if not validate_environment():
        logger.error("❌ Validation environnement échouée")
        sys.exit(1)
    
    # Test DB (non-bloquant)
    try:
        db_ok = asyncio.run(test_database_connection())
        if not db_ok:
            logger.info("ℹ️ Application démarrera sans DB (mode dégradé)")
    except Exception as e:
        logger.warning(f"Impossible de tester DB: {e}")
    
    logger.info("✅ Pré-vérifications terminées - démarrage serveur")
    
    # Import et démarrage du serveur FastAPI
    try:
        import uvicorn
        from server import app
        
        port = int(os.getenv('PORT', 8001))
        workers = int(os.getenv('WORKERS', 1))
        
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"❌ Erreur démarrage serveur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()