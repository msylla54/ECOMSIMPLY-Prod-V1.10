# Amazon SEO + Price Routes - Phase 3
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Services Phase 3
from services.amazon_scraping_service import AmazonScrapingService
from services.seo_optimizer_service import SEOOptimizerService  
from services.price_optimizer_service import PriceOptimizerService
from services.amazon_publisher_service import AmazonPublisherService

# Services existants
from modules.security import verify_jwt_token

logger = logging.getLogger(__name__)

# Router pour Phase 3 Amazon SEO + Prix
amazon_seo_price_router = APIRouter(prefix="/api/amazon", tags=["Amazon SEO & Price Phase 3"])
security = HTTPBearer()

# Initialiser les services avec gestion d'erreurs
try:
    scraping_service = AmazonScrapingService()
    seo_optimizer = SEOOptimizerService()
    price_optimizer = PriceOptimizerService()
    publisher_service = AmazonPublisherService()
    SERVICES_AVAILABLE = True
    logger.info("✅ Amazon SEO+Price services initialized")
except Exception as e:
    logger.warning(f"⚠️ Amazon SEO+Price services not available: {e}")
    scraping_service = None
    seo_optimizer = None
    price_optimizer = None
    publisher_service = None
    SERVICES_AVAILABLE = False

@amazon_seo_price_router.get("/scraping/{asin}")
async def scrape_amazon_product(
    asin: str,
    marketplace: str = "FR",
    token: str = Depends(security)
):
    """
    Scraper SEO + prix réels Amazon pour un ASIN
    
    Args:
        asin: Amazon Standard Identification Number
        marketplace: Marketplace (FR, DE, UK, US, IT, ES)
    
    Returns:
        Données SEO et prix scrapées
    """
    try:
        # Vérification des services
        if not SERVICES_AVAILABLE or not scraping_service:
            raise HTTPException(
                status_code=503, 
                detail="Amazon SEO+Price services not available. Check environment configuration."
            )
            
        # Vérification JWT
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        logger.info(f"🔍 Scraping request for ASIN {asin} from user {user_id}")
        
        # Scraper les données
        scraped_data = await scraping_service.scrape_product_seo_and_price(
            asin=asin,
            marketplace=marketplace
        )
        
        # Enrichir avec métadonnées utilisateur
        scraped_data.update({
            'user_id': user_id,
            'request_timestamp': datetime.utcnow().isoformat(),
            'api_version': 'v3.0'
        })
        
        return {
            'success': True,
            'data': scraped_data,
            'asin': asin,
            'marketplace': marketplace
        }
        
    except Exception as e:
        logger.error(f"❌ Scraping failed for ASIN {asin}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@amazon_seo_price_router.get("/scraping/competitors/{search_query}")
async def scrape_competitor_prices(
    search_query: str,
    marketplace: str = "FR",
    max_results: int = 5,
    token: str = Depends(security)
):
    """
    Scraper les prix des concurrents pour une recherche
    
    Args:
        search_query: Terme de recherche
        marketplace: Marketplace Amazon
        max_results: Nombre maximum de résultats
    
    Returns:
        Prix des concurrents trouvés
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        logger.info(f"🔍 Competitor scraping for '{search_query}' from user {user_id}")
        
        # Scraper les concurrents
        competitor_data = await scraping_service.scrape_competitor_prices(
            search_query=search_query,
            marketplace=marketplace,
            max_results=min(max_results, 10)  # Limiter à 10 max
        )
        
        return {
            'success': True,
            'data': competitor_data,
            'search_query': search_query,
            'marketplace': marketplace,
            'results_count': len(competitor_data),
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Competitor scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Competitor scraping failed: {str(e)}")

@amazon_seo_price_router.post("/seo/optimize")
async def optimize_seo_content(
    request_data: Dict[str, Any],
    token: str = Depends(security)
):
    """
    Générer SEO optimisé avec IA depuis données scrapées
    
    Request Body:
        scraped_data: Données scrapées Amazon
        target_keywords: Mots-clés cibles (optionnel)
        optimization_goals: Objectifs d'optimisation (optionnel)
    
    Returns:
        SEO optimisé conforme Amazon A9/A10
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        # Extraire les données de la requête
        scraped_data = request_data.get('scraped_data', {})
        target_keywords = request_data.get('target_keywords', [])
        optimization_goals = request_data.get('optimization_goals', {})
        
        if not scraped_data:
            raise HTTPException(status_code=400, detail="scraped_data is required")
        
        logger.info(f"🚀 SEO optimization request from user {user_id}")
        
        # Optimiser le SEO
        optimization_result = await seo_optimizer.optimize_seo_from_scraped_data(
            scraped_data=scraped_data,
            target_keywords=target_keywords,
            optimization_goals=optimization_goals
        )
        
        # Enrichir avec métadonnées utilisateur
        optimization_result.update({
            'user_id': user_id,
            'request_timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'optimization_result': optimization_result,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ SEO optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SEO optimization failed: {str(e)}")

@amazon_seo_price_router.post("/seo/variants")
async def generate_seo_variants(
    request_data: Dict[str, Any],
    token: str = Depends(security)
):
    """
    Générer plusieurs variantes SEO pour A/B testing
    
    Request Body:
        base_seo: SEO de base
        variant_count: Nombre de variantes (défaut: 3)
    
    Returns:
        Liste de variantes SEO
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        base_seo = request_data.get('base_seo', {})
        variant_count = request_data.get('variant_count', 3)
        
        if not base_seo:
            raise HTTPException(status_code=400, detail="base_seo is required")
        
        logger.info(f"🔄 SEO variants generation from user {user_id}")
        
        # Générer les variantes
        variants = await seo_optimizer.generate_seo_variants(
            base_seo=base_seo,
            variant_count=min(variant_count, 5)  # Max 5 variantes
        )
        
        return {
            'success': True,
            'variants': variants,
            'base_seo': base_seo,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ SEO variants generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SEO variants generation failed: {str(e)}")

@amazon_seo_price_router.post("/price/optimize")
async def optimize_product_price(
    request_data: Dict[str, Any],
    token: str = Depends(security)
):
    """
    Calculer prix recommandé basé sur concurrence et règles
    
    Request Body:
        product_data: Données du produit (coût, prix actuel, etc.)
        competitor_prices: Prix des concurrents
        pricing_rules: Règles de pricing (optionnel)
        target_marketplace: Marketplace cible
    
    Returns:
        Prix optimisé avec métadonnées et justification
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        product_data = request_data.get('product_data', {})
        competitor_prices = request_data.get('competitor_prices', [])
        pricing_rules = request_data.get('pricing_rules')
        target_marketplace = request_data.get('target_marketplace', 'FR')
        
        if not product_data:
            raise HTTPException(status_code=400, detail="product_data is required")
        
        logger.info(f"💰 Price optimization request from user {user_id}")
        
        # Optimiser le prix
        price_optimization = await price_optimizer.optimize_price_from_market_data(
            product_data=product_data,
            competitor_prices=competitor_prices,
            pricing_rules=pricing_rules,
            target_marketplace=target_marketplace
        )
        
        # Enrichir avec métadonnées utilisateur
        price_optimization.update({
            'user_id': user_id,
            'request_timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'price_optimization': price_optimization,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Price optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Price optimization failed: {str(e)}")

@amazon_seo_price_router.post("/price/validate")
async def validate_price_rules(
    request_data: Dict[str, Any],
    token: str = Depends(security)
):
    """
    Valider un prix contre les règles définies
    
    Request Body:
        price: Prix à valider
        product_data: Données du produit
        rules: Règles de validation (optionnel)
    
    Returns:
        Résultat de validation avec erreurs/warnings
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        price = request_data.get('price')
        product_data = request_data.get('product_data', {})
        rules = request_data.get('rules')
        
        if price is None:
            raise HTTPException(status_code=400, detail="price is required")
        
        logger.info(f"✅ Price validation request from user {user_id}")
        
        # Valider le prix
        validation_result = await price_optimizer.validate_price_rules(
            price=price,
            product_data=product_data,
            rules=rules
        )
        
        return {
            'success': True,
            'validation': validation_result,
            'price': price,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Price validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Price validation failed: {str(e)}")

@amazon_seo_price_router.post("/publish")
async def publish_seo_and_price_updates(
    request_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
):
    """
    Publier mises à jour SEO + prix via Amazon SP-API
    
    Request Body:
        marketplace_id: ID marketplace Amazon
        updates: Liste des mises à jour à appliquer
        update_type: Type de mise à jour (seo_only, price_only, full_update)
        validation_required: Validation obligatoire (défaut: true)
        async_mode: Mode asynchrone (défaut: false)
    
    Returns:
        Résultats de publication ou ID de session si async
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        marketplace_id = request_data.get('marketplace_id')
        updates = request_data.get('updates', [])
        update_type = request_data.get('update_type', 'full_update')
        validation_required = request_data.get('validation_required', True)
        async_mode = request_data.get('async_mode', False)
        
        if not marketplace_id:
            raise HTTPException(status_code=400, detail="marketplace_id is required")
        if not updates:
            raise HTTPException(status_code=400, detail="updates list is required")
        
        logger.info(f"🚀 Publication request from user {user_id}: {len(updates)} updates")
        
        if async_mode:
            # Mode asynchrone - démarrer en background
            session_id = f"pub_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            background_tasks.add_task(
                publisher_service.publish_seo_and_price_updates,
                user_id=user_id,
                marketplace_id=marketplace_id,
                updates=updates,
                update_type=update_type,
                validation_required=validation_required
            )
            
            return {
                'success': True,
                'async_mode': True,
                'session_id': session_id,
                'message': 'Publication started in background',
                'user_id': user_id
            }
        else:
            # Mode synchrone
            publication_result = await publisher_service.publish_seo_and_price_updates(
                user_id=user_id,
                marketplace_id=marketplace_id,
                updates=updates,
                update_type=update_type,
                validation_required=validation_required
            )
            
            return {
                'success': publication_result.get('success', False),
                'async_mode': False,
                'publication_result': publication_result,
                'user_id': user_id
            }
        
    except Exception as e:
        logger.error(f"❌ Publication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Publication failed: {str(e)}")

@amazon_seo_price_router.get("/monitoring")
async def get_monitoring_data(
    session_id: Optional[str] = None,
    limit: int = 50,
    token: str = Depends(security)
):
    """
    Obtenir les logs des actions (scraping, optimisation, publication)
    
    Args:
        session_id: ID de session spécifique (optionnel)
        limit: Nombre d'entrées à retourner (max 100)
    
    Returns:
        Logs des actions avec filtres et métadonnées
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        logger.info(f"📊 Monitoring request from user {user_id}")
        
        # Limitation du nombre de résultats
        limit = min(limit, 100)
        
        # Ici on récupérerait les données depuis la base ou un système de monitoring
        # Pour l'instant, retour de données simulées
        
        monitoring_data = {
            'user_id': user_id,
            'session_filter': session_id,
            'total_entries': 0,
            'entries': [],
            'summary': {
                'scraping_operations': 0,
                'seo_optimizations': 0,
                'price_optimizations': 0,
                'publications': 0,
                'success_rate': 0
            },
            'last_24h_activity': {
                'operations_count': 0,
                'avg_response_time': 0,
                'error_rate': 0
            },
            'queried_at': datetime.utcnow().isoformat()
        }
        
        return {
            'success': True,
            'monitoring_data': monitoring_data
        }
        
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

@amazon_seo_price_router.get("/monitoring/session/{session_id}")
async def get_session_status(
    session_id: str,
    token: str = Depends(security)
):
    """
    Obtenir le statut d'une session de publication
    
    Args:
        session_id: ID de la session de publication
    
    Returns:
        Statut détaillé de la session
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        logger.info(f"📋 Session status request for {session_id} from user {user_id}")
        
        # Obtenir le statut de la session
        session_status = await publisher_service.get_publication_status(session_id)
        
        return {
            'success': True,
            'session_status': session_status,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Session status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session status failed: {str(e)}")

@amazon_seo_price_router.post("/monitoring/session/{session_id}/cancel")
async def cancel_publication_session(
    session_id: str,
    token: str = Depends(security)
):
    """
    Annuler une session de publication en cours
    
    Args:
        session_id: ID de la session à annuler
    
    Returns:
        Confirmation d'annulation
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        logger.info(f"❌ Publication cancellation for {session_id} from user {user_id}")
        
        # Annuler la publication
        cancellation_result = await publisher_service.cancel_publication(session_id)
        
        return {
            'success': True,
            'cancellation_result': cancellation_result,
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")

# Endpoints de test et validation

@amazon_seo_price_router.get("/health/phase3")
async def health_check_phase3():
    """
    Health check pour les services Phase 3
    """
    try:
        health_status = {
            'phase': 'Phase 3 - SEO + Prix Amazon',
            'services': {
                'scraping_service': 'healthy',
                'seo_optimizer': 'healthy', 
                'price_optimizer': 'healthy',
                'publisher_service': 'healthy'
            },
            'external_dependencies': {
                'amazon_sp_api': 'available',
                'openai_api': 'available' if seo_optimizer.openai_api_key else 'missing_key',
                'fx_api': 'available' if price_optimizer.fx_api_key else 'missing_key'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'success': True,
            'health': health_status
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

@amazon_seo_price_router.get("/config/phase3")
async def get_phase3_configuration(token: str = Depends(security)):
    """
    Obtenir la configuration Phase 3 pour l'utilisateur
    """
    try:
        user_payload = verify_jwt_token(token.credentials)
        user_id = user_payload.get('user_id')
        
        config = {
            'scraping': {
                'supported_marketplaces': ['FR', 'DE', 'UK', 'US', 'IT', 'ES'],
                'max_competitor_results': 10,
                'rate_limiting': {
                    'requests_per_minute': 30,
                    'burst_limit': 5
                }
            },
            'seo_optimization': {
                'ai_models_available': ['gpt-4-turbo-preview'],
                'max_variants': 5,
                'amazon_rules': seo_optimizer.amazon_rules
            },
            'price_optimization': {
                'supported_currencies': ['EUR', 'USD', 'GBP'],
                'pricing_strategies': ['competitive', 'premium', 'aggressive', 'value'],
                'default_margins': price_optimizer.default_config
            },
            'publication': {
                'supported_update_types': list(publisher_service.update_types.keys()),
                'batch_size': publisher_service.publication_config['batch_size'],
                'retry_policy': {
                    'max_attempts': publisher_service.publication_config['retry_attempts'],
                    'base_delay': publisher_service.publication_config['retry_delay_base']
                }
            },
            'user_id': user_id
        }
        
        return {
            'success': True,
            'configuration': config
        }
        
    except Exception as e:
        logger.error(f"❌ Configuration retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")