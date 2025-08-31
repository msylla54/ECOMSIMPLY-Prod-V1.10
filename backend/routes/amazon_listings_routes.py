# Amazon Listings Routes - Phase 2
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
import os
import jwt
from datetime import datetime

# Import des modules Phase 2
from amazon.listings.generator import AmazonListingGenerator
from amazon.listings.validators import AmazonListingValidator, ValidationStatus
from amazon.listings.publisher import AmazonListingPublisher

# Import des modules Phase 1
from integrations.amazon.models import AmazonConnection

logger = logging.getLogger(__name__)

# Router avec préfixe /api/amazon/listings
amazon_listings_router = APIRouter(prefix="/api/amazon/listings", tags=["Amazon Listings Phase 2"])

# Security
security = HTTPBearer()

# Dépendance pour obtenir la base de données
async def get_database():
    """Récupère l'instance MongoDB"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        raise HTTPException(
            status_code=500,
            detail="Database configuration error"
        )
    
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
    return client[db_name]

# Dépendance pour obtenir l'utilisateur authentifié
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extrait l'utilisateur depuis le JWT token"""
    try:
        token = credentials.credentials
        secret = os.environ.get('JWT_SECRET')
        
        if not secret:
            raise HTTPException(status_code=500, detail="JWT configuration error")
        
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

async def get_user_amazon_connection(user_id: str, db) -> Dict[str, Any]:
    """Récupère la connexion Amazon active de l'utilisateur"""
    connection = await db.amazon_connections.find_one({
        "user_id": user_id,
        "status": "connected"
    })
    
    if not connection:
        raise HTTPException(
            status_code=412,  # Precondition Failed
            detail="No active Amazon connection found. Please connect your Amazon account first."
        )
    
    return connection

# 1. POST /api/amazon/listings/generate - Générer fiche par IA
@amazon_listings_router.post("/generate")
async def generate_amazon_listing(
    product_data: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db = Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Génère une fiche produit Amazon par IA
    
    Body:
    {
        "brand": "Apple",
        "product_name": "iPhone 15 Pro Max",
        "features": ["A17 Pro chip", "Titanium design", "Action Button"],
        "category": "électronique",
        "target_keywords": ["smartphone", "premium", "apple"],
        "size": "6.7 pouces",
        "color": "Titanium naturel",
        "price": 1479.00,
        "description": "Le smartphone le plus avancé d'Apple"
    }
    """
    try:
        logger.info(f"🤖 Generating listing for user {current_user[:8]}*** - Product: {product_data.get('product_name')}")
        
        # Validation des données d'entrée
        if not product_data.get('brand') or not product_data.get('product_name'):
            raise HTTPException(
                status_code=400,
                detail="Brand and product_name are required"
            )
        
        # Vérifier connexion Amazon active
        await get_user_amazon_connection(current_user, db)
        
        # Initialiser le générateur IA
        generator = AmazonListingGenerator()
        
        # Générer la fiche complète
        generated_listing = await generator.generate_amazon_listing(product_data)
        
        # Ajouter métadonnées utilisateur
        generated_listing['user_id'] = current_user
        generated_listing['generated_for_amazon'] = True
        
        # Sauvegarder en base (optionnel - pour historique)
        background_tasks.add_task(
            save_generated_listing, 
            db, 
            generated_listing
        )
        
        logger.info(f"✅ Listing generated successfully - Score: {generated_listing['generation_metadata']['optimization_score']}")
        
        return {
            "status": "success",
            "message": "Fiche produit générée avec succès",
            "data": generated_listing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Génération échouée: {str(e)}"
        )

# 2. POST /api/amazon/listings/validate - Valider fiche
@amazon_listings_router.post("/validate")
async def validate_amazon_listing(
    listing_data: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Valide une fiche produit selon les règles Amazon
    
    Body: Fiche générée (output de /generate)
    """
    try:
        logger.info(f"🔍 Validating listing for user {current_user[:8]}***")
        
        # Vérifier connexion Amazon active
        await get_user_amazon_connection(current_user, db)
        
        # Initialiser le validateur
        validator = AmazonListingValidator()
        
        # Validation complète
        validation_result = validator.validate_complete_listing(listing_data)
        
        # Ajouter contexte utilisateur
        validation_result['user_id'] = current_user
        validation_result['listing_id'] = listing_data.get('listing_id')
        
        # Génerer résumé textuel
        summary = validator.get_validation_summary(validation_result)
        
        logger.info(f"✅ Validation completed - Status: {validation_result['overall_status']}")
        
        return {
            "status": "success",
            "message": "Validation terminée",
            "summary": summary,
            "data": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation échouée: {str(e)}"
        )

# 3. POST /api/amazon/listings/publish - Publier sur Amazon
@amazon_listings_router.post("/publish")
async def publish_listing_to_amazon(
    publication_request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db = Depends(get_database),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Publie réellement une fiche sur Amazon via SP-API
    
    Body:
    {
        "listing_data": {...},  // Fiche générée
        "validation_data": {...},  // Résultat de validation
        "marketplace_id": "A13V1IB3VIYZZH",  // Optionnel, prend connexion par défaut
        "sku": "CUSTOM-SKU-123",  // Optionnel, généré automatiquement
        "force_publish": false  // Publier même si validation PENDING_REVIEW
    }
    """
    try:
        logger.info(f"📤 Publishing listing for user {current_user[:8]}***")
        
        # Extraction des données
        listing_data = publication_request.get('listing_data')
        validation_data = publication_request.get('validation_data', {})
        force_publish = publication_request.get('force_publish', False)
        
        if not listing_data:
            raise HTTPException(
                status_code=400,
                detail="listing_data is required"
            )
        
        # Vérifier connexion Amazon active
        connection = await get_user_amazon_connection(current_user, db)
        
        # Vérifier statut de validation si fourni
        validation_status = validation_data.get('overall_status')
        if validation_status == ValidationStatus.REJECTED and not force_publish:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish rejected listing. Fix errors or use force_publish=true"
            )
        
        if validation_status == ValidationStatus.PENDING_REVIEW and not force_publish:
            raise HTTPException(
                status_code=400,
                detail="Listing requires review. Fix warnings or use force_publish=true"
            )
        
        # Initialiser le publisher
        publisher = AmazonListingPublisher()
        
        # Publication réelle
        publication_result = await publisher.publish_listing_to_amazon(
            product_data=listing_data.get('product_data', {}),
            seo_data=listing_data.get('seo_content', {}),
            connection_data=connection
        )
        
        # Sauvegarder le résultat
        background_tasks.add_task(
            save_publication_result,
            db,
            current_user,
            publication_result
        )
        
        # Réponse selon le résultat
        if publication_result['status'] == 'success':
            logger.info(f"✅ Publication successful - SKU: {publication_result['sku']}")
            return {
                "status": "success",
                "message": "Fiche publiée avec succès sur Amazon",
                "data": publication_result
            }
        else:
            logger.warning(f"⚠️ Publication failed - Errors: {publication_result['errors']}")
            return {
                "status": "error",
                "message": "Échec de la publication sur Amazon",
                "errors": publication_result['errors'],
                "data": publication_result
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Publication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de publication: {str(e)}"
        )

# 4. GET /api/amazon/listings/status/{sku} - Statut d'une fiche
@amazon_listings_router.get("/status/{sku}")
async def get_listing_status(
    sku: str,
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Vérifie le statut d'une fiche publiée sur Amazon
    """
    try:
        logger.info(f"🔍 Checking status for SKU: {sku}")
        
        # Vérifier connexion Amazon active
        connection = await get_user_amazon_connection(current_user, db)
        
        # Initialiser le publisher pour vérification
        publisher = AmazonListingPublisher()
        
        # Vérifier statut sur Amazon
        status_result = await publisher.check_listing_status(sku, connection)
        
        return {
            "status": "success",
            "data": status_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vérification statut échouée: {str(e)}"
        )

# 5. GET /api/amazon/listings/history - Historique des générations
@amazon_listings_router.get("/history")
async def get_listings_history(
    current_user: str = Depends(get_current_user),
    db = Depends(get_database),
    limit: int = 20,
    skip: int = 0
):
    """
    Récupère l'historique des fiches générées/publiées
    """
    try:
        logger.info(f"📚 Getting listings history for user {current_user[:8]}***")
        
        # Récupérer depuis la base
        cursor = db.generated_listings.find(
            {"user_id": current_user}
        ).sort("generated_at", -1).limit(limit).skip(skip)
        
        listings = await cursor.to_list(length=None)
        
        # Compter le total
        total_count = await db.generated_listings.count_documents({"user_id": current_user})
        
        return {
            "status": "success",
            "data": {
                "listings": listings,
                "total_count": total_count,
                "limit": limit,
                "skip": skip
            }
        }
        
    except Exception as e:
        logger.error(f"❌ History retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Récupération historique échouée: {str(e)}"
        )

# 6. PUT /api/amazon/listings/update/{sku} - Mettre à jour une fiche
@amazon_listings_router.put("/update/{sku}")
async def update_amazon_listing(
    sku: str,
    updates: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Met à jour une fiche existante sur Amazon
    """
    try:
        logger.info(f"📝 Updating listing SKU: {sku}")
        
        # Vérifier connexion Amazon active
        connection = await get_user_amazon_connection(current_user, db)
        
        # Initialiser le publisher
        publisher = AmazonListingPublisher()
        
        # Mise à jour
        update_result = await publisher.update_listing_on_amazon(sku, updates, connection)
        
        return {
            "status": "success" if update_result.get('status') == 'success' else "error",
            "message": "Mise à jour effectuée" if update_result.get('status') == 'success' else "Échec de mise à jour",
            "data": update_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mise à jour échouée: {str(e)}"
        )

# Fonctions utilitaires pour tâches d'arrière-plan

async def save_generated_listing(db, listing_data: Dict[str, Any]):
    """Sauvegarde une fiche générée en base"""
    try:
        listing_data['_id'] = listing_data['listing_id']
        await db.generated_listings.insert_one(listing_data)
        logger.info(f"💾 Listing saved to database: {listing_data['listing_id']}")
    except Exception as e:
        logger.error(f"❌ Failed to save listing: {str(e)}")

async def save_publication_result(db, user_id: str, publication_result: Dict[str, Any]):
    """Sauvegarde le résultat de publication"""
    try:
        publication_record = {
            '_id': publication_result['publication_id'],
            'user_id': user_id,
            'sku': publication_result['sku'],
            'status': publication_result['status'],
            'published_at': publication_result['published_at'],
            'marketplace_id': publication_result['marketplace_id'],
            'listing_url': publication_result.get('listing_url'),
            'errors': publication_result.get('errors', [])
        }
        
        await db.publication_results.insert_one(publication_record)
        logger.info(f"💾 Publication result saved: {publication_result['publication_id']}")
    except Exception as e:
        logger.error(f"❌ Failed to save publication result: {str(e)}")