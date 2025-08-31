"""
Amazon Variations Builder Engine - Phase 6
Construction automatique des familles Parent/Child via SP-API (réel)
"""
import logging
import asyncio
import time
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Set
import json
import uuid
import re
from collections import defaultdict

from models.amazon_phase6 import (
    VariationFamily, ProductRelationship, VariationStatus
)
from integrations.amazon.client import AmazonSPAPIClient

logger = logging.getLogger(__name__)


class VariationsBuilderEngine:
    """
    Moteur de construction de variations Amazon
    
    Fonctionnalités:
    - Détection automatique des familles de variations
    - Construction Parent/Child via POST_PRODUCT_RELATIONSHIP_DATA
    - Synchronisation prix et inventaire
    - Gestion des thèmes de variation (taille, couleur, style, etc.)
    """
    
    def __init__(self):
        self.sp_api_client = AmazonSPAPIClient()
        
        # Thèmes de variation supportés par Amazon
        self.variation_themes = {
            'Size': {
                'name': 'Taille',
                'attributes': ['size', 'size_name', 'item_dimensions'],
                'common_values': ['XS', 'S', 'M', 'L', 'XL', 'XXL', '32', '34', '36', '38', '40', '42']
            },
            'Color': {
                'name': 'Couleur',
                'attributes': ['color', 'color_name', 'color_map'],
                'common_values': ['Noir', 'Blanc', 'Rouge', 'Bleu', 'Vert', 'Jaune', 'Rose', 'Gris']
            },
            'Style': {
                'name': 'Style',
                'attributes': ['style', 'style_name', 'model_name'],
                'common_values': ['Classique', 'Sport', 'Casual', 'Élégant', 'Moderne', 'Vintage']
            },
            'Material': {
                'name': 'Matériau',
                'attributes': ['material', 'material_type', 'fabric_type'],
                'common_values': ['Coton', 'Polyester', 'Cuir', 'Métal', 'Plastique', 'Bois']
            },
            'Pattern': {
                'name': 'Motif',
                'attributes': ['pattern', 'pattern_type'],
                'common_values': ['Uni', 'Rayé', 'Floral', 'Géométrique', 'Animal', 'Abstrait']
            },
            'Flavor': {
                'name': 'Parfum/Saveur',
                'attributes': ['flavor', 'flavor_name', 'scent'],
                'common_values': ['Vanille', 'Chocolat', 'Fraise', 'Citron', 'Menthe', 'Nature']
            }
        }
        
        # Configuration des feeds Amazon
        self.feed_config = {
            'feed_type': 'POST_PRODUCT_RELATIONSHIP_DATA',
            'purge_and_replace': False,
            'batch_size': 100,
            'retry_attempts': 3,
            'processing_timeout': 300
        }
        
        # Patterns de détection automatique
        self.detection_patterns = {
            'size_indicators': [
                r'\b(XS|S|M|L|XL|XXL)\b',
                r'\b(\d{2,3})\s*(cm|mm|L|ml|kg|g)\b',
                r'\b(Petit|Moyen|Grand|Très\s+grand)\b'
            ],
            'color_indicators': [
                r'\b(Noir|Blanc|Rouge|Bleu|Vert|Jaune|Rose|Gris|Marron)\b',
                r'\b(Black|White|Red|Blue|Green|Yellow|Pink|Gray|Brown)\b',
                r'#[0-9A-Fa-f]{6}\b'
            ],
            'style_indicators': [
                r'\b(Classique|Sport|Casual|Élégant|Moderne|Vintage)\b',
                r'\b(Classic|Sport|Casual|Elegant|Modern|Vintage)\b'
            ]
        }
    
    async def detect_variation_families(
        self, 
        user_id: str, 
        marketplace_id: str, 
        sku_list: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Détecter automatiquement les familles de variations
        
        Args:
            user_id: ID utilisateur
            marketplace_id: ID marketplace Amazon
            sku_list: Liste spécifique de SKUs à analyser (optionnel)
            
        Returns:
            Liste des familles détectées avec suggestions
        """
        try:
            logger.info(f"🔍 Detecting variation families for user {user_id} on marketplace {marketplace_id}")
            
            # Récupérer les produits de l'utilisateur
            products_data = await self._get_user_products(user_id, marketplace_id, sku_list)
            
            if not products_data:
                logger.warning("No products found for variation detection")
                return []
            
            # Analyser les produits pour détecter les familles
            detected_families = await self._analyze_products_for_variations(products_data)
            
            # Enrichir avec les données SP-API
            enriched_families = []
            for family in detected_families:
                enriched_family = await self._enrich_family_data(family, marketplace_id)
                enriched_families.append(enriched_family)
            
            logger.info(f"✅ Detected {len(enriched_families)} potential variation families")
            
            return enriched_families
            
        except Exception as e:
            logger.error(f"❌ Error detecting variation families: {str(e)}")
            return []
    
    async def _get_user_products(
        self, 
        user_id: str, 
        marketplace_id: str, 
        sku_list: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Récupérer les données produits de l'utilisateur"""
        
        try:
            # Si SKU liste spécifiée, utiliser celle-ci
            if sku_list:
                target_skus = sku_list
            else:
                # Sinon, récupérer tous les SKUs de l'utilisateur
                # TODO: Implémenter la récupération depuis la base de données
                # Pour l'instant, utiliser une liste d'exemple
                target_skus = [
                    "TEST-SHIRT-RED-M", "TEST-SHIRT-RED-L", "TEST-SHIRT-BLUE-M", 
                    "TEST-SHIRT-BLUE-L", "TEST-PHONE-32GB", "TEST-PHONE-64GB"
                ]
            
            products_data = []
            
            # Récupérer les données détaillées de chaque SKU
            for sku in target_skus:
                try:
                    product_data = await self._get_detailed_product_data(sku, marketplace_id)
                    if product_data:
                        products_data.append(product_data)
                        
                    # Éviter la limitation de débit
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Could not retrieve data for SKU {sku}: {str(e)}")
                    continue
            
            logger.info(f"✅ Retrieved data for {len(products_data)} products")
            return products_data
            
        except Exception as e:
            logger.error(f"❌ Error getting user products: {str(e)}")
            return []
    
    async def _get_detailed_product_data(self, sku: str, marketplace_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données détaillées d'un produit"""
        try:
            response = await self.sp_api_client.make_request(
                method="GET",
                endpoint=f"/catalog/2022-04-01/items/{sku}",
                marketplace_id=marketplace_id,
                params={
                    "marketplaceIds": marketplace_id,
                    "includedData": "attributes,identifiers,images,productTypes,summaries,relationships"
                }
            )
            
            if response.get('success'):
                item_data = response['data']
                
                # Extraire les informations pertinentes pour les variations
                product_data = {
                    'sku': sku,
                    'asin': item_data.get('asin'),
                    'title': self._extract_attribute(item_data.get('attributes', {}), 'item_name'),
                    'brand': self._extract_attribute(item_data.get('attributes', {}), 'brand'),
                    'product_type': item_data.get('productTypes', [{}])[0].get('productType'),
                    'category': self._extract_attribute(item_data.get('attributes', {}), 'item_type_name'),
                    
                    # Attributs de variation potentiels
                    'size': self._extract_variation_attribute(item_data.get('attributes', {}), 'size'),
                    'color': self._extract_variation_attribute(item_data.get('attributes', {}), 'color'),
                    'style': self._extract_variation_attribute(item_data.get('attributes', {}), 'style'),
                    'material': self._extract_variation_attribute(item_data.get('attributes', {}), 'material'),
                    'pattern': self._extract_variation_attribute(item_data.get('attributes', {}), 'pattern'),
                    'flavor': self._extract_variation_attribute(item_data.get('attributes', {}), 'flavor'),
                    
                    # Données complètes pour analyse
                    'attributes': item_data.get('attributes', {}),
                    'relationships': item_data.get('relationships', []),
                    'images': [img.get('link') for img in item_data.get('images', []) if img.get('link')]
                }
                
                return product_data
            else:
                logger.warning(f"Could not retrieve catalog data for SKU {sku}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting detailed product data for {sku}: {str(e)}")
            return None
    
    def _extract_attribute(self, attributes: Dict, key: str) -> Optional[str]:
        """Extraire un attribut du catalog Amazon"""
        for possible_key in [key, f"{key}_name", f"{key}_value"]:
            if possible_key in attributes and attributes[possible_key]:
                attr = attributes[possible_key]
                if isinstance(attr, list) and attr:
                    return str(attr[0])
                elif isinstance(attr, str):
                    return attr
        return None
    
    def _extract_variation_attribute(self, attributes: Dict, variation_type: str) -> Optional[str]:
        """Extraire un attribut de variation spécifique"""
        # Chercher dans les attributs possibles pour ce type de variation
        possible_keys = self.variation_themes.get(variation_type.title(), {}).get('attributes', [variation_type])
        
        for key in possible_keys:
            value = self._extract_attribute(attributes, key)
            if value:
                return value
        
        return None
    
    async def _analyze_products_for_variations(self, products_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyser les produits pour détecter les familles de variations"""
        
        # Grouper par similarité (titre sans variations, marque, catégorie)
        potential_families = defaultdict(list)
        
        for product in products_data:
            # Créer une clé de base en retirant les mots de variation
            base_title = self._normalize_title_for_grouping(product.get('title', ''))
            brand = product.get('brand', 'unknown')
            category = product.get('category', 'unknown')
            
            family_key = f"{brand}_{category}_{base_title}".lower()
            potential_families[family_key].append(product)
        
        # Analyser chaque famille potentielle
        detected_families = []
        
        for family_key, family_products in potential_families.items():
            if len(family_products) >= 2:  # Minimum 2 produits pour une famille
                family_analysis = await self._analyze_family_variations(family_products)
                
                if family_analysis['has_variations']:
                    detected_families.append(family_analysis)
        
        return detected_families
    
    def _normalize_title_for_grouping(self, title: str) -> str:
        """Normaliser le titre en retirant les mots de variation"""
        if not title:
            return ""
        
        normalized = title
        
        # Retirer les indicateurs de variation courants
        for theme, theme_data in self.variation_themes.items():
            for pattern in self.detection_patterns.get(f"{theme.lower()}_indicators", []):
                normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
            
            # Retirer les valeurs communes
            for value in theme_data.get('common_values', []):
                normalized = re.sub(rf'\b{re.escape(value)}\b', '', normalized, flags=re.IGNORECASE)
        
        # Nettoyer les espaces multiples et caractères spéciaux
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        normalized = re.sub(r'[,\-\(\)\[\]]+', '', normalized).strip()
        
        return normalized
    
    async def _analyze_family_variations(self, family_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les variations dans une famille de produits"""
        
        variation_analysis = {
            'has_variations': False,
            'family_name': '',
            'base_title': '',
            'brand': '',
            'category': '',
            'variation_themes': [],
            'products': family_products,
            'suggested_parent': None,
            'variation_matrix': {},
            'confidence_score': 0.0
        }
        
        if not family_products:
            return variation_analysis
        
        # Informations de base de la famille
        first_product = family_products[0]
        variation_analysis['base_title'] = self._normalize_title_for_grouping(first_product.get('title', ''))
        variation_analysis['brand'] = first_product.get('brand', '')
        variation_analysis['category'] = first_product.get('category', '')
        variation_analysis['family_name'] = f"{variation_analysis['brand']} {variation_analysis['base_title']}".strip()
        
        # Analyser les différences entre les produits
        detected_themes = {}
        
        for theme_name, theme_data in self.variation_themes.items():
            theme_values = set()
            theme_products = {}
            
            for product in family_products:
                theme_value = product.get(theme_name.lower())
                if theme_value:
                    theme_values.add(theme_value)
                    theme_products[theme_value] = theme_products.get(theme_value, []) + [product]
                else:
                    # Essayer de détecter dans le titre
                    detected_value = self._detect_theme_in_title(product.get('title', ''), theme_name)
                    if detected_value:
                        theme_values.add(detected_value)
                        theme_products[detected_value] = theme_products.get(detected_value, []) + [product]
            
            # Si on a trouvé plusieurs valeurs pour ce thème, c'est une variation valide
            if len(theme_values) >= 2:
                detected_themes[theme_name] = {
                    'name': theme_data['name'],
                    'values': list(theme_values),
                    'products': theme_products,
                    'coverage': len(theme_values) / len(family_products)
                }
        
        # Évaluer la qualité des variations détectées
        if detected_themes:
            variation_analysis['has_variations'] = True
            variation_analysis['variation_themes'] = list(detected_themes.keys())
            variation_analysis['variation_matrix'] = detected_themes
            
            # Calculer le score de confiance
            confidence_factors = []
            
            # Facteur 1: Couverture des variations
            avg_coverage = sum(theme['coverage'] for theme in detected_themes.values()) / len(detected_themes)
            confidence_factors.append(avg_coverage)
            
            # Facteur 2: Nombre de produits
            product_count_factor = min(len(family_products) / 10, 1.0)  # Normalisé à 10 produits max
            confidence_factors.append(product_count_factor)
            
            # Facteur 3: Qualité des données attributs
            complete_attributes = sum(1 for p in family_products if len([v for v in p.values() if v]) > 5)
            attribute_factor = complete_attributes / len(family_products)
            confidence_factors.append(attribute_factor)
            
            variation_analysis['confidence_score'] = sum(confidence_factors) / len(confidence_factors)
            
            # Suggérer le produit parent (celui avec le plus d'attributs remplis)
            best_parent = max(
                family_products,
                key=lambda p: len([v for v in p.values() if v])
            )
            variation_analysis['suggested_parent'] = best_parent['sku']
        
        return variation_analysis
    
    def _detect_theme_in_title(self, title: str, theme_name: str) -> Optional[str]:
        """Détecter un thème de variation dans le titre du produit"""
        if not title:
            return None
        
        # Chercher les patterns spécifiques au thème
        patterns = self.detection_patterns.get(f"{theme_name.lower()}_indicators", [])
        
        for pattern in patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            if matches:
                return matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        # Chercher les valeurs communes du thème
        theme_values = self.variation_themes.get(theme_name, {}).get('common_values', [])
        for value in theme_values:
            if re.search(rf'\b{re.escape(value)}\b', title, re.IGNORECASE):
                return value
        
        return None
    
    async def _enrich_family_data(self, family: Dict[str, Any], marketplace_id: str) -> Dict[str, Any]:
        """Enrichir les données d'une famille avec les informations SP-API"""
        
        # Ajouter des informations sur les relations existantes
        for product in family['products']:
            sku = product['sku']
            
            # Vérifier s'il existe déjà des relations parent/child
            existing_relationships = await self._check_existing_relationships(sku, marketplace_id)
            product['existing_relationships'] = existing_relationships
            
            # Vérifier les contraintes de catégorie pour les variations
            category_constraints = await self._check_category_variation_constraints(
                product.get('product_type'), marketplace_id
            )
            product['category_constraints'] = category_constraints
        
        # Ajouter des recommandations d'optimisation
        family['optimization_recommendations'] = self._generate_optimization_recommendations(family)
        
        return family
    
    async def _check_existing_relationships(self, sku: str, marketplace_id: str) -> List[Dict[str, Any]]:
        """Vérifier les relations parent/child existantes"""
        try:
            # Utiliser l'API Catalog pour récupérer les relations
            response = await self.sp_api_client.make_request(
                method="GET",
                endpoint=f"/catalog/2022-04-01/items/{sku}",
                marketplace_id=marketplace_id,
                params={
                    "marketplaceIds": marketplace_id,
                    "includedData": "relationships"
                }
            )
            
            if response.get('success'):
                relationships = response['data'].get('relationships', [])
                return [
                    {
                        'type': rel.get('type'),
                        'identifiers': rel.get('identifiers', {}),
                        'color': rel.get('color'),
                        'edition': rel.get('edition'),
                        'flavor': rel.get('flavor'),
                        'format': rel.get('format'),
                        'size': rel.get('size')
                    }
                    for rel in relationships
                ]
            
        except Exception as e:
            logger.error(f"Error checking relationships for {sku}: {str(e)}")
        
        return []
    
    async def _check_category_variation_constraints(
        self, 
        product_type: Optional[str], 
        marketplace_id: str
    ) -> Dict[str, Any]:
        """Vérifier les contraintes de variation pour une catégorie"""
        
        # Contraintes par défaut (à enrichir avec les vraies données Amazon)
        default_constraints = {
            'allowed_variation_themes': ['Size', 'Color', 'Style'],
            'max_child_products': 2000,
            'requires_parent_asin': True,
            'variation_required_attributes': []
        }
        
        if not product_type:
            return default_constraints
        
        # TODO: Implémenter la récupération des vraies contraintes via Product Type Definitions API
        # Pour l'instant, retourner des contraintes simulées basées sur la catégorie
        
        category_constraints = {
            'CLOTHING': {
                'allowed_variation_themes': ['Size', 'Color', 'Style'],
                'max_child_products': 500,
                'requires_parent_asin': True,
                'variation_required_attributes': ['size', 'color']
            },
            'ELECTRONICS': {
                'allowed_variation_themes': ['Size', 'Color', 'Material'],
                'max_child_products': 100,
                'requires_parent_asin': True,
                'variation_required_attributes': ['color']
            },
            'HOME': {
                'allowed_variation_themes': ['Size', 'Color', 'Material', 'Pattern'],
                'max_child_products': 200,
                'requires_parent_asin': True,
                'variation_required_attributes': []
            }
        }
        
        # Détecter la catégorie générale
        detected_category = 'HOME'  # Défaut
        if any(term in product_type.upper() for term in ['CLOTH', 'APPAREL', 'SHIRT', 'DRESS']):
            detected_category = 'CLOTHING'
        elif any(term in product_type.upper() for term in ['ELECTRON', 'PHONE', 'COMPUTER', 'DEVICE']):
            detected_category = 'ELECTRONICS'
        
        return category_constraints.get(detected_category, default_constraints)
    
    def _generate_optimization_recommendations(self, family: Dict[str, Any]) -> List[str]:
        """Générer des recommandations d'optimisation pour la famille"""
        recommendations = []
        
        # Recommandation sur le nombre de produits
        product_count = len(family['products'])
        if product_count < 3:
            recommendations.append("⚡ Considérez ajouter plus de variations pour améliorer la visibilité")
        elif product_count > 20:
            recommendations.append("⚠️ Trop de variations peuvent diluer les performances. Considérez une consolidation")
        
        # Recommandation sur les thèmes de variation
        variation_themes = family.get('variation_themes', [])
        if len(variation_themes) > 2:
            recommendations.append("📊 Plusieurs thèmes de variation détectés. Priorisez les plus importants")
        
        # Recommandation sur les données manquantes
        incomplete_products = [p for p in family['products'] if len([v for v in p.values() if v]) < 5]
        if incomplete_products:
            recommendations.append(f"📝 {len(incomplete_products)} produits ont des données incomplètes")
        
        # Recommandation sur les images
        products_without_images = [p for p in family['products'] if not p.get('images')]
        if products_without_images:
            recommendations.append(f"🖼️ {len(products_without_images)} produits sans images")
        
        return recommendations
    
    async def create_variation_family(
        self,
        user_id: str,
        marketplace_id: str,
        family_config: Dict[str, Any]
    ) -> VariationFamily:
        """
        Créer une famille de variations
        
        Args:
            user_id: ID utilisateur
            marketplace_id: ID marketplace Amazon
            family_config: Configuration de la famille
            
        Returns:
            VariationFamily créée
        """
        try:
            logger.info(f"🏗️ Creating variation family: {family_config.get('family_name')}")
            
            # Créer l'objet famille de variations
            variation_family = VariationFamily(
                user_id=user_id,
                marketplace_id=marketplace_id,
                parent_sku=family_config['parent_sku'],
                family_name=family_config['family_name'],
                variation_theme=family_config['variation_theme'],
                child_skus=family_config.get('child_skus', []),
                auto_manage=family_config.get('auto_manage', True),
                sync_pricing=family_config.get('sync_pricing', False),
                sync_inventory=family_config.get('sync_inventory', False)
            )
            
            # Créer les relations produit
            await self._create_product_relationships(variation_family, family_config)
            
            # Publier les relations via SP-API Feed
            feed_success = await self._publish_relationships_feed(variation_family)
            
            if feed_success:
                variation_family.status = VariationStatus.ACTIVE
                logger.info(f"✅ Variation family created successfully: {variation_family.id}")
            else:
                variation_family.status = VariationStatus.INACTIVE
                logger.error(f"❌ Failed to publish variation family: {variation_family.id}")
            
            return variation_family
            
        except Exception as e:
            logger.error(f"❌ Error creating variation family: {str(e)}")
            raise
    
    async def _create_product_relationships(
        self,
        variation_family: VariationFamily,
        family_config: Dict[str, Any]
    ):
        """Créer les relations entre produits de la famille"""
        
        parent_sku = variation_family.parent_sku
        variation_theme = variation_family.variation_theme
        
        # Créer une relation pour chaque produit enfant
        for child_sku in variation_family.child_skus:
            # Récupérer les attributs de variation depuis la config
            child_config = next(
                (c for c in family_config.get('children', []) if c['sku'] == child_sku),
                {}
            )
            
            variation_attributes = child_config.get('variation_attributes', {})
            
            # Créer la relation
            relationship = ProductRelationship(
                parent_sku=parent_sku,
                child_sku=child_sku,
                variation_theme=variation_theme,
                relationship_type='Variation',
                variation_attributes=variation_attributes
            )
            
            variation_family.relationships.append(relationship)
        
        logger.info(f"✅ Created {len(variation_family.relationships)} product relationships")
    
    async def _publish_relationships_feed(self, variation_family: VariationFamily) -> bool:
        """
        Publier les relations via SP-API Feed POST_PRODUCT_RELATIONSHIP_DATA
        """
        try:
            logger.info(f"📤 Publishing relationships feed for family {variation_family.id}")
            
            # Construire le feed XML pour les relations
            feed_content = await self._build_relationships_feed_xml(variation_family)
            
            # Créer le feed via SP-API
            feed_response = await self.sp_api_client.make_request(
                method="POST",
                endpoint="/feeds/2021-06-30/feeds",
                marketplace_id=variation_family.marketplace_id,
                data={
                    "feedType": self.feed_config['feed_type'],
                    "marketplaceIds": [variation_family.marketplace_id],
                    "inputFeedDocumentId": await self._upload_feed_document(feed_content)
                }
            )
            
            if feed_response.get('success'):
                feed_id = feed_response['data']['feedId']
                variation_family.amazon_relationship_feed_id = feed_id
                
                logger.info(f"✅ Feed created: {feed_id}")
                
                # Surveiller le traitement du feed
                processing_success = await self._monitor_feed_processing(feed_id, variation_family.marketplace_id)
                
                if processing_success:
                    variation_family.last_sync_at = datetime.utcnow()
                    logger.info(f"✅ Relationships published successfully for family {variation_family.id}")
                    return True
                else:
                    logger.error(f"❌ Feed processing failed for family {variation_family.id}")
                    return False
            else:
                error_msg = feed_response.get('error', 'Unknown error')
                variation_family.sync_errors.append(f"Feed creation failed: {error_msg}")
                logger.error(f"❌ Feed creation failed: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Error publishing relationships feed: {str(e)}"
            variation_family.sync_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    async def _build_relationships_feed_xml(self, variation_family: VariationFamily) -> str:
        """Construire le contenu XML du feed de relations"""
        
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
    <Header>
        <DocumentVersion>1.01</DocumentVersion>
        <MerchantIdentifier>{self.sp_api_client.merchant_id}</MerchantIdentifier>
    </Header>
    <MessageType>Relationship</MessageType>
    <PurgeAndReplace>{str(self.feed_config['purge_and_replace']).lower()}</PurgeAndReplace>
"""
        
        message_id = 1
        
        # Parent product definition
        xml_content += f"""    <Message>
        <MessageID>{message_id}</MessageID>
        <OperationType>Update</OperationType>
        <Relationship>
            <ParentSKU>{variation_family.parent_sku}</ParentSKU>
            <Relation>
                <Type>Variation</Type>
                <SKU>{variation_family.parent_sku}</SKU>
            </Relation>
        </Relationship>
    </Message>
"""
        
        message_id += 1
        
        # Child relationships
        for relationship in variation_family.relationships:
            xml_content += f"""    <Message>
        <MessageID>{message_id}</MessageID>
        <OperationType>Update</OperationType>
        <Relationship>
            <ParentSKU>{relationship.parent_sku}</ParentSKU>
            <Relation>
                <Type>{relationship.relationship_type}</Type>
                <SKU>{relationship.child_sku}</SKU>
"""
            
            # Ajouter les attributs de variation
            for attr_name, attr_value in relationship.variation_attributes.items():
                xml_content += f"                <{attr_name}>{attr_value}</{attr_name}>\n"
            
            xml_content += """            </Relation>
        </Relationship>
    </Message>
"""
            message_id += 1
        
        xml_content += """</AmazonEnvelope>"""
        
        return xml_content
    
    async def _upload_feed_document(self, feed_content: str) -> str:
        """Uploader le document feed et récupérer l'ID"""
        try:
            # Créer le document feed
            create_doc_response = await self.sp_api_client.make_request(
                method="POST",
                endpoint="/feeds/2021-06-30/documents",
                data={
                    "contentType": "text/xml; charset=UTF-8"
                }
            )
            
            if create_doc_response.get('success'):
                document_data = create_doc_response['data']
                document_id = document_data['feedDocumentId']
                upload_url = document_data['url']
                
                # Uploader le contenu
                async with aiohttp.ClientSession() as session:
                    async with session.put(
                        upload_url,
                        data=feed_content.encode('utf-8'),
                        headers={'Content-Type': 'text/xml; charset=UTF-8'}
                    ) as upload_response:
                        if upload_response.status == 200:
                            logger.info(f"✅ Feed document uploaded: {document_id}")
                            return document_id
                        else:
                            raise Exception(f"Upload failed with status {upload_response.status}")
            else:
                raise Exception(f"Document creation failed: {create_doc_response.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Error uploading feed document: {str(e)}")
            raise
    
    async def _monitor_feed_processing(self, feed_id: str, marketplace_id: str) -> bool:
        """Surveiller le traitement du feed"""
        try:
            max_wait_time = self.feed_config['processing_timeout']
            wait_interval = 30  # Vérifier toutes les 30 secondes
            total_waited = 0
            
            logger.info(f"⏳ Monitoring feed processing: {feed_id}")
            
            while total_waited < max_wait_time:
                # Vérifier le statut du feed
                status_response = await self.sp_api_client.make_request(
                    method="GET",
                    endpoint=f"/feeds/2021-06-30/feeds/{feed_id}",
                    marketplace_id=marketplace_id
                )
                
                if status_response.get('success'):
                    feed_status = status_response['data']['processingStatus']
                    
                    if feed_status == 'DONE':
                        # Vérifier le rapport de traitement
                        processing_success = await self._check_feed_processing_report(feed_id, marketplace_id)
                        return processing_success
                    
                    elif feed_status == 'FATAL':
                        logger.error(f"❌ Feed processing failed with FATAL status")
                        return False
                    
                    elif feed_status in ['IN_QUEUE', 'IN_PROGRESS']:
                        logger.info(f"⏳ Feed status: {feed_status}, waiting...")
                        await asyncio.sleep(wait_interval)
                        total_waited += wait_interval
                    else:
                        logger.warning(f"⚠️ Unknown feed status: {feed_status}")
                        await asyncio.sleep(wait_interval)
                        total_waited += wait_interval
                else:
                    logger.error(f"❌ Could not check feed status: {status_response.get('error')}")
                    return False
            
            logger.error(f"❌ Feed processing timeout after {max_wait_time} seconds")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error monitoring feed processing: {str(e)}")
            return False
    
    async def _check_feed_processing_report(self, feed_id: str, marketplace_id: str) -> bool:
        """Vérifier le rapport de traitement du feed"""
        try:
            # Récupérer le rapport de traitement
            report_response = await self.sp_api_client.make_request(
                method="GET",
                endpoint=f"/feeds/2021-06-30/feeds/{feed_id}/result",
                marketplace_id=marketplace_id
            )
            
            if report_response.get('success'):
                # Le rapport est généralement un lien vers un document
                report_url = report_response.get('data', {}).get('url')
                
                if report_url:
                    # Télécharger et analyser le rapport
                    async with aiohttp.ClientSession() as session:
                        async with session.get(report_url) as response:
                            if response.status == 200:
                                report_content = await response.text()
                                
                                # Analyser le rapport pour détecter les erreurs
                                success = self._analyze_processing_report(report_content)
                                
                                if success:
                                    logger.info("✅ Feed processing completed successfully")
                                else:
                                    logger.error("❌ Feed processing completed with errors")
                                
                                return success
                            else:
                                logger.error(f"❌ Could not download processing report")
                                return False
                else:
                    # Pas de rapport disponible, considérer comme succès
                    logger.info("✅ Feed processing completed (no detailed report)")
                    return True
            else:
                logger.error(f"❌ Could not retrieve processing report: {report_response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking feed processing report: {str(e)}")
            return False
    
    def _analyze_processing_report(self, report_content: str) -> bool:
        """Analyser le contenu du rapport de traitement"""
        
        # Le rapport peut être au format XML ou TSV
        # Chercher les indicateurs d'erreur courants
        
        error_indicators = [
            'Error', 'ERROR', 'Failed', 'FAILED',
            'Invalid', 'INVALID', 'Rejected', 'REJECTED'
        ]
        
        success_indicators = [
            'Success', 'SUCCESS', 'Processed', 'PROCESSED',
            'Complete', 'COMPLETE'
        ]
        
        has_errors = any(indicator in report_content for indicator in error_indicators)
        has_success = any(indicator in report_content for indicator in success_indicators)
        
        if has_errors and not has_success:
            logger.warning("⚠️ Feed processing report indicates errors")
            return False
        
        return True
    
    async def sync_family_inventory_and_pricing(self, variation_family: VariationFamily) -> bool:
        """Synchroniser les stocks et prix d'une famille de variations"""
        try:
            logger.info(f"🔄 Syncing inventory and pricing for family {variation_family.id}")
            
            sync_results = {
                'inventory_synced': 0,
                'pricing_synced': 0,
                'errors': []
            }
            
            # Synchroniser les stocks si activé
            if variation_family.sync_inventory:
                inventory_result = await self._sync_family_inventory(variation_family)
                sync_results['inventory_synced'] = inventory_result['synced_count']
                sync_results['errors'].extend(inventory_result['errors'])
            
            # Synchroniser les prix si activé
            if variation_family.sync_pricing:
                pricing_result = await self._sync_family_pricing(variation_family)
                sync_results['pricing_synced'] = pricing_result['synced_count']
                sync_results['errors'].extend(pricing_result['errors'])
            
            # Mettre à jour la famille
            variation_family.last_sync_at = datetime.utcnow()
            
            if sync_results['errors']:
                variation_family.sync_errors = sync_results['errors'][-10:]  # Garder les 10 dernières erreurs
                logger.warning(f"⚠️ Sync completed with {len(sync_results['errors'])} errors")
            else:
                variation_family.sync_errors = []
                logger.info(f"✅ Sync completed successfully")
            
            return len(sync_results['errors']) == 0
            
        except Exception as e:
            error_msg = f"Error syncing family: {str(e)}"
            variation_family.sync_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    async def _sync_family_inventory(self, variation_family: VariationFamily) -> Dict[str, Any]:
        """Synchroniser les stocks de la famille"""
        # TODO: Implémenter la synchronisation des stocks via Inventory API
        # Simulation pour le développement
        
        return {
            'synced_count': len(variation_family.child_skus),
            'errors': []
        }
    
    async def _sync_family_pricing(self, variation_family: VariationFamily) -> Dict[str, Any]:
        """Synchroniser les prix de la famille"""
        # TODO: Implémenter la synchronisation des prix via Product Pricing API
        # Simulation pour le développement
        
        return {
            'synced_count': len(variation_family.child_skus),
            'errors': []
        }


# Instance globale du moteur de variations
variations_builder_engine = VariationsBuilderEngine()