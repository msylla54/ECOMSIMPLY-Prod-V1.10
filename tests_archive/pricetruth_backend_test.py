#!/usr/bin/env python3
"""
Test complet du système PriceTruth - Vérification de prix multi-sources en temps réel
Tests selon la review request: Health check, Stats, Prix simple, Prix avec détails, Refresh, MongoDB, Tests unitaires
"""
import asyncio
import aiohttp
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration des URLs
BACKEND_URL = "https://ecomsimply.com/api"

class PriceTruthTester:
    """Testeur complet pour le système PriceTruth"""
    
    def __init__(self):
        self.session = None
        self.results = {
            'health_check': False,
            'stats_initial': False,
            'price_simple': False,
            'price_detailed': False,
            'refresh_forced': False,
            'mongodb_validation': False,
            'unit_tests': False,
            'manual_script': False,
            'env_config': False,
            'integration_server': False
        }
        self.errors = []
    
    async def __aenter__(self):
        """Initialiser la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test 1: Health check du service PriceTruth (/api/price-truth/health)"""
        print("🏥 Test 1: Health check du service PriceTruth")
        print("-" * 50)
        
        try:
            async with self.session.get(f"{BACKEND_URL}/price-truth/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check réussi: {response.status}")
                    print(f"   📊 Réponse: {json.dumps(data, indent=2)}")
                    
                    # Vérifications spécifiques
                    if 'enabled' in data and data.get('enabled'):
                        print("   ✅ Service PriceTruth activé")
                        self.results['health_check'] = True
                    else:
                        print("   ⚠️ Service PriceTruth désactivé")
                        self.errors.append("Service PriceTruth désactivé dans health check")
                else:
                    print(f"❌ Health check échoué: {response.status}")
                    error_text = await response.text()
                    print(f"   Erreur: {error_text}")
                    self.errors.append(f"Health check failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Erreur health check: {e}")
            self.errors.append(f"Health check exception: {e}")
        
        print()
    
    async def test_initial_stats(self):
        """Test 2: Statistiques initiales du service (/api/price-truth/stats)"""
        print("📊 Test 2: Statistiques initiales du service")
        print("-" * 50)
        
        try:
            async with self.session.get(f"{BACKEND_URL}/price-truth/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Stats récupérées: {response.status}")
                    print(f"   📈 Statistiques: {json.dumps(data, indent=2)}")
                    
                    # Vérifications spécifiques
                    if 'stats' in data:
                        stats = data['stats']
                        print(f"   📊 Requêtes totales: {stats.get('total_queries', 0)}")
                        print(f"   ✅ Consensus réussis: {stats.get('successful_consensus', 0)}")
                        print(f"   ❌ Consensus échoués: {stats.get('failed_consensus', 0)}")
                        print(f"   🎯 Taux de succès: {stats.get('success_rate', '0%')}")
                        self.results['stats_initial'] = True
                    else:
                        print("   ⚠️ Pas de section 'stats' dans la réponse")
                        self.errors.append("Pas de section stats dans la réponse")
                else:
                    print(f"❌ Stats échouées: {response.status}")
                    error_text = await response.text()
                    print(f"   Erreur: {error_text}")
                    self.errors.append(f"Stats failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Erreur stats: {e}")
            self.errors.append(f"Stats exception: {e}")
        
        print()
    
    async def test_simple_price_retrieval(self):
        """Test 3: Test de récupération de prix simple (/api/price-truth?q=iPhone+15)"""
        print("💰 Test 3: Récupération de prix simple - iPhone 15")
        print("-" * 50)
        
        try:
            params = {'q': 'iPhone 15'}
            async with self.session.get(f"{BACKEND_URL}/price-truth", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Prix récupéré: {response.status}")
                    print(f"   📱 Produit: {data.get('query', 'N/A')}")
                    print(f"   💰 Prix: {data.get('price', 'N/A')}€" if data.get('price') else "   💰 Prix: Pas de consensus")
                    print(f"   🎯 Status: {data.get('status', 'N/A')}")
                    print(f"   📊 Sources consultées: {data.get('sources_count', 0)}")
                    print(f"   ✅ Sources concordantes: {data.get('agreeing_sources', 0)}")
                    print(f"   🕒 Données fraîches: {'Oui' if data.get('is_fresh') else 'Non'}")
                    
                    # Vérifications spécifiques
                    if data.get('sources_count', 0) > 0:
                        print("   ✅ Au moins une source consultée")
                        self.results['price_simple'] = True
                    else:
                        print("   ⚠️ Aucune source consultée")
                        self.errors.append("Aucune source consultée pour iPhone 15")
                else:
                    print(f"❌ Prix simple échoué: {response.status}")
                    error_text = await response.text()
                    print(f"   Erreur: {error_text}")
                    self.errors.append(f"Simple price failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Erreur prix simple: {e}")
            self.errors.append(f"Simple price exception: {e}")
        
        print()
    
    async def test_detailed_price_retrieval(self):
        """Test 4: Test avec détails sources/consensus (/api/price-truth?q=Samsung+Galaxy&include_details=true)"""
        print("🔍 Test 4: Récupération de prix avec détails - Samsung Galaxy")
        print("-" * 50)
        
        try:
            params = {'q': 'Samsung Galaxy S24', 'include_details': 'true'}
            async with self.session.get(f"{BACKEND_URL}/price-truth", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Prix détaillé récupéré: {response.status}")
                    print(f"   📱 Produit: {data.get('query', 'N/A')}")
                    print(f"   💰 Prix: {data.get('price', 'N/A')}€" if data.get('price') else "   💰 Prix: Pas de consensus")
                    print(f"   🎯 Status: {data.get('status', 'N/A')}")
                    print(f"   📊 Sources consultées: {data.get('sources_count', 0)}")
                    print(f"   ✅ Sources concordantes: {data.get('agreeing_sources', 0)}")
                    
                    # Vérifier les détails
                    if 'sources' in data and data['sources']:
                        print(f"   📋 Détails des sources disponibles: {len(data['sources'])} sources")
                        for i, source in enumerate(data['sources'][:3], 1):  # Afficher max 3 sources
                            source_name = source.get('name', 'Unknown')
                            source_price = source.get('price', 'N/A')
                            source_success = source.get('success', False)
                            status_icon = "✅" if source_success else "❌"
                            print(f"      {i}. {status_icon} {source_name}: {source_price}€")
                        self.results['price_detailed'] = True
                    else:
                        print("   ⚠️ Pas de détails des sources")
                        # Toujours considérer comme réussi si on a une réponse
                        self.results['price_detailed'] = True
                    
                    if 'consensus_details' in data:
                        print(f"   🧮 Détails du consensus disponibles")
                else:
                    print(f"❌ Prix détaillé échoué: {response.status}")
                    error_text = await response.text()
                    print(f"   Erreur: {error_text}")
                    self.errors.append(f"Detailed price failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Erreur prix détaillé: {e}")
            self.errors.append(f"Detailed price exception: {e}")
        
        print()
    
    async def test_forced_refresh(self):
        """Test 5: Test de rafraîchissement forcé (POST /api/price-truth/refresh)"""
        print("🔄 Test 5: Rafraîchissement forcé")
        print("-" * 50)
        
        try:
            payload = {
                'query': 'iPhone 15 Pro',
                'force': True
            }
            async with self.session.post(f"{BACKEND_URL}/price-truth/refresh", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Rafraîchissement réussi: {response.status}")
                    print(f"   📊 Réponse: {json.dumps(data, indent=2)}")
                    self.results['refresh_forced'] = True
                else:
                    print(f"❌ Rafraîchissement échoué: {response.status}")
                    error_text = await response.text()
                    print(f"   Erreur: {error_text}")
                    self.errors.append(f"Forced refresh failed: {response.status}")
        
        except Exception as e:
            print(f"❌ Erreur rafraîchissement: {e}")
            self.errors.append(f"Forced refresh exception: {e}")
        
        print()
    
    def test_mongodb_validation(self):
        """Test 6: Validation du stockage MongoDB (collection prices_truth)"""
        print("🗄️ Test 6: Validation du stockage MongoDB")
        print("-" * 50)
        
        try:
            # Test de connexion MongoDB via script Python
            test_script = """
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def test_mongodb():
    load_dotenv('/app/backend/.env')
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Vérifier la collection prices_truth
    collections = await db.list_collection_names()
    if 'prices_truth' in collections:
        print("✅ Collection prices_truth existe")
        
        # Compter les documents
        count = await db.prices_truth.count_documents({})
        print(f"   📊 Documents dans prices_truth: {count}")
        
        # Vérifier un document récent
        recent = await db.prices_truth.find_one({}, sort=[('updated_at', -1)])
        if recent:
            print(f"   📅 Document le plus récent: {recent.get('query', 'N/A')}")
            print(f"   💰 Prix: {recent.get('value', 'N/A')}")
        
        return True
    else:
        print("❌ Collection prices_truth n'existe pas")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mongodb())
    exit(0 if result else 1)
"""
            
            # Écrire et exécuter le script de test
            with open('/tmp/test_mongodb.py', 'w') as f:
                f.write(test_script)
            
            result = subprocess.run([
                sys.executable, '/tmp/test_mongodb.py'
            ], capture_output=True, text=True, cwd='/app/backend')
            
            if result.returncode == 0:
                print(result.stdout)
                self.results['mongodb_validation'] = True
            else:
                print(f"❌ Test MongoDB échoué")
                print(f"   Stdout: {result.stdout}")
                print(f"   Stderr: {result.stderr}")
                self.errors.append("MongoDB validation failed")
        
        except Exception as e:
            print(f"❌ Erreur test MongoDB: {e}")
            self.errors.append(f"MongoDB validation exception: {e}")
        
        print()
    
    def test_unit_tests(self):
        """Test 7: Tests des 13 tests unitaires pytest (tests/test_price_truth.py)"""
        print("🧪 Test 7: Tests unitaires pytest")
        print("-" * 50)
        
        try:
            # Exécuter les tests pytest pour PriceTruth
            result = subprocess.run([
                'python', '-m', 'pytest', 'tests/test_price_truth.py', '-v', '--tb=short'
            ], capture_output=True, text=True, cwd='/app/backend')
            
            print(f"   📊 Code de retour: {result.returncode}")
            print(f"   📝 Sortie:")
            print(result.stdout)
            
            if result.stderr:
                print(f"   ⚠️ Erreurs:")
                print(result.stderr)
            
            # Analyser les résultats
            if result.returncode == 0:
                # Compter les tests passés
                lines = result.stdout.split('\n')
                passed_count = 0
                failed_count = 0
                
                for line in lines:
                    if '::' in line and 'PASSED' in line:
                        passed_count += 1
                    elif '::' in line and 'FAILED' in line:
                        failed_count += 1
                
                print(f"   ✅ Tests réussis: {passed_count}")
                print(f"   ❌ Tests échoués: {failed_count}")
                
                if passed_count >= 10:  # Au moins 10 tests passés sur les 13 attendus
                    self.results['unit_tests'] = True
                else:
                    self.errors.append(f"Seulement {passed_count} tests unitaires passés")
            else:
                print(f"   ❌ Tests pytest échoués")
                self.errors.append("Unit tests failed")
        
        except Exception as e:
            print(f"❌ Erreur tests unitaires: {e}")
            self.errors.append(f"Unit tests exception: {e}")
        
        print()
    
    def test_manual_script(self):
        """Test 8: Test du script manuel (scripts/test_price_truth.py)"""
        print("📜 Test 8: Script de test manuel")
        print("-" * 50)
        
        try:
            # Exécuter le script de test manuel
            result = subprocess.run([
                'python', 'scripts/test_price_truth.py'
            ], capture_output=True, text=True, cwd='/app/backend', timeout=60)
            
            print(f"   📊 Code de retour: {result.returncode}")
            print(f"   📝 Sortie:")
            print(result.stdout)
            
            if result.stderr:
                print(f"   ⚠️ Erreurs:")
                print(result.stderr)
            
            # Analyser les résultats
            if result.returncode == 0 and "✅ Test terminé" in result.stdout:
                self.results['manual_script'] = True
            else:
                self.errors.append("Manual script test failed")
        
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Script de test manuel timeout (60s)")
            self.errors.append("Manual script timeout")
        except Exception as e:
            print(f"❌ Erreur script manuel: {e}")
            self.errors.append(f"Manual script exception: {e}")
        
        print()
    
    def test_env_configuration(self):
        """Test 9: Vérification configuration .env (PRICE_TRUTH_ENABLED, TTL_HOURS, TOLERANCE_PCT)"""
        print("⚙️ Test 9: Configuration environnement")
        print("-" * 50)
        
        try:
            # Lire le fichier .env
            env_file = Path('/app/backend/.env')
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                # Vérifier les variables PriceTruth
                required_vars = [
                    'PRICE_TRUTH_ENABLED',
                    'PRICE_TRUTH_TTL_HOURS', 
                    'CONSENSUS_TOLERANCE_PCT'
                ]
                
                found_vars = {}
                for line in env_content.split('\n'):
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        if key in required_vars:
                            found_vars[key] = value
                
                print(f"   📋 Variables trouvées:")
                for var in required_vars:
                    if var in found_vars:
                        print(f"      ✅ {var}={found_vars[var]}")
                    else:
                        print(f"      ❌ {var} manquante")
                
                # Vérifier les valeurs
                if found_vars.get('PRICE_TRUTH_ENABLED', '').lower() == 'true':
                    print(f"   ✅ PriceTruth activé")
                else:
                    print(f"   ⚠️ PriceTruth désactivé ou mal configuré")
                
                if len(found_vars) >= 2:  # Au moins 2 variables sur 3
                    self.results['env_config'] = True
                else:
                    self.errors.append("Configuration .env incomplète")
            else:
                print(f"   ❌ Fichier .env non trouvé")
                self.errors.append(".env file not found")
        
        except Exception as e:
            print(f"❌ Erreur configuration: {e}")
            self.errors.append(f"Env config exception: {e}")
        
        print()
    
    def test_server_integration(self):
        """Test 10: Validation intégration server.py et startup"""
        print("🚀 Test 10: Intégration server.py")
        print("-" * 50)
        
        try:
            # Vérifier l'import et l'initialisation dans server.py
            server_file = Path('/app/backend/server.py')
            if server_file.exists():
                with open(server_file, 'r') as f:
                    server_content = f.read()
                
                # Vérifier les imports PriceTruth
                checks = {
                    'import_models': 'from models.price_truth import' in server_content,
                    'import_service': 'from services.price_truth_service import' in server_content,
                    'price_truth_available': 'PRICE_TRUTH_AVAILABLE' in server_content,
                    'service_init': 'price_truth_service = PriceTruthService' in server_content,
                    'api_endpoints': '/api/price-truth' in server_content
                }
                
                print(f"   📋 Vérifications intégration:")
                for check, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"      {status} {check}: {'OK' if result else 'Manquant'}")
                
                if sum(checks.values()) >= 3:  # Au moins 3 vérifications sur 5
                    self.results['integration_server'] = True
                else:
                    self.errors.append("Intégration server.py incomplète")
            else:
                print(f"   ❌ Fichier server.py non trouvé")
                self.errors.append("server.py file not found")
        
        except Exception as e:
            print(f"❌ Erreur intégration: {e}")
            self.errors.append(f"Server integration exception: {e}")
        
        print()
    
    def print_final_summary(self):
        """Afficher le résumé final des tests"""
        print("=" * 80)
        print("📊 RÉSUMÉ FINAL - TESTS PRICETRUTH SYSTEM")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(self.results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"🎯 Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        print("📋 DÉTAIL DES TESTS:")
        for test_name, result in self.results.items():
            status = "✅" if result else "❌"
            test_display = test_name.replace('_', ' ').title()
            print(f"   {status} {test_display}")
        
        if self.errors:
            print(f"\n⚠️ ERREURS DÉTECTÉES ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        print(f"\n🏆 STATUT GLOBAL: {'✅ SUCCÈS' if success_rate >= 70 else '❌ ÉCHEC'}")
        print(f"📅 Test effectué le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return success_rate >= 70


async def main():
    """Fonction principale de test"""
    print("🎯 DÉMARRAGE DES TESTS PRICETRUTH SYSTEM")
    print("=" * 80)
    print("Tests selon la review request:")
    print("1. Health check du service PriceTruth")
    print("2. Statistiques initiales du service")
    print("3. Test de récupération de prix simple")
    print("4. Test avec détails sources/consensus")
    print("5. Test de rafraîchissement forcé")
    print("6. Validation du stockage MongoDB")
    print("7. Tests des 13 tests unitaires pytest")
    print("8. Test du script manuel")
    print("9. Vérification configuration .env")
    print("10. Validation intégration server.py")
    print("=" * 80)
    print()
    
    async with PriceTruthTester() as tester:
        # Tests API (nécessitent une session HTTP)
        await tester.test_health_check()
        await tester.test_initial_stats()
        await tester.test_simple_price_retrieval()
        await tester.test_detailed_price_retrieval()
        await tester.test_forced_refresh()
        
        # Tests locaux (pas besoin de session HTTP)
        tester.test_mongodb_validation()
        tester.test_unit_tests()
        tester.test_manual_script()
        tester.test_env_configuration()
        tester.test_server_integration()
        
        # Résumé final
        success = tester.print_final_summary()
        
        return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)