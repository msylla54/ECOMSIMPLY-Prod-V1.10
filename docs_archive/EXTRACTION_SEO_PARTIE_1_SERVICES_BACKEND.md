# 📋 EXTRACTION SEO AUTOMATIQUE - PARTIE 1: SERVICES BACKEND

## 🎯 SERVICES PRINCIPAUX POUR LA GESTION AUTOMATIQUE DES SEO

### 1. Service de Génération de Contenu GPT (`/app/backend/services/gpt_content_service.py`)

```python
"""
GPT Content Service - ECOMSIMPLY
✅ TÂCHE 1: Service de génération de contenu avec routing IA dynamique
Gestion des modèles GPT selon les plans utilisateur avec fallback intelligent
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

# Import OpenAI integration
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class ModelFailureTracker:
    """✅ TÂCHE 1: Tracker pour Cost Guard - limite les coûts après échecs répétés"""
    
    def __init__(self):
        self.failures = {}  # user_id -> [timestamps]
        self.cost_guard_window_minutes = 10
        self.failure_threshold = 2
    
    def record_failure(self, user_id: str):
        """Enregistre un échec pour un utilisateur"""
        now = datetime.utcnow()
        if user_id not in self.failures:
            self.failures[user_id] = []
        self.failures[user_id].append(now)
    
    def should_trigger_cost_guard(self, user_id: str) -> bool:
        """Détermine si le cost guard doit être déclenché"""
        if user_id not in self.failures:
            return False
        
        # Nettoyer les échecs anciens
        cutoff = datetime.utcnow() - timedelta(minutes=self.cost_guard_window_minutes)
        recent_failures = [f for f in self.failures[user_id] if f > cutoff]
        self.failures[user_id] = recent_failures
        
        return len(recent_failures) >= self.failure_threshold

# Instance globale du tracker
failure_tracker = ModelFailureTracker()

class GPTContentService:
    """Service pour génération de contenu avec routing IA intelligent selon le plan utilisateur"""
    
    def __init__(self):
        # ✅ TÂCHE 1: Configuration du routing par plan
        self.model_routing = {
            'premium': {
                'primary': 'gpt-4o',      # GPT-5 Pro simulé pour Premium
                'fallback': 'gpt-4-turbo'
            },
            'pro': {
                'primary': 'gpt-4-turbo',
                'fallback': 'gpt-4o-mini'
            },
            'gratuit': {
                'primary': 'gpt-4-turbo',
                'fallback': 'gpt-4o-mini'
            }
        }
        
        # Feature flags
        self.allow_gpt5_for_non_premium = os.environ.get('ALLOW_GPT5_FOR_NON_PREMIUM', 'false').lower() == 'true'
        
        # Configuration des langues supportées
        self.supported_languages = {
            'fr': {
                'ai_instruction': 'Réponds en français professionnel et précis',
                'content_focus': 'marché français, expressions locales'
            },
            'en': {
                'ai_instruction': 'Respond in professional and precise English',
                'content_focus': 'international market, clear expressions'
            },
            'de': {
                'ai_instruction': 'Antworte auf professionellem und präzisem Deutsch',
                'content_focus': 'deutscher Markt, lokale Ausdrücke'
            },
            'es': {
                'ai_instruction': 'Responde en español profesional y preciso',
                'content_focus': 'mercado español, expresiones locales'
            },
            'pt': {
                'ai_instruction': 'Responda em português profissional e preciso',
                'content_focus': 'mercado português, expressões locais'
            }
        }
        
        # Client OpenAI
        if OPENAI_AVAILABLE:
            self.client = LlmChat()
        else:
            self.client = None
    
    async def generate_product_content(
        self,
        product_name: str,
        product_description: str,
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = 'fr',
        user_plan: str = 'gratuit',
        user_id: Optional[str] = None,
        price_data: Optional[Dict] = None,
        seo_data: Optional[Dict] = None,
        trending_data: Optional[Dict] = None
    ) -> Dict:
        """
        ✅ TÂCHE 1: Génération de contenu avec routing IA dynamique selon le plan
        Cascade: Modèle principal → Fallback → Fallback intelligent
        """
        
        start_time = time.time()
        
        log_info(
            "Démarrage génération contenu avec routing IA",
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan,
            service="GPTContentService",
            operation="generate_product_content",
            language=language,
            category=category
        )
        
        if not self.client:
            log_error(
                "Client OpenAI indisponible",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                error_source="GPTContentService.openai_unavailable"
            )
            return await self._generate_intelligent_fallback(
                product_name, product_description, category, user_plan, language, user_id
            )
        
        # ✅ TÂCHE 1: Sélection du modèle selon le plan
        routing_config = self.model_routing.get(user_plan, self.model_routing['gratuit'])
        primary_model = routing_config['primary']
        fallback_model = routing_config['fallback']
        
        # Feature flag GPT-5 pour non-premium
        if self.allow_gpt5_for_non_premium and user_plan != 'premium':
            fallback_model = 'gpt-4o'
        
        # ✅ TÂCHE 1: Cost Guard - utiliser directement fallback si trop d'échecs
        cost_guard_triggered = failure_tracker.should_trigger_cost_guard(user_id or "anonymous")
        
        if cost_guard_triggered:
            log_info(
                "Cost Guard déclenché - utilisation directe du fallback",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                service="GPTContentService",
                operation="cost_guard_trigger",
                primary_model=primary_model,
                fallback_model=fallback_model
            )
            
            try:
                result = await self._generate_with_model(
                    fallback_model, product_name, product_description, 
                    category, use_case, language, user_plan, 
                    price_data, seo_data, trending_data, user_id
                )
                result.update({
                    "model_used": fallback_model,
                    "generation_method": "cost_guard_fallback",
                    "fallback_level": 2,
                    "primary_model": primary_model,
                    "fallback_model": fallback_model, 
                    "model_route": f"{primary_model} -> {fallback_model}",
                    "cost_guard_triggered": True
                })
                return result
            except Exception as e:
                log_error(
                    "Échec cost guard fallback",
                    user_id=user_id,
                    product_name=product_name,
                    user_plan=user_plan,
                    error_source="GPTContentService.cost_guard_fallback",
                    exception=e
                )
                # Dernier recours
                return await self._generate_intelligent_fallback(
                    product_name, product_description, category, user_plan, language, user_id
                )
        
        # ✅ TÂCHE 1: Tentative avec modèle principal
        try:
            log_info(
                f"Tentative génération avec modèle principal: {primary_model}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                service="GPTContentService",
                primary_model=primary_model
            )
            
            result = await self._generate_with_model(
                primary_model, product_name, product_description,
                category, use_case, language, user_plan,
                price_data, seo_data, trending_data, user_id
            )
            
            result.update({
                "model_used": primary_model,
                "generation_method": "routing_primary",
                "fallback_level": 1,
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "model_route": f"{primary_model} -> {fallback_model}",
                "cost_guard_triggered": False
            })
            
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "GPTContentService",
                "generate_content_primary",
                "success",
                duration_ms=duration_ms,
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                model_used=primary_model
            )
            return result
            
        except Exception as primary_error:
            log_error(
                f"Échec modèle principal {primary_model}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                error_source="GPTContentService.primary_model",
                exception=primary_error
            )
            
            # Enregistrer l'échec pour le cost guard
            if user_id:
                failure_tracker.record_failure(user_id)
        
        # ✅ TÂCHE 1: Tentative avec modèle de fallback
        try:
            log_info(
                f"Tentative génération avec modèle fallback: {fallback_model}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                service="GPTContentService",
                fallback_model=fallback_model
            )
            
            result = await self._generate_with_model(
                fallback_model, product_name, product_description,
                category, use_case, language, user_plan,
                price_data, seo_data, trending_data, user_id
            )
            
            result.update({
                "model_used": fallback_model,
                "generation_method": "routing_fallback", 
                "fallback_level": 2,
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "model_route": f"{primary_model} -> {fallback_model}",
                "cost_guard_triggered": False
            })
            
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "GPTContentService",
                "generate_content_fallback",
                "success", 
                duration_ms=duration_ms,
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                model_used=fallback_model
            )
            return result
            
        except Exception as fallback_error:
            log_error(
                f"Échec modèle fallback {fallback_model}",
                user_id=user_id, 
                product_name=product_name,
                user_plan=user_plan,
                error_source="GPTContentService.fallback_model",
                exception=fallback_error
            )
            
            # Enregistrer l'échec pour le cost guard
            if user_id:
                failure_tracker.record_failure(user_id)
        
        # ✅ TÂCHE 1: Fallback intelligent final
        log_info(
            "Utilisation du fallback intelligent final",
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan,
            service="GPTContentService",
            operation="intelligent_fallback"
        )
        
        result = await self._generate_intelligent_fallback(
            product_name, product_description, category, user_plan, language, user_id
        )
        
        result.update({
            "model_used": "intelligent_fallback",
            "generation_method": "intelligent_template",
            "fallback_level": 4,
            "primary_model": primary_model,
            "fallback_model": fallback_model,
            "model_route": f"{primary_model} -> {fallback_model} -> intelligent_fallback",
            "cost_guard_triggered": False
        })
        
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            "GPTContentService",
            "generate_content_intelligent_fallback",
            "success",
            duration_ms=duration_ms,
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan
        )
        
        return result
    
    def _enrich_seo_with_20_tags(
        self,
        result: Dict,
        trending_data: Dict,
        product_name: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ TÂCHE 2: Enrichissement avec 20 tags SEO uniques avec diversité Jaccard
        """
        # Import du générateur de tags 
        from .seo_scraping_service import SEOTagGenerator
        
        tag_generator = SEOTagGenerator()
        
        log_info(
            "Enrichissement avec 20 tags SEO",
            user_id=user_id,
            product_name=product_name,
            service="GPTContentService",
            operation="enrich_20_tags",
            trending_keywords_count=len(trending_data.get('keywords', [])),
            ai_tags_count=len(result.get('seo_tags', []))
        )
        
        # Génération des 20 tags
        tag_result = tag_generator.generate_20_seo_tags(
            product_name=product_name,
            category=category,
            trending_keywords=trending_data.get('keywords', []),
            ai_generated_tags=result.get('seo_tags', []),
            user_id=user_id
        )
        
        # Mise à jour du résultat
        result['seo_tags'] = tag_result['tags']
        result['seo_tags_count'] = tag_result['count']
        result['seo_tags_source'] = 'mixed' if tag_result['source_breakdown']['trending'] > 0 else 'ai_static'
        result['seo_diversity_score'] = tag_result['diversity_score']
        result['seo_source_breakdown'] = tag_result['source_breakdown']
        result['seo_validation_passed'] = tag_result['validation_passed']
        result['seo_target_reached'] = tag_result['target_reached']
        
        log_info(
            "20 tags SEO générés avec succès",
            user_id=user_id,
            product_name=product_name,
            service="GPTContentService",
            tags_count=tag_result['count'],
            diversity_score=tag_result['diversity_score'],
            target_reached=tag_result['target_reached'],
            **tag_result['source_breakdown']
        )
        
        return result
```

### 2. Service de Scraping SEO (`/app/backend/services/seo_scraping_service.py`)

```python
"""
SEO Scraping Service - ECOMSIMPLY
✅ TÂCHE 2 : Service pour le scraping concurrentiel et l'extraction de données SEO
Génération de 20 tags uniques avec diversité Jaccard < 0.7
"""

import aiohttp
import asyncio
import time
import math
from aiohttp_retry import RetryClient, ExponentialRetry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Set

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

class SEOTagGenerator:
    """✅ TÂCHE 2 : Générateur de tags SEO avec diversité Jaccard"""
    
    def __init__(self):
        self.target_tag_count = 20
        self.max_jaccard_similarity = 0.7
        self.min_tag_length = 2
        self.max_tag_length = 5  # 2-5 mots par tag
    
    def calculate_jaccard_similarity(self, tag1: str, tag2: str) -> float:
        """Calcule la similarité Jaccard entre deux tags"""
        words1 = set(tag1.lower().split('-'))
        words2 = set(tag2.lower().split('-'))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def is_diverse_enough(self, new_tag: str, existing_tags: List[str]) -> bool:
        """Vérifie si un nouveau tag est suffisamment diversifié"""
        for existing_tag in existing_tags:
            similarity = self.calculate_jaccard_similarity(new_tag, existing_tag)
            if similarity >= self.max_jaccard_similarity:
                return False
        return True
    
    def validate_tag_format(self, tag: str) -> bool:
        """Valide le format d'un tag (2-5 mots)"""
        if not tag or not tag.strip():
            return False
        
        words = tag.split('-')
        word_count = len([w for w in words if w.strip()])
        
        return self.min_tag_length <= word_count <= self.max_tag_length
    
    def generate_20_seo_tags(
        self,
        product_name: str,
        category: Optional[str] = None,
        trending_keywords: Optional[List[str]] = None,
        ai_generated_tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ TÂCHE 2 : Génère 20 tags SEO uniques avec diversité Jaccard
        Priorité : tendances (8 max) → tags IA → complétion statique
        """
        log_info(
            "Démarrage génération 20 tags SEO",
            user_id=user_id,
            product_name=product_name,
            service="SEOTagGenerator",
            operation="generate_20_seo_tags",
            trending_count=len(trending_keywords or []),
            ai_tags_count=len(ai_generated_tags or [])
        )
        
        final_tags = []
        source_info = {"trending": 0, "ai": 0, "static": 0}
        
        # PHASE 1: Priorité aux mots-clés tendance (max 8)
        if trending_keywords:
            for keyword in trending_keywords[:8]:  # Maximum 8 tendances
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(keyword)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["trending"] += 1
        
        # PHASE 2: Tags générés par IA
        if ai_generated_tags and len(final_tags) < self.target_tag_count:
            for ai_tag in ai_generated_tags:
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(ai_tag)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["ai"] += 1
        
        # PHASE 3: Complétion avec tags statiques
        if len(final_tags) < self.target_tag_count:
            static_tags = self._generate_comprehensive_static_tags(product_name, category)
            
            for static_tag in static_tags:
                if len(final_tags) >= self.target_tag_count:
                    break
                
                clean_tag = self._clean_and_format_tag(static_tag)
                if (clean_tag and 
                    self.validate_tag_format(clean_tag) and 
                    self.is_diverse_enough(clean_tag, final_tags) and
                    clean_tag not in final_tags):
                    
                    final_tags.append(clean_tag)
                    source_info["static"] += 1
        
        # Validation finale de la diversité
        diversity_scores = self._calculate_diversity_matrix(final_tags)
        avg_diversity = sum(diversity_scores) / len(diversity_scores) if diversity_scores else 1.0
        
        result = {
            "tags": final_tags,
            "count": len(final_tags),
            "target_reached": len(final_tags) == self.target_tag_count,
            "source_breakdown": source_info,
            "diversity_score": round(1.0 - avg_diversity, 3),  # Plus haut = plus diversifié
            "average_jaccard": round(avg_diversity, 3),
            "validation_passed": all(self.validate_tag_format(tag) for tag in final_tags)
        }
        
        log_operation(
            "SEOTagGenerator",
            "generate_20_seo_tags",
            "success",
            user_id=user_id,
            product_name=product_name,
            tags_generated=len(final_tags),
            target_reached=result["target_reached"],
            diversity_score=result["diversity_score"],
            **source_info
        )
        
        return result

class SEOScrapingService:
    """Service pour le scraping SEO et analyse concurrentielle avec génération de 20 tags"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.tag_generator = SEOTagGenerator()  # ✅ TÂCHE 2
        
    async def fetch_trending_keywords(
        self,
        product_name: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ PHASE 5: Récupération de mots-clés tendance avec source tracking
        Retourne: {"keywords": [...], "source": "trending|static", "confidence": 0-100}
        """
        
        log_info(
            "Recherche mots-clés tendance",
            user_id=user_id,
            product_name=product_name,
            service="SEOScrapingService",
            operation="fetch_trending_keywords",
            category=category
        )
        
        trending_keywords = []
        confidence_score = 0
        source = "static"  # Par défaut
        
        try:
            # Base de données de tendances simulée (mise à jour régulièrement)
            trends_database = {
                "électronique": {
                    "2024": ["eco-responsable", "intelligence-artificielle", "5g", "durabilite", "reconditionne"],
                    "seasonal": ["black-friday", "cyber-monday", "rentrée", "noel"]
                },
                "smartphone": {
                    "2024": ["camera-pro", "batterie-longue-duree", "ecran-oled", "charge-rapide", "photo-nuit"],
                    "seasonal": ["comparatif-2024", "meilleur-rapport-qualite-prix"]
                },
                "mode": {
                    "2024": ["mode-durable", "seconde-main", "upcycling", "slow-fashion", "made-in-france"],
                    "seasonal": ["tendance-automne", "collection-hiver", "soldes"]
                },
                "beauté": {
                    "2024": ["cosmetique-bio", "zero-dechet", "skincare-routine", "anti-age-naturel", "vegan"],
                    "seasonal": ["routine-hiver", "protection-solaire"]
                }
            }
            
            # Recherche des tendances pour la catégorie
            category_trends = []
            if category and category.lower() in trends_database:
                category_trends.extend(trends_database[category.lower()].get("2024", []))
                category_trends.extend(trends_database[category.lower()].get("seasonal", []))
                source = "trending"
                confidence_score = 75
            
            # Génération de mots-clés tendance spécifiques au produit
            product_based_trends = []
            
            # Tendances 2024 génériques
            general_2024_trends = [
                "2024", "nouveau", "derniere-generation", "eco-friendly", 
                "innovation", "performance", "qualite-prix", "livraison-rapide"
            ]
            
            # Sélection intelligente basée sur le produit
            for trend in general_2024_trends[:3]:  # Top 3 tendances générales
                product_based_trends.append(f"{product_name.lower().replace(' ', '-')}-{trend}")
            
            # Combinaison des différentes sources
            all_trends = category_trends + product_based_trends
            
            # Nettoyage et validation
            for trend in all_trends[:8]:  # Maximum 8 tendances
                clean_trend = self._clean_keyword(trend)
                if clean_trend and len(clean_trend) > 3:
                    trending_keywords.append(clean_trend)
            
            # Augmenter le score de confiance si on a trouvé des tendances
            if trending_keywords:
                if source == "static":
                    source = "trending"
                    confidence_score = 50
        
        except Exception as e:
            log_error(
                "Erreur récupération mots-clés tendance",
                user_id=user_id,
                product_name=product_name,
                error_source="SEOScrapingService.fetch_trending_keywords",
                exception=e
            )
            
            # Fallback vers statique
            trending_keywords = self._generate_static_keywords(product_name, category)
            source = "static"
            confidence_score = 20
        
        result = {
            "keywords": trending_keywords,
            "source": source,
            "confidence": confidence_score,
            "total_found": len(trending_keywords)
        }
        
        log_operation(
            "SEOScrapingService",
            "fetch_trending_keywords",
            "success",
            user_id=user_id,
            product_name=product_name,
            keywords_count=len(trending_keywords),
            source=source,
            confidence=confidence_score
        )
        
        return result
```