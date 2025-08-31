# Amazon SP-API Publisher avec orchestrateur et ProductDTO - Conforme Bloc 2 Phase 2
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from dataclasses import dataclass
from enum import Enum

from models.amazon_spapi import AmazonConnection, ConnectionStatus, SPAPIRegion
from services.amazon_connection_service import AmazonConnectionService
from services.amazon_seo_service import AmazonSEORules

logger = logging.getLogger(__name__)

class PublicationChannel(str, Enum):
    """Canaux de publication supportés"""
    AMAZON = "amazon"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    PRESTASHOP = "prestashop"

@dataclass
class ProductDTO:
    """Data Transfer Object pour produits - Format unifié"""
    # Identifiants
    product_id: str
    sku: str
    
    # Informations de base
    title: str
    brand: str
    description: str
    
    # Contenu structuré
    bullet_points: List[str]
    key_features: List[str]
    benefits: List[str]
    
    # Informations commerciales
    price: float
    currency: str = "EUR"
    stock_quantity: int = 1
    condition: str = "new"
    
    # Identifiants produit
    ean: Optional[str] = None
    upc: Optional[str] = None
    gtin: Optional[str] = None
    mpn: Optional[str] = None
    
    # Médias
    images: List[Dict[str, Any]] = None
    
    # Métadonnées
    category: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        """Initialisation post-création"""
        if self.images is None:
            self.images = []
        if self.tags is None:
            self.tags = []
        if not self.bullet_points:
            self.bullet_points = []

class AmazonPublicationResult:
    """Résultat de publication Amazon enrichi avec feedId"""
    def __init__(self, success: bool, listing_id: Optional[str] = None, 
                 feed_id: Optional[str] = None, submission_id: Optional[str] = None,
                 errors: List[str] = None, warnings: List[str] = None,
                 seo_score: float = 0.0):
        self.success = success
        self.listing_id = listing_id
        self.feed_id = feed_id  # ID du feed Amazon pour suivi
        self.submission_id = submission_id  # ID de soumission SP-API
        self.errors = errors or []
        self.warnings = warnings or []
        self.seo_score = seo_score
        self.published_at = datetime.utcnow()
        self.channel = PublicationChannel.AMAZON

class SPAPIRetryManager:
    """Gestionnaire de retry/backoff pour quotas SP-API"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_factor = 2.0
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Exécute une fonction avec retry automatique sur quotas"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                
                # Vérifier si c'est un problème de quota (429 ou 503)
                if e.response.status_code in [429, 503]:
                    if attempt < self.max_retries:
                        # Calculer délai avec backoff exponentiel
                        delay = min(
                            self.base_delay * (self.backoff_factor ** attempt),
                            self.max_delay
                        )
                        
                        logger.warning(f"Quota SP-API atteint, retry dans {delay}s (tentative {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                
                # Si ce n'est pas un problème de quota, ne pas retry
                raise
                
            except Exception as e:
                last_exception = e
                # Pour les autres erreurs, ne pas retry
                raise
        
        # Si toutes les tentatives échouent
        logger.error(f"Échec après {self.max_retries + 1} tentatives")
        raise last_exception

class AmazonSPAPIPublisher:
    """
    Publisher Amazon SP-API conforme Bloc 2 Phase 2
    
    Fonctionnalités:
    - Utilise connexion utilisateur courant (Phase 1)
    - Support Listings Items / Feeds
    - Gestion erreurs 412 PRECONDITION_REQUIRED
    - Retry/backoff automatique pour quotas
    - Stockage feedId pour suivi
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """Initialise le publisher Amazon"""
        self.db = database
        self.connection_service = AmazonConnectionService(database)
        self.seo_service = AmazonSEORules()
        self.retry_manager = SPAPIRetryManager()
        
        # Configuration SP-API par région
        self._spapi_endpoints = {
            SPAPIRegion.EU: "https://sellingpartnerapi-eu.amazon.com",
            SPAPIRegion.NA: "https://sellingpartnerapi-na.amazon.com",
            SPAPIRegion.FE: "https://sellingpartnerapi-fe.amazon.com"
        }
        
        logger.info("✅ Amazon SP-API Publisher initialized")
    
    async def publish_product(
        self, 
        user_id: str, 
        product_dto: ProductDTO,
        marketplace_id: str,
        use_images: bool = True
    ) -> AmazonPublicationResult:
        """
        Publie un produit Amazon via SP-API
        
        Args:
            user_id: Identifiant utilisateur
            product_dto: Données produit au format unifié  
            marketplace_id: Marketplace Amazon cible
            use_images: Inclure les images dans la publication
            
        Returns:
            AmazonPublicationResult avec feedId pour suivi
            
        Raises:
            HTTPException(412): Si connexion Amazon absente (PRECONDITION_REQUIRED)
        """
        try:
            logger.info(f"📤 Publication Amazon pour user {user_id[:8]}*** produit {product_dto.sku}")
            
            # 1. Vérifier connexion Amazon (Erreur 412 si absente)
            connection = await self.connection_service.get_active_connection(
                user_id=user_id,
                marketplace_id=marketplace_id
            )
            
            if not connection or connection.status != ConnectionStatus.ACTIVE:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail="Connexion Amazon requise. Veuillez vous connecter à Amazon avant de publier."
                )
            
            # 2. Obtenir access token valide
            access_token = await self.connection_service.get_valid_access_token(connection)
            if not access_token:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail="Token Amazon invalide. Veuillez reconnecter votre compte Amazon."
                )
            
            # 3. Mapper ProductDTO vers payload Amazon
            amazon_payload = self._map_product_dto_to_amazon(product_dto, marketplace_id, use_images)
            
            # 4. Optimiser SEO Amazon
            optimized_payload = await self._apply_amazon_seo(amazon_payload)
            
            # 5. Publication via SP-API avec retry automatique
            result = await self.retry_manager.execute_with_retry(
                self._submit_to_spapi,
                connection=connection,
                access_token=access_token,
                payload=optimized_payload,
                marketplace_id=marketplace_id
            )
            
            # 6. Sauvegarder résultat avec feedId
            await self._save_publication_record(user_id, connection.id, product_dto, result)
            
            logger.info(f"✅ Publication Amazon terminée - FeedId: {result.feed_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur publication Amazon: {str(e)}")
            return AmazonPublicationResult(
                success=False,
                errors=[f"Erreur publication: {str(e)}"]
            )
    
    def _map_product_dto_to_amazon(
        self, 
        product_dto: ProductDTO, 
        marketplace_id: str,
        use_images: bool
    ) -> Dict[str, Any]:
        """
        Mappe ProductDTO vers format Amazon SP-API
        
        Args:
            product_dto: Données produit format unifié
            marketplace_id: Marketplace Amazon
            use_images: Inclure les images
            
        Returns:
            Payload Amazon conforme SP-API
        """
        try:
            # Langue selon marketplace
            language_map = {
                'A13V1IB3VIYZZH': 'fr-FR',  # France
                'A1PA6795UKMFR9': 'de-DE',  # Allemagne
                'ATVPDKIKX0DER': 'en-US',   # États-Unis
                'A1F83G8C2ARO7P': 'en-GB'   # Royaume-Uni
            }
            language = language_map.get(marketplace_id, 'fr-FR')
            
            # Construction payload Amazon Listings Items API
            payload = {
                "productType": "PRODUCT",
                "requirements": "LISTING", 
                "attributes": {
                    # Titre
                    "item_name": [{
                        "value": product_dto.title,
                        "language_tag": language,
                        "marketplace_id": marketplace_id
                    }],
                    
                    # Marque
                    "brand": [{
                        "value": product_dto.brand,
                        "marketplace_id": marketplace_id
                    }],
                    
                    # Description
                    "product_description": [{
                        "value": product_dto.description,
                        "language_tag": language,
                        "marketplace_id": marketplace_id
                    }],
                    
                    # État
                    "condition_type": [{
                        "value": product_dto.condition.upper(),
                        "marketplace_id": marketplace_id
                    }],
                    
                    # Prix
                    "list_price": [{
                        "value": {
                            "Amount": product_dto.price,
                            "CurrencyCode": product_dto.currency
                        },
                        "marketplace_id": marketplace_id
                    }],
                    
                    # Stock
                    "fulfillment_availability": [{
                        "fulfillment_channel_code": "DEFAULT",
                        "quantity": product_dto.stock_quantity,
                        "marketplace_id": marketplace_id
                    }]
                }
            }
            
            # Ajouter bullet points si disponibles
            if product_dto.bullet_points:
                payload["attributes"]["bullet_point"] = [
                    {
                        "value": bullet,
                        "language_tag": language,
                        "marketplace_id": marketplace_id
                    }
                    for bullet in product_dto.bullet_points[:5]  # Max 5 bullets
                ]
            
            # Ajouter identifiants produit
            if product_dto.ean:
                payload["attributes"]["externally_assigned_product_identifier"] = [{
                    "value": {
                        "type": "EAN",
                        "value": product_dto.ean
                    },
                    "marketplace_id": marketplace_id
                }]
            elif product_dto.upc:
                payload["attributes"]["externally_assigned_product_identifier"] = [{
                    "value": {
                        "type": "UPC", 
                        "value": product_dto.upc
                    },
                    "marketplace_id": marketplace_id
                }]
            elif product_dto.gtin:
                payload["attributes"]["externally_assigned_product_identifier"] = [{
                    "value": {
                        "type": "GTIN",
                        "value": product_dto.gtin
                    },
                    "marketplace_id": marketplace_id
                }]
            
            # Ajouter images si demandées
            if use_images and product_dto.images:
                main_images = []
                other_images = []
                
                for image in product_dto.images:
                    image_data = {
                        "value": {
                            "link": image.get('url', ''),
                            "height": image.get('height', 1000),
                            "width": image.get('width', 1000)
                        },
                        "marketplace_id": marketplace_id
                    }
                    
                    if image.get('is_main', False):
                        main_images.append(image_data)
                    else:
                        other_images.append(image_data)
                
                if main_images:
                    payload["attributes"]["main_product_image_locator"] = main_images
                if other_images:
                    payload["attributes"]["other_product_image_locator"] = other_images[:8]
            
            return payload
            
        except Exception as e:
            logger.error(f"❌ Erreur mapping ProductDTO: {str(e)}")
            raise
    
    async def _apply_amazon_seo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Applique les optimisations SEO Amazon au payload"""
        try:
            # Extraire les données pour optimisation
            product_data = {
                'product_name': payload["attributes"]["item_name"][0]["value"],
                'brand': payload["attributes"]["brand"][0]["value"],
                'description': payload["attributes"]["product_description"][0]["value"],
                'key_features': [bp["value"] for bp in payload["attributes"].get("bullet_point", [])],
                'category': 'general'
            }
            
            # Optimiser avec AmazonSEORules
            optimized_title, _ = self.seo_service.optimize_title(product_data)
            optimized_bullets, _ = self.seo_service.generate_bullet_points(product_data)
            optimized_desc, _ = self.seo_service.optimize_description(product_data)
            backend_keywords, _ = self.seo_service.generate_backend_keywords(product_data)
            
            # Appliquer optimisations
            payload["attributes"]["item_name"][0]["value"] = optimized_title
            
            if optimized_bullets:
                marketplace_id = payload["attributes"]["item_name"][0]["marketplace_id"]
                language = payload["attributes"]["item_name"][0]["language_tag"]
                
                payload["attributes"]["bullet_point"] = [
                    {
                        "value": bullet,
                        "language_tag": language,
                        "marketplace_id": marketplace_id
                    }
                    for bullet in optimized_bullets
                ]
            
            payload["attributes"]["product_description"][0]["value"] = optimized_desc
            
            # Ajouter mots-clés backend
            if backend_keywords:
                marketplace_id = payload["attributes"]["item_name"][0]["marketplace_id"]
                language = payload["attributes"]["item_name"][0]["language_tag"]
                
                payload["attributes"]["generic_keyword"] = [{
                    "value": backend_keywords,
                    "language_tag": language,
                    "marketplace_id": marketplace_id
                }]
            
            return payload
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation SEO: {str(e)}")
            return payload  # Retourner payload original en cas d'erreur
    
    async def _submit_to_spapi(
        self,
        connection: AmazonConnection,
        access_token: str,
        payload: Dict[str, Any],
        marketplace_id: str
    ) -> AmazonPublicationResult:
        """Soumet le listing à Amazon SP-API avec gestion des feedId"""
        try:
            spapi_endpoint = self._spapi_endpoints[connection.region]
            
            # Headers SP-API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json',
                'User-Agent': 'ECOMSIMPLY-Publisher/1.0'
            }
            
            # URL Listings Items API
            sku = payload.get("sku", f"ECOM-{int(datetime.utcnow().timestamp())}")
            url = f"{spapi_endpoint}/listings/2021-08-01/items/{connection.seller_id}/{sku}"
            
            # Soumission avec timeout
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.put(url, json=payload, headers=headers)
            
            # Traitement réponse
            if response.status_code in [200, 202]:
                response_data = response.json()
                submission_id = response_data.get('submissionId')
                
                # Extraire feedId si présent dans la réponse
                feed_id = response_data.get('feedId') or response_data.get('feedDocumentId')
                
                logger.info(f"✅ Soumission Amazon acceptée: {submission_id}")
                
                return AmazonPublicationResult(
                    success=True,
                    listing_id=sku,
                    feed_id=feed_id,
                    submission_id=submission_id
                )
            
            else:
                # Gestion erreurs Amazon
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                errors = self._parse_amazon_errors(error_data)
                
                logger.error(f"❌ Échec soumission Amazon: {response.status_code}")
                
                return AmazonPublicationResult(
                    success=False,
                    errors=errors
                )
                
        except httpx.TimeoutException:
            return AmazonPublicationResult(
                success=False,
                errors=["Timeout lors de la soumission à Amazon"]
            )
        except Exception as e:
            logger.error(f"❌ Erreur soumission SP-API: {str(e)}")
            return AmazonPublicationResult(
                success=False,
                errors=[f"Erreur SP-API: {str(e)}"]
            )
    
    def _parse_amazon_errors(self, error_data: Dict[str, Any]) -> List[str]:
        """Parse les erreurs Amazon SP-API"""
        errors = []
        
        if 'errors' in error_data:
            for error in error_data['errors']:
                code = error.get('code', 'UNKNOWN')
                message = error.get('message', 'Erreur inconnue')
                errors.append(f"{code}: {message}")
        
        if not errors:
            errors.append("Erreur Amazon non spécifiée")
        
        return errors
    
    async def _save_publication_record(
        self,
        user_id: str,
        connection_id: str,
        product_dto: ProductDTO,
        result: AmazonPublicationResult
    ):
        """Sauvegarde l'enregistrement de publication avec feedId"""
        try:
            publication_record = {
                "user_id": user_id,
                "connection_id": connection_id,
                "channel": PublicationChannel.AMAZON,
                "product_sku": product_dto.sku,
                "product_title": product_dto.title,
                "success": result.success,
                "listing_id": result.listing_id,
                "feed_id": result.feed_id,  # Stockage du feedId Amazon
                "submission_id": result.submission_id,
                "errors": result.errors,
                "warnings": result.warnings,
                "published_at": result.published_at,
                "marketplace_id": getattr(result, 'marketplace_id', ''),
                "metadata": {
                    "price": product_dto.price,
                    "currency": product_dto.currency,
                    "stock": product_dto.stock_quantity
                }
            }
            
            await self.db.amazon_publications.insert_one(publication_record)
            
            logger.info(f"📁 Publication record sauvé avec feedId: {result.feed_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde publication: {str(e)}")

class PublicationOrchestrator:
    """
    Orchestrateur de publication multi-canal
    
    Gère la publication vers différents canaux (Amazon, Shopify, etc.)
    avec mapping uniforme ProductDTO
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.publishers = {
            PublicationChannel.AMAZON: AmazonSPAPIPublisher(database)
        }
        
        logger.info("✅ Publication Orchestrator initialized")
    
    async def publish_to_channel(
        self,
        channel: PublicationChannel,
        user_id: str,
        product_dto: ProductDTO,
        channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publie un produit vers un canal spécifique
        
        Args:
            channel: Canal de publication (amazon, shopify, etc.)
            user_id: Identifiant utilisateur
            product_dto: Données produit format unifié
            channel_config: Configuration spécifique au canal
            
        Returns:
            Résultat de publication unifié
        """
        try:
            if channel not in self.publishers:
                raise ValueError(f"Canal {channel} non supporté")
            
            publisher = self.publishers[channel]
            
            if channel == PublicationChannel.AMAZON:
                marketplace_id = channel_config.get('marketplace_id', 'A13V1IB3VIYZZH')
                use_images = channel_config.get('use_images', True)
                
                result = await publisher.publish_product(
                    user_id=user_id,
                    product_dto=product_dto,
                    marketplace_id=marketplace_id,
                    use_images=use_images
                )
                
                return {
                    "success": result.success,
                    "channel": channel,
                    "listing_id": result.listing_id,
                    "feed_id": result.feed_id,
                    "submission_id": result.submission_id,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "published_at": result.published_at.isoformat()
                }
            
            # Autres canaux à implémenter...
            else:
                raise NotImplementedError(f"Publisher {channel} pas encore implémenté")
                
        except Exception as e:
            logger.error(f"❌ Erreur orchestrateur publication: {str(e)}")
            return {
                "success": False,
                "channel": channel,
                "errors": [str(e)]
            }