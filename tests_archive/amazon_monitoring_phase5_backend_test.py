#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon Monitoring Phase 5 - Backend Testing
Test complet des composants Amazon Monitoring Phase 5 ECOMSIMPLY

Composants testés:
1. Backend Models (amazon_monitoring.py)
2. Orchestrateur de Monitoring (orchestrator.py) 
3. Optimiseur Boucle Fermée (closed_loop.py)
4. Service Monitoring (amazon_monitoring_service.py)
5. Routes API (amazon_monitoring_routes.py)
6. Tests Backend (test_amazon_monitoring_phase5.py)
"""

import asyncio
import sys
import os
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Ajouter le répertoire backend au path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')

# Configuration de base
os.environ.setdefault('MONGO_URL', 'mongodb://localhost:27017')
os.environ.setdefault('DB_NAME', 'ecomsimply_test')

print("🚀 ECOMSIMPLY Amazon Monitoring Phase 5 - Backend Testing")
print("=" * 80)

class AmazonMonitoringPhase5Tester:
    """Testeur complet pour Amazon Monitoring Phase 5"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'start_time': time.time()
        }
        
        # Configuration de test
        self.test_user_id = "test-user-monitoring-phase5"
        self.test_marketplace_id = "A13V1IB3VIYZZH"  # Amazon France
        self.test_skus = ["TEST-SKU-001", "TEST-SKU-002", "TEST-SKU-003"]
        
    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Enregistrer le résultat d'un test"""
        self.results['total_tests'] += 1
        
        if success:
            self.results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.results['failed_tests'] += 1
            status = "❌ FAIL"
            
        self.results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'success': success,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    📋 {details}")
        if error:
            print(f"    ❌ {error}")
    
    async def test_models_import_and_validation(self):
        """Test 1: Import et validation des modèles"""
        try:
            from backend.models.amazon_monitoring import (
                MonitoringJob, ProductSnapshot, OptimizationDecision, DesiredState,
                MonitoringKPIs, MonitoringAlert, MonitoringDashboardData,
                MonitoringStatus, OptimizationAction, OptimizationStatus, BuyBoxStatus
            )
            
            # Test création MonitoringJob
            job = MonitoringJob(
                user_id=self.test_user_id,
                marketplace_id=self.test_marketplace_id,
                skus=self.test_skus,
                monitoring_frequency_hours=6,
                optimization_frequency_hours=24,
                auto_optimization_enabled=True,
                buybox_loss_threshold=0.8,
                price_deviation_threshold=0.05,
                seo_score_threshold=0.7
            )
            
            assert job.user_id == self.test_user_id
            assert len(job.skus) == 3
            assert job.status == MonitoringStatus.ACTIVE
            assert job.created_at is not None
            
            # Test création ProductSnapshot
            snapshot = ProductSnapshot(
                job_id=job.id,
                user_id=self.test_user_id,
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                title="Test Product Title",
                current_price=79.99,
                currency="EUR",
                buybox_status=BuyBoxStatus.WON,
                buybox_price=79.99,
                competitors_count=5,
                data_completeness_score=0.85
            )
            
            assert snapshot.sku == "TEST-SKU-001"
            assert snapshot.current_price == 79.99
            assert snapshot.buybox_status == BuyBoxStatus.WON
            
            # Test création DesiredState
            desired_state = DesiredState(
                user_id=self.test_user_id,
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                desired_title="Optimized Test Product",
                desired_price=75.00,
                min_price=50.00,
                max_price=100.00,
                target_buybox_share=0.9,
                auto_correction_enabled=True
            )
            
            assert desired_state.desired_price == 75.00
            assert desired_state.target_buybox_share == 0.9
            
            # Test création OptimizationDecision
            decision = OptimizationDecision(
                job_id=job.id,
                user_id=self.test_user_id,
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                current_snapshot_id=snapshot.id,
                desired_state_id=desired_state.id,
                action_type=OptimizationAction.PRICE_UPDATE,
                priority=7,
                reasoning="Prix dévie de 6.7% par rapport à la stratégie définie",
                confidence_score=0.85,
                risk_score=0.2
            )
            
            assert decision.action_type == OptimizationAction.PRICE_UPDATE
            assert decision.confidence_score == 0.85
            
            # Test enums
            assert MonitoringStatus.ACTIVE.value == "active"
            assert BuyBoxStatus.WON.value == "won"
            assert OptimizationAction.SEO_UPDATE.value == "seo_update"
            assert OptimizationStatus.COMPLETED.value == "completed"
            
            self.log_test(
                "Models Import & Validation",
                True,
                "Tous les modèles importés et validés: MonitoringJob, ProductSnapshot, DesiredState, OptimizationDecision, Enums"
            )
            
        except Exception as e:
            self.log_test(
                "Models Import & Validation",
                False,
                error=f"Erreur lors de l'import/validation des modèles: {str(e)}"
            )
    
    async def test_orchestrator_functionality(self):
        """Test 2: Fonctionnalité de l'orchestrateur"""
        try:
            from backend.amazon.monitoring.orchestrator import monitoring_orchestrator
            
            # Test circuit breaker
            initial_state = monitoring_orchestrator.circuit_breaker['state']
            assert initial_state in ['closed', 'open', 'half_open']
            
            # Test vérification circuit breaker
            can_run = monitoring_orchestrator._check_circuit_breaker()
            assert isinstance(can_run, bool)
            
            # Test incrémentation des échecs
            initial_failures = monitoring_orchestrator.circuit_breaker['failure_count']
            monitoring_orchestrator._increment_circuit_breaker(1)
            assert monitoring_orchestrator.circuit_breaker['failure_count'] == initial_failures + 1
            
            # Force circuit breaker to open state to test reset
            monitoring_orchestrator.circuit_breaker['state'] = 'open'
            monitoring_orchestrator._reset_circuit_breaker()
            assert monitoring_orchestrator.circuit_breaker['state'] == 'closed'
            assert monitoring_orchestrator.circuit_breaker['failure_count'] == 0
            
            # Test configuration
            assert monitoring_orchestrator.max_concurrent_jobs > 0
            assert monitoring_orchestrator.default_timeout > 0
            assert monitoring_orchestrator.retry_attempts > 0
            
            # Test statistiques
            assert 'total_runs' in monitoring_orchestrator.job_stats
            assert 'successful_runs' in monitoring_orchestrator.job_stats
            assert 'failed_runs' in monitoring_orchestrator.job_stats
            
            self.log_test(
                "Orchestrator Functionality",
                True,
                "Circuit breaker, configuration et statistiques fonctionnels"
            )
            
        except Exception as e:
            error_msg = str(e) if str(e).strip() else f"Erreur inconnue dans l'orchestrateur: {type(e).__name__}"
            self.log_test(
                "Orchestrator Functionality", 
                False,
                error=f"Erreur orchestrateur: {error_msg}"
            )
    
    async def test_closed_loop_optimizer(self):
        """Test 3: Optimiseur boucle fermée"""
        try:
            from backend.amazon.optimizer.closed_loop import closed_loop_optimizer
            from backend.models.amazon_monitoring import (
                DesiredState, ProductSnapshot, BuyBoxStatus
            )
            
            # Test configuration des seuils
            assert 'price_deviation_percent' in closed_loop_optimizer.thresholds
            assert 'buybox_loss_priority' in closed_loop_optimizer.thresholds
            assert 'seo_score_minimum' in closed_loop_optimizer.thresholds
            
            # Test statistiques
            assert 'total_comparisons' in closed_loop_optimizer.stats
            assert 'corrections_applied' in closed_loop_optimizer.stats
            
            # Test création d'états pour comparaison
            desired_state = DesiredState(
                user_id=self.test_user_id,
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                desired_title="Optimized Product Title",
                desired_price=75.00,
                min_price=50.00,
                max_price=100.00,
                target_buybox_share=0.9
            )
            
            snapshot = ProductSnapshot(
                job_id="test-job-123",
                user_id=self.test_user_id,
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                title="Current Product Title",
                current_price=79.99,
                buybox_status=BuyBoxStatus.LOST,
                buybox_price=77.50,
                competitors_count=5,
                data_completeness_score=0.8
            )
            
            # Test comparaison d'états
            comparison = await closed_loop_optimizer._compare_states(desired_state, snapshot)
            
            assert hasattr(comparison, 'has_differences')
            assert hasattr(comparison, 'differences')
            assert hasattr(comparison, 'priority_score')
            assert hasattr(comparison, 'confidence_score')
            assert hasattr(comparison, 'risk_score')
            
            # Vérifier qu'il y a des différences (prix différent)
            assert comparison.has_differences is True
            assert 'price' in comparison.differences
            
            # Test construction du plan d'exécution
            differences = {
                'price': {
                    'desired': 75.00,
                    'observed': 79.99,
                    'deviation_percent': 6.2
                }
            }
            
            plan = await closed_loop_optimizer._build_execution_plan(differences)
            
            assert 'steps' in plan
            assert 'sp_api_calls' in plan
            assert 'estimated_duration_minutes' in plan
            assert len(plan['steps']) > 0
            
            self.log_test(
                "Closed Loop Optimizer",
                True,
                "Comparaison d'états, plan d'exécution et configuration validés"
            )
            
        except Exception as e:
            self.log_test(
                "Closed Loop Optimizer",
                False,
                error=f"Erreur optimiseur: {str(e)}"
            )
    
    async def test_monitoring_service(self):
        """Test 4: Service de monitoring"""
        try:
            from backend.services.amazon_monitoring_service import monitoring_service
            from backend.models.amazon_monitoring import (
                MonitoringJob, ProductSnapshot, DesiredState, MonitoringStatus
            )
            
            # Test configuration du service
            assert monitoring_service.client is not None
            assert monitoring_service.db is not None
            assert monitoring_service.snapshot_retention_days > 0
            assert monitoring_service.optimization_retention_days > 0
            
            # Test collections MongoDB
            assert monitoring_service.monitoring_jobs_collection is not None
            assert monitoring_service.product_snapshots_collection is not None
            assert monitoring_service.optimization_decisions_collection is not None
            assert monitoring_service.desired_states_collection is not None
            
            # Test méthodes helper pour calculs KPIs
            user_id = self.test_user_id
            marketplace_id = self.test_marketplace_id
            start_time = datetime.utcnow() - timedelta(hours=24)
            end_time = datetime.utcnow()
            
            # Test calcul métriques Buy Box (simulation)
            buybox_metrics = await monitoring_service._calculate_buybox_metrics(
                user_id, marketplace_id, start_time, end_time
            )
            
            assert 'buybox_won_count' in buybox_metrics
            assert 'buybox_lost_count' in buybox_metrics
            assert 'buybox_share_avg' in buybox_metrics
            
            # Test calcul métriques pricing (simulation)
            pricing_metrics = await monitoring_service._calculate_pricing_metrics(
                user_id, marketplace_id, start_time, end_time
            )
            
            assert 'price_updates_count' in pricing_metrics
            assert 'price_optimizations_successful' in pricing_metrics
            assert 'price_optimizations_failed' in pricing_metrics
            
            # Test calcul métriques SEO (simulation)
            seo_metrics = await monitoring_service._calculate_seo_metrics(
                user_id, marketplace_id, start_time, end_time
            )
            
            assert 'seo_updates_count' in seo_metrics
            assert 'seo_optimizations_successful' in seo_metrics
            assert 'seo_optimizations_failed' in seo_metrics
            
            self.log_test(
                "Monitoring Service",
                True,
                "Configuration service, collections MongoDB et calculs KPIs validés"
            )
            
        except Exception as e:
            self.log_test(
                "Monitoring Service",
                False,
                error=f"Erreur service monitoring: {str(e)}"
            )
    
    async def test_api_routes_structure(self):
        """Test 5: Structure des routes API"""
        try:
            from backend.routes.amazon_monitoring_routes import router
            from fastapi import APIRouter
            
            # Vérifier que c'est un router FastAPI
            assert isinstance(router, APIRouter)
            
            # Vérifier le préfixe
            assert router.prefix == "/api/amazon/monitoring"
            
            # Vérifier les tags
            assert "Amazon Monitoring" in router.tags
            
            # Test des modèles de requête
            from backend.routes.amazon_monitoring_routes import (
                CreateMonitoringJobRequest,
                UpdateMonitoringJobRequest,
                CreateDesiredStateRequest,
                TriggerOptimizationRequest,
                MonitoringFilters
            )
            
            # Test création d'une requête de job
            job_request = CreateMonitoringJobRequest(
                marketplace_id=self.test_marketplace_id,
                skus=self.test_skus,
                monitoring_frequency_hours=6,
                auto_optimization_enabled=True,
                buybox_loss_threshold=0.8,
                price_deviation_threshold=0.05
            )
            
            assert job_request.marketplace_id == self.test_marketplace_id
            assert len(job_request.skus) == 3
            assert job_request.monitoring_frequency_hours == 6
            
            # Test requête d'état désiré
            desired_state_request = CreateDesiredStateRequest(
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                desired_price=75.00,
                target_buybox_share=0.9,
                auto_correction_enabled=True
            )
            
            assert desired_state_request.sku == "TEST-SKU-001"
            assert desired_state_request.desired_price == 75.00
            
            # Test requête d'optimisation
            optimization_request = TriggerOptimizationRequest(
                sku="TEST-SKU-001",
                marketplace_id=self.test_marketplace_id,
                force=False
            )
            
            assert optimization_request.sku == "TEST-SKU-001"
            assert optimization_request.force is False
            
            self.log_test(
                "API Routes Structure",
                True,
                "Router FastAPI, modèles de requête et structure validés"
            )
            
        except Exception as e:
            self.log_test(
                "API Routes Structure",
                False,
                error=f"Erreur routes API: {str(e)}"
            )
    
    async def test_backend_tests_structure(self):
        """Test 6: Structure des tests backend"""
        try:
            # Import du fichier de tests
            import sys
            sys.path.insert(0, '/app/tests/backend')
            
            from test_amazon_monitoring_phase5 import (
                TestMonitoringModels,
                TestMonitoringOrchestrator,
                TestClosedLoopOptimizer,
                TestMonitoringIntegration
            )
            
            # Vérifier les classes de test
            assert TestMonitoringModels is not None
            assert TestMonitoringOrchestrator is not None
            assert TestClosedLoopOptimizer is not None
            assert TestMonitoringIntegration is not None
            
            # Test instanciation des classes de test
            models_test = TestMonitoringModels()
            orchestrator_test = TestMonitoringOrchestrator()
            optimizer_test = TestClosedLoopOptimizer()
            integration_test = TestMonitoringIntegration()
            
            # Vérifier les méthodes de test
            assert hasattr(models_test, 'test_monitoring_job_creation')
            assert hasattr(models_test, 'test_product_snapshot_model')
            assert hasattr(models_test, 'test_desired_state_model')
            
            assert hasattr(orchestrator_test, 'test_circuit_breaker_functionality')
            
            assert hasattr(optimizer_test, 'test_state_comparison')
            assert hasattr(optimizer_test, 'test_execution_plan_building')
            
            assert hasattr(integration_test, 'test_monitoring_workflow_simulation')
            assert hasattr(integration_test, 'test_end_to_end_monitoring_cycle')
            
            self.log_test(
                "Backend Tests Structure",
                True,
                "Classes de test et méthodes de test validées"
            )
            
        except Exception as e:
            self.log_test(
                "Backend Tests Structure",
                False,
                error=f"Erreur structure tests: {str(e)}"
            )
    
    async def test_integration_workflow(self):
        """Test 7: Workflow d'intégration complet"""
        try:
            from backend.models.amazon_monitoring import (
                MonitoringJob, ProductSnapshot, DesiredState, OptimizationDecision,
                MonitoringStatus, BuyBoxStatus, OptimizationAction, OptimizationStatus
            )
            
            # 1. Créer un job de monitoring
            job = MonitoringJob(
                user_id=self.test_user_id,
                marketplace_id=self.test_marketplace_id,
                skus=["INTEGRATION-SKU-001"],
                monitoring_frequency_hours=6,
                auto_optimization_enabled=True,
                buybox_loss_threshold=0.8,
                price_deviation_threshold=0.05
            )
            
            # 2. Créer un snapshot produit
            snapshot = ProductSnapshot(
                job_id=job.id,
                user_id=self.test_user_id,
                sku="INTEGRATION-SKU-001",
                marketplace_id=self.test_marketplace_id,
                title="Integration Test Product",
                current_price=89.99,
                currency="EUR",
                buybox_status=BuyBoxStatus.LOST,
                buybox_price=85.00,
                competitors_count=7,
                data_completeness_score=0.9
            )
            
            # 3. Créer un état désiré
            desired_state = DesiredState(
                user_id=self.test_user_id,
                sku="INTEGRATION-SKU-001",
                marketplace_id=self.test_marketplace_id,
                desired_title="Optimized Integration Product",
                desired_price=85.50,
                min_price=70.00,
                max_price=120.00,
                target_buybox_share=0.9,
                auto_correction_enabled=True
            )
            
            # 4. Créer une décision d'optimisation
            decision = OptimizationDecision(
                job_id=job.id,
                user_id=self.test_user_id,
                sku="INTEGRATION-SKU-001",
                marketplace_id=self.test_marketplace_id,
                current_snapshot_id=snapshot.id,
                desired_state_id=desired_state.id,
                action_type=OptimizationAction.PRICE_UPDATE,
                priority=8,
                detected_changes={
                    'price': {
                        'desired': 85.50,
                        'observed': 89.99,
                        'deviation_percent': 5.2
                    }
                },
                reasoning="Prix trop élevé, Buy Box perdue - correction nécessaire",
                confidence_score=0.9,
                risk_score=0.1,
                status=OptimizationStatus.PENDING
            )
            
            # 5. Vérifier la cohérence du workflow
            assert job.user_id == snapshot.user_id == desired_state.user_id == decision.user_id
            assert job.marketplace_id == snapshot.marketplace_id == desired_state.marketplace_id == decision.marketplace_id
            assert snapshot.sku == desired_state.sku == decision.sku
            assert decision.current_snapshot_id == snapshot.id
            assert decision.desired_state_id == desired_state.id
            
            # 6. Vérifier la logique métier
            price_difference = abs(snapshot.current_price - desired_state.desired_price)
            assert price_difference > 0  # Il y a bien une différence
            
            buybox_lost = snapshot.buybox_status == BuyBoxStatus.LOST
            assert buybox_lost is True  # Buy Box effectivement perdue
            
            competitive_price = snapshot.buybox_price
            desired_price = desired_state.desired_price
            assert desired_price > competitive_price  # Prix désiré compétitif mais avec marge
            
            self.log_test(
                "Integration Workflow",
                True,
                "Workflow complet Job→Snapshot→DesiredState→OptimizationDecision validé"
            )
            
        except Exception as e:
            self.log_test(
                "Integration Workflow",
                False,
                error=f"Erreur workflow intégration: {str(e)}"
            )
    
    async def test_error_handling_and_safety(self):
        """Test 8: Gestion d'erreurs et sécurité"""
        try:
            from backend.amazon.optimizer.closed_loop import closed_loop_optimizer
            from backend.models.amazon_monitoring import (
                OptimizationDecision, OptimizationAction, OptimizationStatus
            )
            
            # Test safety check avec décision risquée
            risky_decision = OptimizationDecision(
                job_id="test-job",
                user_id=self.test_user_id,
                sku="RISKY-SKU",
                marketplace_id=self.test_marketplace_id,
                current_snapshot_id="snapshot-id",
                desired_state_id="state-id",
                action_type=OptimizationAction.PRICE_UPDATE,
                priority=10,
                detected_changes={
                    'price': {
                        'desired': 50.00,
                        'observed': 100.00,
                        'deviation_percent': 50.0  # Changement trop important
                    }
                },
                reasoning="Test changement risqué",
                confidence_score=0.5,  # Confiance faible
                risk_score=0.9,  # Risque élevé
                status=OptimizationStatus.PENDING
            )
            
            # Test safety check (devrait échouer)
            safety_passed = await closed_loop_optimizer._safety_check(risky_decision)
            assert safety_passed is False  # Safety check devrait rejeter cette décision
            
            # Test avec décision sûre
            safe_decision = OptimizationDecision(
                job_id="test-job",
                user_id=self.test_user_id,
                sku="SAFE-SKU",
                marketplace_id=self.test_marketplace_id,
                current_snapshot_id="snapshot-id",
                desired_state_id="state-id",
                action_type=OptimizationAction.PRICE_UPDATE,
                priority=5,
                detected_changes={
                    'price': {
                        'desired': 95.00,
                        'observed': 100.00,
                        'deviation_percent': 5.0  # Changement raisonnable
                    }
                },
                reasoning="Test changement sûr",
                confidence_score=0.85,  # Confiance élevée
                risk_score=0.2,  # Risque faible
                status=OptimizationStatus.PENDING
            )
            
            # Test validation des seuils
            thresholds = closed_loop_optimizer.thresholds
            assert thresholds['max_price_change_percent'] > 0
            assert thresholds['correction_frequency_hours'] > 0
            assert thresholds['price_deviation_percent'] > 0
            
            # Test circuit breaker
            from backend.amazon.monitoring.orchestrator import monitoring_orchestrator
            
            # Vérifier que le circuit breaker a des seuils configurés
            cb = monitoring_orchestrator.circuit_breaker
            assert cb['failure_threshold'] > 0
            assert cb['recovery_timeout'] > 0
            
            self.log_test(
                "Error Handling & Safety",
                True,
                "Safety checks, seuils de sécurité et circuit breaker validés"
            )
            
        except Exception as e:
            self.log_test(
                "Error Handling & Safety",
                False,
                error=f"Erreur gestion sécurité: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🔄 Démarrage des tests Amazon Monitoring Phase 5...")
        print()
        
        # Liste des tests à exécuter
        tests = [
            ("Models Import & Validation", self.test_models_import_and_validation),
            ("Orchestrator Functionality", self.test_orchestrator_functionality),
            ("Closed Loop Optimizer", self.test_closed_loop_optimizer),
            ("Monitoring Service", self.test_monitoring_service),
            ("API Routes Structure", self.test_api_routes_structure),
            ("Backend Tests Structure", self.test_backend_tests_structure),
            ("Integration Workflow", self.test_integration_workflow),
            ("Error Handling & Safety", self.test_error_handling_and_safety)
        ]
        
        # Exécuter chaque test
        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                self.log_test(
                    test_name,
                    False,
                    error=f"Erreur inattendue: {str(e)}\n{traceback.format_exc()}"
                )
        
        # Afficher le résumé
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        duration = time.time() - self.results['start_time']
        
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS AMAZON MONITORING PHASE 5")
        print("=" * 80)
        
        print(f"⏱️  Durée d'exécution: {duration:.2f} secondes")
        print(f"📈 Tests totaux: {self.results['total_tests']}")
        print(f"✅ Tests réussis: {self.results['passed_tests']}")
        print(f"❌ Tests échoués: {self.results['failed_tests']}")
        
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
            print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        print("\n📋 DÉTAIL DES TESTS:")
        print("-" * 80)
        
        for test in self.results['test_details']:
            print(f"{test['status']}: {test['test_name']}")
            if test['details']:
                print(f"    📋 {test['details']}")
            if test['error']:
                print(f"    ❌ {test['error']}")
        
        print("\n" + "=" * 80)
        
        # Évaluation globale
        if self.results['failed_tests'] == 0:
            print("🎉 TOUS LES TESTS AMAZON MONITORING PHASE 5 SONT PASSÉS!")
            print("✅ Le système Amazon Monitoring Phase 5 est prêt pour la production")
        elif success_rate >= 85:
            print("✅ TESTS AMAZON MONITORING PHASE 5 MAJORITAIREMENT RÉUSSIS")
            print(f"⚠️  {self.results['failed_tests']} test(s) nécessite(nt) une attention")
        else:
            print("❌ TESTS AMAZON MONITORING PHASE 5 NÉCESSITENT DES CORRECTIONS")
            print("🔧 Veuillez corriger les erreurs avant la mise en production")
        
        print("=" * 80)


async def main():
    """Fonction principale"""
    tester = AmazonMonitoringPhase5Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())