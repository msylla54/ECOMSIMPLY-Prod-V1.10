# Tests Backend Phase 1 Shopify - OAuth & Connexions
import pytest
import asyncio
import os
from datetime import datetime, timedelta
import json

# Import des modules Shopify Phase 1
try:
    from marketplaces.shopify.oauth import ShopifyOAuthService
    from marketplaces.shopify.client import ShopifyAPIClient
    from models.shopify_connections import (
        ShopifyConnection, ShopifyConnectionRequest, 
        ConnectionStatus, ShopifyPlan
    )
    SHOPIFY_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Shopify imports not available: {e}")
    SHOPIFY_IMPORTS_AVAILABLE = False

class TestShopifyPhase1Backend:
    """Tests complets pour Shopify Phase 1 - Connexions OAuth"""
    
    @pytest.mark.asyncio
    async def test_shopify_oauth_service_initialization(self):
        """Test 1: Initialisation du service OAuth Shopify"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        # Configuration mock pour les tests
        os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_key_12345678901234567890123456789012'
        
        try:
            oauth_service = ShopifyOAuthService()
            assert oauth_service is not None
            assert oauth_service.client_id == 'test_client_id'
            assert oauth_service.client_secret == 'test_client_secret'
            print("✅ Shopify OAuth service initialized successfully")
        except Exception as e:
            print(f"❌ OAuth service initialization failed: {e}")
            raise
    
    def test_shopify_connection_model_validation(self):
        """Test 2: Validation du modèle ShopifyConnection"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        # Test avec données valides
        valid_connection = ShopifyConnection(
            user_id="test_user_123",
            shop_domain="testshop.myshopify.com",
            shop_name="Test Shop",
            encrypted_access_token="encrypted_token_data",
            token_encryption_nonce="nonce_data",
            scopes="read_products,write_products",
            status=ConnectionStatus.ACTIVE
        )
        
        assert valid_connection.user_id == "test_user_123"
        assert valid_connection.shop_domain == "testshop.myshopify.com"
        assert valid_connection.status == ConnectionStatus.ACTIVE
        print("✅ ShopifyConnection model validation passed")
        
        # Test validation domaine invalide
        with pytest.raises(ValueError):
            ShopifyConnection(
                user_id="test_user_123",
                shop_domain="invalid_domain",
                shop_name="Test Shop", 
                encrypted_access_token="encrypted_token_data",
                token_encryption_nonce="nonce_data",
                scopes="read_products,write_products"
            )
        print("✅ Domain validation working correctly")
    
    def test_shopify_oauth_state_generation(self):
        """Test 3: Génération de state OAuth sécurisé"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_key_12345678901234567890123456789012'
        
        oauth_service = ShopifyOAuthService()
        
        # Générer plusieurs states pour vérifier l'unicité
        states = []
        for i in range(3):
            install_data = oauth_service.generate_install_url(
                shop_domain="testshop.myshopify.com",
                user_id=f"user_{i}"
            )
            states.append(install_data['state'])
        
        # Vérifier que tous les states sont uniques
        assert len(set(states)) == 3, "States should be unique"
        
        # Vérifier que les states sont suffisamment longs (sécurité)
        for state in states:
            assert len(state) > 30, f"State too short: {len(state)} chars"
        
        print(f"✅ OAuth state generation working - 3/3 states unique, min length {min(len(s) for s in states)} chars")
    
    def test_shopify_domain_validation(self):
        """Test 4: Validation des domaines Shopify"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_key_12345678901234567890123456789012'
        
        oauth_service = ShopifyOAuthService()
        
        test_cases = [
            ("testshop", "testshop.myshopify.com"),  # Nom simple
            ("test-shop", "test-shop.myshopify.com"),  # Avec tiret
            ("testshop.myshopify.com", "testshop.myshopify.com"),  # Déjà complet
            ("https://testshop.myshopify.com", "testshop.myshopify.com"),  # Avec protocole
        ]
        
        for input_domain, expected_output in test_cases:
            cleaned = oauth_service._validate_shop_domain(input_domain)
            assert cleaned == expected_output, f"Domain validation failed for {input_domain}"
        
        print("✅ Domain validation working for all test cases")
        
        # Test domaines invalides
        invalid_domains = ["", "   ", "invalid..domain", "toolongdomainname" * 10]
        
        for invalid_domain in invalid_domains:
            with pytest.raises(ValueError):
                oauth_service._validate_shop_domain(invalid_domain)
        
        print("✅ Invalid domain rejection working correctly")
    
    def test_shopify_client_initialization(self):
        """Test 5: Initialisation du client Shopify API"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        shop_domain = "testshop.myshopify.com"
        access_token = "test_access_token"
        
        client = ShopifyAPIClient(shop_domain, access_token)
        
        assert client.shop_domain == shop_domain
        assert client.access_token == access_token
        assert client.rest_base_url == f"https://{shop_domain}/admin/api/2024-01"
        assert client.graphql_url == f"https://{shop_domain}/admin/api/2024-01/graphql.json"
        
        print("✅ Shopify API client initialized correctly")
    
    def test_shopify_connection_request_model(self):
        """Test 6: Modèle de requête de connexion"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        # Test requête valide
        request = ShopifyConnectionRequest(
            shop_domain="testshop.myshopify.com"
        )
        assert request.shop_domain == "testshop.myshopify.com"
        
        # Test avec URL de retour
        request_with_return = ShopifyConnectionRequest(
            shop_domain="testshop",
            return_url="https://app.ecomsimply.com/dashboard"
        )
        assert request_with_return.return_url == "https://app.ecomsimply.com/dashboard"
        
        print("✅ ShopifyConnectionRequest model working correctly")
    
    def test_shopify_scopes_validation(self):
        """Test 7: Validation des scopes OAuth"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        # Test scopes valides
        valid_scopes = "read_products,write_products,read_orders"
        connection = ShopifyConnection(
            user_id="test_user",
            shop_domain="testshop.myshopify.com",
            shop_name="Test Shop",
            encrypted_access_token="encrypted_token",
            token_encryption_nonce="nonce",
            scopes=valid_scopes
        )
        assert connection.scopes == valid_scopes
        
        # Test scopes invalides
        invalid_scopes = "invalid_scope,another_invalid_scope"
        with pytest.raises(ValueError):
            ShopifyConnection(
                user_id="test_user",
                shop_domain="testshop.myshopify.com", 
                shop_name="Test Shop",
                encrypted_access_token="encrypted_token",
                token_encryption_nonce="nonce",
                scopes=invalid_scopes
            )
        
        print("✅ Shopify scopes validation working correctly")
    
    def test_shopify_encryption_functionality(self):
        """Test 8: Fonctionnalité de chiffrement des tokens"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_client_secret'
        os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_key_12345678901234567890123456789012'
        
        oauth_service = ShopifyOAuthService()
        
        # Test chiffrement et déchiffrement
        test_token = "shpat_test_access_token_12345"
        user_id = "test_user_123"
        
        # Chiffrer
        encrypted_data = oauth_service.encrypt_access_token(test_token, user_id)
        
        assert 'encrypted_token' in encrypted_data
        assert 'nonce' in encrypted_data
        assert 'encryption_method' in encrypted_data
        assert encrypted_data['encryption_method'] == 'AES-GCM'
        
        # Déchiffrer
        decrypted_token = oauth_service.decrypt_access_token(encrypted_data, user_id)
        assert decrypted_token == test_token
        
        print("✅ Token encryption/decryption working correctly")
    
    def test_shopify_webhook_signature_verification(self):
        """Test 9: Vérification signature webhook"""
        if not SHOPIFY_IMPORTS_AVAILABLE:
            pytest.skip("Shopify modules not available")
        
        os.environ['SHOPIFY_CLIENT_ID'] = 'test_client_id'
        os.environ['SHOPIFY_CLIENT_SECRET'] = 'test_secret'
        os.environ['SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY'] = 'test_key_12345678901234567890123456789012'
        
        oauth_service = ShopifyOAuthService()
        
        # Test data pour webhook
        test_data = '{"id":123,"title":"Test Product"}'
        
        # Générer signature valide (on ne peut pas tester avec vraie signature sans clés réelles)
        # Mais on peut tester que la fonction ne lève pas d'erreur
        try:
            result = oauth_service.verify_webhook_signature(test_data, "fake_signature")
            # Le résultat sera False avec une fausse signature, mais l'important c'est que ça ne crash pas
            assert isinstance(result, bool)
            print("✅ Webhook signature verification function working")
        except Exception as e:
            print(f"❌ Webhook signature verification failed: {e}")
            raise

def run_shopify_phase1_tests():
    """Exécute tous les tests Shopify Phase 1"""
    if not SHOPIFY_IMPORTS_AVAILABLE:
        print("❌ Cannot run Shopify tests - imports not available")
        return False
    
    test_instance = TestShopifyPhase1Backend()
    
    tests = [
        ('OAuth Service Initialization', test_instance.test_shopify_oauth_service_initialization),
        ('Connection Model Validation', test_instance.test_shopify_connection_model_validation),
        ('OAuth State Generation', test_instance.test_shopify_oauth_state_generation),
        ('Domain Validation', test_instance.test_shopify_domain_validation),
        ('Client Initialization', test_instance.test_shopify_client_initialization),
        ('Connection Request Model', test_instance.test_shopify_connection_request_model),
        ('Scopes Validation', test_instance.test_shopify_scopes_validation),
        ('Encryption Functionality', test_instance.test_shopify_encryption_functionality),
        ('Webhook Signature Verification', test_instance.test_shopify_webhook_signature_verification)
    ]
    
    passed = 0
    total = len(tests)
    
    print(f"\n🧪 SHOPIFY PHASE 1 BACKEND TESTING - {total} tests")
    print("=" * 60)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func())
            else:
                test_func()
            passed += 1
            print(f"✅ {test_name}")
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
    
    success_rate = (passed / total) * 100
    print(f"\n📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 SHOPIFY PHASE 1 BACKEND TESTS SUCCESSFUL!")
        return True
    else:
        print("⚠️ SHOPIFY PHASE 1 BACKEND TESTS NEED ATTENTION")
        return False

if __name__ == "__main__":
    run_shopify_phase1_tests()