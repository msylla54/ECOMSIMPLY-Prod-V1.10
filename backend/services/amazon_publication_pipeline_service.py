"""
Amazon Publication Pipeline Service
Orchestrateur pour le pipeline complet : SEO optimisé + Prix réels + Publication Amazon

Author: ECOMSIMPLY
Date: 2025-01-01
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
import asyncio
from datetime import datetime
import uuid

# Services existants à importer
from services.amazon_seo_integration_service import AmazonSEOIntegrationService
from services.multi_country_scraping_service import MultiCountryScrapingService
from services.price_guards_service import PriceGuardsService
from services.amazon_publisher_service import AmazonPublisherService
from services.currency_conversion_service import CurrencyConversionService

logger = logging.getLogger(__name__)

class AmazonPublicationPipelineService:
    """
    Service principal pour orchestrer le pipeline complet :
    1. Génération SEO optimisé (A9/A10)
    2. Scraping prix multi-pays (PriceTruth)
    3. Validation prix + gardes-fou
    4. Publication automatique sur Amazon SP-API
    """
    
    def __init__(self, database=None):
        """Initialiser tous les services nécessaires"""
        self.seo_service = AmazonSEOIntegrationService()
        self.scraping_service = MultiCountryScrapingService()
        self.price_guards_service = PriceGuardsService()
        
        # Initialize publisher service only if database is provided
        if database is not None:
            self.publisher_service = AmazonPublisherService(database)
        else:
            self.publisher_service = None
            
        self.currency_service = CurrencyConversionService()
        
        logger.info("🚀 Amazon Publication Pipeline Service initialized")
    
    async def execute_full_pipeline(
        self,
        product_data: Dict[str, Any],
        user_config: Dict[str, Any],
        publication_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Exécuter le pipeline complet de génération → publication
        
        Args:
            product_data: Données produit de base
            user_config: Configuration utilisateur (market settings, preferences)
            publication_settings: Paramètres de publication (optionnel)
            
        Returns:
            Dict avec résultats complets du pipeline
        """
        pipeline_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        logger.info(f"🎯 Starting full publication pipeline [{pipeline_id}] for product: {product_data.get('product_name', 'Unknown')}")
        
        try:
            pipeline_result = {
                "pipeline_id": pipeline_id,
                "status": "in_progress",
                "start_time": start_time.isoformat(),
                "product_name": product_data.get('product_name'),
                "steps": {}
            }
            
            # ÉTAPE 1: Génération SEO optimisé A9/A10
            logger.info(f"📝 [{pipeline_id}] Step 1: Generating Amazon SEO A9/A10 optimized listing")
            seo_result = await self._generate_optimized_seo(product_data, user_config)
            pipeline_result["steps"]["seo_generation"] = seo_result
            
            if not seo_result["success"]:
                pipeline_result["status"] = "failed"
                pipeline_result["error"] = f"SEO generation failed: {seo_result.get('error', 'Unknown error')}"
                return pipeline_result
            
            # ÉTAPE 2: Scraping prix multi-pays (PriceTruth)
            logger.info(f"💰 [{pipeline_id}] Step 2: Multi-country price scraping (PriceTruth)")
            price_result = await self._get_real_prices(product_data, user_config)
            pipeline_result["steps"]["price_scraping"] = price_result
            
            if not price_result["success"]:
                pipeline_result["status"] = "failed"
                pipeline_result["error"] = f"Price scraping failed: {price_result.get('error', 'Unknown error')}"
                return pipeline_result
            
            # ÉTAPE 3: Validation prix + gardes-fou
            logger.info(f"⚖️ [{pipeline_id}] Step 3: Price validation and guards")
            price_validation = await self._validate_prices(price_result["data"], user_config)
            pipeline_result["steps"]["price_validation"] = price_validation
            
            if price_validation["status"] == "PENDING_REVIEW":
                pipeline_result["status"] = "pending_review"
                pipeline_result["reason"] = "Prices require manual review due to guards"
                return pipeline_result
            
            # ÉTAPE 4: Fusion SEO + Prix pour publication
            logger.info(f"🔗 [{pipeline_id}] Step 4: Merging SEO + Prices for publication")
            merged_listing = await self._merge_seo_and_prices(
                seo_result["data"], 
                price_validation["validated_price"], 
                user_config
            )
            pipeline_result["steps"]["listing_merge"] = merged_listing
            
            # ÉTAPE 5: Publication sur Amazon SP-API
            logger.info(f"🚀 [{pipeline_id}] Step 5: Publishing to Amazon SP-API")
            publication_result = await self._publish_to_amazon(
                merged_listing["listing"], 
                user_config, 
                publication_settings
            )
            pipeline_result["steps"]["amazon_publication"] = publication_result
            
            # Finaliser le pipeline
            pipeline_result["status"] = "completed" if publication_result["success"] else "failed"
            pipeline_result["end_time"] = datetime.now().isoformat()
            pipeline_result["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            if publication_result["success"]:
                pipeline_result["amazon_listing_id"] = publication_result.get("listing_id")
                pipeline_result["amazon_feed_id"] = publication_result.get("feed_id")
                logger.info(f"✅ [{pipeline_id}] Pipeline completed successfully - Amazon Feed ID: {pipeline_result.get('amazon_feed_id')}")
            else:
                pipeline_result["error"] = f"Amazon publication failed: {publication_result.get('error')}"
                logger.error(f"❌ [{pipeline_id}] Pipeline failed at publication step")
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"❌ [{pipeline_id}] Pipeline exception: {e}")
            pipeline_result["status"] = "failed"
            pipeline_result["error"] = f"Pipeline exception: {str(e)}"
            pipeline_result["end_time"] = datetime.now().isoformat()
            return pipeline_result
    
    async def _generate_optimized_seo(self, product_data: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Générer un listing SEO optimisé selon A9/A10"""
        try:
            # Utiliser le service SEO existant
            seo_result = await self.seo_service.generate_optimized_listing(product_data)
            
            return {
                "success": True,
                "data": seo_result,
                "message": "SEO listing generated successfully"
            }
            
        except Exception as e:
            logger.error(f"SEO generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate SEO listing"
            }
    
    async def _get_real_prices(self, product_data: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Récupérer les prix réels via scraping multi-pays"""
        try:
            # Extraire le nom du produit pour le scraping
            product_name = product_data.get('product_name', '')
            
            # Utiliser le service de scraping multi-pays existant
            scraping_result = await self.scraping_service.scrape_product_prices(
                product_name=product_name,
                country_code=user_config.get('country_code', 'FR'),
                currency_preference=user_config.get('currency_preference', 'EUR')
            )
            
            return {
                "success": True,
                "data": scraping_result,
                "message": f"Found {len(scraping_result.get('sources', []))} price sources"
            }
            
        except Exception as e:
            logger.error(f"Price scraping failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to scrape real prices"
            }
    
    async def _validate_prices(self, price_data: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Valider les prix avec les gardes-fou"""
        try:
            # Extraire le prix de référence
            reference_price = price_data.get('reference_price')
            if not reference_price:
                return {
                    "status": "REJECTED",
                    "reason": "No reference price found",
                    "validated_price": None
                }
            
            # Appliquer les gardes-fou
            validation_result = self.price_guards_service.validate_price(
                price=Decimal(str(reference_price)),
                user_settings=user_config
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Price validation failed: {e}")
            return {
                "status": "REJECTED",
                "reason": f"Validation error: {str(e)}",
                "validated_price": None
            }
    
    async def _merge_seo_and_prices(
        self, 
        seo_data: Dict[str, Any], 
        validated_price: Decimal, 
        user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fusionner les données SEO optimisées avec le prix validé"""
        try:
            # Récupérer le listing SEO
            listing = seo_data.get('listing', {})
            
            # Ajouter le prix validé au format Amazon
            listing['price'] = {
                'amount': float(validated_price),
                'currency': user_config.get('currency_preference', 'EUR')
            }
            
            # Ajouter les métadonnées de pipeline
            listing['pipeline_metadata'] = {
                'seo_optimized': True,
                'real_price_validated': True,
                'a9_a10_compliant': seo_data.get('validation', {}).get('status') == 'approved',
                'price_source': 'multi_country_scraping',
                'generation_timestamp': datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "listing": listing,
                "message": "SEO and price data merged successfully"
            }
            
        except Exception as e:
            logger.error(f"SEO/Price merge failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "listing": None
            }
    
    async def _publish_to_amazon(
        self, 
        listing_data: Dict[str, Any], 
        user_config: Dict[str, Any], 
        publication_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Publier le listing sur Amazon SP-API"""
        try:
            # Check if publisher service is available
            if not self.publisher_service:
                return {
                    "success": False,
                    "error": "Amazon publisher service not initialized - database required",
                    "feed_id": None,
                    "listing_id": None
                }
            
            # Utiliser le service de publication Amazon existant
            publication_result = await self.publisher_service.publish_listing(
                listing_data=listing_data,
                marketplace_ids=publication_settings.get('marketplace_ids', ['A13V1IB3VIYZZH']),  # Amazon.fr par défaut
                user_credentials=user_config.get('amazon_credentials')
            )
            
            return publication_result
            
        except Exception as e:
            logger.error(f"Amazon publication failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "feed_id": None,
                "listing_id": None
            }
    
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Récupérer le statut d'un pipeline en cours"""
        # TODO: Implémenter un système de cache/DB pour suivre les pipelines
        # Pour l'instant, retourner un statut générique
        return {
            "pipeline_id": pipeline_id,
            "status": "unknown",
            "message": "Pipeline status tracking not yet implemented"
        }
    
    async def validate_pipeline_prerequisites(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Valider que tous les prérequis sont présents pour exécuter le pipeline"""
        prerequisites = {
            "amazon_connection": False,
            "market_settings": False,
            "subscription_valid": False,
            "price_guards_configured": False
        }
        
        errors = []
        
        # Vérifier la connexion Amazon
        if not user_config.get('amazon_credentials'):
            errors.append("Amazon SP-API connection required")
        else:
            prerequisites["amazon_connection"] = True
        
        # Vérifier les paramètres de marché
        if user_config.get('country_code') and user_config.get('currency_preference'):
            prerequisites["market_settings"] = True
        else:
            errors.append("Market settings (country/currency) required")
        
        # Vérifier l'abonnement (Premium pour publication automatique)
        if user_config.get('subscription_plan') in ['premium', 'pro']:
            prerequisites["subscription_valid"] = True
        else:
            errors.append("Premium or Pro subscription required for automatic publication")
        
        # Vérifier les gardes-fou prix
        if user_config.get('price_guards'):
            prerequisites["price_guards_configured"] = True
        else:
            errors.append("Price guards configuration recommended")
        
        return {
            "valid": len(errors) == 0,
            "prerequisites": prerequisites,
            "errors": errors,
            "message": "All prerequisites met" if len(errors) == 0 else f"{len(errors)} prerequisites missing"
        }


class PipelineMonitor:
    """Moniteur pour suivre les pipelines de publication"""
    
    def __init__(self):
        self.active_pipelines = {}
    
    def track_pipeline(self, pipeline_id: str, pipeline_data: Dict[str, Any]):
        """Suivre un pipeline actif"""
        self.active_pipelines[pipeline_id] = {
            **pipeline_data,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Récupérer les statistiques des pipelines"""
        return {
            "total_pipelines": len(self.active_pipelines),
            "active_count": len([p for p in self.active_pipelines.values() if p.get('status') == 'in_progress']),
            "completed_count": len([p for p in self.active_pipelines.values() if p.get('status') == 'completed']),
            "failed_count": len([p for p in self.active_pipelines.values() if p.get('status') == 'failed'])
        }