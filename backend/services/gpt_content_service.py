"""
GPT Content Service - ECOMSIMPLY
✅ TÂCHE 1 : IA Routing par plan avec cost guard et feature flags
Service pour la génération de contenu avec routing intelligent selon les plans
"""

import os
import json
import traceback
import time
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

# Import OpenAI
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ModelFailureTracker:
    """Tracker pour les échecs de modèles - Cost Guard"""
    def __init__(self):
        self.failures = defaultdict(list)  # user_id -> list of timestamps
        self.cost_guard_window = 10  # 10 minutes
        self.failure_threshold = 2   # 2 échecs
    
    def record_failure(self, user_id: str):
        """Enregistrer un échec"""
        now = datetime.utcnow()
        self.failures[user_id].append(now)
        # Nettoyer les anciens échecs
        cutoff = now - timedelta(minutes=self.cost_guard_window)
        self.failures[user_id] = [
            ts for ts in self.failures[user_id] 
            if ts > cutoff
        ]
    
    def should_trigger_cost_guard(self, user_id: str) -> bool:
        """Vérifier si le cost guard doit être déclenché"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.cost_guard_window)
        recent_failures = [
            ts for ts in self.failures[user_id] 
            if ts > cutoff
        ]
        return len(recent_failures) >= self.failure_threshold

# Instance globale du tracker
failure_tracker = ModelFailureTracker()

class GPTContentService:
    """Service pour la génération de contenu IA avec routing intelligent par plan"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.client = None
        
        # ✅ TÂCHE 1: Feature flags
        self.allow_gpt5_for_non_premium = os.environ.get('ALLOW_GPT5_FOR_NON_PREMIUM', 'false').lower() == 'true'
        
        # Configuration des modèles par plan
        self.model_routing = {
            'premium': {
                'primary': 'gpt-4o',  # GPT-5 Pro (simulé par GPT-4o pour le moment)
                'fallback': 'gpt-4-turbo'
            },
            'pro': {
                'primary': 'gpt-4-turbo',
                'fallback': 'gpt-4o' if self.allow_gpt5_for_non_premium else 'gpt-4o-mini'
            },
            'premium': {
                'primary': 'gpt-4-turbo',
                'fallback': 'gpt-4o' if self.allow_gpt5_for_non_premium else 'gpt-4o-mini'
            }
        }
        
        self.supported_languages = {
            'fr': {'name': 'Français', 'ai_instruction': 'Réponds en français professionnel'},
            'en': {'name': 'English', 'ai_instruction': 'Reply in professional English'}
        }
        
        if OPENAI_AVAILABLE and self.openai_key:
            try:
                self.client = AsyncOpenAI(api_key=self.openai_key, timeout=60.0)
            except Exception as e:
                print(f"❌ Erreur initialisation OpenAI: {e}")
    
    async def generate_product_content(
        self,
        product_name: str,
        product_description: str,
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = 'fr',
        user_plan: str = 'premium',
        price_data: Optional[Dict] = None,
        seo_data: Optional[Dict] = None,
        trending_data: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        ✅ TÂCHE 1 : Point d'entrée principal avec routing intelligent par plan
        """
        start_time = time.time()
        
        # Détermination du routing selon le plan
        routing_config = self.model_routing.get(user_plan, self.model_routing['premium'])
        primary_model = routing_config['primary']
        fallback_model = routing_config['fallback']
        
        # Vérification du cost guard
        cost_guard_triggered = False
        if user_id and failure_tracker.should_trigger_cost_guard(user_id):
            cost_guard_triggered = True
            # Utiliser directement le modèle de fallback
            primary_model = fallback_model
            log_info(
                "Cost guard déclenché - utilisation directe du fallback",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                service="GPTContentService",
                cost_guard_triggered=True,
                fallback_model=fallback_model
            )
        
        log_info(
            "Démarrage génération contenu avec routing intelligent",
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan,
            service="GPTContentService",
            operation="generate_content_with_routing",
            primary_model=primary_model,
            fallback_model=fallback_model,
            cost_guard_triggered=cost_guard_triggered
        )
        
        # Variables de tracking
        model_route = f"{primary_model} -> {fallback_model}"
        generation_method = "routing_primary"
        fallback_level = 1
        
        # NIVEAU 1: Tentative avec le modèle principal
        try:
            log_info(
                f"NIVEAU 1: Tentative modèle principal {primary_model}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                model=primary_model
            )
            
            result = await self._generate_with_gpt(
                product_name=product_name,
                product_description=product_description,
                category=category,
                use_case=use_case,
                language=language,
                user_plan=user_plan,
                price_data=price_data,
                seo_data=seo_data,
                trending_data=trending_data,
                model=primary_model,
                user_id=user_id
            )
            
            # ✅ TÂCHE 1: Enrichir la réponse avec les métadonnées de routing
            result.update({
                "model_used": primary_model,
                "generation_method": generation_method,
                "fallback_level": fallback_level,
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "model_route": model_route,
                "cost_guard_triggered": cost_guard_triggered
            })
            
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "GPTContentService",
                "generate_content",
                "success_primary",
                duration_ms=duration_ms,
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                model_used=primary_model,
                fallback_level=fallback_level,
                cost_guard_triggered=cost_guard_triggered
            )
            
            return result
            
        except Exception as e:
            # Enregistrer l'échec pour le cost guard
            if user_id:
                failure_tracker.record_failure(user_id)
            
            log_error(
                f"NIVEAU 1 ÉCHEC: {primary_model}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                error_source="GPTContentService.primary_model",
                exception=e,
                model=primary_model
            )
            
            # NIVEAU 2: Fallback vers le modèle secondaire
            if primary_model != fallback_model:  # Éviter la boucle infinie
                try:
                    log_info(
                        f"NIVEAU 2: Tentative fallback {fallback_model}",
                        user_id=user_id,
                        product_name=product_name,
                        user_plan=user_plan,
                        model=fallback_model
                    )
                    
                    result = await self._generate_with_gpt(
                        product_name=product_name,
                        product_description=product_description,
                        category=category,
                        use_case=use_case,
                        language=language,
                        user_plan=user_plan,
                        price_data=price_data,
                        seo_data=seo_data,
                        trending_data=trending_data,
                        model=fallback_model,
                        user_id=user_id
                    )
                    
                    # ✅ TÂCHE 1: Enrichir la réponse avec les métadonnées de routing
                    result.update({
                        "model_used": fallback_model,
                        "generation_method": "routing_fallback",
                        "fallback_level": 2,
                        "primary_model": primary_model,
                        "fallback_model": fallback_model,
                        "model_route": model_route,
                        "cost_guard_triggered": cost_guard_triggered
                    })
                    
                    duration_ms = (time.time() - start_time) * 1000
                    log_operation(
                        "GPTContentService",
                        "generate_content",
                        "success_fallback",
                        duration_ms=duration_ms,
                        user_id=user_id,
                        product_name=product_name,
                        user_plan=user_plan,
                        model_used=fallback_model,
                        fallback_level=2,
                        primary_model_failed=primary_model,
                        cost_guard_triggered=cost_guard_triggered
                    )
                    
                    return result
                    
                except Exception as e2:
                    # Enregistrer le second échec
                    if user_id:
                        failure_tracker.record_failure(user_id)
                    
                    log_error(
                        f"NIVEAU 2 ÉCHEC: {fallback_model}",
                        user_id=user_id,
                        product_name=product_name,
                        user_plan=user_plan,
                        error_source="GPTContentService.fallback_model",
                        exception=e2,
                        model=fallback_model
                    )
            
            # NIVEAU 3: Fallback intelligent final
            try:
                log_info(
                    "NIVEAU 3: Activation fallback intelligent",
                    user_id=user_id,
                    product_name=product_name,
                    user_plan=user_plan
                )
                
                result = await self._generate_intelligent_fallback(
                    product_name=product_name,
                    product_description=product_description,
                    category=category,
                    user_plan=user_plan,
                    language=language,
                    user_id=user_id
                )
                
                # ✅ TÂCHE 1: Enrichir la réponse avec les métadonnées de routing
                result.update({
                    "model_used": "intelligent_fallback",
                    "generation_method": "intelligent_fallback",
                    "fallback_level": 3,
                    "primary_model": primary_model,
                    "fallback_model": fallback_model,
                    "model_route": f"{model_route} -> intelligent_fallback",
                    "cost_guard_triggered": cost_guard_triggered
                })
                
                duration_ms = (time.time() - start_time) * 1000
                log_operation(
                    "GPTContentService",
                    "generate_content",
                    "success_intelligent_fallback",
                    duration_ms=duration_ms,
                    user_id=user_id,
                    product_name=product_name,
                    user_plan=user_plan,
                    model_used="intelligent_fallback",
                    fallback_level=3,
                    all_ai_models_failed=True,
                    cost_guard_triggered=cost_guard_triggered
                )
                
                return result
                
            except Exception as e3:
                duration_ms = (time.time() - start_time) * 1000
                log_error(
                    "ÉCHEC COMPLET: Tous les niveaux ont échoué",
                    user_id=user_id,
                    product_name=product_name,
                    user_plan=user_plan,
                    error_source="GPTContentService.complete_failure",
                    exception=e3,
                    duration_ms=duration_ms
                )
                
                # Dernière tentative: contenu d'urgence
                return {
                    "generated_title": f"{product_name} - Produit de Qualité",
                    "marketing_description": f"Découvrez {product_name}. {product_description}",
                    "key_features": ["Qualité garantie", "Livraison rapide", "Service client"],
                    "seo_tags": [product_name.lower().replace(' ', '-'), "qualite", "garantie"],
                    "price_suggestions": "Prix compétitif selon le marché",
                    "target_audience": "Consommateurs exigeants",
                    "call_to_action": "Commandez dès maintenant !",
                    "model_used": "emergency_template",
                    "generation_method": "emergency",
                    "fallback_level": 4,
                    "primary_model": primary_model,
                    "fallback_model": fallback_model,
                    "model_route": f"{model_route} -> emergency",
                    "cost_guard_triggered": cost_guard_triggered,
                    "is_ai_generated": False
                }
    
    async def _generate_with_gpt(
        self,
        product_name: str,
        product_description: str,
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = 'fr',
        user_plan: str = 'premium',
        price_data: Optional[Dict] = None,
        seo_data: Optional[Dict] = None,
        trending_data: Optional[Dict] = None,  # ✅ PHASE 5: Données tendance
        model: str = "gpt-4o-mini",
        user_id: Optional[str] = None
    ) -> Dict:
        """Génération avec GPT (4 ou 3.5)"""
        
        if not self.client:
            raise Exception("Client OpenAI non disponible")
        
        # Construction du contexte
        context = self._build_context(price_data, seo_data, trending_data, category, use_case)
        
        # Détermination du niveau utilisateur
        user_level = self._get_user_level(user_plan)
        
        # Construction des prompts
        system_prompt = self._build_system_prompt(user_level, language, category)
        user_prompt = self._build_user_prompt(
            product_name, product_description, category, use_case, 
            language, user_level, context
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"🚀 Appel {model} avec contexte {user_level}")
        
        # Appel OpenAI
        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
            top_p=0.9
        )
        
        response_content = completion.choices[0].message.content
        print(f"✅ {model} Response: {len(response_content)} caractères")
        
        # Parsing JSON avec enrichissement SEO tendance
        result = self._parse_gpt_response(response_content)
        
        # ✅ TÂCHE 2: Enrichissement avec 20 tags SEO uniques avec diversité Jaccard
        if trending_data and trending_data.get('keywords'):
            result = self._enrich_seo_with_20_tags(result, trending_data, product_name, category, user_id)
        
        result["is_ai_generated"] = True
        
        return result
    
    def _build_context(
        self, 
        price_data: Optional[Dict], 
        seo_data: Optional[Dict], 
        trending_data: Optional[Dict],  # ✅ PHASE 5: Données tendance
        category: Optional[str], 
        use_case: Optional[str]
    ) -> str:
        """Construction du contexte pour le prompt avec données tendance"""
        
        context_parts = []
        
        # Contexte prix
        if price_data and price_data.get('found_prices', 0) > 0:
            context_parts.append(f"""
📊 DONNÉES PRIX CONCURRENTS:
- Sources: {', '.join(price_data.get('sites_analyzed', []))}
- Prix moyen: {price_data.get('avg_price', 0):.2f}€
- Stratégies: Agressive {price_data.get('recommended_price_range', {}).get('aggressive', 0):.2f}€ | Compétitive {price_data.get('recommended_price_range', {}).get('competitive', 0):.2f}€ | Premium {price_data.get('recommended_price_range', {}).get('premium', 0):.2f}€
""")
        
        # Contexte SEO
        if seo_data and seo_data.get('keywords'):
            context_parts.append(f"""
🔍 DONNÉES SEO SCRAPÉES:
- Mots-clés: {', '.join(seo_data['keywords'][:5])}
- Titres analysés: {len(seo_data.get('titles', []))}
""")
        
        # ✅ PHASE 5: Contexte tendances
        if trending_data and trending_data.get('keywords'):
            from datetime import datetime
            current_year = datetime.now().year
            keywords_preview = ', '.join(trending_data['keywords'][:6])
            context_parts.append(f"""
📈 MOTS-CLÉS TENDANCE ({trending_data.get('source', 'unknown')}):
- Tendances {current_year}: {keywords_preview}
- Confiance: {trending_data.get('confidence', 0)}%
- Source: {trending_data.get('source', 'static')}
💡 PRIORITÉ ABSOLUE: Intégrer ces mots-clés tendance dans les seo_tags
""")
        
        return "\n".join(context_parts)
    
    def _get_user_level(self, user_plan: str) -> str:
        """Détermination du niveau utilisateur"""
        if user_plan == "premium":
            return "ULTIMATE PREMIUM"
        elif user_plan == "premium":
            return "PRO PREMIUM"
        else:
            return "STANDARD"
    
    def _build_system_prompt(self, user_level: str, language: str, category: Optional[str]) -> str:
        """Construction du prompt système"""
        
        lang_instruction = self.supported_languages.get(language, {}).get('ai_instruction', 'Réponds en français professionnel')
        
        features_count = 6 if user_level == "ULTIMATE PREMIUM" else 5
        seo_count = 6 if user_level == "ULTIMATE PREMIUM" else 5
        description_length = "500+ mots" if user_level == "ULTIMATE PREMIUM" else "300+ mots" if user_level == "PRO PREMIUM" else "150+ mots"
        
        return f"""Tu es ECOMSIMPLY GPT, assistant IA EXCELLENCE pour la génération de fiches produits e-commerce.

NIVEAU: {user_level}
LANGUE: {lang_instruction}

MISSION: Génère une fiche produit PARFAITE optimisée SEO avec pricing intelligence.

CONTRAINTES STRICTES:
1. Titre: 50-70 caractères SEO optimisé
2. Description: {description_length} avec storytelling
3. Caractéristiques: {features_count} features techniques ET émotionnelles
4. SEO Tags: {seo_count} tags longue traîne
5. Prix: Basé sur analyse concurrentielle
6. Audience: Persona détaillé
7. Call-to-action: Personnalisé niveau {user_level}

FORMAT JSON OBLIGATOIRE:
{{
  "generated_title": "Titre SEO 50-70 caractères",
  "marketing_description": "Description {description_length}",
  "key_features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"{', "Feature 6"' if features_count == 6 else ''}],
  "seo_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"{', "tag6"' if seo_count == 6 else ''}],
  "price_suggestions": "Analyse pricing avec stratégies",
  "target_audience": "Persona détaillé",
  "call_to_action": "CTA {user_level}"
}}"""
    
    def _build_user_prompt(
        self, 
        product_name: str, 
        product_description: str, 
        category: Optional[str], 
        use_case: Optional[str],
        language: str, 
        user_level: str, 
        context: str
    ) -> str:
        """Construction du prompt utilisateur"""
        
        return f"""Génère la fiche EXCELLENCE niveau {user_level} pour:

PRODUIT: {product_name}
DESCRIPTION: {product_description}
{f'CATÉGORIE: {category}' if category else ''}
{f'USE-CASE: {use_case}' if use_case else ''}
LANGUE: {language}

{context}

Génère maintenant le JSON complet:"""
    
    def _parse_gpt_response(self, response_content: str) -> Dict:
        """Parsing robuste de la réponse GPT"""
        
        # Nettoyage
        cleaned_response = response_content.strip()
        
        # Suppression des balises markdown
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        cleaned_response = cleaned_response.strip()
        
        try:
            result = json.loads(cleaned_response)
            return result
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            print(f"📄 Contenu: {cleaned_response[:200]}...")
            raise Exception(f"Erreur parsing réponse GPT: {e}")
    
    async def _generate_intelligent_fallback(
        self,
        product_name: str,
        product_description: str,
        category: Optional[str] = None,
        user_plan: str = 'premium',
        language: str = 'fr',
        user_id: Optional[str] = None
    ) -> Dict:
        """Génération de contenu fallback intelligent"""
        
        print("🔄 GÉNÉRATION FALLBACK INTELLIGENT")
        
        # Templates de base par langue
        templates = {
            'fr': {
                'title_template': "{product_name} - {category} de Qualité Supérieure",
                'description_start': "Découvrez le {product_name}, un produit d'exception",
                'features_base': [
                    "Design moderne et élégant",
                    "Qualité premium garantie", 
                    "Installation facile et rapide",
                    "Garantie constructeur incluse",
                    "Service client réactif"
                ],
                'seo_base': [
                    f"{product_name.lower().replace(' ', '-')}",
                    "qualite-premium",
                    "garantie",
                    "livraison-rapide",
                    "service-client"
                ],
                'cta': "Commandez maintenant et profitez de la livraison gratuite !",
                'audience': "Particuliers et professionnels recherchant la qualité"
            },
            'en': {
                'title_template': "{product_name} - Premium Quality {category}",
                'description_start': "Discover the {product_name}, an exceptional product",
                'features_base': [
                    "Modern and elegant design",
                    "Premium quality guaranteed",
                    "Easy and fast installation", 
                    "Manufacturer warranty included",
                    "Responsive customer service"
                ],
                'seo_base': [
                    f"{product_name.lower().replace(' ', '-')}",
                    "premium-quality",
                    "warranty",
                    "fast-delivery",
                    "customer-service"
                ],
                'cta': "Order now and enjoy free delivery!",
                'audience': "Individuals and professionals seeking quality"
            }
        }
        
        template = templates.get(language, templates['fr'])
        
        # Construction fallback
        features_count = 6 if user_plan == "premium" else 5
        seo_count = 6 if user_plan == "premium" else 5
        
        result = {
            "generated_title": template['title_template'].format(
                product_name=product_name,
                category=category or "Produit"
            )[:70],
            
            "marketing_description": f"{template['description_start']}. {product_description} "
                                   f"Ce produit allie performance et design pour répondre à tous vos besoins. "
                                   f"Fabriqué selon les plus hauts standards de qualité, il vous garantit "
                                   f"satisfaction et durabilité. Un choix intelligent pour les connaisseurs.",
            
            "key_features": template['features_base'][:features_count],
            
            "seo_tags": template['seo_base'][:seo_count],
            
            "price_suggestions": "Prix compétitif selon analyse marché. Consultez nos offres spéciales.",
            
            "target_audience": template['audience'],
            
            "call_to_action": template['cta'],
            
            "is_ai_generated": True
        }
        
        print("✅ FALLBACK INTELLIGENT généré")
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


# Instance globale du service
gpt_content_service = GPTContentService()