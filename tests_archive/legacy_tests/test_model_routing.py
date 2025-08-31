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
            "marketing_description": "Description marketing test",
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "seo_tags": ["test", "product", "excellence"],
            "price_suggestions": "Prix compétitif",
            "target_audience": "Consommateurs test",
            "call_to_action": "Achetez maintenant !"
        }
        '''
        return mock_response

    @pytest.mark.asyncio
    async def test_premium_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Premium : gpt-4o -> gpt-4-turbo"""
        gpt_service.client.chat.completions.create.return_value = mock_openai_response
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Premium",
            product_description="Description test premium",
            user_plan="premium",
            user_id="user_premium_test"
        )
        
        # Vérifications
        assert result["model_used"] == "gpt-4o"  # GPT-5 Pro simulé
        assert result["primary_model"] == "gpt-4o"
        assert result["fallback_model"] == "gpt-4-turbo"
        assert result["generation_method"] == "routing_primary"
        assert result["fallback_level"] == 1
        assert result["model_route"] == "gpt-4o -> gpt-4-turbo"
        assert result["cost_guard_triggered"] is False

    @pytest.mark.asyncio
    async def test_gratuit_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Gratuit : gpt-4-turbo -> gpt-4o-mini"""
        gpt_service.client.chat.completions.create.return_value = mock_openai_response
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Gratuit",
            product_description="Description test gratuit",
            user_plan="gratuit",
            user_id="user_gratuit_test"
        )
        
        # Vérifications
        assert result["model_used"] == "gpt-4-turbo"
        assert result["primary_model"] == "gpt-4-turbo"
        assert result["fallback_model"] == "gpt-4o-mini"
        assert result["generation_method"] == "routing_primary"
        assert result["fallback_level"] == 1
        assert result["model_route"] == "gpt-4-turbo -> gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_pro_plan_routing(self, gpt_service, mock_openai_response):
        """Test du routing pour plan Pro : gpt-4-turbo -> gpt-4o-mini"""
        gpt_service.client.chat.completions.create.return_value = mock_openai_response
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Pro",
            product_description="Description test pro",
            user_plan="pro",
            user_id="user_pro_test"
        )
        
        # Vérifications
        assert result["model_used"] == "gpt-4-turbo"
        assert result["primary_model"] == "gpt-4-turbo"
        assert result["fallback_model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, gpt_service, mock_openai_response):
        """Test du fallback quand le modèle principal échoue"""
        # Premier appel échoue, deuxième réussit
        gpt_service.client.chat.completions.create.side_effect = [
            Exception("Primary model failed"),
            mock_openai_response
        ]
        
        result = await gpt_service.generate_product_content(
            product_name="Test Product Fallback",
            product_description="Description test fallback",
            user_plan="premium",
            user_id="user_fallback_test"
        )
        
        # Vérifications
        assert result["model_used"] == "gpt-4-turbo"  # Modèle de fallback
        assert result["primary_model"] == "gpt-4o"
        assert result["fallback_model"] == "gpt-4-turbo"
        assert result["generation_method"] == "routing_fallback"
        assert result["fallback_level"] == 2
        assert result["model_route"] == "gpt-4o -> gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_gpt5_feature_flag_enabled(self, gpt_service, mock_openai_response):
        """Test avec feature flag ALLOW_GPT5_FOR_NON_PREMIUM activé"""
        # Simuler feature flag activé
        gpt_service.allow_gpt5_for_non_premium = True
        gpt_service.model_routing['gratuit']['fallback'] = 'gpt-4o'
        
        gpt_service.client.chat.completions.create.side_effect = [
            Exception("Primary failed"),
            mock_openai_response
        ]
        
        result = await gpt_service.generate_product_content(
            product_name="Test GPT5 Flag",
            product_description="Description test flag",
            user_plan="gratuit",
            user_id="user_flag_test"
        )
        
        # Vérifications
        assert result["fallback_model"] == "gpt-4o"  # GPT-5 accessible aux non-premium

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
        
        # Deuxième échec
        failure_tracker.record_failure(user_id)
        assert failure_tracker.should_trigger_cost_guard(user_id)
    
    def test_cost_guard_window_expiry(self, failure_tracker):
        """Test que les échecs expirent après 10 minutes"""
        user_id = "test_user_window"
        
        # Simuler des échecs anciens
        old_time = datetime.utcnow() - timedelta(minutes=15)
        failure_tracker.failures[user_id] = [old_time, old_time]
        
        # Les échecs anciens ne comptent pas
        assert not failure_tracker.should_trigger_cost_guard(user_id)
    
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
        mock_response.choices[0].message.content = '{"generated_title": "Test"}'
        service.client.chat.completions.create.return_value = mock_response
        
        result = await service.generate_product_content(
            product_name="Test Cost Guard",
            product_description="Description test",
            user_plan="premium",
            user_id="test_cost_guard_user"
        )
        
        # Vérifications
        assert result["cost_guard_triggered"] is True
        assert result["model_used"] == "gpt-4-turbo"  # Fallback direct

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
    
    @pytest.mark.asyncio
    async def test_api_response_contains_routing_fields(self):
        """Test que l'API retourne bien tous les champs de routing"""
        from server import ProductSheetResponse
        
        # Données de test avec tous les champs
        test_data = {
            "generated_title": "Test Title",
            "marketing_description": "Test Description",
            "key_features": ["Feature 1", "Feature 2"],
            "seo_tags": ["tag1", "tag2"],
            "price_suggestions": "Prix test",
            "target_audience": "Audience test",
            "call_to_action": "Action test",
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
        
        # Vérifications
        assert response.model_used == "gpt-4o"
        assert response.generation_method == "routing_primary"
        assert response.fallback_level == 1
        assert response.primary_model == "gpt-4o"
        assert response.fallback_model == "gpt-4-turbo"
        assert response.model_route == "gpt-4o -> gpt-4-turbo"
        assert response.cost_guard_triggered is False

if __name__ == "__main__":
    # Tests pour la ligne de commande
    import subprocess
    result = subprocess.run(["python", "-m", "pytest", __file__, "-v"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)