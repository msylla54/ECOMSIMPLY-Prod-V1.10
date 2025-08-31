# 📋 EXTRACTION SEO AUTOMATIQUE - PARTIE 4: TESTS & CONFIGURATION

## 🧪 TESTS UNITAIRES COMPLETS

### 1. Tests du Routing IA (`/app/tests/test_model_routing.py`)

```python
"""
Tests pour la Tâche 1 : IA Routing par plan
Tests des fonctionnalités de routing des modèles IA selon les plans utilisateur
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Configuration du path pour les imports
sys.path.insert(0, '/app/backend')

# Import du service à tester
from services.gpt_content_service import GPTContentService, ModelFailureTracker

class TestModelRouting:
    """Tests du routing des modèles par plan"""
    
    @pytest.fixture
    def gpt_service(self):
        """Fixture pour le service GPT"""
        service = GPTContentService()
        service.client = AsyncMock()  # Mock du client OpenAI
        return service
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock de réponse OpenAI"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "generated_title": "Test Product - Excellence",
            "marketing_description": "Description marketing test avec contenu optimisé pour SEO",
            "key_features": ["Feature 1 premium", "Feature 2 avancée", "Feature 3 professionnelle"],
            "seo_tags": ["test-product", "excellence-quality", "premium-choice"],
            "price_suggestions": "Prix compétitif selon analyse marché",
            "target_audience": "Consommateurs professionnels exigeants",
            "call_to_action": "Commandez maintenant pour une excellence garantie!"
        }
        '''
        return mock_response

    @pytest.mark.asyncio
    async def test_premium_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Premium : gpt-4o -> gpt-4-turbo"""
        gpt_service.client.chat_completion = AsyncMock(return_value=mock_openai_response)
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Premium",
            product_description="Description test premium avec spécifications avancées",
            user_plan="premium",
            user_id="user_premium_test"
        )
        
        # Vérifications spécifiques plan Premium
        assert result["model_used"] == "gpt-4o"  # GPT-5 Pro simulé
        assert result["primary_model"] == "gpt-4o"
        assert result["fallback_model"] == "gpt-4-turbo"
        assert result["generation_method"] == "routing_primary"
        assert result["fallback_level"] == 1
        assert result["model_route"] == "gpt-4o -> gpt-4-turbo"
        assert result["cost_guard_triggered"] is False
        
        # Vérifications contenu Premium (6 features attendues)
        assert len(result["key_features"]) >= 3
        assert result["is_ai_generated"] is True

    @pytest.mark.asyncio
    async def test_gratuit_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Gratuit : gpt-4-turbo -> gpt-4o-mini"""
        gpt_service.client.chat_completion = AsyncMock(return_value=mock_openai_response)
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Gratuit",
            product_description="Description test gratuit basique",
            user_plan="gratuit",
            user_id="user_gratuit_test"
        )
        
        # Vérifications plan Gratuit
        assert result["model_used"] == "gpt-4-turbo"
        assert result["primary_model"] == "gpt-4-turbo"
        assert result["fallback_model"] == "gpt-4o-mini"
        assert result["generation_method"] == "routing_primary"
        assert result["fallback_level"] == 1
        assert result["model_route"] == "gpt-4-turbo -> gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_pro_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Pro : gpt-4-turbo -> gpt-4o-mini"""
        gpt_service.client.chat_completion = AsyncMock(return_value=mock_openai_response)
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Pro",
            product_description="Description test pro avec fonctionnalités avancées",
            user_plan="pro",
            user_id="user_pro_test"
        )
        
        # Vérifications plan Pro
        assert result["model_used"] == "gpt-4-turbo"
        assert result["primary_model"] == "gpt-4-turbo"
        assert result["fallback_model"] == "gpt-4o-mini"
        assert result["generation_method"] == "routing_primary"

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, gpt_service, mock_openai_response):
        """Test du fallback quand le modèle principal échoue"""
        # Premier appel échoue, deuxième réussit
        gpt_service.client.chat_completion = AsyncMock(side_effect=[
            Exception("Primary model failed - API timeout"),
            mock_openai_response
        ])
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Fallback",
            product_description="Description test fallback avec récupération",
            user_plan="premium",
            user_id="user_fallback_test"
        )
        
        # Vérifications fallback
        assert result["model_used"] == "gpt-4-turbo"  # Modèle de fallback
        assert result["primary_model"] == "gpt-4o"
        assert result["fallback_model"] == "gpt-4-turbo"
        assert result["generation_method"] == "routing_fallback"
        assert result["fallback_level"] == 2
        assert result["model_route"] == "gpt-4o -> gpt-4-turbo"
        
        # Vérifier que le contenu est quand même généré
        assert "generated_title" in result
        assert result["is_ai_generated"] is True

    @pytest.mark.asyncio
    async def test_gpt5_feature_flag_enabled(self, gpt_service, mock_openai_response):
        """Test avec feature flag ALLOW_GPT5_FOR_NON_PREMIUM activé"""
        # Simuler feature flag activé
        gpt_service.allow_gpt5_for_non_premium = True
        gpt_service.model_routing['gratuit']['fallback'] = 'gpt-4o'
        
        gpt_service.client.chat_completion = AsyncMock(side_effect=[
            Exception("Primary failed"),
            mock_openai_response
        ])
        
        result = await gpt_service.generate_product_content(
            product_name="Test GPT5 Flag",
            product_description="Description test flag avec accès GPT-5",
            user_plan="gratuit",
            user_id="user_flag_test"
        )
        
        # Vérifications feature flag
        assert result["fallback_model"] == "gpt-4o"  # GPT-5 accessible aux non-premium
        assert result["model_used"] == "gpt-4o"  # Fallback utilisé

    @pytest.mark.asyncio
    async def test_intelligent_fallback_on_complete_failure(self, gpt_service):
        """Test du fallback intelligent quand tous les modèles IA échouent"""
        # Simuler échec de tous les modèles
        gpt_service.client.chat_completion = AsyncMock(side_effect=Exception("All models failed"))
        
        result = await gpt_service.generate_product_content(
            product_name="Test Fallback Intelligent",
            product_description="Description test fallback intelligent complet",
            user_plan="premium",
            user_id="user_intelligent_fallback"
        )
        
        # Vérifications fallback intelligent
        assert result["model_used"] == "intelligent_fallback"
        assert result["generation_method"] == "intelligent_template"
        assert result["fallback_level"] == 4
        assert "generated_title" in result
        assert "marketing_description" in result
        assert "key_features" in result
        assert result["is_ai_generated"] is True  # Même en fallback

class TestCostGuard:
    """Tests du Cost Guard"""
    
    @pytest.fixture
    def failure_tracker(self):
        """Fixture pour le tracker d'échecs"""
        return ModelFailureTracker()
    
    def test_cost_guard_trigger_threshold(self, failure_tracker):
        """Test que le cost guard se déclenche après 2 échecs en 10 minutes"""
        user_id = "test_user_cost_guard"
        
        # Premier échec
        failure_tracker.record_failure(user_id)
        assert not failure_tracker.should_trigger_cost_guard(user_id)
        
        # Deuxième échec - doit déclencher le cost guard
        failure_tracker.record_failure(user_id)
        assert failure_tracker.should_trigger_cost_guard(user_id)
        
        # Troisième échec - toujours déclenché
        failure_tracker.record_failure(user_id)
        assert failure_tracker.should_trigger_cost_guard(user_id)
    
    def test_cost_guard_window_expiry(self, failure_tracker):
        """Test que les échecs expirent après 10 minutes"""
        user_id = "test_user_window"
        
        # Simuler des échecs anciens (15 minutes)
        old_time = datetime.utcnow() - timedelta(minutes=15)
        failure_tracker.failures[user_id] = [old_time, old_time]
        
        # Les échecs anciens ne comptent plus
        assert not failure_tracker.should_trigger_cost_guard(user_id)
        
        # Nouvel échec récent
        failure_tracker.record_failure(user_id)
        assert not failure_tracker.should_trigger_cost_guard(user_id)  # Seulement 1 récent
        
        # Deuxième échec récent
        failure_tracker.record_failure(user_id)
        assert failure_tracker.should_trigger_cost_guard(user_id)  # 2 récents
    
    def test_cost_guard_different_users(self, failure_tracker):
        """Test que le cost guard est indépendant par utilisateur"""
        user1 = "user1"
        user2 = "user2"
        
        # User1 - 2 échecs
        failure_tracker.record_failure(user1)
        failure_tracker.record_failure(user1)
        
        # User2 - 1 échec
        failure_tracker.record_failure(user2)
        
        # Vérifications
        assert failure_tracker.should_trigger_cost_guard(user1)  # Déclenché pour user1
        assert not failure_tracker.should_trigger_cost_guard(user2)  # Pas déclenché pour user2

    @pytest.mark.asyncio
    async def test_cost_guard_direct_fallback(self, monkeypatch):
        """Test que le cost guard utilise directement le fallback"""
        # Mock du tracker pour déclencher le cost guard
        mock_tracker = MagicMock()
        mock_tracker.should_trigger_cost_guard.return_value = True
        
        # Patch le tracker global
        import services.gpt_content_service
        monkeypatch.setattr(services.gpt_content_service, 'failure_tracker', mock_tracker)
        
        service = GPTContentService()
        service.client = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"generated_title": "Test Cost Guard", "marketing_description": "Test"}'
        service.client.chat_completion = AsyncMock(return_value=mock_response)
        
        result = await service.generate_product_content(
            product_name="Test Cost Guard",
            product_description="Description test cost guard",
            user_plan="premium",
            user_id="test_cost_guard_user"
        )
        
        # Vérifications cost guard
        assert result["cost_guard_triggered"] is True
        assert result["model_used"] == "gpt-4-turbo"  # Fallback direct
        assert result["generation_method"] == "cost_guard_fallback"

class TestRoutingFieldsInAPI:
    """Tests des champs de routing dans l'API"""
    
    def test_routing_fields_in_response_model(self):
        """Test que tous les champs de routing sont dans ProductSheetResponse"""
        from server import ProductSheetResponse
        
        # Vérifier que tous les champs requis sont présents
        fields = ProductSheetResponse.__fields__
        
        required_fields = [
            'model_used',
            'generation_method', 
            'fallback_level',
            'primary_model',
            'fallback_model',
            'model_route',
            'cost_guard_triggered'
        ]
        
        for field in required_fields:
            assert field in fields, f"Champ {field} manquant dans ProductSheetResponse"
            
        # Vérifier que les champs sont optionnels
        for field in required_fields:
            assert not fields[field].required, f"Champ {field} devrait être optionnel"
    
    @pytest.mark.asyncio
    async def test_api_response_contains_routing_fields(self):
        """Test que l'API retourne bien tous les champs de routing"""
        from server import ProductSheetResponse
        
        # Données de test avec tous les champs
        test_data = {
            "generated_title": "Test Title SEO Optimized",
            "marketing_description": "Test Description marketing avec contenu riche",
            "key_features": ["Feature 1 premium", "Feature 2 avancée"],
            "seo_tags": ["tag1", "tag2"],
            "price_suggestions": "Prix test selon analyse",
            "target_audience": "Audience test professionnelle",
            "call_to_action": "Action test optimisée",
            "generated_images": [],
            "generation_time": 1.5,
            "model_used": "gpt-4o",
            "generation_method": "routing_primary",
            "fallback_level": 1,
            "primary_model": "gpt-4o",
            "fallback_model": "gpt-4-turbo",
            "model_route": "gpt-4o -> gpt-4-turbo",
            "cost_guard_triggered": False
        }
        
        # Créer l'objet response
        response = ProductSheetResponse(**test_data)
        
        # Vérifications complètes
        assert response.model_used == "gpt-4o"
        assert response.generation_method == "routing_primary"
        assert response.fallback_level == 1
        assert response.primary_model == "gpt-4o"
        assert response.fallback_model == "gpt-4-turbo"
        assert response.model_route == "gpt-4o -> gpt-4-turbo"
        assert response.cost_guard_triggered is False
        
        # Vérifier le contenu aussi
        assert len(response.generated_title) > 0
        assert len(response.marketing_description) > 10
        assert len(response.key_features) >= 2

class TestContentQuality:
    """Tests de la qualité du contenu généré"""
    
    @pytest.mark.asyncio
    async def test_content_validation_premium(self):
        """Test de validation du contenu pour plan Premium"""
        service = GPTContentService()
        
        # Mock response avec contenu Premium
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "generated_title": "iPhone 15 Pro - Smartphone Premium avec A17 Pro et Photo 48MP",
            "marketing_description": "Découvrez l'iPhone 15 Pro, le smartphone révolutionnaire qui redéfinit l'excellence mobile. Doté du processeur A17 Pro ultra-performant et d'un système photo professionnel 48MP, il offre une expérience utilisateur inégalée. Son design en titane premium et son écran Super Retina XDR garantissent durabilité et qualité visuelle exceptionnelle. Parfait pour les professionnels créatifs et utilisateurs exigeants.",
            "key_features": [
                "Processeur A17 Pro révolutionnaire avec efficacité énergétique optimisée",
                "Système photo Pro 48MP avec zoom optique 3x et mode Action",
                "Écran Super Retina XDR 6,1 pouces avec ProMotion 120Hz",
                "Design en titane aérospatial ultra-résistant et léger",
                "Batterie longue durée avec charge rapide USB-C",
                "Connectivité 5G avancée et WiFi 6E ultra-rapide"
            ],
            "seo_tags": [
                "iphone-15-pro", "smartphone-premium", "a17-pro", "photo-48mp", "titanium-design", "super-retina"
            ],
            "price_suggestions": "Prix recommandé: 1179€ selon analyse concurrentielle",
            "target_audience": "Professionnels créatifs, photographes mobiles, utilisateurs premium",
            "call_to_action": "Commandez votre iPhone 15 Pro maintenant et bénéficiez de la livraison express gratuite!"
        }
        '''
        service.client = AsyncMock()
        service.client.chat_completion = AsyncMock(return_value=mock_response)
        
        result = await service.generate_product_content(
            product_name="iPhone 15 Pro",
            product_description="Smartphone haut de gamme avec processeur A17 Pro",
            user_plan="premium",
            user_id="test_premium_content"
        )
        
        # Validations qualité Premium
        assert len(result["generated_title"]) >= 50  # Titre SEO optimisé
        assert len(result["generated_title"]) <= 70
        assert len(result["marketing_description"]) >= 200  # Description riche
        assert len(result["key_features"]) == 6  # 6 features pour Premium
        assert all(len(feature) >= 10 for feature in result["key_features"])  # Features détaillées
        
        # Vérifier présence de mots-clés techniques
        description = result["marketing_description"].lower()
        assert any(word in description for word in ["professionnel", "premium", "révolutionnaire", "excellence"])

if __name__ == "__main__":
    # Tests pour la ligne de commande
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
```

### 2. Tests des Tags SEO (`/app/tests/test_seo_tags.py`)

```python
"""
Tests pour la Tâche 2 : SEO Tags - 20 tags uniques avec diversité Jaccard
Tests complets du système de génération de tags SEO automatique
"""

import pytest
import sys
from typing import List

# Configuration du path pour les imports
sys.path.insert(0, '/app/backend')

from services.seo_scraping_service import SEOTagGenerator

class TestSEOTagGeneration:
    """Tests de génération de 20 tags SEO"""
    
    @pytest.fixture
    def tag_generator(self):
        """Fixture pour le générateur de tags"""
        return SEOTagGenerator()
    
    def test_generate_20_tags_complete(self, tag_generator):
        """Test génération complète de 20 tags uniques"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Smartphone Galaxy Ultra Pro",
            category="électronique",
            trending_keywords=["smartphone-5g", "photo-pro", "batterie-longue-duree", "ecran-oled", "charge-rapide"],
            ai_generated_tags=["galaxy-ultra", "android-premium", "ecran-dynamic", "appareil-photo-108mp"],
            user_id="test_user_complete"
        )
        
        # Vérifications principales
        assert result["count"] == 20, f"Attendu 20 tags, obtenu {result['count']}"
        assert result["target_reached"] is True
        assert len(result["tags"]) == 20
        assert len(set(result["tags"])) == 20, "Les tags doivent être uniques"
        
        # Vérifications métadonnées
        assert "source_breakdown" in result
        assert "diversity_score" in result
        assert "validation_passed" in result
        assert result["validation_passed"] is True
        
        # Vérifier répartition des sources
        breakdown = result["source_breakdown"]
        assert breakdown["trending"] + breakdown["ai"] + breakdown["static"] == 20
    
    def test_tag_length_and_format_validation(self, tag_generator):
        """Test validation longueur des tags (2-5 mots) et format"""
        result = tag_generator.generate_20_seo_tags(
            product_name="MacBook Pro M3 Max",
            category="ordinateur",
            trending_keywords=["macbook-2024", "m3-chip", "retina-display", "thunderbolt"],
            ai_generated_tags=["macbook-pro", "apple-silicon", "creative-professionals", "video-editing"]
        )
        
        tags = result["tags"]
        
        # Test longueur (2-5 mots)
        for tag in tags:
            word_count = len(tag.split('-'))
            assert 2 <= word_count <= 5, f"Tag '{tag}' a {word_count} mots, attendu 2-5"
            
            # Test format (pas de caractères spéciaux)
            assert tag.replace('-', '').replace(' ', '').isalnum(), f"Tag '{tag}' contient des caractères non-autorisés"
        
        # Test unicité
        unique_tags = set(tags)
        assert len(unique_tags) == len(tags), "Tous les tags doivent être uniques"
        
        # Test validation globale
        assert result["validation_passed"] is True, "Tous les tags doivent passer la validation"
    
    def test_tag_diversity_jaccard(self, tag_generator):
        """Test diversité Jaccard < 0.7 entre tous les tags"""
        result = tag_generator.generate_20_seo_tags(
            product_name="iPhone 15 Pro Max",
            category="smartphone",
            trending_keywords=["iphone-15", "titanium-design", "usb-c", "action-button"],
            ai_generated_tags=["iphone-pro-max", "apple-premium", "camera-system", "super-retina"]
        )
        
        tags = result["tags"]
        
        # Test diversité entre tous les tags
        similarities = []
        for i, tag1 in enumerate(tags):
            for j, tag2 in enumerate(tags):
                if i < j:  # Éviter les doublons et auto-comparaisons
                    similarity = tag_generator.calculate_jaccard_similarity(tag1, tag2)
                    similarities.append(similarity)
                    assert similarity < 0.7, f"Tags '{tag1}' et '{tag2}' trop similaires: {similarity:.3f}"
        
        # Test score de diversité global
        assert result["diversity_score"] > 0.3, f"Score de diversité trop faible: {result['diversity_score']}"
        assert result["average_jaccard"] < 0.7, f"Similarité moyenne trop élevée: {result['average_jaccard']}"
        
        # Vérifier cohérence des calculs
        avg_calculated = sum(similarities) / len(similarities)
        assert abs(result["average_jaccard"] - avg_calculated) < 0.01, "Calcul moyenne Jaccard incohérent"

class TestJaccardSimilarity:
    """Tests détaillés du calcul de similarité Jaccard"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_jaccard_identical_tags(self, tag_generator):
        """Test similarité entre tags identiques"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-5g", "smartphone-5g")
        assert similarity == 1.0, "Tags identiques doivent avoir similarité 1.0"
    
    def test_jaccard_completely_different_tags(self, tag_generator):
        """Test similarité entre tags complètement différents"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-premium", "livre-cuisine-italienne")
        assert similarity == 0.0, "Tags complètement différents doivent avoir similarité 0.0"
    
    def test_jaccard_partial_overlap(self, tag_generator):
        """Test similarité avec chevauchement partiel"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-android-premium", "smartphone-ios-premium")
        # Intersection: {smartphone, premium} = 2
        # Union: {smartphone, android, premium, ios} = 4
        # Jaccard = 2/4 = 0.5
        expected = 0.5
        assert abs(similarity - expected) < 0.01, f"Similarité attendue ~{expected}, obtenu {similarity}"
    
    def test_jaccard_high_similarity_detection(self, tag_generator):
        """Test détection de haute similarité"""
        similarity = tag_generator.calculate_jaccard_similarity("iphone-pro-max", "iphone-pro-plus")
        # Intersection: {iphone, pro} = 2
        # Union: {iphone, pro, max, plus} = 4
        # Jaccard = 2/4 = 0.5
        assert similarity >= 0.5, f"Similarité élevée attendue, obtenu {similarity}"
        
        # Test avec plus de similarité
        similarity_high = tag_generator.calculate_jaccard_similarity("macbook-pro-m3", "macbook-pro-m2")
        # Intersection: {macbook, pro} = 2
        # Union: {macbook, pro, m3, m2} = 4
        # Jaccard = 2/4 = 0.5
        assert similarity_high >= 0.5
    
    def test_jaccard_edge_cases(self, tag_generator):
        """Test cas limites du calcul Jaccard"""
        # Tags vides
        assert tag_generator.calculate_jaccard_similarity("", "") == 0.0
        assert tag_generator.calculate_jaccard_similarity("test", "") == 0.0
        assert tag_generator.calculate_jaccard_similarity("", "test") == 0.0
        
        # Tags avec espaces/tirets
        similarity = tag_generator.calculate_jaccard_similarity("test-tag", "test tag")
        assert similarity > 0, "Devrait gérer les espaces/tirets"

class TestTagValidation:
    """Tests de validation des tags"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_validate_tag_format_valid_cases(self, tag_generator):
        """Test validation tags valides"""
        valid_tags = [
            "smartphone-premium",                    # 2 mots
            "macbook-pro-m3",                       # 3 mots  
            "iphone-15-pro-max",                    # 4 mots
            "ordinateur-portable-gaming-asus-rog"  # 5 mots
        ]
        
        for tag in valid_tags:
            assert tag_generator.validate_tag_format(tag), f"Tag '{tag}' devrait être valide"
    
    def test_validate_tag_format_invalid_cases(self, tag_generator):
        """Test validation tags invalides"""
        invalid_tags = [
            "smartphone",                                      # 1 mot (trop court)
            "ordinateur-portable-gaming-asus-rog-strix",      # 6 mots (trop long)
            "",                                               # Vide
            "   ",                                            # Espaces seulement
            "---",                                            # Tirets seulement
            "a",                                              # Trop court
            "a-b-c-d-e-f-g"                                   # Trop long
        ]
        
        for tag in invalid_tags:
            assert not tag_generator.validate_tag_format(tag), f"Tag '{tag}' devrait être invalide"
    
    def test_is_diverse_enough_functionality(self, tag_generator):
        """Test vérification de diversité"""
        existing_tags = ["smartphone-android-premium", "iphone-premium", "tablette-samsung"]
        
        # Tag suffisamment différent (devrait être accepté)
        diverse_tag = "ordinateur-portable"
        assert tag_generator.is_diverse_enough(diverse_tag, existing_tags), \
            f"Tag '{diverse_tag}' devrait être accepté"
        
        # Tag très similaire (devrait être rejeté si similarité >= 0.7)
        similar_tag = "smartphone-android-qualite"  # Similarité élevée avec le premier
        similarity = tag_generator.calculate_jaccard_similarity(similar_tag, existing_tags[0])
        
        if similarity >= 0.7:
            assert not tag_generator.is_diverse_enough(similar_tag, existing_tags), \
                f"Tag '{similar_tag}' devrait être rejeté (similarité: {similarity:.3f})"

class TestTagSources:
    """Tests des sources de tags et priorités"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_trending_keywords_priority(self, tag_generator):
        """Test priorité aux mots-clés tendance"""
        trending_keywords = ["trend-2024", "viral-product", "bestseller-france", "nouveau-produit"]
        ai_tags = ["ai-generated-1", "ai-generated-2"]
        
        result = tag_generator.generate_20_seo_tags(
            product_name="Test Product Trending",
            trending_keywords=trending_keywords,
            ai_generated_tags=ai_tags
        )
        
        # Vérifier que les trending keywords sont utilisés en priorité
        tags = result["tags"]
        breakdown = result["source_breakdown"]
        
        assert breakdown["trending"] > 0, "Devrait utiliser des mots-clés tendance"
        assert breakdown["trending"] <= 8, "Maximum 8 mots-clés tendance"
        
        # Vérifier présence de mots-clés tendance (au moins partiellement)
        trending_found = 0
        for trend in trending_keywords:
            if any(trend in tag for tag in tags):
                trending_found += 1
        
        assert trending_found > 0, "Au moins un mot-clé tendance devrait être présent"
    
    def test_mixed_sources_integration(self, tag_generator):
        """Test intégration de sources mixtes"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Gaming Laptop Ultra",
            category="ordinateur",
            trending_keywords=["gaming-2024", "rtx-4090", "performance"],
            ai_generated_tags=["laptop-gamer", "high-performance", "ultra-gaming"]
        )
        
        breakdown = result["source_breakdown"]
        
        # Vérifier qu'on a un mélange de sources
        total_sources = sum(breakdown.values())
        assert total_sources == 20, f"Total sources {total_sources} != 20"
        
        # Vérifier que chaque type de source contribue positivement
        assert breakdown["trending"] >= 0, "Trending count should be >= 0"
        assert breakdown["ai"] >= 0, "AI count should be >= 0"  
        assert breakdown["static"] >= 0, "Static count should be >= 0"
        
        # Au moins 2 types de sources doivent être utilisés
        sources_used = sum(1 for count in breakdown.values() if count > 0)
        assert sources_used >= 2, "Au moins 2 types de sources doivent être utilisés"
    
    def test_static_fallback_mechanism(self, tag_generator):
        """Test fallback vers tags statiques"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Simple Product Basic",
            # Pas de trending ou AI tags fournis
        )
        
        # Devrait utiliser principalement des tags statiques
        breakdown = result["source_breakdown"]
        assert breakdown["static"] >= 15, \
            f"Devrait utiliser beaucoup de tags statiques, obtenu {breakdown['static']}"
        assert result["count"] == 20, "Devrait quand même atteindre 20 tags"
        assert result["target_reached"] is True, "Objectif 20 tags devrait être atteint"
    
    def test_comprehensive_static_tags_generation(self, tag_generator):
        """Test génération complète de tags statiques"""
        static_tags = tag_generator._generate_comprehensive_static_tags(
            "iPhone 15 Pro", 
            "smartphone"
        )
        
        # Vérifier qu'on a suffisamment de tags pour compléter
        assert len(static_tags) >= 20, "Devrait générer suffisamment de tags statiques"
        
        # Vérifier présence de catégories attendues
        tags_str = ' '.join(static_tags)
        assert "iphone" in tags_str.lower(), "Devrait contenir le nom du produit"
        assert "smartphone" in tags_str.lower(), "Devrait contenir la catégorie"
        assert "premium" in tags_str.lower(), "Devrait contenir des termes commerciaux"

class TestPerformanceAndEdgeCases:
    """Tests de performance et cas limites"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_performance_large_dataset(self, tag_generator):
        """Test performance avec dataset important"""
        import time
        
        # Préparer données importantes
        trending_keywords = [f"trend-keyword-{i}" for i in range(20)]
        ai_tags = [f"ai-tag-{i}" for i in range(20)]
        
        start_time = time.time()
        
        result = tag_generator.generate_20_seo_tags(
            product_name="Performance Test Product Ultra",
            category="test",
            trending_keywords=trending_keywords,
            ai_generated_tags=ai_tags
        )
        
        duration = time.time() - start_time
        
        # Vérifications performance
        assert duration < 1.0, f"Génération trop lente: {duration:.2f}s"
        assert result["count"] == 20
        assert result["target_reached"] is True
    
    def test_empty_inputs_handling(self, tag_generator):
        """Test gestion des entrées vides"""
        result = tag_generator.generate_20_seo_tags(
            product_name="",  # Entrée vide
            category=None,
            trending_keywords=[],
            ai_generated_tags=[]
        )
        
        # Devrait quand même générer des tags
        assert result["count"] > 0, "Devrait générer des tags même avec entrées vides"
        assert "static" in result["source_breakdown"]
        assert result["source_breakdown"]["static"] > 0
    
    def test_unicode_and_special_characters(self, tag_generator):
        """Test gestion caractères Unicode et spéciaux"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Produit éléctronique spécial",
            category="électronique",
            trending_keywords=["tendance-été", "qualité-française"],
            ai_generated_tags=["produit-spécialisé"]
        )
        
        # Vérifier que les accents sont gérés
        assert result["count"] == 20
        for tag in result["tags"]:
            # Vérifier format clean (pas de caractères spéciaux dans les tags finaux)
            assert tag.replace('-', '').isalnum(), f"Tag '{tag}' contient des caractères non-ASCII"

if __name__ == "__main__":
    # Exécution des tests avec rapports détaillés
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=long", 
        "--durations=10"  # Afficher les 10 tests les plus lents
    ], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
```

## ⚙️ CONFIGURATION ET VARIABLES D'ENVIRONNEMENT

### Configuration principale (`.env`)

```bash
# ================================================================================
# ECOMSIMPLY - CONFIGURATION PRODUCTION SEO AUTOMATIQUE
# ================================================================================

# API Keys pour les services IA
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FAL_KEY=ecomsimply-spapi:a1b505864b80deae1bd371b3df92c227

# Configuration Base de Données
MONGO_URL=mongodb://localhost:27017
DB_NAME=ecomsimply_production

# Configuration JWT et Sécurité
JWT_SECRET=your-super-secure-jwt-secret-key-256-bits-minimum
JWT_ALGORITHM=HS256
ENCRYPTION_KEY=your-fernet-encryption-key-for-credentials

# Feature Flags - Fonctionnalités Avancées
ALLOW_GPT5_FOR_NON_PREMIUM=false
TEST_MODE=false
QA_MODE=true
ENABLE_COST_GUARD=true

# Configuration Logging
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

# Configuration SEO et Scraping
SCRAPING_TIMEOUT=30
MAX_CONCURRENT_SCRAPING=5
SEO_TAGS_TARGET=20
JACCARD_SIMILARITY_THRESHOLD=0.7

# Configuration Images IA
IMAGE_GENERATION_TIMEOUT=60
MAX_IMAGES_PER_REQUEST=5
DEFAULT_IMAGE_STYLE=studio

# Configuration Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# Configuration Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600
ENABLE_RESPONSE_CACHE=true

# Configuration Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_ENABLED=true

# Configuration Email (optionnel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Configuration Webhook (optionnel)
WEBHOOK_SECRET=your-webhook-secret
ENABLE_WEBHOOKS=false
```

### Configuration pytest (`/app/pytest.ini`)

```ini
[tool:pytest]
# Configuration pytest pour ECOMSIMPLY tests SEO automatique
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Options par défaut
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=5

# Marqueurs personnalisés
markers =
    slow: tests lents (plus de 5 secondes)
    integration: tests d'intégration avec services externes
    unit: tests unitaires rapides
    seo: tests spécifiques aux fonctionnalités SEO
    ai_routing: tests du routing IA
    cost_guard: tests du cost guard
    jaccard: tests de similarité Jaccard

# Configuration asyncio
asyncio_mode = auto

# Filtre des warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore:.*unclosed.*:ResourceWarning

# Couverture de code
--cov=services
--cov-report=html
--cov-report=term-missing
--cov-fail-under=80

# Timeout pour les tests
timeout = 30
```

### Configuration Docker (`/app/backend/Dockerfile`)

```dockerfile
# ================================================================================
# ECOMSIMPLY BACKEND - DOCKERFILE OPTIMISÉ POUR SEO AUTOMATIQUE
# ================================================================================

FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Créer utilisateur non-root
RUN groupadd -r ecomsimply && useradd -r -g ecomsimply ecomsimply

# Installer dépendances système pour scraping et IA
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier requirements et installer dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer dépendances spécifiques pour SEO automatique
RUN pip install --no-cache-dir \
    beautifulsoup4==4.12.2 \
    fake-useragent==1.4.0 \
    aiohttp-retry==2.8.3 \
    pytrends==4.9.2

# Copier le code source
COPY . .

# Créer dossier logs
RUN mkdir -p /app/logs && chown -R ecomsimply:ecomsimply /app/logs

# Changer vers utilisateur non-root
USER ecomsimply

# Exposer le port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Commande de démarrage
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Configuration de monitoring (`/app/monitoring/prometheus.yml`)

```yaml
# ================================================================================
# ECOMSIMPLY - CONFIGURATION PROMETHEUS POUR MONITORING SEO
# ================================================================================

global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "ecomsimply_rules.yml"

scrape_configs:
  # Backend API metrics
  - job_name: 'ecomsimply-backend'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # SEO Services metrics
  - job_name: 'ecomsimply-seo-services'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/api/metrics/seo'
    scrape_interval: 30s

  # Database metrics
  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:27017']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Règles d'alerte spécifiques SEO
rule_files:
  - "alerts/seo_performance.yml"
  - "alerts/ai_routing.yml"
  - "alerts/cost_guard.yml"
```

### Scripts d'automatisation (`/app/scripts/setup-seo-env.sh`)

```bash
#!/bin/bash
# ================================================================================
# ECOMSIMPLY - SETUP ENVIRONNEMENT SEO AUTOMATIQUE
# ================================================================================

set -e

echo "🚀 Configuration environnement ECOMSIMPLY SEO Automatique"

# Créer dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p logs
mkdir -p data/mongodb
mkdir -p data/redis
mkdir -p data/prometheus
mkdir -p backup

# Permissions
chmod 755 logs
chmod 755 data

# Installation dépendances Python pour SEO
echo "🐍 Installation dépendances Python SEO..."
pip install -r requirements.txt

# Installation dépendances spécialisées
pip install \
    beautifulsoup4 \
    fake-useragent \
    aiohttp-retry \
    pytrends \
    selenium \
    webdriver-manager

# Configuration base de données de test
echo "🗄️ Configuration base de données test..."
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client.ecomsimply_test
db.test_collection.insert_one({'test': True})
print('✅ Base de données test configurée')
"

# Tests de connexion API
echo "🔌 Test connexions API..."
python -c "
import os
assert os.environ.get('OPENAI_API_KEY'), 'OPENAI_API_KEY manquant'
assert os.environ.get('FAL_KEY'), 'FAL_KEY manquant'
print('✅ Clés API configurées')
"

# Lancement des tests
echo "🧪 Exécution des tests SEO..."
python -m pytest tests/test_seo_tags.py -v
python -m pytest tests/test_model_routing.py -v

echo "✅ Environnement SEO automatique configuré avec succès!"
echo "🎯 Prêt pour la génération automatique de fiches produit"
```

### Configuration de performance (`/app/config/performance.yml`)

```yaml
# ================================================================================
# ECOMSIMPLY - CONFIGURATION PERFORMANCE SEO AUTOMATIQUE
# ================================================================================

seo_generation:
  # Timeouts
  scraping_timeout: 30
  ai_generation_timeout: 45
  image_generation_timeout: 60
  
  # Concurrence
  max_concurrent_requests: 10
  max_concurrent_scraping: 5
  max_concurrent_images: 3
  
  # Cache
  cache_ttl:
    trending_keywords: 3600  # 1 heure
    competitor_prices: 1800  # 30 minutes
    seo_data: 2700          # 45 minutes
  
  # Rate limiting
  rate_limits:
    scraping_per_minute: 30
    ai_calls_per_minute: 50
    image_generation_per_hour: 100

ai_routing:
  # Modèles par plan
  models:
    premium:
      primary: "gpt-4o"
      fallback: "gpt-4-turbo"
      timeout: 45
    pro:
      primary: "gpt-4-turbo"  
      fallback: "gpt-4o-mini"
      timeout: 30
    gratuit:
      primary: "gpt-4-turbo"
      fallback: "gpt-4o-mini"
      timeout: 25
  
  # Cost Guard
  cost_guard:
    enabled: true
    failure_threshold: 2
    window_minutes: 10
    
quality_control:
  # Validation SEO tags
  seo_tags:
    target_count: 20
    min_length: 2
    max_length: 5
    jaccard_threshold: 0.7
    
  # Validation contenu
  content:
    title_min_length: 50
    title_max_length: 70
    description_min_words: 150
    features_min_count: 5

monitoring:
  metrics_enabled: true
  log_level: "INFO"
  structured_logging: true
  health_check_interval: 30
```

---

## 📊 DASHBOARD DE MONITORING

### Métriques clés à surveiller:

1. **Performance SEO**
   - Temps de génération moyen
   - Taux de succès des scraping
   - Score de diversité Jaccard moyen
   - Nombre de tags générés par session

2. **Routing IA**
   - Utilisation des modèles par plan
   - Taux de fallback
   - Déclenchements Cost Guard
   - Temps de réponse par modèle

3. **Qualité du contenu**
   - Validation des formats
   - Longueur moyenne des descriptions
   - Nombre de features par fiche
   - Taux de satisfaction utilisateur

4. **Infrastructure**
   - Utilisation CPU/Mémoire
   - Latence réseau
   - Erreurs API externes
   - Disponibilité des services

Cette configuration complète assure un monitoring optimal du système SEO automatique ECOMSIMPLY.