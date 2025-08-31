#!/usr/bin/env python3
"""
Test complet de l'implémentation Shopify Phase 1 - OAuth & Connexions
OBJECTIF: Valider l'implémentation complète de la Phase 1 Shopify avec tests réels des modules créés.

MODULES À TESTER:
1. `/app/backend/marketplaces/shopify/oauth.py` - Service OAuth Shopify
2. `/app/backend/marketplaces/shopify/client.py` - Client API Shopify 
3. `/app/backend/models/shopify_connections.py` - Modèles de données
4. `/app/backend/routes/shopify_routes.py` - Routes API
5. `/app/tests/backend/test_shopify_phase1.py` - Tests unitaires

TESTS À EFFECTUER:
1. **Vérification des imports et availability des modules Shopify**
2. **Test OAuth Service**: Initialisation, génération state, validation domaines, chiffrement tokens
3. **Test Client Shopify**: Initialisation, configuration endpoints, retry logic
4. **Test Models**: Validation ShopifyConnection, scopes, domaines, statuts
5. **Test Routes**: Endpoints /api/shopify/install, /callback, /status, /disconnect, /health
6. **Test Intégration**: Exécution du fichier test_shopify_phase1.py
7. **Vérification Server.py**: Import et enregistrement des routes Shopify

CRITÈRES DE SUCCÈS:
- Tous les modules Shopify importables sans erreur
- Service OAuth fonctionnel avec chiffrement AES-GCM
- Modèles Pydantic validant correctement les données
- Routes API accessibles et sécurisées (401 si non auth)
- Tests unitaires passant à ≥80%
- Integration dans server.py confirmée
"""

import os
import sys
import asyncio
import json
import time
import traceback
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration des URLs pour les tests
BACKEND_URL = "http://localhost:8001"
API_BASE_URL = f"{BACKEND_URL}/api"

class ShopifyPhase1BackendTester:
    """Testeur complet pour Shopify Phase 1 Backend"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'critical_issues': [],
            'success_rate': 0.0
        }
        self.start_time = time.time()
        
    def log_test(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log un résultat de test"""
        self.results['total_tests'] += 1
        
        if status == "PASS":
            self.results['passed_tests'] += 1
            print(f"✅ {test_name}: {details}")
        else:
            self.results['failed_tests'] += 1
            print(f"❌ {test_name}: {error}")
            if "CRITICAL" in test_name.upper():
                self.results['critical_issues'].append(f"{test_name}: {error}")
        
        self.results['test_details'].append({
            'test': test_name,
            'status': status,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_1_module_imports_availability(self):
        """Test 1: Vérification des imports et availability des modules Shopify"""
        print("\n🧪 TEST 1: VÉRIFICATION DES IMPORTS ET AVAILABILITY DES MODULES SHOPIFY")
        print("=" * 80)
        
        # Test 1.1: Import OAuth Service
        try:
            sys.path.append('/app/backend')
            from marketplaces.shopify.oauth import ShopifyOAuthService
            self.log_test("1.1 Import OAuth Service", "PASS", "ShopifyOAuthService importé avec succès")
        except ImportError as e:
            self.log_test("1.1 Import OAuth Service", "FAIL", error=f"Import failed: {str(e)}")
            return False
        
        # Test 1.2: Import Client API
        try:
            from marketplaces.shopify.client import ShopifyAPIClient
            self.log_test("1.2 Import Client API", "PASS", "ShopifyAPIClient importé avec succès")
        except ImportError as e:
            self.log_test("1.2 Import Client API", "FAIL", error=f"Import failed: {str(e)}")
            return False
        
        # Test 1.3: Import Models
        try:
            from models.shopify_connections import (
                ShopifyConnection, ShopifyConnectionRequest, ShopifyConnectionResponse,
                ConnectionStatus, ShopifyPlan, ShopifyTokenData
            )
            self.log_test("1.3 Import Models", "PASS", "Tous les modèles Shopify importés avec succès")
        except ImportError as e:
            self.log_test("1.3 Import Models", "FAIL", error=f"Import failed: {str(e)}")
            return False
        
        # Test 1.4: Import Routes
        try:
            from routes.shopify_routes import shopify_router
            self.log_test("1.4 Import Routes", "PASS", "shopify_router importé avec succès")
        except ImportError as e:
            self.log_test("1.4 Import Routes", "FAIL", error=f"Import failed: {str(e)}")
            return False
        
        # Test 1.5: Vérification fichier de tests unitaires
        test_file_path = "/app/tests/backend/test_shopify_phase1.py"
        if os.path.exists(test_file_path):
            self.log_test("1.5 Tests unitaires disponibles", "PASS", f"Fichier trouvé: {test_file_path}")
        else:
            self.log_test("1.5 Tests unitaires disponibles", "FAIL", error=f"Fichier non trouvé: {test_file_path}")
        
        return True
    
    def test_2_oauth_service_functionality(self):
        """Test 2: Test OAuth Service - Initialisation, génération state, validation domaines, chiffrement tokens"""
        print("\n🧪 TEST 2: OAUTH SERVICE FUNCTIONALITY")
        print("=" * 80)
        
        try:
            sys.path.append('/app/backend')
            from marketplaces.shopify.oauth import ShopifyOAuthService
            
            # Configuration mock pour les tests
            os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id_12345'
            os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_client_secret_67890'
            os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_encryption_key_1234567890123456789012345678901234567890'
            
            # Test 2.1: Initialisation du service
            try:
                oauth_service = ShopifyOAuthService()
                self.log_test("2.1 OAuth Service Initialization", "PASS", 
                            f"Service initialisé avec client_id: {oauth_service.client_id[:10]}***")
            except Exception as e:
                self.log_test("2.1 OAuth Service Initialization", "FAIL", error=str(e))
                return False
            
            # Test 2.2: Génération de state OAuth sécurisé
            try:
                install_data = oauth_service.generate_install_url(
                    shop_domain="testshop.myshopify.com",
                    user_id="test_user_123"
                )
                
                state = install_data['state']
                if len(state) > 30 and 'install_url' in install_data:
                    self.log_test("2.2 OAuth State Generation", "PASS", 
                                f"State généré: {len(state)} caractères, URL: {install_data['install_url'][:50]}...")
                else:
                    self.log_test("2.2 OAuth State Generation", "FAIL", 
                                error=f"State trop court ({len(state)}) ou URL manquante")
            except Exception as e:
                self.log_test("2.2 OAuth State Generation", "FAIL", error=str(e))
            
            # Test 2.3: Validation des domaines
            try:
                test_domains = [
                    ("testshop", "testshop.myshopify.com"),
                    ("test-shop.myshopify.com", "test-shop.myshopify.com"),
                    ("https://myshop.myshopify.com", "myshop.myshopify.com")
                ]
                
                all_valid = True
                for input_domain, expected in test_domains:
                    result = oauth_service._validate_shop_domain(input_domain)
                    if result != expected:
                        all_valid = False
                        break
                
                if all_valid:
                    self.log_test("2.3 Domain Validation", "PASS", 
                                f"Validation réussie pour {len(test_domains)} domaines")
                else:
                    self.log_test("2.3 Domain Validation", "FAIL", 
                                error="Validation échouée pour certains domaines")
            except Exception as e:
                self.log_test("2.3 Domain Validation", "FAIL", error=str(e))
            
            # Test 2.4: Chiffrement des tokens AES-GCM
            try:
                test_token = "shpat_test_access_token_12345678901234567890"
                user_id = "test_user_123"
                
                # Chiffrer
                encrypted_data = oauth_service.encrypt_access_token(test_token, user_id)
                
                # Vérifier la structure
                required_fields = ['encrypted_token', 'nonce', 'encryption_method']
                if all(field in encrypted_data for field in required_fields):
                    # Déchiffrer pour vérifier
                    decrypted = oauth_service.decrypt_access_token(encrypted_data, user_id)
                    if decrypted == test_token:
                        self.log_test("2.4 Token Encryption AES-GCM", "PASS", 
                                    f"Chiffrement/déchiffrement réussi, méthode: {encrypted_data['encryption_method']}")
                    else:
                        self.log_test("2.4 Token Encryption AES-GCM", "FAIL", 
                                    error="Déchiffrement incorrect")
                else:
                    self.log_test("2.4 Token Encryption AES-GCM", "FAIL", 
                                error=f"Champs manquants: {required_fields}")
            except Exception as e:
                self.log_test("2.4 Token Encryption AES-GCM", "FAIL", error=str(e))
            
            return True
            
        except Exception as e:
            self.log_test("2.0 OAuth Service Setup", "FAIL", error=str(e))
            return False
    
    def test_3_shopify_client_functionality(self):
        """Test 3: Test Client Shopify - Initialisation, configuration endpoints, retry logic"""
        print("\n🧪 TEST 3: SHOPIFY CLIENT FUNCTIONALITY")
        print("=" * 80)
        
        try:
            sys.path.append('/app/backend')
            from marketplaces.shopify.client import ShopifyAPIClient
            
            # Test 3.1: Initialisation du client
            try:
                shop_domain = "testshop.myshopify.com"
                access_token = "shpat_test_token_12345"
                
                client = ShopifyAPIClient(shop_domain, access_token)
                
                expected_rest_url = f"https://{shop_domain}/admin/api/2024-01"
                expected_graphql_url = f"https://{shop_domain}/admin/api/2024-01/graphql.json"
                
                if (client.shop_domain == shop_domain and 
                    client.access_token == access_token and
                    client.rest_base_url == expected_rest_url and
                    client.graphql_url == expected_graphql_url):
                    self.log_test("3.1 Client Initialization", "PASS", 
                                f"Client initialisé pour {shop_domain}, REST: {expected_rest_url}")
                else:
                    self.log_test("3.1 Client Initialization", "FAIL", 
                                error="Configuration des URLs incorrecte")
            except Exception as e:
                self.log_test("3.1 Client Initialization", "FAIL", error=str(e))
                return False
            
            # Test 3.2: Configuration des endpoints
            try:
                if (hasattr(client, 'rest_base_url') and 
                    hasattr(client, 'graphql_url') and
                    hasattr(client, 'max_retries') and
                    hasattr(client, 'base_delay')):
                    self.log_test("3.2 Endpoints Configuration", "PASS", 
                                f"Endpoints configurés, max_retries: {client.max_retries}")
                else:
                    self.log_test("3.2 Endpoints Configuration", "FAIL", 
                                error="Attributs de configuration manquants")
            except Exception as e:
                self.log_test("3.2 Endpoints Configuration", "FAIL", error=str(e))
            
            # Test 3.3: Retry logic configuration
            try:
                if (client.max_retries >= 3 and 
                    client.base_delay > 0 and
                    client.backoff_factor >= 2.0):
                    self.log_test("3.3 Retry Logic Configuration", "PASS", 
                                f"Retry configuré: {client.max_retries} tentatives, délai base: {client.base_delay}s")
                else:
                    self.log_test("3.3 Retry Logic Configuration", "FAIL", 
                                error="Configuration retry insuffisante")
            except Exception as e:
                self.log_test("3.3 Retry Logic Configuration", "FAIL", error=str(e))
            
            # Test 3.4: Méthodes utilitaires disponibles
            try:
                required_methods = [
                    'make_rest_request', 'make_graphql_request', 'get_shop_info',
                    'get_products', 'create_product', 'health_check'
                ]
                
                missing_methods = []
                for method in required_methods:
                    if not hasattr(client, method):
                        missing_methods.append(method)
                
                if not missing_methods:
                    self.log_test("3.4 Utility Methods Available", "PASS", 
                                f"Toutes les méthodes disponibles: {', '.join(required_methods)}")
                else:
                    self.log_test("3.4 Utility Methods Available", "FAIL", 
                                error=f"Méthodes manquantes: {', '.join(missing_methods)}")
            except Exception as e:
                self.log_test("3.4 Utility Methods Available", "FAIL", error=str(e))
            
            return True
            
        except Exception as e:
            self.log_test("3.0 Client Setup", "FAIL", error=str(e))
            return False
    
    def test_4_models_validation(self):
        """Test 4: Test Models - Validation ShopifyConnection, scopes, domaines, statuts"""
        print("\n🧪 TEST 4: MODELS VALIDATION")
        print("=" * 80)
        
        try:
            sys.path.append('/app/backend')
            from models.shopify_connections import (
                ShopifyConnection, ShopifyConnectionRequest, ConnectionStatus, ShopifyPlan
            )
            
            # Test 4.1: Validation ShopifyConnection avec données valides
            try:
                valid_connection = ShopifyConnection(
                    user_id="test_user_123",
                    shop_domain="testshop.myshopify.com",
                    shop_name="Test Shop",
                    encrypted_access_token="encrypted_token_data_12345",
                    token_encryption_nonce="nonce_data_67890",
                    scopes="read_products,write_products,read_orders",
                    status=ConnectionStatus.ACTIVE
                )
                
                if (valid_connection.user_id == "test_user_123" and
                    valid_connection.status == ConnectionStatus.ACTIVE and
                    valid_connection.shop_domain == "testshop.myshopify.com"):
                    self.log_test("4.1 ShopifyConnection Valid Data", "PASS", 
                                f"Connexion créée: {valid_connection.shop_name}, statut: {valid_connection.status}")
                else:
                    self.log_test("4.1 ShopifyConnection Valid Data", "FAIL", 
                                error="Données de connexion incorrectes")
            except Exception as e:
                self.log_test("4.1 ShopifyConnection Valid Data", "FAIL", error=str(e))
            
            # Test 4.2: Validation des scopes
            try:
                valid_scopes = [
                    "read_products,write_products",
                    "read_orders,write_orders,read_customers",
                    "read_inventory,write_inventory"
                ]
                
                scopes_valid = True
                for scopes in valid_scopes:
                    try:
                        connection = ShopifyConnection(
                            user_id="test_user",
                            shop_domain="testshop.myshopify.com",
                            shop_name="Test Shop",
                            encrypted_access_token="token",
                            token_encryption_nonce="nonce",
                            scopes=scopes
                        )
                    except Exception:
                        scopes_valid = False
                        break
                
                if scopes_valid:
                    self.log_test("4.2 Scopes Validation", "PASS", 
                                f"Validation réussie pour {len(valid_scopes)} combinaisons de scopes")
                else:
                    self.log_test("4.2 Scopes Validation", "FAIL", 
                                error="Validation échouée pour certains scopes")
            except Exception as e:
                self.log_test("4.2 Scopes Validation", "FAIL", error=str(e))
            
            # Test 4.3: Validation des domaines (rejet des invalides)
            try:
                invalid_domains = ["", "invalid_domain", "toolong" * 50]
                domain_validation_working = True
                
                for invalid_domain in invalid_domains:
                    try:
                        ShopifyConnection(
                            user_id="test_user",
                            shop_domain=invalid_domain,
                            shop_name="Test Shop",
                            encrypted_access_token="token",
                            token_encryption_nonce="nonce",
                            scopes="read_products"
                        )
                        # Si on arrive ici, la validation n'a pas fonctionné
                        domain_validation_working = False
                        break
                    except ValueError:
                        # C'est ce qu'on attend
                        continue
                    except Exception:
                        # Autre erreur inattendue
                        domain_validation_working = False
                        break
                
                if domain_validation_working:
                    self.log_test("4.3 Domain Validation Rejection", "PASS", 
                                f"Rejet correct de {len(invalid_domains)} domaines invalides")
                else:
                    self.log_test("4.3 Domain Validation Rejection", "FAIL", 
                                error="Validation des domaines insuffisante")
            except Exception as e:
                self.log_test("4.3 Domain Validation Rejection", "FAIL", error=str(e))
            
            # Test 4.4: Validation des statuts
            try:
                all_statuses = [ConnectionStatus.PENDING, ConnectionStatus.ACTIVE, 
                              ConnectionStatus.EXPIRED, ConnectionStatus.REVOKED, ConnectionStatus.ERROR]
                
                status_validation_working = True
                for status in all_statuses:
                    try:
                        connection = ShopifyConnection(
                            user_id="test_user",
                            shop_domain="testshop.myshopify.com",
                            shop_name="Test Shop",
                            encrypted_access_token="token",
                            token_encryption_nonce="nonce",
                            scopes="read_products",
                            status=status
                        )
                        if connection.status != status:
                            status_validation_working = False
                            break
                    except Exception:
                        status_validation_working = False
                        break
                
                if status_validation_working:
                    self.log_test("4.4 Status Validation", "PASS", 
                                f"Validation réussie pour {len(all_statuses)} statuts")
                else:
                    self.log_test("4.4 Status Validation", "FAIL", 
                                error="Validation des statuts échouée")
            except Exception as e:
                self.log_test("4.4 Status Validation", "FAIL", error=str(e))
            
            return True
            
        except Exception as e:
            self.log_test("4.0 Models Setup", "FAIL", error=str(e))
            return False
    
    def test_5_api_routes_endpoints(self):
        """Test 5: Test Routes - Endpoints /api/shopify/install, /callback, /status, /disconnect, /health"""
        print("\n🧪 TEST 5: API ROUTES ENDPOINTS")
        print("=" * 80)
        
        # Test 5.1: Health endpoint (public)
        try:
            response = requests.get(f"{API_BASE_URL}/shopify/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                if 'service' in health_data and health_data.get('service') == 'shopify_integration':
                    self.log_test("5.1 Health Endpoint", "PASS", 
                                f"Health check OK: {health_data.get('status', 'unknown')}")
                else:
                    self.log_test("5.1 Health Endpoint", "FAIL", 
                                error=f"Réponse health incorrecte: {health_data}")
            else:
                self.log_test("5.1 Health Endpoint", "FAIL", 
                            error=f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("5.1 Health Endpoint", "FAIL", error=str(e))
        
        # Test 5.2: Install endpoint (doit nécessiter auth)
        try:
            install_data = {
                "shop_domain": "testshop.myshopify.com"
            }
            response = requests.post(f"{API_BASE_URL}/shopify/install", 
                                   json=install_data, timeout=10)
            
            if response.status_code == 401:
                self.log_test("5.2 Install Endpoint Auth Required", "PASS", 
                            "Endpoint correctement protégé (401 Unauthorized)")
            elif response.status_code == 403:
                self.log_test("5.2 Install Endpoint Auth Required", "PASS", 
                            "Endpoint correctement protégé (403 Forbidden)")
            else:
                self.log_test("5.2 Install Endpoint Auth Required", "FAIL", 
                            error=f"Endpoint non protégé, status: {response.status_code}")
        except Exception as e:
            self.log_test("5.2 Install Endpoint Auth Required", "FAIL", error=str(e))
        
        # Test 5.3: Status endpoint (doit nécessiter auth)
        try:
            response = requests.get(f"{API_BASE_URL}/shopify/status", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("5.3 Status Endpoint Auth Required", "PASS", 
                            f"Endpoint correctement protégé ({response.status_code})")
            else:
                self.log_test("5.3 Status Endpoint Auth Required", "FAIL", 
                            error=f"Endpoint non protégé, status: {response.status_code}")
        except Exception as e:
            self.log_test("5.3 Status Endpoint Auth Required", "FAIL", error=str(e))
        
        # Test 5.4: Disconnect endpoint (doit nécessiter auth)
        try:
            response = requests.post(f"{API_BASE_URL}/shopify/disconnect", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("5.4 Disconnect Endpoint Auth Required", "PASS", 
                            f"Endpoint correctement protégé ({response.status_code})")
            else:
                self.log_test("5.4 Disconnect Endpoint Auth Required", "FAIL", 
                            error=f"Endpoint non protégé, status: {response.status_code}")
        except Exception as e:
            self.log_test("5.4 Disconnect Endpoint Auth Required", "FAIL", error=str(e))
        
        # Test 5.5: Callback endpoint (public mais avec paramètres requis)
        try:
            # Test sans paramètres (doit échouer)
            response = requests.get(f"{API_BASE_URL}/shopify/callback", timeout=10)
            
            if response.status_code in [400, 422]:
                self.log_test("5.5 Callback Endpoint Parameter Validation", "PASS", 
                            f"Validation des paramètres OK ({response.status_code})")
            elif response.status_code == 302:
                # Redirection vers page d'erreur
                self.log_test("5.5 Callback Endpoint Parameter Validation", "PASS", 
                            "Redirection d'erreur correcte (302)")
            else:
                self.log_test("5.5 Callback Endpoint Parameter Validation", "FAIL", 
                            error=f"Validation insuffisante, status: {response.status_code}")
        except Exception as e:
            self.log_test("5.5 Callback Endpoint Parameter Validation", "FAIL", error=str(e))
        
        return True
    
    def test_6_unit_tests_execution(self):
        """Test 6: Test Intégration - Exécution du fichier test_shopify_phase1.py"""
        print("\n🧪 TEST 6: UNIT TESTS EXECUTION")
        print("=" * 80)
        
        try:
            # Changer vers le répertoire des tests
            original_cwd = os.getcwd()
            os.chdir('/app')
            
            # Ajouter le chemin backend au PYTHONPATH
            sys.path.insert(0, '/app/backend')
            
            # Importer et exécuter les tests
            from tests.backend.test_shopify_phase1 import run_shopify_phase1_tests
            
            # Exécuter les tests unitaires
            test_result = run_shopify_phase1_tests()
            
            if test_result:
                self.log_test("6.1 Unit Tests Execution", "PASS", 
                            "Tests unitaires Shopify Phase 1 exécutés avec succès (≥80%)")
            else:
                self.log_test("6.1 Unit Tests Execution", "FAIL", 
                            error="Tests unitaires échoués (<80% de réussite)")
            
            # Restaurer le répertoire de travail
            os.chdir(original_cwd)
            
            return test_result
            
        except Exception as e:
            self.log_test("6.1 Unit Tests Execution", "FAIL", error=str(e))
            # Restaurer le répertoire de travail en cas d'erreur
            try:
                os.chdir(original_cwd)
            except:
                pass
            return False
    
    def test_7_server_integration(self):
        """Test 7: Vérification Server.py - Import et enregistrement des routes Shopify"""
        print("\n🧪 TEST 7: SERVER INTEGRATION")
        print("=" * 80)
        
        # Test 7.1: Vérification de l'import dans server.py
        try:
            server_file = '/app/backend/server.py'
            with open(server_file, 'r', encoding='utf-8') as f:
                server_content = f.read()
            
            # Vérifier l'import
            if 'from routes.shopify_routes import shopify_router' in server_content:
                self.log_test("7.1 Router Import in Server", "PASS", 
                            "Import shopify_router trouvé dans server.py")
            else:
                self.log_test("7.1 Router Import in Server", "FAIL", 
                            error="Import shopify_router non trouvé dans server.py")
                return False
            
            # Vérifier l'enregistrement
            if 'app.include_router(shopify_router)' in server_content:
                self.log_test("7.2 Router Registration in Server", "PASS", 
                            "Enregistrement shopify_router trouvé dans server.py")
            else:
                self.log_test("7.2 Router Registration in Server", "FAIL", 
                            error="Enregistrement shopify_router non trouvé dans server.py")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("7.1 Server Integration Check", "FAIL", error=str(e))
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests Shopify Phase 1"""
        print("🚀 DÉMARRAGE DES TESTS SHOPIFY PHASE 1 - OAUTH & CONNEXIONS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base URL: {API_BASE_URL}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Exécuter tous les tests
        tests = [
            ("Module Imports & Availability", self.test_1_module_imports_availability),
            ("OAuth Service Functionality", self.test_2_oauth_service_functionality),
            ("Shopify Client Functionality", self.test_3_shopify_client_functionality),
            ("Models Validation", self.test_4_models_validation),
            ("API Routes Endpoints", self.test_5_api_routes_endpoints),
            ("Unit Tests Execution", self.test_6_unit_tests_execution),
            ("Server Integration", self.test_7_server_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Exécution: {test_name}")
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} - CRITICAL ERROR", "FAIL", 
                            error=f"Erreur critique: {str(e)}")
                print(f"❌ ERREUR CRITIQUE dans {test_name}: {str(e)}")
                traceback.print_exc()
        
        # Calculer les résultats finaux
        self.results['success_rate'] = (
            (self.results['passed_tests'] / self.results['total_tests']) * 100 
            if self.results['total_tests'] > 0 else 0
        )
        
        execution_time = time.time() - self.start_time
        
        # Afficher le résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ FINAL - TESTS SHOPIFY PHASE 1")
        print("=" * 80)
        print(f"✅ Tests réussis: {self.results['passed_tests']}")
        print(f"❌ Tests échoués: {self.results['failed_tests']}")
        print(f"📈 Taux de réussite: {self.results['success_rate']:.1f}%")
        print(f"⏱️ Temps d'exécution: {execution_time:.2f}s")
        
        if self.results['critical_issues']:
            print(f"\n🚨 PROBLÈMES CRITIQUES ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues']:
                print(f"   - {issue}")
        
        # Déterminer le statut final
        if self.results['success_rate'] >= 80:
            print("\n🎉 SHOPIFY PHASE 1 BACKEND TESTS - SUCCÈS!")
            print("✅ L'implémentation Shopify Phase 1 est PRODUCTION-READY")
            return True
        else:
            print("\n⚠️ SHOPIFY PHASE 1 BACKEND TESTS - ATTENTION REQUISE")
            print("❌ L'implémentation nécessite des corrections avant production")
            return False

def main():
    """Point d'entrée principal"""
    tester = ShopifyPhase1BackendTester()
    success = tester.run_all_tests()
    
    # Sauvegarder les résultats
    results_file = '/app/shopify_phase1_test_results.json'
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(tester.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés: {results_file}")
    except Exception as e:
        print(f"⚠️ Impossible de sauvegarder les résultats: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())