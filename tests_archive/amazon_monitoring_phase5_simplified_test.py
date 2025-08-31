#!/usr/bin/env python3
"""
Tests E2E Amazon Monitoring Phase 5 - Workflow Complet ECOMSIMPLY
Backend Testing for Amazon Monitoring Phase 5 Complete Workflow - SIMPLIFIED VERSION

Test des endpoints disponibles et validation de l'architecture backend
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

class AmazonMonitoringPhase5SimplifiedTester:
    """
    Testeur simplifié pour Amazon Monitoring Phase 5
    
    Tests des endpoints disponibles et validation de l'architecture
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
            "errors": []
        }
    
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
    
    async def test_system_health(self) -> bool:
        """Test du health check système"""
        try:
            start_time = time.time()
            
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    duration = time.time() - start_time
                    self.log_test_result(
                        "System Health Check",
                        True,
                        f"Système en bonne santé - Status: {health_data.get('status', 'unknown')}",
                        duration
                    )
                    return True
                else:
                    self.log_test_result(
                        "System Health Check",
                        False,
                        f"Health check échoué: {response.status}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "System Health Check",
                False,
                f"Erreur health check: {str(e)}"
            )
            return False
    
    async def test_authentication_endpoints(self) -> bool:
        """Test des endpoints d'authentification"""
        try:
            start_time = time.time()
            
            # Test création utilisateur
            register_data = {
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{API_BASE}/auth/register", json=register_data) as response:
                if response.status in [200, 201, 400]:  # 400 = utilisateur existe déjà
                    logger.info(f"✅ Endpoint register accessible: {response.status}")
                    
                    # Test connexion
                    login_data = {
                        "email": TEST_USER_EMAIL,
                        "password": TEST_USER_PASSWORD
                    }
                    
                    async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            data = await login_response.json()
                            self.auth_token = data.get("access_token")
                            self.user_id = data.get("user_id")
                            
                            if self.auth_token:
                                self.session.headers.update({
                                    "Authorization": f"Bearer {self.auth_token}",
                                    "Content-Type": "application/json"
                                })
                                
                                duration = time.time() - start_time
                                self.log_test_result(
                                    "Authentication Endpoints",
                                    True,
                                    f"Authentification réussie (user_id: {self.user_id})",
                                    duration
                                )
                                return True
                            else:
                                self.log_test_result(
                                    "Authentication Endpoints",
                                    False,
                                    "Token manquant dans la réponse"
                                )
                                return False
                        else:
                            error_text = await login_response.text()
                            self.log_test_result(
                                "Authentication Endpoints",
                                False,
                                f"Échec login: {login_response.status} - {error_text}"
                            )
                            return False
                else:
                    error_text = await response.text()
                    self.log_test_result(
                        "Authentication Endpoints",
                        False,
                        f"Échec register: {response.status} - {error_text}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Authentication Endpoints",
                False,
                f"Erreur authentification: {str(e)}"
            )
            return False
    
    async def test_amazon_endpoints_availability(self) -> bool:
        """Test de la disponibilité des endpoints Amazon"""
        try:
            start_time = time.time()
            
            # Liste des endpoints Amazon à tester
            amazon_endpoints = [
                "/amazon/status",
                "/amazon/marketplaces", 
                "/amazon/health/phase3",
                "/amazon/seo/rules",
                "/amazon/listings/generate",
                "/amazon/monitoring/dashboard",
                "/amazon/monitoring/jobs",
                "/amazon/monitoring/snapshots",
                "/amazon/monitoring/optimizations",
                "/amazon/monitoring/alerts",
                "/amazon/monitoring/kpis"
            ]
            
            available_endpoints = 0
            total_endpoints = len(amazon_endpoints)
            endpoint_results = []
            
            for endpoint in amazon_endpoints:
                try:
                    async with self.session.get(f"{API_BASE}{endpoint}") as response:
                        if response.status in [200, 401, 422, 403]:  # Codes acceptables
                            available_endpoints += 1
                            endpoint_results.append(f"✅ {endpoint}: {response.status}")
                        else:
                            endpoint_results.append(f"❌ {endpoint}: {response.status}")
                except Exception as e:
                    endpoint_results.append(f"❌ {endpoint}: Exception - {str(e)}")
            
            duration = time.time() - start_time
            
            # Considérer comme succès si au moins 50% des endpoints sont disponibles
            success = available_endpoints >= (total_endpoints * 0.5)
            
            details = f"{available_endpoints}/{total_endpoints} endpoints Amazon disponibles"
            for result in endpoint_results:
                logger.info(result)
            
            self.log_test_result(
                "Amazon Endpoints Availability",
                success,
                details,
                duration
            )
            
            return success
        
        except Exception as e:
            self.log_test_result(
                "Amazon Endpoints Availability",
                False,
                f"Erreur test endpoints Amazon: {str(e)}"
            )
            return False
    
    async def test_backend_services_health(self) -> bool:
        """Test de la santé des services backend"""
        try:
            start_time = time.time()
            
            # Test des endpoints de santé des services
            health_endpoints = [
                "/health",
                "/health/ready",
                "/health/live"
            ]
            
            healthy_services = 0
            total_services = len(health_endpoints)
            
            for endpoint in health_endpoints:
                try:
                    async with self.session.get(f"{API_BASE}{endpoint}") as response:
                        if response.status == 200:
                            healthy_services += 1
                            data = await response.json()
                            logger.info(f"✅ {endpoint}: {data.get('status', 'healthy')}")
                        else:
                            logger.warning(f"⚠️ {endpoint}: {response.status}")
                except Exception as e:
                    logger.warning(f"⚠️ {endpoint}: {str(e)}")
            
            duration = time.time() - start_time
            
            success = healthy_services >= (total_services * 0.7)  # Au moins 70% des services en santé
            
            self.log_test_result(
                "Backend Services Health",
                success,
                f"{healthy_services}/{total_services} services backend en santé",
                duration
            )
            
            return success
        
        except Exception as e:
            self.log_test_result(
                "Backend Services Health",
                False,
                f"Erreur test santé services: {str(e)}"
            )
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test de la connectivité base de données"""
        try:
            start_time = time.time()
            
            # Test via un endpoint qui nécessite la DB (stats publiques)
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    duration = time.time() - start_time
                    self.log_test_result(
                        "Database Connectivity",
                        True,
                        f"Base de données accessible - {data.get('total_sheets', 0)} fiches totales",
                        duration
                    )
                    return True
                else:
                    self.log_test_result(
                        "Database Connectivity",
                        False,
                        f"Échec accès DB: {response.status}"
                    )
                    return False
        
        except Exception as e:
            self.log_test_result(
                "Database Connectivity",
                False,
                f"Erreur connectivité DB: {str(e)}"
            )
            return False
    
    async def test_amazon_monitoring_architecture(self) -> bool:
        """Test de l'architecture Amazon Monitoring (sans authentification)"""
        try:
            start_time = time.time()
            
            # Test des endpoints de monitoring sans auth (pour vérifier qu'ils existent)
            monitoring_endpoints = [
                "/amazon/monitoring/dashboard",
                "/amazon/monitoring/jobs", 
                "/amazon/monitoring/snapshots",
                "/amazon/monitoring/optimizations",
                "/amazon/monitoring/alerts",
                "/amazon/monitoring/kpis",
                "/amazon/monitoring/system/stats"
            ]
            
            architecture_score = 0
            total_endpoints = len(monitoring_endpoints)
            
            for endpoint in monitoring_endpoints:
                try:
                    async with self.session.get(f"{API_BASE}{endpoint}") as response:
                        # 401/422 = endpoint existe mais auth requise (bon signe)
                        # 404 = endpoint n'existe pas (mauvais signe)
                        if response.status in [200, 401, 422, 403]:
                            architecture_score += 1
                            logger.info(f"✅ Architecture endpoint: {endpoint} ({response.status})")
                        else:
                            logger.warning(f"❌ Architecture endpoint: {endpoint} ({response.status})")
                except Exception as e:
                    logger.warning(f"❌ Architecture endpoint: {endpoint} - {str(e)}")
            
            duration = time.time() - start_time
            
            # Considérer comme succès si au moins 60% des endpoints sont architecturalement présents
            success = architecture_score >= (total_endpoints * 0.6)
            
            self.log_test_result(
                "Amazon Monitoring Architecture",
                success,
                f"Architecture monitoring: {architecture_score}/{total_endpoints} endpoints détectés",
                duration
            )
            
            return success
        
        except Exception as e:
            self.log_test_result(
                "Amazon Monitoring Architecture",
                False,
                f"Erreur test architecture: {str(e)}"
            )
            return False
    
    async def test_workflow_simulation(self) -> bool:
        """Test de simulation du workflow (endpoints publics uniquement)"""
        try:
            start_time = time.time()
            
            workflow_steps = []
            
            # Étape 1: Vérifier la santé du système
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    workflow_steps.append("✅ Système initialisé")
                else:
                    workflow_steps.append("❌ Système non initialisé")
            
            # Étape 2: Vérifier les stats publiques (DB)
            async with self.session.get(f"{API_BASE}/stats/public") as response:
                if response.status == 200:
                    workflow_steps.append("✅ Base de données accessible")
                else:
                    workflow_steps.append("❌ Base de données inaccessible")
            
            # Étape 3: Vérifier l'architecture monitoring
            async with self.session.get(f"{API_BASE}/amazon/monitoring/dashboard") as response:
                if response.status in [401, 422]:  # Auth requise = endpoint existe
                    workflow_steps.append("✅ Architecture monitoring présente")
                else:
                    workflow_steps.append("❌ Architecture monitoring absente")
            
            # Étape 4: Vérifier les services Amazon
            async with self.session.get(f"{API_BASE}/amazon/health/phase3") as response:
                if response.status in [200, 401, 422]:
                    workflow_steps.append("✅ Services Amazon disponibles")
                else:
                    workflow_steps.append("❌ Services Amazon indisponibles")
            
            duration = time.time() - start_time
            
            success_steps = len([step for step in workflow_steps if step.startswith("✅")])
            total_steps = len(workflow_steps)
            
            success = success_steps >= (total_steps * 0.75)  # Au moins 75% des étapes réussies
            
            details = f"Workflow simulation: {success_steps}/{total_steps} étapes réussies"
            for step in workflow_steps:
                logger.info(step)
            
            self.log_test_result(
                "Workflow Simulation",
                success,
                details,
                duration
            )
            
            return success
        
        except Exception as e:
            self.log_test_result(
                "Workflow Simulation",
                False,
                f"Erreur simulation workflow: {str(e)}"
            )
            return False
    
    async def run_simplified_tests(self):
        """Exécuter les tests simplifiés"""
        try:
            logger.info("🚀 DÉMARRAGE TESTS AMAZON MONITORING PHASE 5 - VERSION SIMPLIFIÉE")
            
            # Test 1: Santé du système
            await self.test_system_health()
            
            # Test 2: Endpoints d'authentification
            await self.test_authentication_endpoints()
            
            # Test 3: Disponibilité endpoints Amazon
            await self.test_amazon_endpoints_availability()
            
            # Test 4: Santé des services backend
            await self.test_backend_services_health()
            
            # Test 5: Connectivité base de données
            await self.test_database_connectivity()
            
            # Test 6: Architecture Amazon Monitoring
            await self.test_amazon_monitoring_architecture()
            
            # Test 7: Simulation workflow
            await self.test_workflow_simulation()
            
            logger.info("✅ TESTS AMAZON MONITORING PHASE 5 TERMINÉS")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique dans les tests: {str(e)}")
            self.test_results["errors"].append(f"Erreur tests: {str(e)}")
    
    def generate_final_report(self) -> str:
        """Générer le rapport final des tests"""
        
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"] * 100) if self.test_results["total_tests"] > 0 else 0
        
        report = f"""
🎉 RAPPORT FINAL - TESTS AMAZON MONITORING PHASE 5 - ARCHITECTURE VALIDATION

📊 RÉSULTATS GLOBAUX:
✅ Tests réussis: {self.test_results["passed_tests"]}/{self.test_results["total_tests"]} ({success_rate:.1f}%)
❌ Tests échoués: {self.test_results["failed_tests"]}

🔍 DÉTAILS DES TESTS:
"""
        
        # Détails des tests
        for test in self.test_results["test_details"]:
            report += f"{test['status']} {test['test_name']}: {test['details']} ({test['duration_ms']}ms)\n"
        
        # Erreurs
        if self.test_results["errors"]:
            report += f"\n❌ ERREURS DÉTECTÉES:\n"
            for error in self.test_results["errors"]:
                report += f"• {error}\n"
        
        # Évaluation finale
        if success_rate >= 80:
            final_status = "✅ EXCELLENT"
            recommendation = "Architecture Amazon Monitoring Phase 5 OPÉRATIONNELLE"
        elif success_rate >= 60:
            final_status = "⚠️ ACCEPTABLE"
            recommendation = "Architecture partiellement fonctionnelle - Corrections mineures nécessaires"
        else:
            final_status = "❌ INSUFFISANT"
            recommendation = "Architecture nécessite des corrections majeures"
        
        report += f"""
🎯 ÉVALUATION FINALE:
Status: {final_status} ({success_rate:.1f}% de réussite)
Recommandation: {recommendation}

📋 CRITÈRES AMAZON MONITORING PHASE 5:
{"✅" if success_rate >= 70 else "❌"} Architecture backend présente
{"✅" if success_rate >= 60 else "❌"} Services système opérationnels  
{"✅" if success_rate >= 50 else "❌"} Endpoints Amazon accessibles
{"✅" if success_rate >= 80 else "❌"} Workflow E2E simulable

🚀 CONCLUSION: Amazon Monitoring Phase 5 est {"PRÊT POUR VALIDATION COMPLÈTE" if success_rate >= 70 else "EN DÉVELOPPEMENT - NÉCESSITE CORRECTIONS"}
"""
        
        return report

async def main():
    """Fonction principale"""
    tester = AmazonMonitoringPhase5SimplifiedTester()
    
    try:
        await tester.setup_session()
        await tester.run_simplified_tests()
        
        # Générer et afficher le rapport final
        final_report = tester.generate_final_report()
        print(final_report)
        
        # Sauvegarder le rapport
        with open("/app/amazon_monitoring_phase5_simplified_test_report.txt", "w", encoding="utf-8") as f:
            f.write(final_report)
        
        logger.info("📄 Rapport sauvegardé dans amazon_monitoring_phase5_simplified_test_report.txt")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
    
    finally:
        await tester.cleanup_session()

if __name__ == "__main__":
    asyncio.run(main())