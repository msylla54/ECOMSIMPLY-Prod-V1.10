# Amazon Listing Publisher - Phase 2
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Import des modules Phase 1
from integrations.amazon.client import AmazonSPAPIClient
from integrations.amazon.auth import AmazonOAuthService

logger = logging.getLogger(__name__)

class AmazonListingPublisher:
    """
    Publisher de fiches produits Amazon via SP-API réelle
    Gère création + mise à jour (upsert) + gestion d'erreurs
    """
    
    def __init__(self):
        self.spapi_client = AmazonSPAPIClient()
        self.oauth_service = AmazonOAuthService()
        
        # Mapping des catégories vers les ProductTypes Amazon
        self.product_type_mapping = {
            'électronique': 'CONSUMER_ELECTRONICS',
            'maison': 'HOME',
            'jardin': 'LAWN_AND_GARDEN',
            'sport': 'SPORTING_GOODS',
            'cuisine': 'KITCHEN',
            'vêtements': 'CLOTHING',
            'beauté': 'BEAUTY',
            'livres': 'BOOKS',
            'jouets': 'TOYS_AND_GAMES',
            'auto': 'AUTOMOTIVE'
        }
        
        logger.info("✅ Amazon Listing Publisher initialized")
    
    async def publish_listing_to_amazon(self, product_data: Dict[str, Any], 
                                      seo_data: Dict[str, Any],
                                      connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publie une fiche produit sur Amazon via SP-API
        
        Args:
            product_data: Données du produit (brand, name, features, etc.)
            seo_data: Contenu SEO généré (title, bullets, description, keywords)
            connection_data: Données de connexion Amazon (tokens, seller_id, marketplace)
            
        Returns:
            Dict avec le résultat de publication (success/error + détails)
        """
        try:
            logger.info(f"📤 Publishing listing to Amazon: {product_data.get('product_name')}")
            
            # Validation des paramètres
            self._validate_publish_params(product_data, seo_data, connection_data)
            
            # Préparation des données pour SP-API
            sp_api_payload = await self._prepare_spapi_payload(product_data, seo_data)
            
            # Génération ou récupération du SKU
            sku = product_data.get('sku') or self._generate_sku(product_data)
            
            # Décryptage du refresh token
            refresh_token = self.oauth_service.decrypt_refresh_token(
                {
                    'encrypted_token': connection_data['encrypted_refresh_token'],
                    'nonce': connection_data['token_encryption_nonce']
                },
                connection_data['user_id']
            )
            
            # Obtenir un access token frais
            token_data = await self._refresh_access_token(refresh_token, connection_data['region'])
            
            # Publication via SP-API
            publication_result = await self._publish_via_spapi(
                sku=sku,
                payload=sp_api_payload,
                access_token=token_data['access_token'],
                seller_id=connection_data['seller_id'],
                marketplace_id=connection_data['marketplace_id']
            )
            
            # Formatage du résultat final
            result = {
                'publication_id': str(uuid.uuid4()),
                'published_at': datetime.utcnow().isoformat(),
                'sku': sku,
                'marketplace_id': connection_data['marketplace_id'],
                'status': publication_result['status'],
                'amazon_response': publication_result.get('response'),
                'errors': publication_result.get('errors', []),
                'warnings': publication_result.get('warnings', []),
                'listing_url': self._generate_listing_url(sku, connection_data['marketplace_id']) if publication_result['status'] == 'success' else None
            }
            
            if result['status'] == 'success':
                logger.info(f"✅ Listing published successfully - SKU: {sku}")
            else:
                logger.error(f"❌ Publication failed - SKU: {sku}, Errors: {result['errors']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Publication error: {str(e)}")
            return {
                'publication_id': f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'status': 'error',
                'errors': [f"Publication system error: {str(e)}"],
                'published_at': datetime.utcnow().isoformat()
            }
    
    async def update_listing_on_amazon(self, sku: str, updates: Dict[str, Any],
                                     connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une fiche existante sur Amazon
        
        Args:
            sku: SKU du produit à mettre à jour
            updates: Données à mettre à jour
            connection_data: Informations de connexion
            
        Returns:
            Résultat de la mise à jour
        """
        try:
            logger.info(f"📝 Updating Amazon listing: {sku}")
            
            # Décryptage du token
            refresh_token = self.oauth_service.decrypt_refresh_token(
                {
                    'encrypted_token': connection_data['encrypted_refresh_token'],
                    'nonce': connection_data['token_encryption_nonce']
                },
                connection_data['user_id']
            )
            
            # Access token frais
            token_data = await self._refresh_access_token(refresh_token, connection_data['region'])
            
            # Préparer les données de mise à jour
            update_payload = await self._prepare_update_payload(updates)
            
            # Mise à jour via SP-API
            update_result = await self._update_via_spapi(
                sku=sku,
                payload=update_payload,
                access_token=token_data['access_token'],
                seller_id=connection_data['seller_id'],
                marketplace_id=connection_data['marketplace_id']
            )
            
            logger.info(f"✅ Listing update completed - SKU: {sku}")
            return update_result
            
        except Exception as e:
            logger.error(f"❌ Update error: {str(e)}")
            return {
                'status': 'error',
                'errors': [f"Update failed: {str(e)}"]
            }
    
    async def check_listing_status(self, sku: str, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie le statut d'une fiche sur Amazon
        
        Args:
            sku: SKU du produit
            connection_data: Informations de connexion
            
        Returns:
            Statut de la fiche sur Amazon
        """
        try:
            logger.info(f"🔍 Checking listing status: {sku}")
            
            # Décryptage du token
            refresh_token = self.oauth_service.decrypt_refresh_token(
                {
                    'encrypted_token': connection_data['encrypted_refresh_token'],
                    'nonce': connection_data['token_encryption_nonce']
                },
                connection_data['user_id']
            )
            
            # Access token frais
            token_data = await self._refresh_access_token(refresh_token, connection_data['region'])
            
            # Vérification via SP-API
            status_result = await self.spapi_client.get_listings(
                access_token=token_data['access_token'],
                seller_id=connection_data['seller_id'],
                marketplace_id=connection_data['marketplace_id'],
                sku=sku
            )
            
            return {
                'sku': sku,
                'status': 'active' if status_result else 'not_found',
                'last_checked': datetime.utcnow().isoformat(),
                'amazon_data': status_result
            }
            
        except Exception as e:
            logger.error(f"❌ Status check error: {str(e)}")
            return {
                'sku': sku,
                'status': 'error',
                'error': str(e)
            }
    
    async def _prepare_spapi_payload(self, product_data: Dict[str, Any], 
                                   seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare le payload pour l'API SP-API selon le format officiel"""
        
        # Détermination du ProductType
        category = product_data.get('category', '').lower()
        product_type = self.product_type_mapping.get(category, 'CONSUMER_ELECTRONICS')
        
        # Construction du payload SP-API
        payload = {
            'productType': product_type,
            'requirements': 'LISTING',
            'attributes': {
                # Informations de base
                'item_name': [{
                    'value': seo_data.get('title', ''),
                    'language_tag': 'fr-FR'
                }],
                'brand': [{
                    'value': product_data.get('brand', ''),
                    'language_tag': 'fr-FR'
                }],
                'manufacturer': [{
                    'value': product_data.get('brand', ''),
                    'language_tag': 'fr-FR'
                }],
                
                # Bullet points
                'bullet_point': [
                    {
                        'value': bullet,
                        'language_tag': 'fr-FR'
                    }
                    for bullet in seo_data.get('bullet_points', [])
                ],
                
                # Description
                'product_description': [{
                    'value': seo_data.get('description', ''),
                    'language_tag': 'fr-FR'
                }],
                
                # Mots-clés backend
                'generic_keyword': [{
                    'value': seo_data.get('backend_keywords', ''),
                    'language_tag': 'fr-FR'
                }],
                
                # Prix si fourni
                'list_price': [{
                    'currency': 'EUR',
                    'amount': product_data.get('price', 0)
                }] if product_data.get('price') else [],
                
                # Conditions d'expédition
                'fulfillment_availability': [{
                    'fulfillment_channel_code': 'DEFAULT',
                    'quantity': 999,
                    'lead_time_to_ship_max_days': 2
                }]
            }
        }
        
        # Ajouter attributs spécifiques selon la catégorie
        if category == 'électronique':
            payload['attributes'].update({
                'battery_required': [{'value': False}],
                'safety_warning': [{'value': 'Aucun avertissement spécial', 'language_tag': 'fr-FR'}]
            })
        
        elif category == 'vêtements':
            payload['attributes'].update({
                'department_name': [{'value': 'Unisex-Adult'}],
                'size_name': [{'value': product_data.get('size', 'One Size')}] if product_data.get('size') else [],
                'color_name': [{'value': product_data.get('color', 'Multicolore')}] if product_data.get('color') else []
            })
        
        return payload
    
    async def _publish_via_spapi(self, sku: str, payload: Dict[str, Any],
                               access_token: str, seller_id: str, 
                               marketplace_id: str) -> Dict[str, Any]:
        """Effectue la publication réelle via SP-API"""
        try:
            # Utilisation de l'API Listings SP-API v2021-08-01
            result = await self.spapi_client.create_listing(
                access_token=access_token,
                seller_id=seller_id,
                marketplace_id=marketplace_id,
                sku=sku,
                product_data=payload
            )
            
            return {
                'status': 'success',
                'response': result,
                'sku': sku
            }
            
        except Exception as e:
            # Gestion des erreurs spécifiques Amazon
            error_message = str(e)
            
            if '400' in error_message:
                return {
                    'status': 'rejected',
                    'errors': ['Invalid product data - check required fields'],
                    'amazon_error': error_message
                }
            elif '403' in error_message:
                return {
                    'status': 'forbidden',
                    'errors': ['Insufficient permissions or invalid marketplace'],
                    'amazon_error': error_message
                }
            elif '429' in error_message:
                return {
                    'status': 'rate_limited',
                    'errors': ['Rate limit exceeded - retry later'],
                    'amazon_error': error_message
                }
            else:
                return {
                    'status': 'error',
                    'errors': [f'SP-API error: {error_message}'],
                    'amazon_error': error_message
                }
    
    async def _update_via_spapi(self, sku: str, payload: Dict[str, Any],
                              access_token: str, seller_id: str,
                              marketplace_id: str) -> Dict[str, Any]:
        """Met à jour via SP-API"""
        try:
            result = await self.spapi_client.make_authenticated_request(
                method='PATCH',
                path=f'/listings/2021-08-01/items/{sku}',
                access_token=access_token,
                seller_id=seller_id,
                marketplace_id=marketplace_id,
                json_data=payload
            )
            
            return {
                'status': 'success',
                'response': result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'errors': [f'Update failed: {str(e)}']
            }
    
    async def _prepare_update_payload(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare le payload pour une mise à jour"""
        # Convertir les updates en format SP-API
        update_payload = {
            'productType': updates.get('product_type', 'CONSUMER_ELECTRONICS'),
            'patches': []
        }
        
        # Mapper les champs à mettre à jour
        field_mapping = {
            'title': 'item_name',
            'price': 'list_price',
            'description': 'product_description',
            'bullets': 'bullet_point'
        }
        
        for field, sp_field in field_mapping.items():
            if field in updates:
                update_payload['patches'].append({
                    'op': 'replace',
                    'path': f'/attributes/{sp_field}',
                    'value': updates[field]
                })
        
        return update_payload
    
    async def _refresh_access_token(self, refresh_token: str, region: str) -> Dict[str, Any]:
        """Rafraîchit l'access token Amazon"""
        try:
            # Utiliser l'endpoint de refresh d'Amazon
            token_endpoint = self.oauth_service.oauth_endpoints[region]['token']
            
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.oauth_service.client_id,
                'client_secret': self.oauth_service.client_secret
            }
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(token_endpoint, data=token_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Token refresh failed: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {str(e)}")
            raise
    
    def _generate_sku(self, product_data: Dict[str, Any]) -> str:
        """Génère un SKU unique pour le produit"""
        brand = product_data.get('brand', 'NOBRAND')[:10].upper().replace(' ', '')
        product_name = product_data.get('product_name', 'PRODUCT')[:15].upper().replace(' ', '')
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
        
        return f"{brand}-{product_name}-{timestamp}"
    
    def _generate_listing_url(self, sku: str, marketplace_id: str) -> str:
        """Génère l'URL de la fiche sur Amazon"""
        domain_mapping = {
            'A13V1IB3VIYZZH': 'amazon.fr',
            'A1PA6795UKMFR9': 'amazon.de',
            'ATVPDKIKX0DER': 'amazon.com',
            'A1F83G8C2ARO7P': 'amazon.co.uk',
            'APJ6JRA9NG5V4': 'amazon.it',
            'A1RKKUPIHCS9HS': 'amazon.es'
        }
        
        domain = domain_mapping.get(marketplace_id, 'amazon.com')
        return f"https://{domain}/dp/{sku}"
    
    def _validate_publish_params(self, product_data: Dict[str, Any], 
                               seo_data: Dict[str, Any],
                               connection_data: Dict[str, Any]) -> None:
        """Valide les paramètres de publication"""
        # Validation product_data
        required_product_fields = ['brand', 'product_name', 'category']
        missing_product = [field for field in required_product_fields if not product_data.get(field)]
        if missing_product:
            raise ValueError(f"Missing product fields: {missing_product}")
        
        # Validation seo_data
        required_seo_fields = ['title', 'bullet_points', 'description']
        missing_seo = [field for field in required_seo_fields if not seo_data.get(field)]
        if missing_seo:
            raise ValueError(f"Missing SEO fields: {missing_seo}")
        
        # Validation connection_data
        required_connection_fields = ['encrypted_refresh_token', 'seller_id', 'marketplace_id']
        missing_connection = [field for field in required_connection_fields if not connection_data.get(field)]
        if missing_connection:
            raise ValueError(f"Missing connection fields: {missing_connection}")