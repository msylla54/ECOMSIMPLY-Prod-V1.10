# Amazon SP-API Publisher - Intégration avec l'orchestrateur générique
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from services.amazon_publisher_service import AmazonPublisherService
from services.amazon_connection_service import AmazonConnectionService
from models.amazon_publishing import AmazonPublishingResult

logger = logging.getLogger(__name__)

class AmazonSPAPIPublisher:
    """
    Publisher Amazon SP-API pour l'orchestrateur générique
    
    Implémente l'interface IPublisher avec support:
    - Mapping ProductDTO vers Amazon Listing
    - Gestion des erreurs HTTP 412 (connexion manquante)
    - Retry/backoff pour les quotas SP-API
    - Stockage du feedId pour suivi
    """
    
    def __init__(self, database, connection_service: Optional[AmazonConnectionService] = None):
        """
        Initialise le publisher Amazon
        
        Args:
            database: Instance de base de données
            connection_service: Service de connexion Amazon (optionnel)
        """
        self.db = database
        self.connection_service = connection_service or AmazonConnectionService(database)
        self.publisher_service = AmazonPublisherService(
            database=database,
            connection_service=self.connection_service
        )
        
        logger.info("✅ Amazon SP-API Publisher initialized")
    
    async def publish(
        self, 
        user_id: str, 
        product_dto: Dict[str, Any], 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publication d'un produit via Amazon SP-API
        
        Args:
            user_id: ID utilisateur ECOMSIMPLY
            product_dto: Données produit standardisées (ProductDTO)
            options: Options de publication (marketplace_id, etc.)
            
        Returns:
            Résultat de publication avec feedId si succès
        """
        try:
            logger.info(f"📤 Amazon SP-API publication pour user {user_id[:8]}***")
            
            # Options par défaut
            options = options or {}
            marketplace_id = options.get('marketplace_id', 'A13V1IB3VIYZZH')  # Amazon France par défaut
            max_retries = options.get('max_retries', 3)
            
            # Vérification de connexion Amazon active
            connection = await self.connection_service.get_active_connection(
                user_id=user_id,
                marketplace_id=marketplace_id
            )
            
            if not connection:
                logger.warning(f"❌ Aucune connexion Amazon active pour user {user_id[:8]}***")
                return {
                    "success": False,
                    "channel": "amazon",
                    "error_code": "HTTP_412",
                    "error": "Aucune connexion Amazon active. Connectez-vous d'abord à Amazon Seller Central.",
                    "needs_connection": True,
                    "marketplace_id": marketplace_id
                }
            
            # Mapping ProductDTO vers Amazon Listing
            amazon_product_data = await self._map_product_dto_to_amazon(product_dto, options)
            
            # Publication avec retry/backoff
            result = await self._publish_with_retry(
                user_id=user_id,
                product_data=amazon_product_data,
                marketplace_id=marketplace_id,
                max_retries=max_retries
            )
            
            # Formater la réponse pour l'orchestrateur
            response = {
                "success": result.success,
                "channel": "amazon",
                "marketplace_id": marketplace_id,
                "connection_id": connection.id
            }
            
            if result.success:
                # Stocker le feedId pour suivi
                if result.listing_id:
                    await self._store_feed_id(user_id, result.listing_id, marketplace_id)
                
                response.update({
                    "listing_id": result.listing_id,
                    "feed_id": result.listing_id,  # Amazon utilise submission_id comme feedId
                    "seo_score": result.seo_score,
                    "published_at": result.published_at
                })
            else:
                response.update({
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "error_code": self._classify_error_code(result.errors)
                })
            
            logger.info(f"✅ Amazon publication terminée - Succès: {result.success}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur publication Amazon: {str(e)}")
            return {
                "success": False,
                "channel": "amazon",
                "error_code": "INTERNAL_ERROR",
                "error": f"Erreur interne: {str(e)}"
            }
    
    async def _map_product_dto_to_amazon(
        self, 
        product_dto: Dict[str, Any], 
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mappe un ProductDTO vers les données Amazon
        
        Args:
            product_dto: Données produit standardisées
            options: Options de mapping
            
        Returns:
            Données produit formatées pour Amazon
        """
        try:
            # Mapping des champs standards
            amazon_data = {
                "product_name": product_dto.get("title", product_dto.get("name", "")),
                "brand": product_dto.get("brand", "Generic"),
                "description": product_dto.get("description", ""),
                "key_features": product_dto.get("features", []),
                "price": product_dto.get("price", 0.0),
                "currency": product_dto.get("currency", "EUR"),
                "category": product_dto.get("category", ""),
                "condition": product_dto.get("condition", "new"),
                "quantity": product_dto.get("stock", product_dto.get("quantity", 1))
            }
            
            # Mapping des identifiants produit
            if "identifiers" in product_dto:
                identifiers = product_dto["identifiers"]
                amazon_data.update({
                    "ean": identifiers.get("ean"),
                    "upc": identifiers.get("upc"),
                    "isbn": identifiers.get("isbn"),
                    "sku": identifiers.get("sku", f"ECOM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                })
            
            # Mapping des images
            if "images" in product_dto:
                amazon_images = []
                for i, image in enumerate(product_dto["images"]):
                    amazon_image = {
                        "url": image.get("url", ""),
                        "alt_text": image.get("alt_text", f"Image produit {i+1}"),
                        "is_main": i == 0,
                        "width": image.get("width", 1000),
                        "height": image.get("height", 1000)
                    }
                    amazon_images.append(amazon_image)
                
                amazon_data["images"] = amazon_images
            
            # Mapping des spécifications
            if "specifications" in product_dto:
                amazon_data["specifications"] = product_dto["specifications"]
            
            logger.info(f"🔄 ProductDTO mappé vers Amazon: {len(amazon_data)} champs")
            return amazon_data
            
        except Exception as e:
            logger.error(f"❌ Erreur mapping ProductDTO: {str(e)}")
            raise
    
    async def _publish_with_retry(
        self,
        user_id: str,
        product_data: Dict[str, Any],
        marketplace_id: str,
        max_retries: int = 3
    ) -> AmazonPublishingResult:
        """
        Publication avec retry/backoff pour gérer les quotas SP-API
        
        Args:
            user_id: ID utilisateur
            product_data: Données produit
            marketplace_id: Marketplace Amazon
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Résultat de publication Amazon
        """
        last_result = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🔄 Tentative {attempt + 1}/{max_retries + 1} de publication Amazon")
                
                # Tentative de publication
                result = await self.publisher_service.publish_to_amazon(
                    user_id=user_id,
                    product_data=product_data,
                    marketplace_id=marketplace_id
                )
                
                # Succès - retourner immédiatement
                if result.success:
                    logger.info(f"✅ Publication Amazon réussie à la tentative {attempt + 1}")
                    return result
                
                # Échec - vérifier si c'est une erreur de quota
                last_result = result
                
                if self._is_quota_error(result.errors):
                    if attempt < max_retries:
                        # Calculer le délai d'attente (exponential backoff)
                        delay = min(2 ** attempt, 60)  # Cap à 60 secondes
                        logger.info(f"⏳ Quota SP-API atteint, attente {delay}s avant retry...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Quota SP-API dépassé après {max_retries} tentatives")
                        break
                else:
                    # Erreur non liée au quota - pas de retry
                    logger.error(f"❌ Erreur non-quota, arrêt des tentatives: {result.errors}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Exception lors de la tentative {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    # Dernière tentative - créer un résultat d'erreur
                    last_result = AmazonPublishingResult(
                        success=False,
                        errors=[f"Exception après {max_retries} tentatives: {str(e)}"]
                    )
                else:
                    # Retry après exception
                    delay = min(2 ** attempt, 30)
                    await asyncio.sleep(delay)
        
        return last_result or AmazonPublishingResult(
            success=False,
            errors=["Échec de publication après toutes les tentatives"]
        )
    
    def _is_quota_error(self, errors: list) -> bool:
        """
        Détermine si l'erreur est liée aux quotas SP-API
        
        Args:
            errors: Liste des erreurs
            
        Returns:
            True si c'est une erreur de quota
        """
        quota_indicators = [
            "QuotaExceeded",
            "Throttled", 
            "TooManyRequests",
            "429",
            "rate limit",
            "quota exceeded"
        ]
        
        error_text = " ".join(errors).lower()
        return any(indicator.lower() in error_text for indicator in quota_indicators)
    
    def _classify_error_code(self, errors: list) -> str:
        """
        Classifie le type d'erreur pour l'orchestrateur
        
        Args:
            errors: Liste des erreurs
            
        Returns:
            Code d'erreur classifié
        """
        if not errors:
            return "UNKNOWN_ERROR"
        
        error_text = " ".join(errors).lower()
        
        if "quota" in error_text or "throttle" in error_text or "429" in error_text:
            return "QUOTA_ERROR"
        elif "unauthorized" in error_text or "401" in error_text:
            return "AUTH_ERROR"
        elif "forbidden" in error_text or "403" in error_text:
            return "PERMISSION_ERROR"
        elif "not found" in error_text or "404" in error_text:
            return "NOT_FOUND_ERROR"
        elif "invalid" in error_text or "validation" in error_text:
            return "VALIDATION_ERROR"
        elif "timeout" in error_text:
            return "TIMEOUT_ERROR"
        else:
            return "API_ERROR"
    
    async def _store_feed_id(self, user_id: str, feed_id: str, marketplace_id: str):
        """
        Stocke le feedId pour suivi des publications
        
        Args:
            user_id: ID utilisateur
            feed_id: ID du feed Amazon
            marketplace_id: Marketplace Amazon
        """
        try:
            feed_record = {
                "user_id": user_id,
                "feed_id": feed_id,
                "marketplace_id": marketplace_id,
                "channel": "amazon",
                "status": "submitted",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db.amazon_feeds.insert_one(feed_record)
            logger.info(f"📁 FeedId {feed_id} stocké pour user {user_id[:8]}***")
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage feedId: {str(e)}")
    
    async def get_publication_status(
        self, 
        user_id: str, 
        feed_id: str
    ) -> Dict[str, Any]:
        """
        Récupère le statut d'une publication via feedId
        
        Args:
            user_id: ID utilisateur
            feed_id: ID du feed Amazon
            
        Returns:
            Statut de la publication
        """
        try:
            # Récupérer le feed en base
            feed_record = await self.db.amazon_feeds.find_one({
                "user_id": user_id,
                "feed_id": feed_id
            })
            
            if not feed_record:
                return {"error": "Feed non trouvé"}
            
            # Récupérer le statut via le publisher service
            status = await self.publisher_service.get_amazon_listing_status(
                user_id=user_id,
                listing_id=feed_id,
                marketplace_id=feed_record["marketplace_id"]
            )
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération statut feed: {str(e)}")
            return {"error": f"Erreur: {str(e)}"}
    
    # Interface IPublisher compatibility
    
    async def can_publish(self, user_id: str, product_dto: Dict[str, Any]) -> bool:
        """
        Vérifie si l'utilisateur peut publier sur Amazon
        
        Args:
            user_id: ID utilisateur
            product_dto: Données produit
            
        Returns:
            True si la publication est possible
        """
        try:
            connection = await self.connection_service.get_active_connection(user_id)
            return connection is not None
        except:
            return False
    
    async def get_channel_info(self) -> Dict[str, Any]:
        """
        Informations sur le canal Amazon
        
        Returns:
            Métadonnées du canal
        """
        return {
            "channel": "amazon",
            "name": "Amazon Seller Central",
            "requires_connection": True,
            "supports_images": True,
            "supports_variations": True,
            "max_images": 9,
            "supported_marketplaces": [
                "A13V1IB3VIYZZH",  # France
                "A1PA6795UKMFR9",  # Germany  
                "ATVPDKIKX0DER",   # US
                "A1F83G8C2ARO7P"   # UK
            ]
        }