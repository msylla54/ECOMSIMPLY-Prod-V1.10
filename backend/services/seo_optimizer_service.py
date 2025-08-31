# SEO Optimizer Service - Phase 3
import os
import json
import re
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class SEOOptimizerService:
    """
    Service d'optimisation SEO Amazon avec IA
    Génère titre, bullets, description et backend keywords optimisés
    """
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.openai_api_url = 'https://api.openai.com/v1/chat/completions'
        
        # Règles Amazon A9/A10
        self.amazon_rules = {
            'title_max_chars': 200,
            'bullet_max_chars': 255,
            'bullet_max_count': 5,
            'description_min_chars': 100,
            'description_max_chars': 2000,
            'backend_keywords_max_bytes': 250
        }
        
        # Mots interdits Amazon
        self.forbidden_words = [
            'best', 'meilleur', 'top', 'premium', 'quality', 'qualité',
            'amazing', 'incroyable', 'perfect', 'parfait', 'guaranteed', 'garanti',
            'free shipping', 'livraison gratuite', 'sale', 'solde', 'discount', 'réduction'
        ]
        
    async def optimize_seo_from_scraped_data(
        self, 
        scraped_data: Dict[str, Any],
        target_keywords: List[str] = None,
        optimization_goals: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Optimiser le SEO à partir des données scrapées
        
        Args:
            scraped_data: Données scrapées depuis Amazon
            target_keywords: Mots-clés cibles à intégrer
            optimization_goals: Objectifs d'optimisation (CTR, conversion, etc.)
        
        Returns:
            Dict contenant SEO optimisé et métadonnées
        """
        try:
            logger.info("🚀 Starting SEO optimization from scraped data")
            
            # Extraire les données sources
            current_seo = scraped_data.get('seo_data', {})
            product_data = scraped_data.get('product_data', {})
            price_data = scraped_data.get('price_data', {})
            
            # Construire le contexte pour l'IA
            context = self._build_optimization_context(
                current_seo, product_data, price_data, target_keywords, optimization_goals
            )
            
            # Générer SEO optimisé avec IA
            optimized_seo = await self._generate_optimized_seo_with_ai(context)
            
            # Valider selon les règles Amazon
            validation_result = self._validate_amazon_seo(optimized_seo)
            
            # Score d'optimisation
            optimization_score = self._calculate_optimization_score(
                current_seo, optimized_seo, validation_result
            )
            
            result = {
                'optimized_seo': optimized_seo,
                'validation': validation_result,
                'optimization_score': optimization_score,
                'optimization_metadata': {
                    'optimized_at': datetime.utcnow().isoformat(),
                    'target_keywords': target_keywords or [],
                    'context_used': context,
                    'ai_model': 'gpt-4-turbo-preview',
                    'amazon_rules_applied': True
                },
                'comparison': {
                    'original_title_length': len(current_seo.get('title', '')),
                    'optimized_title_length': len(optimized_seo.get('title', '')),
                    'original_bullets_count': len(current_seo.get('bullet_points', [])),
                    'optimized_bullets_count': len(optimized_seo.get('bullet_points', [])),
                    'keywords_added': len(target_keywords or [])
                }
            }
            
            logger.info(f"✅ SEO optimization completed - Score: {optimization_score}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ SEO optimization failed: {str(e)}")
            return {
                'optimized_seo': {},
                'validation': {'overall_status': 'ERROR', 'errors': [str(e)]},
                'optimization_score': 0,
                'error': str(e)
            }
    
    def _build_optimization_context(
        self,
        current_seo: Dict[str, Any],
        product_data: Dict[str, Any], 
        price_data: Dict[str, Any],
        target_keywords: List[str],
        optimization_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construire le contexte d'optimisation pour l'IA
        """
        context = {
            'current_seo': {
                'title': current_seo.get('title', ''),
                'bullet_points': current_seo.get('bullet_points', []),
                'description': current_seo.get('description', ''),
                'keywords': current_seo.get('extracted_keywords', [])
            },
            'product_info': {
                'brand': product_data.get('brand', ''),
                'categories': product_data.get('categories', []),
                'rating': product_data.get('rating', 0),
                'reviews_count': product_data.get('reviews_count', 0)
            },
            'price_info': {
                'current_price': price_data.get('current_price', 0),
                'currency': price_data.get('currency', 'EUR')
            },
            'optimization_targets': {
                'keywords': target_keywords or [],
                'goals': optimization_goals or {'primary': 'conversion', 'secondary': 'visibility'},
                'language': 'fr',
                'marketplace': 'FR'
            },
            'amazon_constraints': self.amazon_rules
        }
        
        return context
    
    async def _generate_optimized_seo_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Générer SEO optimisé avec OpenAI GPT-4
        """
        if not self.openai_api_key:
            logger.warning("⚠️ OpenAI API key not found, using fallback optimization")
            return self._fallback_seo_optimization(context)
        
        try:
            # Construire le prompt d'optimisation
            prompt = self._build_ai_optimization_prompt(context)
            
            # Appel à l'API OpenAI
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4-turbo-preview',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Tu es un expert en SEO Amazon A9/A10. Tu optimises les listings pour maximiser la visibilité et les conversions. Tu réponds UNIQUEMENT en JSON valide.'
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.openai_api_url, 
                    headers=headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        ai_content = result['choices'][0]['message']['content']
                        
                        # Parser la réponse JSON
                        try:
                            optimized_seo = json.loads(ai_content)
                            logger.info("✅ AI SEO optimization successful")
                            return optimized_seo
                        except json.JSONDecodeError:
                            logger.warning("⚠️ AI response not valid JSON, using fallback")
                            return self._fallback_seo_optimization(context)
                    else:
                        logger.warning(f"⚠️ OpenAI API error {response.status}, using fallback")
                        return self._fallback_seo_optimization(context)
        
        except Exception as e:
            logger.error(f"❌ AI optimization error: {str(e)}, using fallback")
            return self._fallback_seo_optimization(context)
    
    def _build_ai_optimization_prompt(self, context: Dict[str, Any]) -> str:
        """
        Construire le prompt d'optimisation pour l'IA
        """
        current_seo = context['current_seo']
        product_info = context['product_info']
        targets = context['optimization_targets']
        constraints = context['amazon_constraints']
        
        prompt = f"""OPTIMISE ce listing Amazon selon les règles A9/A10 strictes:

DONNÉES ACTUELLES:
- Titre: "{current_seo['title']}"
- Bullets: {current_seo['bullet_points']}
- Description: "{current_seo['description'][:200]}..."
- Marque: {product_info['brand']}
- Note: {product_info['rating']}/5 ({product_info['reviews_count']} avis)

MOTS-CLÉS CIBLES: {', '.join(targets['keywords'])}

CONTRAINTES AMAZON:
- Titre: MAX {constraints['title_max_chars']} caractères
- Bullets: EXACTEMENT 5 points, MAX {constraints['bullet_max_chars']} chars chacun
- Description: {constraints['description_min_chars']}-{constraints['description_max_chars']} caractères
- Backend Keywords: MAX {constraints['backend_keywords_max_bytes']} bytes

RÈGLES STRICTES:
- PAS d'emojis, PAS de mots interdits (best, top, premium, etc.)
- Intégrer naturellement les mots-clés cibles
- Optimiser pour la recherche ET la conversion
- Format bullets: [BÉNÉFICE]: [Description détaillée]

RÉPONDS EN JSON:
{{
  "title": "Titre optimisé (max {constraints['title_max_chars']} chars)",
  "bullet_points": [
    "Point 1 (max {constraints['bullet_max_chars']} chars)",
    "Point 2...",
    "Point 3...",
    "Point 4...",
    "Point 5..."
  ],
  "description": "Description optimisée structurée",
  "backend_keywords": "mot1 mot2 mot3 (français + anglais, max {constraints['backend_keywords_max_bytes']} bytes)"
}}"""
        
        return prompt
    
    def _fallback_seo_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimisation SEO de fallback sans IA
        """
        current_seo = context['current_seo']
        product_info = context['product_info']
        targets = context['optimization_targets']
        
        # Titre optimisé
        brand = product_info.get('brand', '')
        original_title = current_seo.get('title', '')
        target_keywords = targets.get('keywords', [])
        
        # Construire un nouveau titre
        title_parts = []
        if brand:
            title_parts.append(brand)
        
        # Ajouter les mots-clés principaux
        for keyword in target_keywords[:3]:  # Max 3 mots-clés
            if keyword.lower() not in original_title.lower():
                title_parts.append(keyword.title())
        
        # Ajouter des éléments du titre original
        original_clean = re.sub(r'[^\w\s-]', '', original_title)
        title_words = original_clean.split()[:8]  # Max 8 mots du titre original
        title_parts.extend(title_words)
        
        optimized_title = ' '.join(title_parts)[:self.amazon_rules['title_max_chars']]
        
        # Bullets optimisés
        original_bullets = current_seo.get('bullet_points', [])
        optimized_bullets = []
        
        bullet_templates = [
            "QUALITÉ SUPÉRIEURE - {}",
            "UTILISATION FACILE - {}",
            "DESIGN MODERNE - {}", 
            "PERFORMANCE OPTIMALE - {}",
            "SATISFACTION GARANTIE - {}"
        ]
        
        for i, template in enumerate(bullet_templates):
            if i < len(original_bullets):
                content = original_bullets[i][:200]  # Tronquer si trop long
            else:
                content = f"Caractéristique premium {i+1} pour une expérience optimale"
            
            bullet = template.format(content)[:self.amazon_rules['bullet_max_chars']]
            optimized_bullets.append(bullet)
        
        # Description optimisée
        original_description = current_seo.get('description', '')
        optimized_description = f"""Découvrez ce produit {brand} exceptionnel qui allie qualité et performance.

CARACTÉRISTIQUES PRINCIPALES:
{chr(10).join([f'• {bullet.split(" - ")[1] if " - " in bullet else bullet}' for bullet in optimized_bullets[:3]])}

AVANTAGES:
• Qualité certifiée et durabilité garantie
• Installation simple et utilisation intuitive
• Design adapté à tous les besoins

UTILISATION:
Parfait pour un usage quotidien, ce produit s'adapte à vos exigences. 

{original_description[:500] if original_description else 'Description détaillée disponible.'}"""
        
        # Limiter la description
        if len(optimized_description) > self.amazon_rules['description_max_chars']:
            optimized_description = optimized_description[:self.amazon_rules['description_max_chars']-3] + '...'
        
        # Backend keywords
        keywords = []
        keywords.extend(target_keywords)
        keywords.extend(current_seo.get('keywords', [])[:10])
        
        # Ajouter des mots du titre et bullets
        for bullet in optimized_bullets:
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', bullet.lower())
            keywords.extend(words[:2])
        
        # Nettoyer et limiter
        unique_keywords = list(dict.fromkeys([kw.strip().lower() for kw in keywords if kw.strip()]))
        backend_keywords = ' '.join(unique_keywords)
        
        # Respecter la limite de bytes
        while len(backend_keywords.encode('utf-8')) > self.amazon_rules['backend_keywords_max_bytes']:
            unique_keywords.pop()
            backend_keywords = ' '.join(unique_keywords)
        
        return {
            'title': optimized_title,
            'bullet_points': optimized_bullets,
            'description': optimized_description,
            'backend_keywords': backend_keywords
        }
    
    def _validate_amazon_seo(self, seo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valider le SEO selon les règles Amazon A9/A10
        """
        validation = {
            'overall_status': 'APPROVED',
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        # Validation titre
        title = seo_data.get('title', '')
        title_validation = {
            'status': 'APPROVED',
            'length': len(title),
            'issues': []
        }
        
        if len(title) > self.amazon_rules['title_max_chars']:
            title_validation['status'] = 'REJECTED'
            title_validation['issues'].append(f'Titre trop long: {len(title)}/{self.amazon_rules["title_max_chars"]} chars')
            validation['errors'].append('Titre trop long')
        elif len(title) < 15:
            title_validation['status'] = 'WARNING'
            title_validation['issues'].append('Titre potentiellement trop court')
            validation['warnings'].append('Titre court')
        
        # Vérifier mots interdits
        for word in self.forbidden_words:
            if word.lower() in title.lower():
                title_validation['status'] = 'WARNING'
                title_validation['issues'].append(f'Mot potentiellement interdit: {word}')
                validation['warnings'].append(f'Mot suspect: {word}')
        
        validation['details']['title'] = title_validation
        
        # Validation bullets
        bullets = seo_data.get('bullet_points', [])
        bullets_validation = {
            'status': 'APPROVED',
            'count': len(bullets),
            'issues': []
        }
        
        if len(bullets) != 5:
            bullets_validation['status'] = 'WARNING'
            bullets_validation['issues'].append(f'Nombre de bullets: {len(bullets)}/5')
            validation['warnings'].append('Bullets incomplets')
        
        for i, bullet in enumerate(bullets):
            if len(bullet) > self.amazon_rules['bullet_max_chars']:
                bullets_validation['status'] = 'REJECTED'
                bullets_validation['issues'].append(f'Bullet {i+1} trop long: {len(bullet)}/{self.amazon_rules["bullet_max_chars"]}')
                validation['errors'].append(f'Bullet {i+1} trop long')
        
        validation['details']['bullets'] = bullets_validation
        
        # Validation description
        description = seo_data.get('description', '')
        description_validation = {
            'status': 'APPROVED',
            'length': len(description),
            'issues': []
        }
        
        if len(description) < self.amazon_rules['description_min_chars']:
            description_validation['status'] = 'WARNING'
            description_validation['issues'].append(f'Description trop courte: {len(description)}/{self.amazon_rules["description_min_chars"]}')
            validation['warnings'].append('Description courte')
        elif len(description) > self.amazon_rules['description_max_chars']:
            description_validation['status'] = 'REJECTED'
            description_validation['issues'].append(f'Description trop longue: {len(description)}/{self.amazon_rules["description_max_chars"]}')
            validation['errors'].append('Description trop longue')
        
        validation['details']['description'] = description_validation
        
        # Validation backend keywords
        keywords = seo_data.get('backend_keywords', '')
        keywords_validation = {
            'status': 'APPROVED',
            'bytes': len(keywords.encode('utf-8')),
            'issues': []
        }
        
        if len(keywords.encode('utf-8')) > self.amazon_rules['backend_keywords_max_bytes']:
            keywords_validation['status'] = 'REJECTED'
            keywords_validation['issues'].append(f'Keywords trop longs: {len(keywords.encode("utf-8"))}/{self.amazon_rules["backend_keywords_max_bytes"]} bytes')
            validation['errors'].append('Keywords trop longs')
        
        validation['details']['keywords'] = keywords_validation
        
        # Statut global
        if validation['errors']:
            validation['overall_status'] = 'REJECTED'
        elif validation['warnings']:
            validation['overall_status'] = 'WARNING'
        
        return validation
    
    def _calculate_optimization_score(
        self, 
        original_seo: Dict[str, Any], 
        optimized_seo: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> int:
        """
        Calculer le score d'optimisation (0-100)
        """
        score = 0
        
        # Score de base selon validation (50%)
        if validation['overall_status'] == 'APPROVED':
            score += 50
        elif validation['overall_status'] == 'WARNING':
            score += 35
        else:
            score += 10
        
        # Score d'amélioration du contenu (30%)
        original_title_len = len(original_seo.get('title', ''))
        optimized_title_len = len(optimized_seo.get('title', ''))
        
        if optimized_title_len > original_title_len and optimized_title_len <= self.amazon_rules['title_max_chars']:
            score += 10
        
        original_bullets = len(original_seo.get('bullet_points', []))
        optimized_bullets = len(optimized_seo.get('bullet_points', []))
        
        if optimized_bullets >= 5:
            score += 10
        elif optimized_bullets > original_bullets:
            score += 5
        
        original_desc_len = len(original_seo.get('description', ''))
        optimized_desc_len = len(optimized_seo.get('description', ''))
        
        if optimized_desc_len > original_desc_len and optimized_desc_len >= self.amazon_rules['description_min_chars']:
            score += 10
        
        # Score de conformité (20%)
        if not validation['errors']:
            score += 15
        if len(validation['warnings']) <= 2:
            score += 5
        
        return min(100, score)
    
    async def generate_seo_variants(
        self, 
        base_seo: Dict[str, Any], 
        variant_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Générer plusieurs variantes SEO pour A/B testing
        """
        variants = []
        
        try:
            base_title = base_seo.get('title', '')
            base_bullets = base_seo.get('bullet_points', [])
            
            for i in range(variant_count):
                variant = {
                    'variant_id': f'v{i+1}',
                    'title': self._generate_title_variant(base_title, i),
                    'bullet_points': self._generate_bullets_variant(base_bullets, i),
                    'description': base_seo.get('description', ''),  # Garder description de base
                    'backend_keywords': base_seo.get('backend_keywords', '')
                }
                
                # Valider chaque variante
                validation = self._validate_amazon_seo(variant)
                variant['validation'] = validation
                
                variants.append(variant)
            
            logger.info(f"✅ Generated {len(variants)} SEO variants")
            return variants
            
        except Exception as e:
            logger.error(f"❌ Error generating SEO variants: {str(e)}")
            return []
    
    def _generate_title_variant(self, base_title: str, variant_index: int) -> str:
        """
        Générer une variante de titre
        """
        words = base_title.split()
        
        if variant_index == 0:
            # Variante 1: Réorganiser l'ordre
            if len(words) > 3:
                return ' '.join(words[1:] + [words[0]])
        elif variant_index == 1:
            # Variante 2: Ajouter des qualificatifs
            qualifiers = ['Professionnel', 'Premium', 'Haute Qualité', 'Certifié']
            qualifier = qualifiers[variant_index % len(qualifiers)]
            return f"{qualifier} {base_title}"[:self.amazon_rules['title_max_chars']]
        else:
            # Variante 3: Synonymes
            synonyms = {
                'Pro': 'Professionnel',
                'Max': 'Maximum',
                'Plus': 'Avancé'
            }
            
            title_variant = base_title
            for original, synonym in synonyms.items():
                if original in title_variant:
                    title_variant = title_variant.replace(original, synonym)
                    break
            
            return title_variant
        
        return base_title  # Fallback
    
    def _generate_bullets_variant(self, base_bullets: List[str], variant_index: int) -> List[str]:
        """
        Générer une variante de bullets
        """
        if not base_bullets:
            return []
        
        variant_bullets = base_bullets.copy()
        
        if variant_index == 0:
            # Variante 1: Réorganiser l'ordre
            if len(variant_bullets) >= 3:
                variant_bullets[0], variant_bullets[2] = variant_bullets[2], variant_bullets[0]
        elif variant_index == 1:
            # Variante 2: Modifier les préfixes
            prefixes = ['AVANTAGE UNIQUE', 'CARACTÉRISTIQUE', 'BÉNÉFICE CLEF', 'INNOVATION', 'PERFORMANCE']
            for i, bullet in enumerate(variant_bullets):
                if ' - ' in bullet:
                    content = bullet.split(' - ', 1)[1]
                    new_prefix = prefixes[i % len(prefixes)]
                    variant_bullets[i] = f"{new_prefix} - {content}"[:self.amazon_rules['bullet_max_chars']]
        
        return variant_bullets