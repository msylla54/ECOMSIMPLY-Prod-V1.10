# Amazon Listing Generator with AI - Phase 2
import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class AmazonListingGenerator:
    """
    Générateur IA de fiches produits Amazon conformes aux règles A9/A10
    Génère automatiquement : Title, Bullets, Description, Backend Keywords, Images
    """
    
    def __init__(self):
        # Règles Amazon pour la génération
        self.title_rules = {
            'max_length': 200,
            'format': '{Brand} {Model} {Feature} {Size} {Color}',
            'forbidden_words': ['best', 'cheapest', 'guarantee', 'free shipping']
        }
        
        self.bullet_rules = {
            'max_count': 5,
            'max_length': 255,
            'format': 'benefit_focused'
        }
        
        self.description_rules = {
            'min_length': 100,
            'max_length': 2000,
            'format': 'structured_html'
        }
        
        self.keywords_rules = {
            'max_bytes': 250,
            'languages': ['fr', 'en'],
            'separator': ', '
        }
        
        self.image_rules = {
            'min_count': 1,
            'max_count': 9,
            'min_resolution': 1000,
            'background': 'white',
            'format': ['jpg', 'jpeg', 'png']
        }
        
        logger.info("✅ Amazon Listing Generator initialized")
    
    async def generate_amazon_listing(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère une fiche produit Amazon complète par IA
        
        Args:
            product_data: {
                "brand": str,
                "product_name": str, 
                "features": List[str],
                "category": str,
                "target_keywords": List[str],
                "size": Optional[str],
                "color": Optional[str],
                "price": Optional[float],
                "description": Optional[str]
            }
            
        Returns:
            Dict contenant la fiche générée avec title, bullets, description, keywords, images
        """
        try:
            logger.info(f"🤖 Generating Amazon listing for: {product_data.get('product_name')}")
            
            # Validation des données d'entrée
            self._validate_input_data(product_data)
            
            # Génération parallèle des différents éléments
            tasks = [
                self._generate_title(product_data),
                self._generate_bullets(product_data),
                self._generate_description(product_data),
                self._generate_backend_keywords(product_data),
                self._generate_image_requirements(product_data)
            ]
            
            title, bullets, description, keywords, image_reqs = await asyncio.gather(*tasks)
            
            # Assemblage de la fiche complète
            generated_listing = {
                'listing_id': str(uuid.uuid4()),
                'generated_at': datetime.utcnow().isoformat(),
                'product_data': product_data,
                'seo_content': {
                    'title': title,
                    'bullet_points': bullets,
                    'description': description,
                    'backend_keywords': keywords,
                    'image_requirements': image_reqs
                },
                'generation_metadata': {
                    'generator_version': '2.0.0',
                    'rules_applied': ['A9', 'A10', 'Amazon_2025'],
                    'languages': ['fr', 'en'],
                    'optimization_score': await self._calculate_optimization_score(title, bullets, description, keywords)
                }
            }
            
            logger.info(f"✅ Listing generated successfully - Score: {generated_listing['generation_metadata']['optimization_score']}")
            return generated_listing
            
        except Exception as e:
            logger.error(f"❌ Failed to generate Amazon listing: {str(e)}")
            raise
    
    def _validate_input_data(self, product_data: Dict[str, Any]) -> None:
        """Valide les données d'entrée"""
        required_fields = ['brand', 'product_name', 'category']
        missing_fields = [field for field in required_fields if not product_data.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validation des types et longueurs
        if len(product_data['product_name']) < 3:
            raise ValueError("Product name too short")
        
        if len(product_data['brand']) < 2:
            raise ValueError("Brand name too short")
    
    async def _generate_title(self, product_data: Dict[str, Any]) -> str:
        """
        Génère un titre optimisé Amazon selon le format :
        {Brand} {Model} {Feature} {Size} {Color}
        Max 200 caractères
        """
        try:
            brand = product_data['brand'].strip()
            product_name = product_data['product_name'].strip()
            features = product_data.get('features', [])
            size = product_data.get('size', '')
            color = product_data.get('color', '')
            
            # Construction du titre selon les règles Amazon
            title_parts = [brand]
            
            # Ajouter le nom du produit
            if product_name not in title_parts:
                title_parts.append(product_name)
            
            # Ajouter les features principales (max 2)
            main_features = features[:2] if features else []
            for feature in main_features:
                if len(' '.join(title_parts + [feature])) <= 180:  # Garde marge pour size/color
                    title_parts.append(feature)
            
            # Ajouter size et color si fournis
            if size and len(' '.join(title_parts + [size])) <= 190:
                title_parts.append(size)
            
            if color and len(' '.join(title_parts + [color])) <= self.title_rules['max_length']:
                title_parts.append(color)
            
            # Assemblage final
            title = ' '.join(title_parts)
            
            # Nettoyage et optimisation
            title = self._clean_title(title)
            
            # Validation de longueur finale
            if len(title) > self.title_rules['max_length']:
                title = title[:self.title_rules['max_length']].rsplit(' ', 1)[0]
            
            logger.info(f"📝 Generated title ({len(title)} chars): {title}")
            return title
            
        except Exception as e:
            logger.error(f"❌ Title generation failed: {str(e)}")
            # Fallback simple
            return f"{product_data['brand']} {product_data['product_name']}"
    
    async def _generate_bullets(self, product_data: Dict[str, Any]) -> List[str]:
        """
        Génère 5 bullet points maximum focalisés sur les bénéfices
        Max 255 caractères par bullet
        """
        try:
            features = product_data.get('features', [])
            keywords = product_data.get('target_keywords', [])
            category = product_data.get('category', '')
            
            # Templates de bullets orientés bénéfices
            bullet_templates = [
                "🎯 PERFORMANCE SUPÉRIEURE : {feature} pour {benefit}",
                "✅ QUALITÉ GARANTIE : {feature} certifié pour {usage}",
                "🚀 INNOVATION : {feature} avec technologie avancée",
                "💪 DURABILITÉ : {feature} résistant et fiable",
                "🎁 AVANTAGE UNIQUE : {feature} exclusif pour {category}"
            ]
            
            bullets = []
            
            # Générer des bullets basés sur les features
            for i, feature in enumerate(features[:5]):
                if i < len(bullet_templates):
                    template = bullet_templates[i]
                    
                    # Remplacer les placeholders
                    bullet = template.format(
                        feature=feature,
                        benefit=self._get_benefit_for_feature(feature, category),
                        usage=self._get_usage_for_category(category),
                        category=category
                    )
                    
                    # Validation de longueur
                    if len(bullet) > self.bullet_rules['max_length']:
                        bullet = bullet[:self.bullet_rules['max_length']-3] + "..."
                    
                    bullets.append(bullet)
            
            # Si pas assez de features, ajouter des bullets génériques
            while len(bullets) < 3:
                generic_bullets = [
                    f"✨ FACILITÉ D'UTILISATION : Interface intuitive pour {category}",
                    f"🔒 SÉCURITÉ : Conception sûre et fiable",
                    f"🎨 DESIGN ÉLÉGANT : Esthétique moderne et fonctionnelle"
                ]
                
                for generic in generic_bullets:
                    if len(bullets) < 5 and generic not in bullets:
                        bullets.append(generic)
                        break
                break
            
            logger.info(f"📝 Generated {len(bullets)} bullet points")
            return bullets[:5]  # Max 5 bullets
            
        except Exception as e:
            logger.error(f"❌ Bullets generation failed: {str(e)}")
            # Fallback
            return [
                f"✅ {product_data['product_name']} de qualité supérieure",
                f"🎯 Idéal pour {product_data.get('category', 'usage quotidien')}",
                f"💪 Fabriqué par {product_data['brand']}"
            ]
    
    async def _generate_description(self, product_data: Dict[str, Any]) -> str:
        """
        Génère une description structurée en HTML
        100-2000 caractères, riche et lisible
        """
        try:
            brand = product_data['brand']
            product_name = product_data['product_name']
            features = product_data.get('features', [])
            category = product_data.get('category', '')
            description_input = product_data.get('description', '')
            
            # Structure HTML de la description
            html_parts = []
            
            # Introduction
            intro = f"""
            <h3>🌟 {brand} {product_name}</h3>
            <p>Découvrez notre <strong>{product_name}</strong> conçu pour répondre à tous vos besoins en matière de <em>{category}</em>. 
            {brand} vous garantit une qualité exceptionnelle et une performance optimale.</p>
            """
            html_parts.append(intro)
            
            # Caractéristiques principales
            if features:
                html_parts.append("<h4>✨ Caractéristiques principales :</h4>")
                html_parts.append("<ul>")
                for feature in features[:6]:  # Max 6 features
                    html_parts.append(f"<li><strong>{feature}</strong> - Pour une expérience utilisateur optimale</li>")
                html_parts.append("</ul>")
            
            # Section utilisation
            usage_section = f"""
            <h4>🎯 Utilisation recommandée :</h4>
            <p>Ce {product_name} est parfait pour {self._get_usage_for_category(category)}. 
            Sa conception innovante garantit une utilisation simple et efficace au quotidien.</p>
            """
            html_parts.append(usage_section)
            
            # Garantie et support
            warranty_section = f"""
            <h4>🔒 Garantie {brand} :</h4>
            <p>Nous nous engageons à vous fournir un produit de qualité supérieure. 
            Notre service client est à votre disposition pour toute question.</p>
            """
            html_parts.append(warranty_section)
            
            # Description personnalisée si fournie
            if description_input:
                custom_section = f"""
                <h4>📋 Informations complémentaires :</h4>
                <p>{description_input}</p>
                """
                html_parts.append(custom_section)
            
            # Assemblage final
            description = ''.join(html_parts)
            
            # Validation de longueur
            if len(description) > self.description_rules['max_length']:
                # Raccourcir en gardant la structure
                description = description[:self.description_rules['max_length']-100] + "</p>"
            
            logger.info(f"📝 Generated description ({len(description)} chars)")
            return description
            
        except Exception as e:
            logger.error(f"❌ Description generation failed: {str(e)}")
            # Fallback simple
            return f"""
            <h3>{product_data['brand']} {product_data['product_name']}</h3>
            <p>Produit de qualité supérieure conçu pour répondre à vos besoins.</p>
            """
    
    async def _generate_backend_keywords(self, product_data: Dict[str, Any]) -> str:
        """
        Génère les mots-clés backend (FR + EN)
        Max 250 bytes, séparés par des virgules
        """
        try:
            keywords_fr = []
            keywords_en = []
            
            # Keywords basés sur le produit
            product_name = product_data['product_name'].lower()
            brand = product_data['brand'].lower()
            category = product_data.get('category', '').lower()
            
            # Keywords français
            keywords_fr.extend([
                product_name, brand, category,
                f"{brand} {category}",
                f"{category} {brand}",
                "qualité", "premium", "france", "livraison"
            ])
            
            # Keywords anglais
            keywords_en.extend([
                product_name.replace(' ', ''), 
                brand, 
                category.replace(' ', ''),
                "quality", "premium", "brand", "new"
            ])
            
            # Ajouter les keywords fournis
            target_keywords = product_data.get('target_keywords', [])
            for keyword in target_keywords:
                if keyword not in keywords_fr:
                    keywords_fr.append(keyword.lower())
            
            # Ajouter des keywords basés sur les features
            features = product_data.get('features', [])
            for feature in features:
                feature_words = feature.lower().split()
                keywords_fr.extend(feature_words[:2])  # Max 2 mots par feature
            
            # Combiner FR + EN
            all_keywords = list(set(keywords_fr + keywords_en))  # Supprimer doublons
            
            # Assemblage final avec validation de taille
            keywords_string = self.keywords_rules['separator'].join(all_keywords)
            
            # Validation des 250 bytes
            while len(keywords_string.encode('utf-8')) > self.keywords_rules['max_bytes']:
                if all_keywords:
                    all_keywords.pop()
                    keywords_string = self.keywords_rules['separator'].join(all_keywords)
                else:
                    break
            
            logger.info(f"📝 Generated backend keywords ({len(keywords_string.encode('utf-8'))} bytes)")
            return keywords_string
            
        except Exception as e:
            logger.error(f"❌ Keywords generation failed: {str(e)}")
            # Fallback
            return f"{product_data['brand']}, {product_data['product_name']}, {product_data.get('category', '')}"
    
    async def _generate_image_requirements(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère les exigences pour les images du produit
        Min 1000px, fond blanc obligatoire
        """
        try:
            requirements = {
                'main_image': {
                    'description': f"Image principale de {product_data['product_name']} sur fond blanc pur",
                    'min_resolution': f"{self.image_rules['min_resolution']}x{self.image_rules['min_resolution']}",
                    'background': self.image_rules['background'],
                    'format': 'JPEG ou PNG',
                    'position': 'Centré, occupant 85% du cadre',
                    'required': True
                },
                'additional_images': []
            }
            
            # Images supplémentaires suggérées
            additional_suggestions = [
                f"{product_data['product_name']} en utilisation",
                f"Détails et caractéristiques de {product_data['product_name']}",
                f"Comparaison des tailles de {product_data['product_name']}",
                f"{product_data['product_name']} avec accessoires",
                f"Packaging de {product_data['product_name']}"
            ]
            
            for i, suggestion in enumerate(additional_suggestions[:8], 2):  # Max 8 images additionelles
                requirements['additional_images'].append({
                    'image_position': i,
                    'description': suggestion,
                    'min_resolution': f"{self.image_rules['min_resolution']}x{self.image_rules['min_resolution']}",
                    'background': 'Blanc ou contexte approprié',
                    'required': False
                })
            
            requirements['total_count'] = len(requirements['additional_images']) + 1
            requirements['validation_rules'] = self.image_rules
            
            logger.info(f"📸 Generated image requirements for {requirements['total_count']} images")
            return requirements
            
        except Exception as e:
            logger.error(f"❌ Image requirements generation failed: {str(e)}")
            return {
                'main_image': {
                    'description': f"Image de {product_data['product_name']} sur fond blanc",
                    'required': True
                }
            }
    
    async def _calculate_optimization_score(self, title: str, bullets: List[str], 
                                         description: str, keywords: str) -> float:
        """Calcule un score d'optimisation SEO Amazon (0-100)"""
        try:
            score = 0.0
            
            # Score titre (25 points)
            if len(title) >= 20:
                score += 10
            if len(title) <= self.title_rules['max_length']:
                score += 10
            if any(word in title.lower() for word in ['premium', 'qualité', 'pro']):
                score += 5
            
            # Score bullets (25 points)
            if len(bullets) >= 3:
                score += 10
            if all(len(bullet) <= self.bullet_rules['max_length'] for bullet in bullets):
                score += 10
            if any('✅' in bullet or '🎯' in bullet for bullet in bullets):
                score += 5
            
            # Score description (25 points)
            if len(description) >= self.description_rules['min_length']:
                score += 10
            if '<h3>' in description or '<h4>' in description:
                score += 10
            if '<ul>' in description or '<li>' in description:
                score += 5
            
            # Score keywords (25 points)
            keyword_count = len(keywords.split(','))
            if keyword_count >= 5:
                score += 10
            if len(keywords.encode('utf-8')) <= self.keywords_rules['max_bytes']:
                score += 10
            if keyword_count <= 20:  # Pas trop de keywords
                score += 5
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"⚠️ Score calculation failed: {str(e)}")
            return 0.0
    
    # Méthodes utilitaires
    
    def _clean_title(self, title: str) -> str:
        """Nettoie le titre des mots interdits et caractères spéciaux"""
        # Supprimer mots interdits
        for forbidden_word in self.title_rules['forbidden_words']:
            title = re.sub(rf'\b{forbidden_word}\b', '', title, flags=re.IGNORECASE)
        
        # Nettoyer espaces multiples
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _get_benefit_for_feature(self, feature: str, category: str) -> str:
        """Génère un bénéfice pour une caractéristique"""
        benefit_map = {
            'durable': 'une utilisation longue durée',
            'léger': 'un transport facile',
            'compact': 'un gain de place',
            'étanche': 'une protection optimale',
            'silencieux': 'un confort d\'usage'
        }
        
        for key, benefit in benefit_map.items():
            if key in feature.lower():
                return benefit
        
        return f'une meilleure expérience {category}'
    
    def _get_usage_for_category(self, category: str) -> str:
        """Génère une utilisation pour une catégorie"""
        usage_map = {
            'électronique': 'vos besoins technologiques quotidiens',
            'maison': 'améliorer votre intérieur',
            'jardin': 'entretenir votre espace vert',
            'sport': 'vos activités physiques',
            'cuisine': 'préparer vos repas'
        }
        
        for key, usage in usage_map.items():
            if key in category.lower():
                return usage
        
        return 'un usage quotidien optimal'