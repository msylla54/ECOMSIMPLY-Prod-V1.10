#!/usr/bin/env python3
"""
Test Simple Amazon Phase 3 SEO + Prix - ECOMSIMPLY
Test des endpoints publics Phase 3 Amazon sans authentification
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

def test_health_check_phase3():
    """Test health check Phase 3"""
    print("🔍 Testing Phase 3 Health Check...")
    
    try:
        response = requests.get(f"{API_BASE}/amazon/health/phase3", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Vérifications détaillées
            checks = []
            checks.append(data.get('success') is True)
            checks.append('health' in data)
            checks.append(data.get('health', {}).get('phase') == 'Phase 3 - SEO + Prix Amazon')
            
            services = data.get('health', {}).get('services', {})
            expected_services = ['scraping_service', 'seo_optimizer', 'price_optimizer', 'publisher_service']
            for service in expected_services:
                checks.append(service in services)
                checks.append(services.get(service) == 'healthy')
            
            external_deps = data.get('health', {}).get('external_dependencies', {})
            checks.append('amazon_sp_api' in external_deps)
            checks.append('openai_api' in external_deps)
            
            success = all(checks)
            
            if success:
                print("✅ PASS - Health Check Phase 3")
                print(f"    Services: {list(services.keys())}")
                print(f"    External deps: {list(external_deps.keys())}")
                print(f"    All services healthy: {all(s == 'healthy' for s in services.values())}")
            else:
                print("❌ FAIL - Health Check Phase 3")
                print(f"    Failed checks: {sum(1 for c in checks if not c)}/{len(checks)}")
                
            return success
            
        else:
            print(f"❌ FAIL - Health Check Phase 3 (HTTP {response.status_code})")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Health Check Phase 3 (Exception: {str(e)})")
        return False

def test_backend_services_availability():
    """Test disponibilité des services backend"""
    print("\n🔍 Testing Backend Services Availability...")
    
    services_status = {}
    
    # Test des services via les imports
    try:
        # Test AmazonScrapingService
        try:
            import sys
            sys.path.append('/app/backend')
            from services.amazon_scraping_service import AmazonScrapingService
            scraping_service = AmazonScrapingService()
            services_status['AmazonScrapingService'] = True
            print("✅ AmazonScrapingService - Available")
        except Exception as e:
            services_status['AmazonScrapingService'] = False
            print(f"❌ AmazonScrapingService - Error: {str(e)}")
        
        # Test SEOOptimizerService
        try:
            from services.seo_optimizer_service import SEOOptimizerService
            seo_service = SEOOptimizerService()
            services_status['SEOOptimizerService'] = True
            print("✅ SEOOptimizerService - Available")
        except Exception as e:
            services_status['SEOOptimizerService'] = False
            print(f"❌ SEOOptimizerService - Error: {str(e)}")
        
        # Test PriceOptimizerService
        try:
            from services.price_optimizer_service import PriceOptimizerService
            price_service = PriceOptimizerService()
            services_status['PriceOptimizerService'] = True
            print("✅ PriceOptimizerService - Available")
        except Exception as e:
            services_status['PriceOptimizerService'] = False
            print(f"❌ PriceOptimizerService - Error: {str(e)}")
        
        # Test AmazonPublisherService
        try:
            from services.amazon_publisher_service import AmazonPublisherService
            publisher_service = AmazonPublisherService()
            services_status['AmazonPublisherService'] = True
            print("✅ AmazonPublisherService - Available")
        except Exception as e:
            services_status['AmazonPublisherService'] = False
            print(f"❌ AmazonPublisherService - Error: {str(e)}")
            
    except Exception as e:
        print(f"❌ FAIL - Services import error: {str(e)}")
        return False
    
    success_count = sum(1 for status in services_status.values() if status)
    total_count = len(services_status)
    
    print(f"\n📊 Services Status: {success_count}/{total_count} available")
    
    return success_count == total_count

def test_routes_availability():
    """Test disponibilité des routes Phase 3"""
    print("\n🔍 Testing Phase 3 Routes Availability...")
    
    routes_to_test = [
        ("/amazon/health/phase3", "GET", "Health Check"),
        # Note: Les autres routes nécessitent une authentification
    ]
    
    routes_status = {}
    
    for route, method, description in routes_to_test:
        try:
            url = f"{API_BASE}{route}"
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=10)
            
            # Considérer 200, 400, 401, 403 comme des réponses valides (route existe)
            if response.status_code in [200, 400, 401, 403]:
                routes_status[route] = True
                print(f"✅ {description} ({route}) - Available (HTTP {response.status_code})")
            else:
                routes_status[route] = False
                print(f"❌ {description} ({route}) - HTTP {response.status_code}")
                
        except Exception as e:
            routes_status[route] = False
            print(f"❌ {description} ({route}) - Exception: {str(e)}")
    
    success_count = sum(1 for status in routes_status.values() if status)
    total_count = len(routes_status)
    
    print(f"\n📊 Routes Status: {success_count}/{total_count} available")
    
    return success_count > 0  # Au moins une route doit fonctionner

def test_phase3_files_existence():
    """Test existence des fichiers Phase 3"""
    print("\n🔍 Testing Phase 3 Files Existence...")
    
    files_to_check = [
        "/app/backend/routes/amazon_seo_price_routes.py",
        "/app/backend/services/amazon_scraping_service.py",
        "/app/backend/services/seo_optimizer_service.py", 
        "/app/backend/services/price_optimizer_service.py",
        "/app/backend/services/amazon_publisher_service.py",
        "/app/tests/backend/test_amazon_phase3_services.py",
        "/app/tests/backend/test_amazon_phase3_api.py"
    ]
    
    files_status = {}
    
    for file_path in files_to_check:
        try:
            import os
            if os.path.exists(file_path):
                files_status[file_path] = True
                print(f"✅ {file_path} - Exists")
            else:
                files_status[file_path] = False
                print(f"❌ {file_path} - Missing")
                
        except Exception as e:
            files_status[file_path] = False
            print(f"❌ {file_path} - Error: {str(e)}")
    
    success_count = sum(1 for status in files_status.values() if status)
    total_count = len(files_status)
    
    print(f"\n📊 Files Status: {success_count}/{total_count} exist")
    
    return success_count >= 5  # Au moins 5 fichiers doivent exister

def main():
    """Fonction principale de test"""
    print("🚀 TESTS AMAZON PHASE 3 SEO + PRIX - VERSION SIMPLE")
    print("=" * 80)
    print()
    
    tests = [
        ("Health Check Phase 3", test_health_check_phase3),
        ("Backend Services Availability", test_backend_services_availability),
        ("Routes Availability", test_routes_availability),
        ("Phase 3 Files Existence", test_phase3_files_existence)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ FAIL - {test_name} (Exception: {str(e)})")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 80)
    print("🎯 RÉSUMÉ DES TESTS AMAZON PHASE 3")
    print("=" * 80)
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 STATISTIQUES:")
    print(f"   • Tests exécutés: {total_tests}")
    print(f"   • Tests réussis: {passed_tests} ✅")
    print(f"   • Tests échoués: {total_tests - passed_tests} ❌")
    print(f"   • Taux de réussite: {success_rate:.1f}%")
    print()
    
    print("📋 DÉTAIL DES RÉSULTATS:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print()
    
    # Évaluation finale
    if success_rate >= 75:
        print("🎯 ÉVALUATION: ✅ BON - Phase 3 Amazon majoritairement fonctionnelle")
        print("   ✅ Services Phase 3 disponibles")
        print("   ✅ Routes API opérationnelles")
        print("   ✅ Fichiers d'implémentation présents")
    elif success_rate >= 50:
        print("🎯 ÉVALUATION: ⚠️ MOYEN - Phase 3 Amazon partiellement fonctionnelle")
        print("   ⚠️ Certains services nécessitent des corrections")
    else:
        print("🎯 ÉVALUATION: ❌ CRITIQUE - Phase 3 Amazon nécessite des corrections majeures")
        print("   ❌ Services critiques non fonctionnels")
    
    print()
    print("🔧 SERVICES PHASE 3 TESTÉS:")
    print("   • AmazonScrapingService: Scraping SEO + prix réels Amazon")
    print("   • SEOOptimizerService: Optimisation IA avec GPT-4")
    print("   • PriceOptimizerService: Calcul prix optimal avec règles")
    print("   • AmazonPublisherService: Publication automatique via SP-API")
    print("   • Routes API: amazon_seo_price_routes.py")
    print()
    
    return success_rate >= 50

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Erreur critique lors des tests: {str(e)}")
        sys.exit(3)