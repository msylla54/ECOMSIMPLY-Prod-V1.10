#!/usr/bin/env python3
"""
Test de Validation Post-Réinitialisation Phase 5 Amazon Monitoring
Validation rapide pour confirmer que la Phase 5 Amazon Monitoring est toujours opérationnelle.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

def test_system_status():
    """Test 1: STATUT SYSTÈME - Services actifs, health check API"""
    print("🔍 TEST 1: STATUT SYSTÈME")
    
    results = {
        "health_check": False,
        "ready_check": False,
        "system_metrics": False
    }
    
    try:
        # Health check principal
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check: {health_data.get('status', 'unknown')}")
            results["health_check"] = health_data.get('status') == 'healthy'
        else:
            print(f"❌ Health Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check error: {e}")
    
    try:
        # Ready check
        response = requests.get(f"{API_BASE}/health/ready", timeout=10)
        if response.status_code == 200:
            print("✅ Ready Check: OK")
            results["ready_check"] = True
        else:
            print(f"❌ Ready Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Ready Check error: {e}")
    
    try:
        # System metrics check
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'cpu_usage' in data and 'memory_usage' in data:
                cpu = data.get('cpu_usage', 0)
                memory = data.get('memory_usage', 0)
                print(f"✅ System Metrics: CPU {cpu}%, Memory {memory}%")
                results["system_metrics"] = True
            else:
                print("⚠️ System metrics not available")
    except Exception as e:
        print(f"❌ System metrics error: {e}")
    
    return results

def test_monitoring_endpoints():
    """Test 2: ENDPOINTS MONITORING ACCESSIBLES - Doivent retourner 403 (auth requise), pas 404"""
    print("\n🔍 TEST 2: ENDPOINTS MONITORING ACCESSIBLES")
    
    endpoints = [
        "/amazon/monitoring/dashboard",
        "/amazon/monitoring/jobs", 
        "/amazon/monitoring/snapshots"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            status = response.status_code
            
            if status == 403:
                print(f"✅ {endpoint} → 403 (authentification requise - NORMAL)")
                results[endpoint] = "OK"
            elif status == 404:
                print(f"❌ {endpoint} → 404 (route non enregistrée - PROBLÈME)")
                results[endpoint] = "NOT_FOUND"
            elif status == 401:
                print(f"✅ {endpoint} → 401 (authentification requise - NORMAL)")
                results[endpoint] = "OK"
            else:
                print(f"⚠️ {endpoint} → {status} (statut inattendu)")
                results[endpoint] = f"UNEXPECTED_{status}"
                
        except Exception as e:
            print(f"❌ {endpoint} → Erreur: {e}")
            results[endpoint] = "ERROR"
    
    return results

def test_backend_components():
    """Test 3: COMPOSANTS BACKEND PRÉSENTS - Vérification des fichiers Phase 5"""
    print("\n🔍 TEST 3: COMPOSANTS BACKEND PRÉSENTS")
    
    components = {
        "models/amazon_monitoring.py": "Modèles Pydantic",
        "routes/amazon_monitoring_routes.py": "Routes API", 
        "services/amazon_monitoring_service.py": "Service MongoDB",
        "amazon/monitoring/orchestrator.py": "Orchestrateur",
        "amazon/optimizer/closed_loop.py": "Optimiseur"
    }
    
    results = {}
    
    for component, description in components.items():
        file_path = f"/app/backend/{component}"
        if os.path.exists(file_path):
            print(f"✅ {component}: {description} - PRÉSENT")
            results[component] = True
        else:
            print(f"❌ {component}: {description} - MANQUANT")
            results[component] = False
    
    return results

def test_frontend_components():
    """Test 4: FRONTEND COMPONENTS - Vérification des composants Phase 5"""
    print("\n🔍 TEST 4: FRONTEND COMPONENTS")
    
    components = {
        "frontend/src/components/AmazonMonitoringDashboard.js": "Dashboard principal",
        "frontend/src/pages/AmazonIntegrationPage.js": "Page d'intégration"
    }
    
    results = {}
    
    for component, description in components.items():
        file_path = f"/app/{component}"
        if os.path.exists(file_path):
            print(f"✅ {component}: {description} - PRÉSENT")
            results[component] = True
            
            # Vérification spéciale pour AmazonIntegrationPage.js
            if "AmazonIntegrationPage.js" in component:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'PHASE 5' in content and 'Monitoring' in content:
                            print(f"✅ Onglet 'Monitoring' avec badge 'PHASE 5' détecté")
                        else:
                            print(f"⚠️ Badge 'PHASE 5' ou onglet 'Monitoring' non détecté")
                except Exception as e:
                    print(f"⚠️ Erreur lecture {component}: {e}")
        else:
            print(f"❌ {component}: {description} - MANQUANT")
            results[component] = False
    
    return results

def test_imports_validation():
    """Test 5: VALIDATION IMPORTS PYTHON - Test des imports sans erreurs"""
    print("\n🔍 TEST 5: VALIDATION IMPORTS PYTHON")
    
    results = {}
    
    # Test d'import des modules Amazon monitoring
    modules_to_test = [
        ("backend.models.amazon_monitoring", "Modèles Amazon Monitoring"),
        ("backend.services.amazon_monitoring_service", "Service Amazon Monitoring"),
        ("backend.routes.amazon_monitoring_routes", "Routes Amazon Monitoring")
    ]
    
    for module_name, description in modules_to_test:
        try:
            # Changement du répertoire de travail pour les imports
            sys.path.insert(0, '/app')
            __import__(module_name)
            print(f"✅ {module_name}: {description} - IMPORT OK")
            results[module_name] = True
        except ImportError as e:
            print(f"❌ {module_name}: {description} - IMPORT FAILED: {e}")
            results[module_name] = False
        except Exception as e:
            print(f"⚠️ {module_name}: {description} - ERREUR: {e}")
            results[module_name] = False
    
    return results

def generate_summary(all_results):
    """Génération du résumé final"""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE VALIDATION PHASE 5 AMAZON MONITORING")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for test_name, results in all_results.items():
        print(f"\n🔍 {test_name.upper()}:")
        
        if isinstance(results, dict):
            for key, value in results.items():
                total_tests += 1
                if value == True or value == "OK":
                    print(f"  ✅ {key}")
                    passed_tests += 1
                else:
                    print(f"  ❌ {key}: {value}")
        else:
            total_tests += 1
            if results:
                print(f"  ✅ Test réussi")
                passed_tests += 1
            else:
                print(f"  ❌ Test échoué")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 TAUX DE RÉUSSITE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 PHASE 5 AMAZON MONITORING: OPÉRATIONNELLE")
        return True
    else:
        print("⚠️ PHASE 5 AMAZON MONITORING: PROBLÈMES DÉTECTÉS")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 VALIDATION POST-RÉINITIALISATION PHASE 5 AMAZON MONITORING")
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print("-" * 60)
    
    all_results = {}
    
    # Exécution des tests
    all_results["system_status"] = test_system_status()
    all_results["monitoring_endpoints"] = test_monitoring_endpoints()
    all_results["backend_components"] = test_backend_components()
    all_results["frontend_components"] = test_frontend_components()
    all_results["imports_validation"] = test_imports_validation()
    
    # Génération du résumé
    success = generate_summary(all_results)
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)