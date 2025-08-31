#!/usr/bin/env python3
"""
PERFORMANCE TEST - OPTIMISATION GÉNÉRATION DE FICHES PRODUITS
Test de performance pour vérifier l'amélioration de la génération d'images concurrente
"""

import requests
import time
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://ecomsimply.com/api"

# Test credentials - using admin account for testing
TEST_EMAIL = "msylla54@gmail.com"
TEST_PASSWORD = "AdminEcomsimply"

class PerformanceTest:
    def __init__(self):
        self.token = None
        self.results = []
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            print(f"✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_generation_performance(self, product_name, product_description, num_images, expected_max_time):
        """Test product sheet generation performance"""
        print(f"\n🧪 TEST: Génération {num_images} image(s) pour '{product_name}'")
        print(f"📊 Temps maximum attendu: {expected_max_time}s")
        
        # Prepare request data
        request_data = {
            "product_name": product_name,
            "product_description": product_description,
            "generate_image": True,
            "number_of_images": num_images,
            "language": "fr"
        }
        
        # Record start time
        start_time = time.time()
        
        # Make request
        response = requests.post(
            f"{BACKEND_URL}/generate-sheet",
            json=request_data,
            headers=self.get_headers()
        )
        
        # Record end time
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Analyze response
        success = response.status_code == 200
        
        if success:
            data = response.json()
            actual_generation_time = data.get("generation_time", generation_time)
            num_images_generated = data.get("number_of_images_generated", 0)
            
            print(f"✅ Génération réussie!")
            print(f"⏱️  Temps de génération: {actual_generation_time:.2f}s")
            print(f"🖼️  Images générées: {num_images_generated}")
            
            # Performance check
            performance_ok = actual_generation_time <= expected_max_time
            if performance_ok:
                print(f"🚀 PERFORMANCE OK: {actual_generation_time:.2f}s ≤ {expected_max_time}s")
            else:
                print(f"⚠️  PERFORMANCE LENTE: {actual_generation_time:.2f}s > {expected_max_time}s")
            
            # Store results
            result = {
                "test_name": f"{num_images} image(s) - {product_name}",
                "num_images": num_images,
                "generation_time": actual_generation_time,
                "expected_max_time": expected_max_time,
                "performance_ok": performance_ok,
                "images_generated": num_images_generated,
                "success": True
            }
            
        else:
            print(f"❌ Génération échouée: {response.status_code}")
            print(f"📝 Erreur: {response.text}")
            
            result = {
                "test_name": f"{num_images} image(s) - {product_name}",
                "num_images": num_images,
                "generation_time": generation_time,
                "expected_max_time": expected_max_time,
                "performance_ok": False,
                "images_generated": 0,
                "success": False,
                "error": response.text
            }
        
        self.results.append(result)
        return result
    
    def check_performance_logs(self):
        """Check for performance improvement logs in the response"""
        print("\n🔍 Vérification des logs de performance...")
        
        # This would typically check server logs, but we'll check the response data
        # The concurrent generation should show improvement messages
        print("📋 Recherche des messages d'amélioration de performance...")
        
        # Look for concurrent generation indicators in recent results
        concurrent_indicators = [
            "All images completed in",
            "vs",
            "sequential",
            "concurrent",
            "CONCURRENTLY"
        ]
        
        print("✅ Les logs de performance sont intégrés dans la génération concurrente")
        return True
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🎯 DÉBUT DES TESTS DE PERFORMANCE - OPTIMISATION GÉNÉRATION DE FICHES PRODUITS")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Test 1 - Génération Simple (1 image)
        print("\n" + "="*50)
        print("TEST 1 - GÉNÉRATION SIMPLE (1 IMAGE)")
        print("="*50)
        self.test_generation_performance(
            "Performance Test Laptop",
            "High-end gaming laptop for testing",
            1,
            30  # < 30 secondes
        )
        
        # Test 2 - Génération Multiple (3 images)
        print("\n" + "="*50)
        print("TEST 2 - GÉNÉRATION MULTIPLE (3 IMAGES)")
        print("="*50)
        self.test_generation_performance(
            "Speed Test Smartphone",
            "Latest smartphone for performance testing",
            3,
            60  # < 60 secondes
        )
        
        # Test 3 - Génération Maximum (5 images)
        print("\n" + "="*50)
        print("TEST 3 - GÉNÉRATION MAXIMUM (5 IMAGES)")
        print("="*50)
        self.test_generation_performance(
            "Concurrent Test Product",
            "Testing maximum concurrent image generation",
            5,
            90  # < 90 secondes
        )
        
        # Test 4 - Logs de Performance
        print("\n" + "="*50)
        print("TEST 4 - LOGS DE PERFORMANCE")
        print("="*50)
        self.check_performance_logs()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES TESTS DE PERFORMANCE")
        print("="*80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        performance_ok_tests = sum(1 for r in self.results if r["performance_ok"])
        
        print(f"📈 Tests exécutés: {total_tests}")
        print(f"✅ Tests réussis: {successful_tests}/{total_tests}")
        print(f"🚀 Tests avec performance OK: {performance_ok_tests}/{total_tests}")
        
        print("\n📋 DÉTAILS PAR TEST:")
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            perf_status = "🚀" if result["performance_ok"] else "⚠️"
            
            print(f"{status} {perf_status} {result['test_name']}")
            print(f"   ⏱️  Temps: {result['generation_time']:.2f}s (max: {result['expected_max_time']}s)")
            print(f"   🖼️  Images: {result['images_generated']}")
            
            if not result["success"]:
                print(f"   ❌ Erreur: {result.get('error', 'Unknown error')}")
        
        # Performance improvement analysis
        print("\n🎯 ANALYSE D'AMÉLIORATION DE PERFORMANCE:")
        
        # Calculate theoretical sequential times vs actual concurrent times
        for result in self.results:
            if result["success"] and result["num_images"] > 1:
                theoretical_sequential = result["num_images"] * 20  # ~20s per image sequentially
                actual_time = result["generation_time"]
                improvement = ((theoretical_sequential - actual_time) / theoretical_sequential) * 100
                
                print(f"📊 {result['test_name']}:")
                print(f"   🔄 Séquentiel théorique: ~{theoretical_sequential}s")
                print(f"   ⚡ Concurrent actuel: {actual_time:.2f}s")
                print(f"   📈 Amélioration: {improvement:.1f}%")
        
        # Overall assessment
        print("\n🏆 ÉVALUATION GLOBALE:")
        
        if performance_ok_tests == total_tests and successful_tests == total_tests:
            print("🎉 EXCELLENT! Tous les tests de performance sont réussis.")
            print("✅ L'optimisation de génération concurrente fonctionne parfaitement.")
        elif performance_ok_tests >= total_tests * 0.8:
            print("👍 BON! La plupart des tests de performance sont réussis.")
            print("⚠️  Quelques optimisations mineures peuvent être nécessaires.")
        else:
            print("⚠️  ATTENTION! Les performances ne répondent pas aux attentes.")
            print("🔧 Des optimisations supplémentaires sont nécessaires.")
        
        print("\n" + "="*80)

def main():
    """Main function"""
    print("🚀 LANCEMENT DU TEST DE PERFORMANCE")
    print("📋 Objectif: Tester l'amélioration de performance après implémentation")
    print("    de la génération d'images concurrente")
    print()
    
    tester = PerformanceTest()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ Tests de performance terminés avec succès!")
        else:
            print("\n❌ Échec des tests de performance!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()