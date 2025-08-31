# Amazon Publisher Service - Phase 3
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import aiohttp
import uuid

# Import des services Amazon existants
from integrations.amazon.client import AmazonSPAPIClient
from integrations.amazon.auth import AmazonOAuthService
from models.amazon_spapi import AmazonConnection

logger = logging.getLogger(__name__)

class AmazonPublisherService:
    """
    Service de publication automatique SEO + Prix sur Amazon via SP-API
    Mise à jour en temps réel avec validation et journalisation
    """
    
    def __init__(self):
        self.oauth_service = AmazonOAuthService()
        self.sp_client = AmazonSPAPIClient()
        
        # Configuration publication
        self.publication_config = {
            'batch_size': 10,           # Produits par batch
            'retry_attempts': 3,        # Tentatives par produit
            'retry_delay_base': 2,      # Délai base retry (secondes)
            'rate_limit_delay': 1.5,    # Délai entre publications
            'validation_required': True, # Validation avant publication
            'backup_original': True     # Sauvegarde données originales
        }
        
        # Types de mise à jour supportés
        self.update_types = {
            'seo_only': ['title', 'bullet_points', 'description', 'search_terms'],
            'price_only': ['standard_price'],
            'full_update': ['title', 'bullet_points', 'description', 'search_terms', 'standard_price'],
            'inventory': ['fulfillment_availability']
        }
    
    async def publish_seo_and_price_updates(
        self,
        user_id: str,
        marketplace_id: str,
        updates: List[Dict[str, Any]],
        update_type: str = 'full_update',
        validation_required: bool = True
    ) -> Dict[str, Any]:
        """
        Publier les mises à jour SEO et prix sur Amazon
        
        Args:
            user_id: ID utilisateur
            marketplace_id: ID marketplace Amazon
            updates: Liste des mises à jour à appliquer
            update_type: Type de mise à jour (seo_only, price_only, full_update)
            validation_required: Validation obligatoire avant publication
        
        Returns:
            Résultats de publication avec détails succès/erreurs
        """
        try:
            logger.info(f"🚀 Starting Amazon publication for user {user_id}, {len(updates)} updates")
            
            # Vérifier la connexion Amazon
            connection_status = await self._verify_amazon_connection(user_id, marketplace_id)
            if not connection_status['connected']:
                raise Exception(f"Amazon connection required: {connection_status['error']}")
            
            # Préparer le contexte de publication
            publication_context = {
                'user_id': user_id,
                'marketplace_id': marketplace_id,
                'update_type': update_type,
                'validation_required': validation_required,
                'started_at': datetime.utcnow().isoformat(),
                'session_id': str(uuid.uuid4())
            }
            
            # Valider les données si requis
            if validation_required:
                validation_results = await self._validate_updates_batch(updates, update_type)
                if validation_results['invalid_count'] > 0:
                    logger.warning(f"⚠️ {validation_results['invalid_count']} updates failed validation")
                    # Filtrer les mises à jour valides seulement
                    updates = [u for u in updates if u.get('validation_status') == 'valid']
            
            # Traiter par batches
            all_results = []
            batch_count = 0
            
            for i in range(0, len(updates), self.publication_config['batch_size']):
                batch = updates[i:i + self.publication_config['batch_size']]
                batch_count += 1
                
                logger.info(f"📦 Processing batch {batch_count}: {len(batch)} updates")
                
                # Publier le batch
                batch_results = await self._publish_batch(
                    batch, connection_status['connection'], publication_context
                )
                
                all_results.extend(batch_results)
                
                # Délai entre batches pour respecter les quotas
                if i + self.publication_config['batch_size'] < len(updates):
                    await asyncio.sleep(self.publication_config['rate_limit_delay'])
            
            # Compiler les résultats finaux
            publication_summary = self._compile_publication_results(
                all_results, publication_context
            )
            
            # Journaliser les résultats
            await self._log_publication_results(publication_summary)
            
            logger.info(f"✅ Publication completed - Success: {publication_summary['success_count']}, Errors: {publication_summary['error_count']}")
            return publication_summary
            
        except Exception as e:
            logger.error(f"❌ Publication failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'session_id': publication_context.get('session_id'),
                'results': []
            }
    
    async def _verify_amazon_connection(self, user_id: str, marketplace_id: str) -> Dict[str, Any]:
        """
        Vérifier la validité de la connexion Amazon
        """
        try:
            # Récupérer la connexion depuis la base
            connection = await AmazonConnection.find_by_user_and_marketplace(user_id, marketplace_id)
            
            if not connection:
                return {
                    'connected': False,
                    'error': 'No Amazon connection found for this marketplace',
                    'connection': None
                }
            
            # Vérifier la validité du token
            if connection.is_token_expired():
                # Tenter de rafraîchir le token
                refresh_result = await self.oauth_service.refresh_access_token(connection)
                if not refresh_result['success']:
                    return {
                        'connected': False,
                        'error': 'Token expired and refresh failed',
                        'connection': None
                    }
            
            # Test de connectivité SP-API
            connectivity_test = await self._test_sp_api_connectivity(connection)
            if not connectivity_test['success']:
                return {
                    'connected': False,
                    'error': f'SP-API connectivity failed: {connectivity_test["error"]}',
                    'connection': None
                }
            
            return {
                'connected': True,
                'connection': connection,
                'last_tested': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Connection verification failed: {str(e)}")
            return {
                'connected': False,
                'error': str(e),
                'connection': None
            }
    
    async def _test_sp_api_connectivity(self, connection: AmazonConnection) -> Dict[str, Any]:
        """
        Tester la connectivité SP-API avec un appel simple
        """
        try:
            # Appel de test simple (getMarketplaceParticipations)
            response = await self.sp_client.get_marketplace_participations(
                access_token=connection.decrypted_refresh_token,
                marketplace_id=connection.marketplace_id
            )
            
            if response.get('success'):
                return {
                    'success': True,
                    'test_endpoint': 'getMarketplaceParticipations',
                    'response_time': response.get('response_time', 0)
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Unknown SP-API error'),
                    'test_endpoint': 'getMarketplaceParticipations'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_endpoint': 'getMarketplaceParticipations'
            }
    
    async def _validate_updates_batch(
        self, 
        updates: List[Dict[str, Any]], 
        update_type: str
    ) -> Dict[str, Any]:
        """
        Valider un batch de mises à jour avant publication
        """
        validation_results = {
            'valid_count': 0,
            'invalid_count': 0,
            'validation_details': []
        }
        
        allowed_fields = self.update_types.get(update_type, [])
        
        for i, update in enumerate(updates):
            try:
                # Validation de base
                validation = {
                    'index': i,
                    'sku': update.get('sku'),
                    'valid': True,
                    'errors': [],
                    'warnings': []
                }
                
                # Vérifier SKU obligatoire
                if not update.get('sku'):
                    validation['valid'] = False
                    validation['errors'].append('SKU is required')
                
                # Valider les champs selon le type de mise à jour
                for field in allowed_fields:
                    if field in update:
                        field_validation = await self._validate_field(field, update[field])
                        if not field_validation['valid']:
                            validation['valid'] = False
                            validation['errors'].extend(field_validation['errors'])
                        if field_validation.get('warnings'):
                            validation['warnings'].extend(field_validation['warnings'])
                
                # Validation spécifique SEO
                if 'seo' in update_type:
                    seo_validation = await self._validate_seo_update(update)
                    if not seo_validation['valid']:
                        validation['valid'] = False
                        validation['errors'].extend(seo_validation['errors'])
                
                # Validation spécifique prix
                if 'price' in update_type:
                    price_validation = await self._validate_price_update(update)
                    if not price_validation['valid']:
                        validation['valid'] = False
                        validation['errors'].extend(price_validation['errors'])
                
                # Marquer l'update avec son statut de validation
                update['validation_status'] = 'valid' if validation['valid'] else 'invalid'
                update['validation_details'] = validation
                
                validation_results['validation_details'].append(validation)
                
                if validation['valid']:
                    validation_results['valid_count'] += 1
                else:
                    validation_results['invalid_count'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Validation error for update {i}: {str(e)}")
                validation_results['invalid_count'] += 1
                update['validation_status'] = 'error'
                update['validation_error'] = str(e)
        
        return validation_results
    
    async def _validate_field(self, field: str, value: Any) -> Dict[str, Any]:
        """
        Valider un champ spécifique
        """
        validation = {'valid': True, 'errors': [], 'warnings': []}
        
        if field == 'title':
            if not isinstance(value, str):
                validation['valid'] = False
                validation['errors'].append('Title must be a string')
            elif len(value) > 200:
                validation['valid'] = False
                validation['errors'].append(f'Title too long: {len(value)}/200 characters')
            elif len(value) < 10:
                validation['warnings'].append('Title might be too short')
        
        elif field == 'bullet_points':
            if not isinstance(value, list):
                validation['valid'] = False
                validation['errors'].append('Bullet points must be a list')
            elif len(value) > 5:
                validation['valid'] = False
                validation['errors'].append(f'Too many bullet points: {len(value)}/5')
            else:
                for i, bullet in enumerate(value):
                    if not isinstance(bullet, str):
                        validation['valid'] = False
                        validation['errors'].append(f'Bullet {i+1} must be a string')
                    elif len(bullet) > 255:
                        validation['valid'] = False
                        validation['errors'].append(f'Bullet {i+1} too long: {len(bullet)}/255 characters')
        
        elif field == 'description':
            if not isinstance(value, str):
                validation['valid'] = False
                validation['errors'].append('Description must be a string')
            elif len(value) > 2000:
                validation['valid'] = False
                validation['errors'].append(f'Description too long: {len(value)}/2000 characters')
            elif len(value) < 100:
                validation['warnings'].append('Description might be too short')
        
        elif field == 'search_terms':
            if not isinstance(value, str):
                validation['valid'] = False
                validation['errors'].append('Search terms must be a string')
            elif len(value.encode('utf-8')) > 250:
                validation['valid'] = False
                validation['errors'].append(f'Search terms too long: {len(value.encode("utf-8"))}/250 bytes')
        
        elif field == 'standard_price':
            if not isinstance(value, (int, float)):
                validation['valid'] = False
                validation['errors'].append('Price must be a number')
            elif value <= 0:
                validation['valid'] = False
                validation['errors'].append('Price must be positive')
        
        return validation
    
    async def _validate_seo_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation spécifique SEO Amazon A9/A10
        """
        validation = {'valid': True, 'errors': []}
        
        # Utiliser le validateur existant si disponible
        try:
            from amazon.listings.validators import AmazonListingValidator
            validator = AmazonListingValidator()
            
            # Construire un objet listing pour validation
            listing_data = {
                'seo_content': {
                    'title': update.get('title', ''),
                    'bullet_points': update.get('bullet_points', []),
                    'description': update.get('description', ''),
                    'backend_keywords': update.get('search_terms', '')
                }
            }
            
            validation_result = validator.validate_complete_listing(listing_data)
            
            if validation_result.get('overall_status') == 'REJECTED':
                validation['valid'] = False
                validation['errors'] = validation_result.get('errors', [])
            
        except ImportError:
            logger.warning("⚠️ Amazon listing validator not available, using basic validation")
            # Validation basique fallback
            pass
        
        return validation
    
    async def _validate_price_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation spécifique prix
        """
        validation = {'valid': True, 'errors': []}
        
        price = update.get('standard_price')
        if price is not None:
            # Vérifications business
            if price < 0.01:
                validation['valid'] = False
                validation['errors'].append('Price must be at least 0.01')
            
            if price > 99999.99:
                validation['valid'] = False
                validation['errors'].append('Price exceeds maximum allowed (99999.99)')
        
        return validation
    
    async def _publish_batch(
        self,
        batch: List[Dict[str, Any]],
        connection: AmazonConnection,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Publier un batch de mises à jour via SP-API
        """
        batch_results = []
        
        for update in batch:
            try:
                # Préparer les données SP-API
                sp_api_data = self._prepare_sp_api_payload(update, context['update_type'])
                
                # Publier via SP-API
                publication_result = await self._publish_single_update(
                    sp_api_data, connection, context
                )
                
                # Ajouter métadonnées
                result = {
                    'sku': update.get('sku'),
                    'update_type': context['update_type'],
                    'success': publication_result['success'],
                    'published_at': datetime.utcnow().isoformat(),
                    'session_id': context['session_id']
                }
                
                if publication_result['success']:
                    result.update({
                        'feed_id': publication_result.get('feed_id'),
                        'submission_id': publication_result.get('submission_id'),
                        'processing_status': 'SUBMITTED'
                    })
                else:
                    result.update({
                        'error': publication_result.get('error'),
                        'error_code': publication_result.get('error_code'),
                        'retry_attempted': publication_result.get('retry_attempted', False)
                    })
                
                batch_results.append(result)
                
                # Délai entre publications individuelles
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error publishing update for SKU {update.get('sku')}: {str(e)}")
                batch_results.append({
                    'sku': update.get('sku'),
                    'success': False,
                    'error': str(e),
                    'published_at': datetime.utcnow().isoformat(),
                    'session_id': context['session_id']
                })
        
        return batch_results
    
    def _prepare_sp_api_payload(self, update: Dict[str, Any], update_type: str) -> Dict[str, Any]:
        """
        Préparer le payload SP-API selon le type de mise à jour
        """
        payload = {
            'sku': update.get('sku'),
            'marketplaceId': update.get('marketplace_id'),
            'productType': update.get('product_type', 'PRODUCT')
        }
        
        # Mapper les champs selon le type
        if update_type in ['seo_only', 'full_update']:
            if 'title' in update:
                payload['title'] = update['title']
            
            if 'bullet_points' in update:
                bullets = update['bullet_points']
                for i, bullet in enumerate(bullets[:5]):  # Max 5 bullets
                    payload[f'bullet_point_{i+1}'] = bullet
            
            if 'description' in update:
                payload['description'] = update['description']
            
            if 'search_terms' in update:
                payload['search_terms'] = update['search_terms']
        
        if update_type in ['price_only', 'full_update']:
            if 'standard_price' in update:
                payload['standard_price'] = {
                    'amount': update['standard_price'],
                    'currency_code': update.get('currency', 'EUR')
                }
        
        # Métadonnées additionnelles
        payload['update_timestamp'] = datetime.utcnow().isoformat()
        payload['update_source'] = 'ECOMSIMPLY_AUTO_PUBLISHER'
        
        return payload
    
    async def _publish_single_update(
        self,
        sp_api_data: Dict[str, Any],
        connection: AmazonConnection,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publier une mise à jour individuelle via SP-API
        """
        for attempt in range(self.publication_config['retry_attempts']):
            try:
                # Appel SP-API
                response = await self.sp_client.submit_feed(
                    feed_type='POST_PRODUCT_DATA',
                    feed_content=json.dumps(sp_api_data),
                    access_token=connection.decrypted_refresh_token,
                    marketplace_id=connection.marketplace_id
                )
                
                if response.get('success'):
                    return {
                        'success': True,
                        'feed_id': response.get('feed_id'),
                        'submission_id': response.get('submission_id'),
                        'attempts': attempt + 1
                    }
                else:
                    error_code = response.get('error_code')
                    
                    # Vérifier si on doit retry
                    if self._should_retry_error(error_code) and attempt < self.publication_config['retry_attempts'] - 1:
                        delay = self.publication_config['retry_delay_base'] * (2 ** attempt)
                        logger.warning(f"⚠️ Retry attempt {attempt + 2} for SKU {sp_api_data.get('sku')} in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    
                    return {
                        'success': False,
                        'error': response.get('error', 'Unknown SP-API error'),
                        'error_code': error_code,
                        'attempts': attempt + 1,
                        'retry_attempted': attempt > 0
                    }
                    
            except Exception as e:
                if attempt < self.publication_config['retry_attempts'] - 1:
                    delay = self.publication_config['retry_delay_base'] * (2 ** attempt)
                    logger.warning(f"⚠️ Exception retry {attempt + 2} for SKU {sp_api_data.get('sku')}: {str(e)}")
                    await asyncio.sleep(delay)
                    continue
                
                return {
                    'success': False,
                    'error': str(e),
                    'attempts': attempt + 1,
                    'retry_attempted': attempt > 0
                }
        
        return {
            'success': False,
            'error': 'Max retry attempts exceeded',
            'attempts': self.publication_config['retry_attempts']
        }
    
    def _should_retry_error(self, error_code: str) -> bool:
        """
        Déterminer si une erreur justifie un retry
        """
        retry_codes = [
            'RequestThrottled',
            'ServiceUnavailable',
            'InternalError',
            'QuotaExceeded',
            'TooManyRequests'
        ]
        
        return error_code in retry_codes
    
    def _compile_publication_results(
        self,
        all_results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compiler les résultats de publication
        """
        success_count = len([r for r in all_results if r.get('success')])
        error_count = len(all_results) - success_count
        
        # Grouper les erreurs par type
        error_summary = {}
        for result in all_results:
            if not result.get('success'):
                error_code = result.get('error_code', 'Unknown')
                if error_code not in error_summary:
                    error_summary[error_code] = 0
                error_summary[error_code] += 1
        
        # Feed IDs créés
        feed_ids = [r.get('feed_id') for r in all_results if r.get('feed_id')]
        
        return {
            'success': error_count == 0,
            'session_id': context['session_id'],
            'summary': {
                'total_updates': len(all_results),
                'success_count': success_count,
                'error_count': error_count,
                'success_rate': round((success_count / len(all_results)) * 100, 1) if all_results else 0
            },
            'timing': {
                'started_at': context['started_at'],
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': (datetime.utcnow() - datetime.fromisoformat(context['started_at'].replace('Z', '+00:00'))).total_seconds()
            },
            'feed_tracking': {
                'feed_ids_created': feed_ids,
                'feeds_count': len(feed_ids)
            },
            'error_breakdown': error_summary,
            'detailed_results': all_results
        }
    
    async def _log_publication_results(self, results: Dict[str, Any]) -> None:
        """
        Journaliser les résultats de publication
        """
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': results['session_id'],
                'operation': 'amazon_publication',
                'success': results['success'],
                'summary': results['summary'],
                'timing': results['timing'],
                'feed_tracking': results['feed_tracking']
            }
            
            # Log niveau approprié
            if results['success']:
                logger.info(f"✅ Publication session {results['session_id']} completed successfully")
            else:
                logger.error(f"❌ Publication session {results['session_id']} completed with errors")
            
            # Ici on pourrait envoyer vers un système de monitoring
            # await self._send_to_monitoring_system(log_entry)
            
        except Exception as e:
            logger.error(f"❌ Error logging publication results: {str(e)}")
    
    async def get_publication_status(self, session_id: str) -> Dict[str, Any]:
        """
        Obtenir le statut d'une session de publication
        """
        # Cette méthode pourrait interroger la base de données ou un cache
        # pour récupérer le statut d'une publication en cours
        
        return {
            'session_id': session_id,
            'status': 'completed',  # completed, in_progress, failed
            'message': 'Publication status tracking not implemented yet'
        }
    
    async def cancel_publication(self, session_id: str) -> Dict[str, Any]:
        """
        Annuler une publication en cours
        """
        return {
            'session_id': session_id,
            'cancelled': False,
            'message': 'Publication cancellation not implemented yet'
        }