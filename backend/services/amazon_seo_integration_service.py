"""
Service d'intégration SEO Amazon avec le Publisher
ECOMSIMPLY Bloc 5 — Phase 5: Amazon SEO Integration Service

Intègre les règles SEO A9/A10 avec le système de publication Amazon existant.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import logging

from seo.amazon_rules import AmazonSEORules, AmazonListing, ValidationResult, ListingValidationStatus
from services.logging_service import log_info, log_error, log_operation


class AmazonSEOIntegrationService:
    """
    Service d'intégration entre les règles SEO Amazon et le Publisher
    Génère des listings optimisés et valide avant publication
    """
    
    def __init__(self):
        self.amazon_seo = AmazonSEORules()
        self.logger = logging.getLogger("ecomsimply.amazon_seo_integration")
        
        log_info(
            "Amazon SEO Integration Service initialisé",
            service="AmazonSEOIntegrationService"
        )
    
    async def generate_optimized_listing(
        self,
        product_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Génère un listing Amazon optimisé pour un produit donné
        
        Args:
            product_data: Données du produit (nom, description, features, etc.)
            user_preferences: Préférences utilisateur pour la génération
            
        Returns:
            Dict: Listing optimisé avec métadonnées de génération
        """
        start_time = datetime.utcnow()
        
        log_info(
            "Génération listing Amazon optimisé",
            service="AmazonSEOIntegrationService",
            product_name=product_data.get('product_name', 'Unknown'),
            category=product_data.get('category')
        )
        
        try:
            # Extraction des données produit
            product_name = product_data.get('product_name', '')
            brand = product_data.get('brand', self._extract_brand_from_name(product_name))
            model = product_data.get('model', self._extract_model_from_name(product_name))
            category = product_data.get('category', 'général')
            
            # Features et benefits
            features = product_data.get('features', [])
            if isinstance(features, str):
                features = [features]
            
            benefits = product_data.get('benefits', [])
            if isinstance(benefits, str):
                benefits = [benefits]
            
            # Informations additionnelles
            size = product_data.get('size')
            color = product_data.get('color')
            use_cases = product_data.get('use_cases', [])
            additional_keywords = product_data.get('additional_keywords', [])
            images = product_data.get('images', [])
            
            # 1. Générer le titre optimisé
            optimized_title = self.amazon_seo.generate_optimized_title(
                brand=brand,
                model=model,
                features=features,
                size=size,
                color=color,
                category=category
            )
            
            # 2. Générer les bullets optimisés
            optimized_bullets = self.amazon_seo.generate_optimized_bullets(
                product_name=product_name,
                features=features,
                benefits=benefits,
                category=category,
                target_keywords=additional_keywords
            )
            
            # 3. Générer la description optimisée
            optimized_description = self.amazon_seo.generate_optimized_description(
                product_name=product_name,
                features=features,
                benefits=benefits,
                use_cases=use_cases,
                category=category
            )
            
            # 4. Générer les backend keywords
            backend_keywords = self.amazon_seo.generate_backend_keywords(
                product_name=product_name,
                category=category,
                features=features,
                additional_keywords=additional_keywords
            )
            
            # 5. Créer le listing complet
            listing = AmazonListing(
                title=optimized_title,
                bullets=optimized_bullets,
                description=optimized_description,
                backend_keywords=backend_keywords,
                images=images,
                brand=brand,
                model=model,
                features=features,
                size=size,
                color=color,
                category=category
            )
            
            # 6. Validation automatique
            validation = self.amazon_seo.validate_amazon_listing(listing)
            
            # Calculer le temps de génération
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'listing': {
                    'title': optimized_title,
                    'bullets': optimized_bullets,
                    'description': optimized_description,
                    'backend_keywords': backend_keywords,
                    'images': images,
                    'metadata': {
                        'brand': brand,
                        'model': model,
                        'category': category,
                        'size': size,
                        'color': color
                    }
                },
                'validation': {
                    'status': validation.status.value,
                    'score': validation.score,
                    'reasons': validation.reasons,
                    'warnings': validation.warnings,
                    'suggestions': validation.suggestions,
                    'details': validation.details
                },
                'generation_info': {
                    'generation_time_seconds': generation_time,
                    'generated_at': start_time.isoformat(),
                    'seo_optimized': True,
                    'a9_a10_compliant': validation.status == ListingValidationStatus.APPROVED
                }
            }
            
            log_operation(
                "AmazonSEOIntegrationService",
                "generate_listing",
                "success",
                product_name=product_name,
                validation_status=validation.status.value,
                validation_score=validation.score,
                generation_time=generation_time,
                title_length=len(optimized_title),
                bullets_count=len(optimized_bullets)
            )
            
            return result
            
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            log_error(
                "Erreur génération listing Amazon",
                service="AmazonSEOIntegrationService",
                product_name=product_data.get('product_name', 'Unknown'),
                generation_time=generation_time,
                exception=str(e)
            )
            
            raise Exception(f"Erreur lors de la génération du listing optimisé: {str(e)}")
    
    async def validate_existing_listing(
        self,
        listing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valide un listing Amazon existant selon les règles SEO A9/A10
        
        Args:
            listing_data: Données du listing à valider
            
        Returns:
            Dict: Résultat de validation détaillé
        """
        log_info(
            "Validation listing Amazon existant",
            service="AmazonSEOIntegrationService",
            title_length=len(listing_data.get('title', ''))
        )
        
        try:
            # Créer l'objet AmazonListing à partir des données
            listing = AmazonListing(
                title=listing_data.get('title', ''),
                bullets=listing_data.get('bullets', []),
                description=listing_data.get('description', ''),
                backend_keywords=listing_data.get('backend_keywords', ''),
                images=listing_data.get('images', []),
                brand=listing_data.get('brand'),
                model=listing_data.get('model'),
                features=listing_data.get('features'),
                size=listing_data.get('size'),
                color=listing_data.get('color'),
                category=listing_data.get('category')
            )
            
            # Validation complète
            validation = self.amazon_seo.validate_amazon_listing(listing)
            
            # Générer des suggestions d'amélioration si nécessaire
            improvements = await self._generate_improvement_suggestions(listing, validation)
            
            result = {
                'validation': {
                    'status': validation.status.value,
                    'score': validation.score,
                    'reasons': validation.reasons,
                    'warnings': validation.warnings,
                    'suggestions': validation.suggestions,
                    'details': validation.details
                },
                'improvements': improvements,
                'compliance': {
                    'a9_a10_compliant': validation.status == ListingValidationStatus.APPROVED,
                    'ready_for_publication': validation.score >= 80,
                    'critical_issues': len([r for r in validation.reasons if 'ERREUR' in r])
                }
            }
            
            log_operation(
                "AmazonSEOIntegrationService",
                "validate_listing",
                "success",
                validation_status=validation.status.value,
                validation_score=validation.score,
                critical_issues=result['compliance']['critical_issues']
            )
            
            return result
            
        except Exception as e:
            log_error(
                "Erreur validation listing Amazon",
                service="AmazonSEOIntegrationService",
                exception=str(e)
            )
            
            raise Exception(f"Erreur lors de la validation du listing: {str(e)}")
    
    async def optimize_existing_listing(
        self,
        listing_data: Dict[str, Any],
        optimization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimise un listing existant selon les suggestions SEO
        
        Args:
            listing_data: Listing actuel
            optimization_options: Options d'optimisation
            
        Returns:
            Dict: Listing optimisé avec comparaison avant/après
        """
        log_info(
            "Optimisation listing Amazon existant",
            service="AmazonSEOIntegrationService"
        )
        
        try:
            # 1. Validation du listing actuel
            current_validation = await self.validate_existing_listing(listing_data)
            
            # 2. Régénération optimisée
            # Extraire les données produit du listing existant de manière plus robuste
            product_data = {
                'product_name': ' '.join(listing_data.get('title', '').split()[:3]) if listing_data.get('title') else 'Produit',
                'brand': listing_data.get('brand', '') or self._extract_brand_from_name(listing_data.get('title', '')),
                'model': listing_data.get('model', '') or self._extract_model_from_name(listing_data.get('title', '')),
                'category': listing_data.get('category', 'général'),
                'features': listing_data.get('features', []) or listing_data.get('bullets', [])[:3],
                'benefits': listing_data.get('benefits', []) or listing_data.get('bullets', []),
                'images': listing_data.get('images', []),
                'size': listing_data.get('size'),
                'color': listing_data.get('color'),
                'additional_keywords': listing_data.get('backend_keywords', '').split() if listing_data.get('backend_keywords') else []
            }
            
            # Si le nom du produit n'est pas disponible, l'extraire du titre
            if not product_data.get('product_name'):
                product_data['product_name'] = listing_data.get('title', '')
            
            # Génération du listing optimisé
            optimized_result = await self.generate_optimized_listing(
                product_data, 
                optimization_options
            )
            
            # 3. Comparaison avant/après
            comparison = self._compare_listings(listing_data, optimized_result['listing'])
            
            result = {
                'original': {
                    'listing': listing_data,
                    'validation': current_validation['validation']
                },
                'optimized': optimized_result,
                'comparison': comparison,
                'recommendations': {
                    'should_update': optimized_result['validation']['score'] > current_validation['validation']['score'],
                    'score_improvement': optimized_result['validation']['score'] - current_validation['validation']['score'],
                    'priority_changes': comparison.get('priority_changes', [])
                }
            }
            
            log_operation(
                "AmazonSEOIntegrationService",
                "optimize_listing",
                "success",
                score_improvement=result['recommendations']['score_improvement'],
                should_update=result['recommendations']['should_update']
            )
            
            return result
            
        except Exception as e:
            log_error(
                "Erreur optimisation listing Amazon",
                service="AmazonSEOIntegrationService",
                exception=str(e)
            )
            
            raise Exception(f"Erreur lors de l'optimisation du listing: {str(e)}")
    
    async def prepare_listing_for_publisher(
        self,
        product_data: Dict[str, Any],
        publisher_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prépare un listing optimisé pour le Amazon Publisher
        
        Args:
            product_data: Données du produit
            publisher_config: Configuration du publisher
            
        Returns:
            Dict: Listing prêt pour publication avec validation
        """
        log_info(
            "Préparation listing pour Amazon Publisher",
            service="AmazonSEOIntegrationService",
            product_name=product_data.get('product_name', 'Unknown')
        )
        
        try:
            # 1. Générer le listing optimisé
            optimized_listing = await self.generate_optimized_listing(product_data)
            
            # 2. Vérifier la conformité pour publication
            if optimized_listing['validation']['status'] == 'rejected':
                raise Exception(
                    f"Listing non conforme pour publication: {'; '.join(optimized_listing['validation']['reasons'])}"
                )
            
            # 3. Adapter au format attendu par le Publisher Amazon
            publisher_format = {
                'title': optimized_listing['listing']['title'],
                'bullet_point_1': optimized_listing['listing']['bullets'][0] if len(optimized_listing['listing']['bullets']) > 0 else '',
                'bullet_point_2': optimized_listing['listing']['bullets'][1] if len(optimized_listing['listing']['bullets']) > 1 else '',
                'bullet_point_3': optimized_listing['listing']['bullets'][2] if len(optimized_listing['listing']['bullets']) > 2 else '',
                'bullet_point_4': optimized_listing['listing']['bullets'][3] if len(optimized_listing['listing']['bullets']) > 3 else '',
                'bullet_point_5': optimized_listing['listing']['bullets'][4] if len(optimized_listing['listing']['bullets']) > 4 else '',
                'description': optimized_listing['listing']['description'],
                'search_terms': optimized_listing['listing']['backend_keywords'],
                'main_image': optimized_listing['listing']['images'][0] if optimized_listing['listing']['images'] else None,
                'additional_images': optimized_listing['listing']['images'][1:] if len(optimized_listing['listing']['images']) > 1 else []
            }
            
            # 4. Métadonnées pour le publisher
            publisher_metadata = {
                'seo_optimized': True,
                'a9_a10_compliant': optimized_listing['validation']['status'] == 'approved',
                'validation_score': optimized_listing['validation']['score'],
                'generated_at': datetime.utcnow().isoformat(),
                'optimization_version': '1.0'
            }
            
            result = {
                'listing_data': publisher_format,
                'metadata': publisher_metadata,
                'validation_summary': {
                    'status': optimized_listing['validation']['status'],
                    'score': optimized_listing['validation']['score'],
                    'ready_for_publication': optimized_listing['validation']['status'] in ['approved', 'warning'],
                    'critical_issues_count': len([r for r in optimized_listing['validation']['reasons'] if 'ERREUR' in r])
                },
                'seo_insights': {
                    'title_optimization': f"Longueur optimale: {len(optimized_listing['listing']['title'])}/200 caractères",
                    'bullets_optimization': f"{len(optimized_listing['listing']['bullets'])} bullets générés",
                    'keywords_optimization': f"Backend keywords: {len(optimized_listing['listing']['backend_keywords'].encode('utf-8'))}/250 bytes"
                }
            }
            
            log_operation(
                "AmazonSEOIntegrationService",
                "prepare_for_publisher",
                "success",
                product_name=product_data.get('product_name', 'Unknown'),
                validation_status=result['validation_summary']['status'],
                ready_for_publication=result['validation_summary']['ready_for_publication']
            )
            
            return result
            
        except Exception as e:
            log_error(
                "Erreur préparation listing pour publisher",
                service="AmazonSEOIntegrationService",
                product_name=product_data.get('product_name', 'Unknown'),
                exception=str(e)
            )
            
            raise Exception(f"Erreur lors de la préparation pour le publisher: {str(e)}")
    
    # Méthodes privées utilitaires
    
    def _extract_brand_from_name(self, product_name: str) -> str:
        """Extrait la marque depuis le nom du produit"""
        if not product_name:
            return "Generic"
        
        # Prendre le premier mot comme marque par défaut
        words = product_name.split()
        return words[0] if words else "Generic"
    
    def _extract_model_from_name(self, product_name: str) -> str:
        """Extrait le modèle depuis le nom du produit"""
        if not product_name:
            return "Standard"
        
        # Prendre le deuxième mot comme modèle par défaut
        words = product_name.split()
        return words[1] if len(words) > 1 else "Standard"
    
    async def _generate_improvement_suggestions(
        self,
        listing: AmazonListing,
        validation: ValidationResult
    ) -> List[Dict[str, Any]]:
        """Génère des suggestions d'amélioration spécifiques"""
        suggestions = []
        
        # Suggestions basées sur les erreurs de validation
        for reason in validation.reasons:
            if "Titre trop long" in reason:
                suggestions.append({
                    'type': 'title_length',
                    'priority': 'high',
                    'suggestion': 'Réduire la longueur du titre en supprimant les mots moins importants',
                    'current_issue': reason
                })
            elif "Bullets manquants" in reason:
                suggestions.append({
                    'type': 'bullets_missing',
                    'priority': 'critical',
                    'suggestion': 'Ajouter les 5 bullets points obligatoires',
                    'current_issue': reason
                })
            elif "Backend keywords trop longs" in reason:
                suggestions.append({
                    'type': 'keywords_length',
                    'priority': 'high', 
                    'suggestion': 'Réduire les mots-clés backend à 250 bytes maximum',
                    'current_issue': reason
                })
        
        # Suggestions basées sur les warnings
        for warning in validation.warnings:
            if "court" in warning.lower():
                suggestions.append({
                    'type': 'content_length',
                    'priority': 'medium',
                    'suggestion': 'Enrichir le contenu pour améliorer le SEO',
                    'current_issue': warning
                })
        
        return suggestions
    
    def _compare_listings(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """Compare deux listings et identifie les changements"""
        comparison = {
            'title': {
                'original': original.get('title', ''),
                'optimized': optimized.get('title', ''),
                'changed': original.get('title', '') != optimized.get('title', ''),
                'length_change': len(optimized.get('title', '')) - len(original.get('title', ''))
            },
            'bullets': {
                'original_count': len(original.get('bullets', [])),
                'optimized_count': len(optimized.get('bullets', [])),
                'changed': original.get('bullets', []) != optimized.get('bullets', [])
            },
            'description': {
                'original_length': len(original.get('description', '')),
                'optimized_length': len(optimized.get('description', '')),
                'changed': original.get('description', '') != optimized.get('description', ''),
                'length_change': len(optimized.get('description', '')) - len(original.get('description', ''))
            },
            'backend_keywords': {
                'original': original.get('backend_keywords', ''),
                'optimized': optimized.get('backend_keywords', ''),
                'changed': original.get('backend_keywords', '') != optimized.get('backend_keywords', ''),
                'byte_change': len(optimized.get('backend_keywords', '').encode('utf-8')) - len(original.get('backend_keywords', '').encode('utf-8'))
            }
        }
        
        # Identifier les changements prioritaires
        priority_changes = []
        if comparison['title']['changed']:
            priority_changes.append('title')
        if comparison['bullets']['changed']:
            priority_changes.append('bullets')
        if comparison['backend_keywords']['changed']:
            priority_changes.append('backend_keywords')
        
        comparison['priority_changes'] = priority_changes
        comparison['total_changes'] = len(priority_changes)
        
        return comparison


# Instance globale du service
amazon_seo_integration_service = None

def get_amazon_seo_integration_service() -> AmazonSEOIntegrationService:
    """Factory pour obtenir l'instance du service d'intégration SEO Amazon"""
    global amazon_seo_integration_service
    if amazon_seo_integration_service is None:
        amazon_seo_integration_service = AmazonSEOIntegrationService()
    return amazon_seo_integration_service