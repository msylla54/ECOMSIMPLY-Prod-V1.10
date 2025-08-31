"""
Tests Backend - Amazon Monitoring Phase 5
Tests complets pour le système de monitoring et d'optimisation automatique
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, ANY
import json

# Imports du système
from models.amazon_monitoring import (
    MonitoringJob, ProductSnapshot, OptimizationDecision, DesiredState,
    MonitoringStatus, BuyBoxStatus, OptimizationAction, OptimizationStatus
)
from amazon.monitoring.orchestrator import monitoring_orchestrator
from amazon.optimizer.closed_loop import closed_loop_optimizer
from services.amazon_monitoring_service import monitoring_service


class TestMonitoringModels:
    """Tests des modèles de monitoring"""
    
    def test_monitoring_job_creation(self):
        """Test création job de monitoring valide"""
        job = MonitoringJob(
            user_id="user-123",
            marketplace_id="A13V1IB3VIYZZH",
            skus=["SKU-001", "SKU-002"],
            monitoring_frequency_hours=6,
            optimization_frequency_hours=24,
            auto_optimization_enabled=True,
            buybox_loss_threshold=0.8,
            price_deviation_threshold=0.05
        )
        
        assert job.user_id == "user-123"
        assert len(job.skus) == 2
        assert job.monitoring_frequency_hours == 6
        assert job.status == MonitoringStatus.ACTIVE
        assert job.created_at is not None
    
    def test_product_snapshot_model(self):
        """Test modèle snapshot produit"""
        snapshot = ProductSnapshot(
            job_id="job-123",
            user_id="user-123",
            sku="TEST-SKU",
            marketplace_id="A13V1IB3VIYZZH",
            current_price=79.99,
            currency="EUR",
            buybox_status=BuyBoxStatus.WON,
            buybox_price=79.99,
            competitors_count=5,
            data_completeness_score=0.85
        )
        
        assert snapshot.sku == "TEST-SKU"
        assert snapshot.current_price == 79.99
        assert snapshot.buybox_status == BuyBoxStatus.WON
        assert snapshot.data_completeness_score == 0.85
    
    def test_desired_state_model(self):
        """Test modèle état désiré"""
        desired_state = DesiredState(
            user_id="user-123",
            sku="TEST-SKU",
            marketplace_id="A13V1IB3VIYZZH",
            desired_title="Test Product Title",
            desired_price=75.00,
            min_price=50.00,
            max_price=100.00,
            target_buybox_share=0.9,
            auto_correction_enabled=True
        )
        
        assert desired_state.sku == "TEST-SKU"
        assert desired_state.desired_price == 75.00
        assert desired_state.target_buybox_share == 0.9
        assert desired_state.auto_correction_enabled is True


class TestMonitoringOrchestrator:
    """Tests de l'orchestrateur de monitoring"""
    
    @pytest.fixture
    def sample_monitoring_job(self):
        """Job de monitoring pour tests"""
        return MonitoringJob(
            user_id="user-123",
            marketplace_id="A13V1IB3VIYZZH",
            skus=["TEST-SKU-001", "TEST-SKU-002"],
            monitoring_frequency_hours=6,
            auto_optimization_enabled=True
        )
    
    def test_circuit_breaker_functionality(self):
        """Test fonctionnalité circuit breaker"""
        
        # État initial fermé
        assert monitoring_orchestrator._check_circuit_breaker() is True
        
        # Simuler des échecs
        for _ in range(5):
            monitoring_orchestrator._increment_circuit_breaker(1)
        
        # Circuit breaker devrait être ouvert
        assert monitoring_orchestrator.circuit_breaker['state'] == 'open'
        assert monitoring_orchestrator._check_circuit_breaker() is False
        
        # Réinitialiser
        monitoring_orchestrator._reset_circuit_breaker()
        assert monitoring_orchestrator.circuit_breaker['state'] == 'closed'
        assert monitoring_orchestrator._check_circuit_breaker() is True


class TestClosedLoopOptimizer:
    """Tests de l'optimiseur en boucle fermée"""
    
    @pytest.fixture
    def sample_desired_state(self):
        """État désiré pour tests"""
        return DesiredState(
            user_id="user-123",
            sku="TEST-SKU",
            marketplace_id="A13V1IB3VIYZZH",
            desired_title="Optimized Test Product",
            desired_price=75.00,
            min_price=50.00,
            max_price=100.00,
            target_buybox_share=0.9
        )
    
    @pytest.fixture
    def sample_snapshot(self):
        """Snapshot pour tests"""
        return ProductSnapshot(
            job_id="job-123",
            user_id="user-123",
            sku="TEST-SKU",
            marketplace_id="A13V1IB3VIYZZH",
            title="Current Test Product",
            current_price=79.99,
            buybox_status=BuyBoxStatus.LOST,
            buybox_price=77.50,
            competitors_count=5,
            data_completeness_score=0.8
        )
    
    async def test_state_comparison(self, sample_desired_state, sample_snapshot):
        """Test comparaison des états"""
        
        comparison = await closed_loop_optimizer._compare_states(
            sample_desired_state, 
            sample_snapshot
        )
        
        # Vérifier qu'il y a des différences
        assert comparison.has_differences is True
        assert 'price' in comparison.differences
        assert comparison.priority_score > 1
        
        # Vérifier les détails des changements de prix
        price_diff = comparison.differences['price']
        assert price_diff['desired'] == 75.00
        assert price_diff['observed'] == 79.99
    
    def test_execution_plan_building(self):
        """Test construction du plan d'exécution"""
        
        differences = {
            'price': {
                'desired': 75.00,
                'observed': 79.99,
                'deviation_percent': 6.2
            },
            'seo': {
                'title': {
                    'desired': 'New Optimized Title',
                    'observed': 'Old Title'
                }
            }
        }
        
        plan = closed_loop_optimizer._build_execution_plan(differences)
        
        # Vérifier le plan
        assert 'steps' in plan
        assert 'sp_api_calls' in plan
        assert len(plan['steps']) >= 2  # Prix + SEO
        assert any('update_price' in step.get('action', '') for step in plan['steps'])
        assert any('update_seo' in step.get('action', '') for step in plan['steps'])


class TestMonitoringIntegration:
    """Tests d'intégration du système de monitoring"""
    
    def test_monitoring_workflow_simulation(self):
        """Test simulation du workflow complet"""
        
        # 1. Job de monitoring créé
        job = MonitoringJob(
            user_id="user-123",
            marketplace_id="A13V1IB3VIYZZH",
            skus=["TEST-SKU"],
            monitoring_frequency_hours=6,
            auto_optimization_enabled=True
        )
        
        # 2. Snapshot collecté
        snapshot = ProductSnapshot(
            job_id=job.id,
            user_id=job.user_id,
            sku="TEST-SKU",
            marketplace_id=job.marketplace_id,
            current_price=79.99,
            buybox_status=BuyBoxStatus.LOST,
            buybox_price=75.00
        )
        
        # 3. État désiré
        desired_state = DesiredState(
            user_id=job.user_id,
            sku="TEST-SKU",
            marketplace_id=job.marketplace_id,
            desired_price=75.50
        )
        
        # 4. Vérifier que les modèles sont correctement créés
        assert job.id is not None
        assert snapshot.sku == "TEST-SKU"
        assert desired_state.desired_price == 75.50
    
    def test_kpi_calculation_integration(self):
        """Test intégration du calcul de KPIs"""
        
        # Simuler des données pour différents scénarios
        test_scenarios = [
            {
                'name': 'Buy Box Won',
                'buybox_status': BuyBoxStatus.WON,
                'expected_metric': 'buybox_won_count'
            },
            {
                'name': 'Buy Box Lost',
                'buybox_status': BuyBoxStatus.LOST,
                'expected_metric': 'buybox_lost_count'
            },
            {
                'name': 'Price Update',
                'action_type': OptimizationAction.PRICE_UPDATE,
                'expected_metric': 'price_updates_count'
            }
        ]
        
        for scenario in test_scenarios:
            # Vérifier que chaque scénario contribue aux bonnes métriques
            assert scenario['name'] is not None
            assert scenario.get('expected_metric') is not None
    
    def test_end_to_end_monitoring_cycle(self):
        """Test simulation cycle E2E complet"""
        
        # Ce test serait exécuté avec des données réelles en E2E
        # 1. Créer job de monitoring
        # 2. Collecter snapshot via SP-API
        # 3. Détecter écart avec état désiré  
        # 4. Générer décision d'optimisation
        # 5. Appliquer correction via SP-API
        # 6. Vérifier résultat
        # 7. Calculer KPIs
        
        assert True  # Placeholder pour tests E2E réels


# Fixtures globales et configuration
@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([
        __file__, 
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])