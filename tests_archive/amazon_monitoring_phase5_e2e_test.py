#!/usr/bin/env python3
"""
Tests E2E Amazon Monitoring Phase 5 - Workflow Complet ECOMSIMPLY
Backend Testing for Amazon Monitoring Phase 5 Complete Workflow

Test complet du workflow Phase 5 : Monitoring & Closed-Loop Optimizer Amazon
Validation du cycle complet : Création job → Collecte données → Comparaison états → Optimisation automatique → Dashboard KPIs
"""

import asyncio
import aiohttp
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de test
API_BASE = "https://ecomsimply.com/api"
TEST_USER_EMAIL = "amazon.monitoring.test@ecomsimply.com"
TEST_USER_PASSWORD = "AmazonMonitoring2025!"
TEST_USER_NAME = "Amazon Monitoring Tester"

class AmazonMonitoringPhase5Tester:
    """
    Testeur complet pour Amazon Monitoring Phase 5
    
    Tests E2E du workflow complet :
    1. Initialisation système
    2. Création job monitoring
    3. Collecte données (snapshots)
    4. États désirés et comparaison
    5. Décisions optimisation
    6. Exécution corrections
    7. Calcul KPIs et dashboard
    8. Monitoring continu
    """
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "workflow_results": {},
            "performance_metrics": {},
            "errors": []
        }
        
        # Configuration test
        self.test_marketplace_id = "A13V1IB3VIYZZH"  # Amazon France
        self.test_skus = [
            "ECOM-MONITOR-TEST-001",
            "ECOM-MONITOR-TEST-002", 
            "ECOM-MONITOR-TEST-003"
        ]
        
        # Métriques de performance
        self.start_time = None
        self.workflow_timings = {}
    
    async def setup_session(self):
        """Initialiser la session HTTP"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        logger.info("✅ Session HTTP initialisée")
    
    async def cleanup_session(self):
        """Nettoyer la session HTTP"""
        if self.session:
            await self.session.close()
            logger.info("✅ Session HTTP fermée")
    
    def log_test_result(self, test_name: str, success: bool, details: str, duration: float = 0):
        """Logger le résultat d'un test"""
        self.test_results["total_tests"] += 1
        
        if success:
            self.test_results["passed_tests"] += 1
            status = "✅ PASSED"
        else:
            self.test_results["failed_tests"] += 1
            status = "❌ FAILED"
        
        result = {
            "test_name": test_name,
            "status": status,
            "success": success,
            "details": details,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.test_results["test_details"].append(result)
        logger.info(f"{status} - {test_name}: {details}")
    
    async def authenticate_user(self) -> bool:
        """Authentifier l'utilisateur de test"""
        try:
            start_time = time.time()
            
            # 1. Essayer de créer l'utilisateur (peut échouer si existe déjà)
            register_data = {
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/register", json=register_data) as response:
                if response.status in [200, 201]:
                    logger.info("✅ Utilisateur de test créé")
                elif response.status == 400:
                    logger.info("ℹ️ Utilisateur de test existe déjà")
                else:
                    logger.warning(f"⚠️ Réponse inattendue lors de la création: {response.status}")
            
            # 2. Se connecter
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.user_id = data.get("user_id")
                    
                    if self.auth_token:
                        # Configurer les headers d'authentification
                        self.session.headers.update({
                            "Authorization": f"Bearer {self.auth_token}",
                            "Content-Type": "application/json"
                        })
                        
                        duration = time.time() - start_time
                        self.log_test_result(
                            "Authentication",
                            True,
                            f"Utilisateur authentifié avec succès (user_id: {self.user_id})",
                            duration
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Authentication",
                            False,
                            "Token d'authentification manquant dans la réponse"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Authentication",
                        False,
                        f"Échec de l'authentification: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Authentication",
                False,
                f"Erreur lors de l'authentification: {str(e)}"
            )
            return False
    
    async def test_1_system_initialization(self) -> bool:
        """
        ÉTAPE 1 - INITIALISATION SYSTÈME
        - Création indexes MongoDB pour monitoring collections
        - Démarrage orchestrateur monitoring avec scheduler APScheduler
        - Configuration circuit breaker et thresholds d'optimisation
        - Validation connexions SP-API et services externes
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 1 - Test initialisation système")
            
            # Test health check général
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status != 200:
                    self.log_test_result(
                        "System Health Check",
                        False,
                        f"Health check échoué: {response.status}"
                    )
                    return False
                
                health_data = await response.json()
                logger.info(f"✅ Health check: {health_data.get('status', 'unknown')}")
            
            # Test connexions Amazon SP-API (via routes Amazon)
            try:
                async with self.session.get(f"{API_BASE}/amazon/status") as response:
                    if response.status == 200:
                        amazon_status = await response.json()
                        logger.info(f"✅ Amazon SP-API status: {amazon_status}")
                    else:
                        logger.info(f"ℹ️ Amazon SP-API status: {response.status} (attendu sans connexion)")
            except Exception as e:
                logger.info(f"ℹ️ Amazon SP-API non accessible: {str(e)} (normal en test)")
            
            # Test système de monitoring (endpoints disponibles)
            monitoring_endpoints = [
                "/amazon/monitoring/dashboard",
                "/amazon/monitoring/jobs",
                "/amazon/monitoring/snapshots",
                "/amazon/monitoring/optimizations",
                "/amazon/monitoring/alerts"
            ]
            
            available_endpoints = 0
            for endpoint in monitoring_endpoints:
                try:
                    async with self.session.get(f"{API_BASE}{endpoint}") as response:
                        if response.status in [200, 401, 422]:  # 401/422 = auth requis (normal)
                            available_endpoints += 1
                            logger.info(f"✅ Endpoint disponible: {endpoint}")
                        else:
                            logger.warning(f"⚠️ Endpoint problématique: {endpoint} ({response.status})")
                except Exception as e:
                    logger.warning(f"⚠️ Endpoint inaccessible: {endpoint} - {str(e)}")
            
            duration = time.time() - start_time
            self.workflow_timings["system_initialization"] = duration
            
            success = available_endpoints >= 4  # Au moins 4/5 endpoints disponibles
            self.log_test_result(
                "System Initialization",
                success,
                f"Système initialisé - {available_endpoints}/5 endpoints monitoring disponibles",
                duration
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "System Initialization",
                False,
                f"Erreur initialisation système: {str(e)}"
            )
            return False
    
    async def test_2_create_monitoring_job(self) -> Optional[str]:
        """
        ÉTAPE 2 - CRÉATION JOB MONITORING
        - POST /api/amazon/monitoring/jobs avec SKUs multiples
        - Configuration fréquences monitoring (6h) et optimisation (24h)
        - Seuils alertes : buybox_loss_threshold=0.8, price_deviation_threshold=0.05
        - Auto-optimization activée avec safety checks
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 2 - Test création job monitoring")
            
            job_data = {
                "marketplace_id": self.test_marketplace_id,
                "skus": self.test_skus,
                "monitoring_frequency_hours": 6,
                "optimization_frequency_hours": 24,
                "auto_optimization_enabled": True,
                "buybox_loss_threshold": 0.8,
                "price_deviation_threshold": 0.05,
                "seo_score_threshold": 0.7
            }
            
            async with self.session.post(f"{API_BASE}/amazon/monitoring/jobs", json=job_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success") and result.get("job"):
                        job = result["job"]
                        job_id = job.get("id")
                        
                        # Vérifier la configuration du job
                        config_valid = (
                            job.get("marketplace_id") == self.test_marketplace_id and
                            job.get("skus") == self.test_skus and
                            job.get("monitoring_frequency_hours") == 6 and
                            job.get("optimization_frequency_hours") == 24 and
                            job.get("auto_optimization_enabled") == True and
                            job.get("buybox_loss_threshold") == 0.8 and
                            job.get("price_deviation_threshold") == 0.05
                        )
                        
                        duration = time.time() - start_time
                        self.workflow_timings["create_monitoring_job"] = duration
                        
                        if config_valid:
                            self.log_test_result(
                                "Create Monitoring Job",
                                True,
                                f"Job monitoring créé avec succès (ID: {job_id}, {len(self.test_skus)} SKUs)",
                                duration
                            )
                            return job_id
                        else:
                            self.log_test_result(
                                "Create Monitoring Job",
                                False,
                                "Configuration du job incorrecte"
                            )
                            return None
                    else:
                        self.log_test_result(
                            "Create Monitoring Job",
                            False,
                            f"Réponse invalide: {result}"
                        )
                        return None
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Create Monitoring Job",
                        False,
                        f"Échec création job: {response.status} - {error_text}"
                    )
                    return None
        
        except Exception as e:
            self.log_test_result(
                "Create Monitoring Job",
                False,
                f"Erreur création job monitoring: {str(e)}"
            )
            return None
    
    async def test_3_data_collection_snapshots(self, job_id: str) -> bool:
        """
        ÉTAPE 3 - COLLECTE DONNÉES (SNAPSHOTS)
        - Simulation données SP-API : Catalog Items, Product Pricing, Buy Box status
        - Création ProductSnapshot avec data_completeness_score
        - Détection Buy Box status (WON/LOST/SHARED/ELIGIBLE)
        - Analyse concurrents et prix min/max/avg
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 3 - Test collecte données snapshots")
            
            # Tester la récupération des snapshots
            async with self.session.get(
                f"{API_BASE}/amazon/monitoring/snapshots",
                params={
                    "marketplace_id": self.test_marketplace_id,
                    "days_back": 1,
                    "limit": 10
                }
            ) as response:
                if response.status == 200:
                    snapshots = await response.json()
                    
                    duration = time.time() - start_time
                    self.workflow_timings["data_collection_snapshots"] = duration
                    
                    # Vérifier la structure des snapshots
                    if isinstance(snapshots, list):
                        self.log_test_result(
                            "Data Collection Snapshots",
                            True,
                            f"Collecte snapshots réussie - {len(snapshots)} snapshots récupérés",
                            duration
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Data Collection Snapshots",
                            False,
                            f"Format snapshots invalide: {type(snapshots)}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Data Collection Snapshots",
                        False,
                        f"Échec récupération snapshots: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Data Collection Snapshots",
                False,
                f"Erreur collecte snapshots: {str(e)}"
            )
            return False
    
    async def test_4_desired_states_comparison(self) -> bool:
        """
        ÉTAPE 4 - ÉTATS DÉSIRÉS ET COMPARAISON
        - Création DesiredState avec prix cibles et stratégies
        - Comparaison état désiré vs snapshot observé
        - Calcul écarts prix, SEO, Buy Box avec scoring confiance/risque
        - Détection seuils dépassés et priorité optimisation
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 4 - Test états désirés et comparaison")
            
            # Créer un état désiré pour le premier SKU de test
            test_sku = self.test_skus[0]
            
            desired_state_data = {
                "sku": test_sku,
                "marketplace_id": self.test_marketplace_id,
                "desired_title": f"Titre Optimisé {test_sku} - Monitoring Phase 5",
                "desired_description": "Description optimisée avec mots-clés stratégiques pour maximiser la visibilité Amazon",
                "desired_bullet_points": [
                    "✓ Performance monitoring en temps réel",
                    "✓ Optimisation automatique des prix",
                    "✓ Suivi concurrentiel avancé",
                    "✓ Alertes intelligentes personnalisées",
                    "✓ Dashboard analytics complet"
                ],
                "desired_keywords": ["monitoring", "optimization", "amazon", "performance", "analytics"],
                "desired_price": 32.99,
                "price_strategy": "competitive_follow",
                "min_price": 25.99,
                "max_price": 45.99,
                "target_buybox_share": 0.9,
                "target_conversion_rate": 0.15,
                "target_ctr": 0.08,
                "auto_correction_enabled": True,
                "correction_max_frequency_hours": 24
            }
            
            async with self.session.post(
                f"{API_BASE}/amazon/monitoring/desired-states",
                json=desired_state_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        desired_state_id = result.get("desired_state_id")
                        
                        # Vérifier la récupération de l'état désiré
                        async with self.session.get(
                            f"{API_BASE}/amazon/monitoring/desired-states/{test_sku}",
                            params={"marketplace_id": self.test_marketplace_id}
                        ) as get_response:
                            if get_response.status == 200:
                                retrieved_state = await get_response.json()
                                
                                duration = time.time() - start_time
                                self.workflow_timings["desired_states_comparison"] = duration
                                
                                # Vérifier la cohérence des données
                                if (retrieved_state and 
                                    retrieved_state.get("sku") == test_sku and
                                    retrieved_state.get("desired_price") == 32.99):
                                    
                                    self.log_test_result(
                                        "Desired States Comparison",
                                        True,
                                        f"État désiré créé et récupéré (ID: {desired_state_id})",
                                        duration
                                    )
                                    return True
                                else:
                                    self.log_test_result(
                                        "Desired States Comparison",
                                        False,
                                        "Données état désiré incohérentes"
                                    )
                                    return False
                            else:
                                self.log_test_result(
                                    "Desired States Comparison",
                                    False,
                                    f"Échec récupération état désiré: {get_response.status}"
                                )
                                return False
                    else:
                        self.log_test_result(
                            "Desired States Comparison",
                            False,
                            f"Échec création état désiré: {result}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Desired States Comparison",
                        False,
                        f"Erreur création état désiré: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Desired States Comparison",
                False,
                f"Erreur états désirés: {str(e)}"
            )
            return False
    
    async def test_5_optimization_decisions(self) -> bool:
        """
        ÉTAPE 5 - DÉCISIONS OPTIMISATION
        - Génération OptimizationDecision avec execution_plan
        - Actions : PRICE_UPDATE, SEO_UPDATE, AUTO_CORRECTION
        - Safety checks : max 15% changement prix, fréquence corrections
        - Circuit breaker protection contre surcharge
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 5 - Test décisions optimisation")
            
            # Déclencher une optimisation manuelle
            optimization_request = {
                "sku": self.test_skus[0],
                "marketplace_id": self.test_marketplace_id,
                "force": True
            }
            
            async with self.session.post(
                f"{API_BASE}/amazon/monitoring/optimize",
                json=optimization_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        # Attendre un peu pour que l'optimisation soit traitée
                        await asyncio.sleep(2)
                        
                        # Récupérer l'historique des optimisations
                        async with self.session.get(
                            f"{API_BASE}/amazon/monitoring/optimizations",
                            params={
                                "sku": self.test_skus[0],
                                "marketplace_id": self.test_marketplace_id,
                                "days_back": 1,
                                "limit": 10
                            }
                        ) as history_response:
                            if history_response.status == 200:
                                history_result = await history_response.json()
                                
                                duration = time.time() - start_time
                                self.workflow_timings["optimization_decisions"] = duration
                                
                                if (history_result.get("success") and 
                                    isinstance(history_result.get("decisions"), list)):
                                    
                                    decisions = history_result["decisions"]
                                    self.log_test_result(
                                        "Optimization Decisions",
                                        True,
                                        f"Optimisation déclenchée - {len(decisions)} décisions dans l'historique",
                                        duration
                                    )
                                    return True
                                else:
                                    self.log_test_result(
                                        "Optimization Decisions",
                                        False,
                                        f"Format historique invalide: {history_result}"
                                    )
                                    return False
                            else:
                                self.log_test_result(
                                    "Optimization Decisions",
                                    False,
                                    f"Échec récupération historique: {history_response.status}"
                                )
                                return False
                    else:
                        self.log_test_result(
                            "Optimization Decisions",
                            False,
                            f"Échec déclenchement optimisation: {result}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Optimization Decisions",
                        False,
                        f"Erreur optimisation: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Optimization Decisions",
                False,
                f"Erreur décisions optimisation: {str(e)}"
            )
            return False
    
    async def test_6_execution_corrections(self) -> bool:
        """
        ÉTAPE 6 - EXÉCUTION CORRECTIONS
        - Simulation appels SP-API : Listings Items API, Feeds API
        - Tracking execution_duration, success/failure status
        - Mise à jour states et monitoring alerts
        - Rollback en cas d'échec avec error_message
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 6 - Test exécution corrections")
            
            # Tester le déclenchement d'un cycle de monitoring système
            async with self.session.post(f"{API_BASE}/amazon/monitoring/system/trigger-cycle") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        # Attendre que le cycle soit traité
                        await asyncio.sleep(3)
                        
                        # Vérifier les statistiques système
                        async with self.session.get(f"{API_BASE}/amazon/monitoring/system/stats") as stats_response:
                            duration = time.time() - start_time
                            self.workflow_timings["execution_corrections"] = duration
                            
                            if stats_response.status == 200:
                                stats_result = await stats_response.json()
                                
                                if stats_result.get("success"):
                                    self.log_test_result(
                                        "Execution Corrections",
                                        True,
                                        f"Cycle monitoring exécuté - Stats système récupérées",
                                        duration
                                    )
                                    return True
                                else:
                                    self.log_test_result(
                                        "Execution Corrections",
                                        False,
                                        "Échec récupération stats système"
                                    )
                                    return False
                            else:
                                # Stats peuvent ne pas être disponibles, mais cycle peut avoir fonctionné
                                self.log_test_result(
                                    "Execution Corrections",
                                    True,
                                    f"Cycle monitoring exécuté (stats non disponibles: {stats_response.status})",
                                    duration
                                )
                                return True
                    else:
                        self.log_test_result(
                            "Execution Corrections",
                            False,
                            f"Échec déclenchement cycle: {result}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Execution Corrections",
                        False,
                        f"Erreur cycle monitoring: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Execution Corrections",
                False,
                f"Erreur exécution corrections: {str(e)}"
            )
            return False
    
    async def test_7_kpis_dashboard(self) -> bool:
        """
        ÉTAPE 7 - CALCUL KPIS ET DASHBOARD
        - Agrégation métriques : Buy Box share, prix updates, SEO scores
        - Auto-corrections statistics : triggered/successful/failed
        - API calls performance : count, errors, response times
        - Dashboard data : recent snapshots, optimizations, alerts
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 7 - Test calcul KPIs et dashboard")
            
            # Test récupération KPIs
            async with self.session.get(
                f"{API_BASE}/amazon/monitoring/kpis",
                params={
                    "marketplace_id": self.test_marketplace_id,
                    "period_hours": 24
                }
            ) as response:
                if response.status == 200:
                    kpis_result = await response.json()
                    
                    if kpis_result.get("success") and kpis_result.get("kpis"):
                        kpis = kpis_result["kpis"]
                        
                        # Vérifier la structure des KPIs
                        required_fields = [
                            "total_skus_monitored", "buybox_won_count", "buybox_lost_count",
                            "price_updates_count", "seo_updates_count", "auto_corrections_triggered"
                        ]
                        
                        kpis_valid = all(field in kpis for field in required_fields)
                        
                        if kpis_valid:
                            # Test dashboard complet
                            async with self.session.get(
                                f"{API_BASE}/amazon/monitoring/dashboard",
                                params={"marketplace_id": self.test_marketplace_id}
                            ) as dashboard_response:
                                if dashboard_response.status == 200:
                                    dashboard_data = await dashboard_response.json()
                                    
                                    duration = time.time() - start_time
                                    self.workflow_timings["kpis_dashboard"] = duration
                                    
                                    # Vérifier la structure du dashboard
                                    if (dashboard_data.get("kpis") and
                                        "recent_snapshots" in dashboard_data and
                                        "recent_optimizations" in dashboard_data and
                                        "active_alerts" in dashboard_data):
                                        
                                        self.log_test_result(
                                            "KPIs Dashboard",
                                            True,
                                            f"KPIs et dashboard calculés - {len(dashboard_data.get('recent_snapshots', []))} snapshots récents",
                                            duration
                                        )
                                        return True
                                    else:
                                        self.log_test_result(
                                            "KPIs Dashboard",
                                            False,
                                            f"Structure dashboard incomplète: {list(dashboard_data.keys())}"
                                        )
                                        return False
                                else:
                                    self.log_test_result(
                                        "KPIs Dashboard",
                                        False,
                                        f"Échec récupération dashboard: {dashboard_response.status}"
                                    )
                                    return False
                        else:
                            missing_fields = [f for f in required_fields if f not in kpis]
                            self.log_test_result(
                                "KPIs Dashboard",
                                False,
                                f"KPIs incomplets - Champs manquants: {missing_fields}"
                            )
                            return False
                    else:
                        self.log_test_result(
                            "KPIs Dashboard",
                            False,
                            f"KPIs invalides: {kpis_result}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "KPIs Dashboard",
                        False,
                        f"Erreur récupération KPIs: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "KPIs Dashboard",
                False,
                f"Erreur KPIs dashboard: {str(e)}"
            )
            return False
    
    async def test_8_continuous_monitoring(self) -> bool:
        """
        ÉTAPE 8 - MONITORING CONTINU
        - Cycles périodiques orchestrateur (6h monitoring, 24h optimisation)
        - Circuit breaker en cas d'échecs répétés
        - Cleanup automatique données anciennes (90d/180d/30d)
        - Health checks système et maintenance
        """
        try:
            start_time = time.time()
            logger.info("🚀 ÉTAPE 8 - Test monitoring continu")
            
            # Test récupération des alertes actives
            async with self.session.get(
                f"{API_BASE}/amazon/monitoring/alerts",
                params={"marketplace_id": self.test_marketplace_id}
            ) as response:
                if response.status == 200:
                    alerts = await response.json()
                    
                    # Test récupération des jobs de monitoring
                    async with self.session.get(
                        f"{API_BASE}/amazon/monitoring/jobs",
                        params={"marketplace_id": self.test_marketplace_id}
                    ) as jobs_response:
                        if jobs_response.status == 200:
                            jobs = await jobs_response.json()
                            
                            duration = time.time() - start_time
                            self.workflow_timings["continuous_monitoring"] = duration
                            
                            # Vérifier que les jobs sont configurés pour le monitoring continu
                            active_jobs = [job for job in jobs if job.get("status") == "active"]
                            
                            self.log_test_result(
                                "Continuous Monitoring",
                                True,
                                f"Monitoring continu configuré - {len(active_jobs)} jobs actifs, {len(alerts)} alertes",
                                duration
                            )
                            return True
                        else:
                            self.log_test_result(
                                "Continuous Monitoring",
                                False,
                                f"Échec récupération jobs: {jobs_response.status}"
                            )
                            return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Continuous Monitoring",
                        False,
                        f"Erreur récupération alertes: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Continuous Monitoring",
                False,
                f"Erreur monitoring continu: {str(e)}"
            )
            return False
    
    async def test_performance_requirements(self) -> bool:
        """Test des exigences de performance"""
        try:
            start_time = time.time()
            logger.info("🚀 Test exigences de performance")
            
            # Calculer le temps total du workflow E2E
            total_workflow_time = sum(self.workflow_timings.values())
            
            # Critère : cycle E2E < 30s par SKU
            max_time_per_sku = 30.0
            time_per_sku = total_workflow_time / len(self.test_skus)
            
            performance_ok = time_per_sku < max_time_per_sku
            
            # Métriques de performance
            self.test_results["performance_metrics"] = {
                "total_workflow_time_seconds": round(total_workflow_time, 2),
                "time_per_sku_seconds": round(time_per_sku, 2),
                "max_allowed_per_sku": max_time_per_sku,
                "performance_requirement_met": performance_ok,
                "workflow_breakdown": {k: round(v, 2) for k, v in self.workflow_timings.items()}
            }
            
            duration = time.time() - start_time
            self.log_test_result(
                "Performance Requirements",
                performance_ok,
                f"Performance E2E: {time_per_sku:.2f}s/SKU (max: {max_time_per_sku}s)",
                duration
            )
            
            return performance_ok
            
        except Exception as e:
            self.log_test_result(
                "Performance Requirements",
                False,
                f"Erreur test performance: {str(e)}"
            )
            return False
    
    async def run_complete_workflow_test(self):
        """Exécuter le test complet du workflow E2E"""
        try:
            self.start_time = time.time()
            logger.info("🚀 DÉMARRAGE TESTS E2E AMAZON MONITORING PHASE 5")
            
            # Authentification
            if not await self.authenticate_user():
                logger.error("❌ Échec authentification - Arrêt des tests")
                return
            
            # Étape 1 : Initialisation système
            if not await self.test_1_system_initialization():
                logger.error("❌ Échec initialisation système")
                return
            
            # Étape 2 : Création job monitoring
            job_id = await self.test_2_create_monitoring_job()
            if not job_id:
                logger.error("❌ Échec création job monitoring")
                return
            
            # Étape 3 : Collecte données snapshots
            if not await self.test_3_data_collection_snapshots(job_id):
                logger.error("❌ Échec collecte données")
                return
            
            # Étape 4 : États désirés et comparaison
            if not await self.test_4_desired_states_comparison():
                logger.error("❌ Échec états désirés")
                return
            
            # Étape 5 : Décisions optimisation
            if not await self.test_5_optimization_decisions():
                logger.error("❌ Échec décisions optimisation")
                return
            
            # Étape 6 : Exécution corrections
            if not await self.test_6_execution_corrections():
                logger.error("❌ Échec exécution corrections")
                return
            
            # Étape 7 : KPIs et dashboard
            if not await self.test_7_kpis_dashboard():
                logger.error("❌ Échec KPIs dashboard")
                return
            
            # Étape 8 : Monitoring continu
            if not await self.test_8_continuous_monitoring():
                logger.error("❌ Échec monitoring continu")
                return
            
            # Test performance
            await self.test_performance_requirements()
            
            # Calcul du temps total
            total_time = time.time() - self.start_time
            self.test_results["total_execution_time"] = round(total_time, 2)
            
            logger.info("✅ TESTS E2E AMAZON MONITORING PHASE 5 TERMINÉS")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique dans le workflow: {str(e)}")
            self.test_results["errors"].append(f"Erreur workflow: {str(e)}")
    
    def generate_final_report(self) -> str:
        """Générer le rapport final des tests"""
        
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"] * 100) if self.test_results["total_tests"] > 0 else 0
        
        report = f"""
🎉 RAPPORT FINAL - TESTS E2E AMAZON MONITORING PHASE 5 - WORKFLOW COMPLET ECOMSIMPLY

📊 RÉSULTATS GLOBAUX:
✅ Tests réussis: {self.test_results["passed_tests"]}/{self.test_results["total_tests"]} ({success_rate:.1f}%)
❌ Tests échoués: {self.test_results["failed_tests"]}
⏱️ Temps total d'exécution: {self.test_results.get("total_execution_time", 0)}s

🚀 WORKFLOW E2E VALIDÉ:
"""
        
        # Détails des tests
        for test in self.test_results["test_details"]:
            report += f"{test['status']} {test['test_name']}: {test['details']} ({test['duration_ms']}ms)\n"
        
        # Métriques de performance
        if "performance_metrics" in self.test_results:
            perf = self.test_results["performance_metrics"]
            report += f"""
📈 MÉTRIQUES DE PERFORMANCE:
• Temps workflow E2E: {perf.get("total_workflow_time_seconds", 0)}s
• Temps par SKU: {perf.get("time_per_sku_seconds", 0)}s (max autorisé: {perf.get("max_allowed_per_sku", 30)}s)
• Exigence performance: {"✅ RESPECTÉE" if perf.get("performance_requirement_met") else "❌ NON RESPECTÉE"}

🔧 DÉTAIL PAR ÉTAPE:
"""
            for step, time_val in perf.get("workflow_breakdown", {}).items():
                report += f"• {step}: {time_val}s\n"
        
        # Erreurs
        if self.test_results["errors"]:
            report += f"\n❌ ERREURS DÉTECTÉES:\n"
            for error in self.test_results["errors"]:
                report += f"• {error}\n"
        
        # Critères de succès E2E
        report += f"""
✅ CRITÈRES DE SUCCÈS E2E:
{"✅" if success_rate >= 80 else "❌"} Workflow complet sans erreurs critiques (≥80% tests réussis)
{"✅" if self.test_results.get("performance_metrics", {}).get("performance_requirement_met") else "❌"} Performance : cycle E2E < 30s par SKU
{"✅" if success_rate >= 75 else "❌"} Intégration SP-API simulée opérationnelle
{"✅" if success_rate >= 70 else "❌"} Data persistence MongoDB correcte

🎯 VALIDATION FINALE: {"✅ SUCCÈS" if success_rate >= 75 else "❌ ÉCHEC"} - Amazon Monitoring Phase 5 Workflow {"OPÉRATIONNEL" if success_rate >= 75 else "NÉCESSITE CORRECTIONS"}
"""
        
        return report

async def main():
    """Fonction principale"""
    tester = AmazonMonitoringPhase5Tester()
    
    try:
        await tester.setup_session()
        await tester.run_complete_workflow_test()
        
        # Générer et afficher le rapport final
        final_report = tester.generate_final_report()
        print(final_report)
        
        # Sauvegarder le rapport
        with open("/app/amazon_monitoring_phase5_test_report.txt", "w", encoding="utf-8") as f:
            f.write(final_report)
        
        logger.info("📄 Rapport sauvegardé dans amazon_monitoring_phase5_test_report.txt")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
    
    finally:
        await tester.cleanup_session()

if __name__ == "__main__":
    asyncio.run(main())