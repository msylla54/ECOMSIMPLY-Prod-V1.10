#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon Listings Phase 2 Backend Testing
Test complet des endpoints et fonctionnalités Phase 2 Amazon SP-API

CONTEXTE:
- Phase 1 Amazon SP-API (OAuth + connexions) complète et testée (84.2% taux de réussite)
- Phase 2 scaffoldée avec modules backend/amazon/listings/ et routes amazon_listings_routes.py
- Workflow complet: saisie produit → génération IA → prévisualisation → validation → publication Amazon réelle

ENDPOINTS TESTÉS:
1. POST /api/amazon/listings/generate - Génération de listing par IA
2. POST /api/amazon/listings/validate - Validation selon règles A9/A10
3. POST /api/amazon/listings/publish - Publication via SP-API réelle
4. GET /api/amazon/listings/status/{sku} - Statut d'une fiche
5. GET /api/amazon/listings/history - Historique des générations
6. PUT /api/amazon/listings/update/{sku} - Mise à jour fiche

CRITÈRES DE RÉUSSITE:
- Toutes les routes répondent avec codes de statut appropriés
- Le générateur IA produit du contenu conforme Amazon
- La validation identifie les listings APPROVED/WARNING/REJECTED
- La publication utilise le vrai SP-API
- La gestion d'erreurs est robuste
"""

import asyncio
import aiohttp
import json
import sys
import time
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configuration des endpoints
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

# Endpoints Amazon Listings Phase 2
AMAZON_LISTINGS_ENDPOINTS = {
    "generate": f"{API_BASE}/amazon/listings/generate",
    "validate": f"{API_BASE}/amazon/listings/validate", 
    "publish": f"{API_BASE}/amazon/listings/publish",
    "status": f"{API_BASE}/amazon/listings/status",
    "history": f"{API_BASE}/amazon/listings/history",
    "update": f"{API_BASE}/amazon/listings/update"
}

# Endpoints de support
SUPPORT_ENDPOINTS = {
    "login": f"{API_BASE}/auth/login",
    "register": f"{API_BASE}/auth/register",
    "amazon_status": f"{API_BASE}/amazon/status",
    "health": f"{API_BASE}/health"
}

# Données de test pour génération de listing
SAMPLE_PRODUCT_DATA = {
    "brand": "Apple",
    "product_name": "iPhone 15 Pro Max 256GB",
    "features": [
        "Puce A17 Pro avec GPU 6 cœurs",
        "Écran Super Retina XDR 6,7 pouces", 
        "Système caméra Pro triple 48 Mpx",
        "Châssis titane qualité aérospatiale",
        "USB-C avec USB 3 transferts rapides"
    ],
    "category": "électronique",
    "target_keywords": ["smartphone", "premium", "apple", "iphone", "pro", "titanium"],
    "size": "6,7 pouces",
    "color": "Titane Naturel",
    "price": 1479.00,
    "description": "Le smartphone le plus avancé d'Apple avec puce A17 Pro et design titane premium"
}

# Données utilisateur de test
TEST_USER_DATA = {
    "email": f"test_amazon_phase2_{int(time.time())}@ecomsimply.com",
    "name": "Test Amazon Phase 2",
    "password": "TestPassword123!"
}

class AmazonListingsPhase2Tester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.test_results = {}
        self.generated_listing = None
        self.validation_result = None
        
        # Résultats de test par endpoint
        self.endpoint_results = {
            "generate": {"tested": False, "success": False, "details": {}},
            "validate": {"tested": False, "success": False, "details": {}},
            "publish": {"tested": False, "success": False, "details": {}},
            "status": {"tested": False, "success": False, "details": {}},
            "history": {"tested": False, "success": False, "details": {}},
            "update": {"tested": False, "success": False, "details": {}}
        }
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=120)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def setup_test_environment(self) -> bool:
        """Configure l'environnement de test avec authentification"""
        print("🔧 Setting up test environment...")
        
        try:
            # 1. Vérifier la santé du backend
            health_ok = await self._check_backend_health()
            if not health_ok:
                print("❌ Backend health check failed")
                return False
            
            # 2. Créer un utilisateur de test
            user_created = await self._create_test_user()
            if not user_created:
                print("❌ Test user creation failed")
                return False
            
            # 3. Se connecter et obtenir un token
            auth_ok = await self._authenticate_test_user()
            if not auth_ok:
                print("❌ Authentication failed")
                return False
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Setup error: {str(e)}")
            return False

    async def _check_backend_health(self) -> bool:
        """Vérifie la santé du backend"""
        try:
            async with self.session.get(SUPPORT_ENDPOINTS["health"]) as response:
                if response.status == 200:
                    print("✅ Backend health check passed")
                    return True
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False

    async def _create_test_user(self) -> bool:
        """Crée un utilisateur de test"""
        try:
            async with self.session.post(
                SUPPORT_ENDPOINTS["register"],
                json=TEST_USER_DATA,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"✅ Test user created: {TEST_USER_DATA['email']}")
                    return True
                elif response.status == 400:
                    # Utilisateur existe déjà, c'est OK
                    print(f"ℹ️ Test user already exists: {TEST_USER_DATA['email']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ User creation failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ User creation error: {str(e)}")
            return False

    async def _authenticate_test_user(self) -> bool:
        """Authentifie l'utilisateur de test"""
        try:
            login_data = {
                "email": TEST_USER_DATA["email"],
                "password": TEST_USER_DATA["password"]
            }
            
            async with self.session.post(
                SUPPORT_ENDPOINTS["login"],
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("token")
                    user_data = data.get("user", {})
                    self.user_id = user_data.get("id")
                    
                    if self.auth_token:
                        print("✅ Authentication successful")
                        return True
                    else:
                        print("❌ No access token received")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def _get_auth_headers(self) -> Dict[str, str]:
        """Retourne les headers d'authentification"""
        if not self.auth_token:
            return {"Content-Type": "application/json"}
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }

    async def test_amazon_connection_status(self) -> bool:
        """Vérifie le statut de connexion Amazon (prérequis)"""
        print("\n🔍 Testing Amazon connection status...")
        
        try:
            headers = self._get_auth_headers()
            async with self.session.get(SUPPORT_ENDPOINTS["amazon_status"], headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Amazon connection status retrieved")
                    print(f"   Connection status: {data.get('status', 'unknown')}")
                    return True
                elif response.status == 412:
                    print("⚠️ No Amazon connection found (expected for Phase 2 testing)")
                    return True  # C'est normal pour les tests
                else:
                    error_text = await response.text()
                    print(f"❌ Amazon status check failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Amazon status error: {str(e)}")
            return False

    async def test_generate_listing_endpoint(self) -> bool:
        """Test de l'endpoint de génération de listing"""
        print("\n🤖 Testing listing generation endpoint...")
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.post(
                AMAZON_LISTINGS_ENDPOINTS["generate"],
                json=SAMPLE_PRODUCT_DATA,
                headers=headers
            ) as response:
                
                self.endpoint_results["generate"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    self.generated_listing = data.get("data")
                    
                    print("✅ Listing generation successful")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Message: {data.get('message')}")
                    
                    # Vérifier la structure de la réponse
                    if self.generated_listing:
                        seo_content = self.generated_listing.get("seo_content", {})
                        print(f"   Generated title: {seo_content.get('title', 'N/A')[:50]}...")
                        print(f"   Bullet points: {len(seo_content.get('bullet_points', []))}")
                        print(f"   Description length: {len(seo_content.get('description', ''))}")
                        print(f"   Keywords: {seo_content.get('backend_keywords', 'N/A')[:50]}...")
                        
                        # Vérifier les métadonnées
                        metadata = self.generated_listing.get("generation_metadata", {})
                        optimization_score = metadata.get("optimization_score", 0)
                        print(f"   Optimization score: {optimization_score}")
                        
                        self.endpoint_results["generate"]["success"] = True
                        self.endpoint_results["generate"]["details"] = {
                            "optimization_score": optimization_score,
                            "title_length": len(seo_content.get('title', '')),
                            "bullets_count": len(seo_content.get('bullet_points', [])),
                            "description_length": len(seo_content.get('description', '')),
                            "keywords_length": len(seo_content.get('backend_keywords', ''))
                        }
                        
                        return True
                    else:
                        print("❌ No generated listing data received")
                        return False
                        
                elif response.status == 412:
                    print("⚠️ Amazon connection required (expected behavior)")
                    self.endpoint_results["generate"]["details"]["error"] = "No Amazon connection"
                    return True  # C'est le comportement attendu
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Generation failed: {response.status} - {error_text}")
                    self.endpoint_results["generate"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ Generation test error: {str(e)}")
            self.endpoint_results["generate"]["details"]["error"] = str(e)
            return False

    async def test_validate_listing_endpoint(self) -> bool:
        """Test de l'endpoint de validation"""
        print("\n🔍 Testing listing validation endpoint...")
        
        if not self.generated_listing:
            print("⚠️ No generated listing available, creating mock data...")
            # Créer des données de test pour la validation
            mock_listing = {
                "listing_id": "test_validation_123",
                "product_data": SAMPLE_PRODUCT_DATA,
                "seo_content": {
                    "title": "Apple iPhone 15 Pro Max 256GB Titane Naturel - Smartphone Premium",
                    "bullet_points": [
                        "✅ PERFORMANCE SUPÉRIEURE : Puce A17 Pro pour des performances exceptionnelles",
                        "🎯 DESIGN TITANIUM : Construction premium en titanium naturel résistant",
                        "📸 SYSTÈME CAMÉRAS PRO : Triple caméra 48MP avec zoom optique 5x",
                        "⚡ BATTERIE LONGUE DURÉE : Jusqu'à 29h de lecture vidéo en continu",
                        "🔒 SÉCURITÉ AVANCÉE : Face ID et chiffrement avancé pour vos données"
                    ],
                    "description": "<h3>🌟 Apple iPhone 15 Pro Max</h3><p>Découvrez notre <strong>iPhone 15 Pro Max</strong> conçu pour répondre à tous vos besoins en matière de <em>électronique</em>. Apple vous garantit une qualité exceptionnelle et une performance optimale.</p><h4>✨ Caractéristiques principales :</h4><ul><li><strong>Puce A17 Pro avec GPU 6 cœurs</strong> - Pour une expérience utilisateur optimale</li><li><strong>Écran Super Retina XDR 6,7 pouces</strong> - Pour une expérience utilisateur optimale</li></ul>",
                    "backend_keywords": "apple, iphone, smartphone, premium, titanium, pro, 15, max, puce, a17",
                    "image_requirements": {
                        "main_image": {
                            "description": "Image principale iPhone 15 Pro Max sur fond blanc",
                            "min_resolution": "1000x1000",
                            "required": True
                        },
                        "total_count": 5
                    }
                }
            }
            self.generated_listing = mock_listing
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.post(
                AMAZON_LISTINGS_ENDPOINTS["validate"],
                json=self.generated_listing,
                headers=headers
            ) as response:
                
                self.endpoint_results["validate"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    self.validation_result = data.get("data")
                    
                    print("✅ Listing validation successful")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Summary: {data.get('summary')}")
                    
                    # Analyser les résultats de validation
                    if self.validation_result:
                        overall_status = self.validation_result.get("overall_status")
                        validation_score = self.validation_result.get("validation_score", 0)
                        errors = self.validation_result.get("errors", [])
                        warnings = self.validation_result.get("warnings", [])
                        
                        print(f"   Overall status: {overall_status}")
                        print(f"   Validation score: {validation_score}%")
                        print(f"   Errors: {len(errors)}")
                        print(f"   Warnings: {len(warnings)}")
                        
                        # Analyser les détails par composant
                        details = self.validation_result.get("details", {})
                        for component, result in details.items():
                            component_status = result.get("status", "unknown")
                            component_score = result.get("score", 0)
                            print(f"   {component}: {component_status} ({component_score}%)")
                        
                        self.endpoint_results["validate"]["success"] = True
                        self.endpoint_results["validate"]["details"] = {
                            "overall_status": overall_status,
                            "validation_score": validation_score,
                            "errors_count": len(errors),
                            "warnings_count": len(warnings),
                            "components_tested": len(details)
                        }
                        
                        return True
                    else:
                        print("❌ No validation result data received")
                        return False
                        
                elif response.status == 412:
                    print("⚠️ Amazon connection required (expected behavior)")
                    self.endpoint_results["validate"]["details"]["error"] = "No Amazon connection"
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Validation failed: {response.status} - {error_text}")
                    self.endpoint_results["validate"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ Validation test error: {str(e)}")
            self.endpoint_results["validate"]["details"]["error"] = str(e)
            return False

    async def test_publish_listing_endpoint(self) -> bool:
        """Test de l'endpoint de publication"""
        print("\n📤 Testing listing publication endpoint...")
        
        if not self.generated_listing or not self.validation_result:
            print("⚠️ No listing/validation data available, creating mock data...")
            # Utiliser des données de test
            publication_request = {
                "listing_data": self.generated_listing or {
                    "product_data": SAMPLE_PRODUCT_DATA,
                    "seo_content": {
                        "title": "Apple iPhone 15 Pro Max Test",
                        "bullet_points": ["Test bullet 1", "Test bullet 2"],
                        "description": "<p>Test description</p>",
                        "backend_keywords": "test, apple, iphone"
                    }
                },
                "validation_data": self.validation_result or {"overall_status": "APPROVED"},
                "force_publish": True  # Pour les tests
            }
        else:
            publication_request = {
                "listing_data": self.generated_listing,
                "validation_data": self.validation_result,
                "force_publish": True
            }
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.post(
                AMAZON_LISTINGS_ENDPOINTS["publish"],
                json=publication_request,
                headers=headers
            ) as response:
                
                self.endpoint_results["publish"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    
                    print("✅ Publication endpoint responded successfully")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Message: {data.get('message')}")
                    
                    # Analyser les résultats de publication
                    publication_data = data.get("data", {})
                    if publication_data:
                        pub_status = publication_data.get("status")
                        sku = publication_data.get("sku")
                        errors = publication_data.get("errors", [])
                        
                        print(f"   Publication status: {pub_status}")
                        print(f"   SKU: {sku}")
                        print(f"   Errors: {len(errors)}")
                        
                        if errors:
                            print(f"   Error details: {errors[:2]}")  # Afficher les 2 premières erreurs
                        
                        self.endpoint_results["publish"]["success"] = True
                        self.endpoint_results["publish"]["details"] = {
                            "publication_status": pub_status,
                            "sku": sku,
                            "errors_count": len(errors),
                            "has_listing_url": bool(publication_data.get("listing_url"))
                        }
                        
                        return True
                    else:
                        print("❌ No publication data received")
                        return False
                        
                elif response.status == 412:
                    print("⚠️ Amazon connection required (expected behavior)")
                    self.endpoint_results["publish"]["details"]["error"] = "No Amazon connection"
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Publication failed: {response.status} - {error_text}")
                    self.endpoint_results["publish"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ Publication test error: {str(e)}")
            self.endpoint_results["publish"]["details"]["error"] = str(e)
            return False

    async def test_history_endpoint(self) -> bool:
        """Test de l'endpoint d'historique"""
        print("\n📚 Testing listings history endpoint...")
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.get(
                AMAZON_LISTINGS_ENDPOINTS["history"],
                headers=headers,
                params={"limit": 10, "skip": 0}
            ) as response:
                
                self.endpoint_results["history"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    
                    print("✅ History endpoint responded successfully")
                    print(f"   Status: {data.get('status')}")
                    
                    # Analyser les données d'historique
                    history_data = data.get("data", {})
                    if history_data:
                        listings = history_data.get("listings", [])
                        total_count = history_data.get("total_count", 0)
                        
                        print(f"   Total listings: {total_count}")
                        print(f"   Retrieved listings: {len(listings)}")
                        
                        if listings:
                            print(f"   Latest listing: {listings[0].get('listing_id', 'N/A')}")
                        
                        self.endpoint_results["history"]["success"] = True
                        self.endpoint_results["history"]["details"] = {
                            "total_count": total_count,
                            "retrieved_count": len(listings),
                            "has_listings": len(listings) > 0
                        }
                        
                        return True
                    else:
                        print("❌ No history data received")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ History retrieval failed: {response.status} - {error_text}")
                    self.endpoint_results["history"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ History test error: {str(e)}")
            self.endpoint_results["history"]["details"]["error"] = str(e)
            return False

    async def test_status_endpoint(self) -> bool:
        """Test de l'endpoint de statut"""
        print("\n🔍 Testing listing status endpoint...")
        
        # Utiliser un SKU de test
        test_sku = "TEST-IPHONE15-20250101"
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.get(
                f"{AMAZON_LISTINGS_ENDPOINTS['status']}/{test_sku}",
                headers=headers
            ) as response:
                
                self.endpoint_results["status"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    
                    print("✅ Status endpoint responded successfully")
                    print(f"   Status: {data.get('status')}")
                    
                    # Analyser les données de statut
                    status_data = data.get("data", {})
                    if status_data:
                        sku = status_data.get("sku")
                        listing_status = status_data.get("status")
                        
                        print(f"   SKU: {sku}")
                        print(f"   Listing status: {listing_status}")
                        
                        self.endpoint_results["status"]["success"] = True
                        self.endpoint_results["status"]["details"] = {
                            "sku": sku,
                            "listing_status": listing_status,
                            "has_amazon_data": bool(status_data.get("amazon_data"))
                        }
                        
                        return True
                    else:
                        print("❌ No status data received")
                        return False
                        
                elif response.status == 412:
                    print("⚠️ Amazon connection required (expected behavior)")
                    self.endpoint_results["status"]["details"]["error"] = "No Amazon connection"
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Status check failed: {response.status} - {error_text}")
                    self.endpoint_results["status"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ Status test error: {str(e)}")
            self.endpoint_results["status"]["details"]["error"] = str(e)
            return False

    async def test_update_endpoint(self) -> bool:
        """Test de l'endpoint de mise à jour"""
        print("\n📝 Testing listing update endpoint...")
        
        # Utiliser un SKU de test et des données de mise à jour
        test_sku = "TEST-IPHONE15-20250101"
        update_data = {
            "title": "Apple iPhone 15 Pro Max 256GB Titane Naturel - UPDATED",
            "price": 1399.00,
            "description": "<p>Description mise à jour pour test</p>"
        }
        
        try:
            headers = self._get_auth_headers()
            
            async with self.session.put(
                f"{AMAZON_LISTINGS_ENDPOINTS['update']}/{test_sku}",
                json=update_data,
                headers=headers
            ) as response:
                
                self.endpoint_results["update"]["tested"] = True
                
                if response.status == 200:
                    data = await response.json()
                    
                    print("✅ Update endpoint responded successfully")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Message: {data.get('message')}")
                    
                    # Analyser les résultats de mise à jour
                    update_result = data.get("data", {})
                    if update_result:
                        update_status = update_result.get("status")
                        errors = update_result.get("errors", [])
                        
                        print(f"   Update status: {update_status}")
                        print(f"   Errors: {len(errors)}")
                        
                        self.endpoint_results["update"]["success"] = True
                        self.endpoint_results["update"]["details"] = {
                            "update_status": update_status,
                            "errors_count": len(errors),
                            "sku": test_sku
                        }
                        
                        return True
                    else:
                        print("❌ No update result data received")
                        return False
                        
                elif response.status == 412:
                    print("⚠️ Amazon connection required (expected behavior)")
                    self.endpoint_results["update"]["details"]["error"] = "No Amazon connection"
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Update failed: {response.status} - {error_text}")
                    self.endpoint_results["update"]["details"]["error"] = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            print(f"❌ Update test error: {str(e)}")
            self.endpoint_results["update"]["details"]["error"] = str(e)
            return False

    def print_comprehensive_summary(self):
        """Affiche un résumé complet des tests"""
        print("\n" + "="*80)
        print("🎯 RÉSUMÉ COMPLET - AMAZON LISTINGS PHASE 2 BACKEND TESTING")
        print("="*80)
        
        # Statistiques globales
        total_endpoints = len(self.endpoint_results)
        tested_endpoints = sum(1 for result in self.endpoint_results.values() if result["tested"])
        successful_endpoints = sum(1 for result in self.endpoint_results.values() if result["success"])
        
        print(f"📊 STATISTIQUES GLOBALES:")
        print(f"   Total endpoints: {total_endpoints}")
        print(f"   Endpoints testés: {tested_endpoints}")
        print(f"   Endpoints réussis: {successful_endpoints}")
        print(f"   Taux de réussite: {(successful_endpoints/tested_endpoints*100):.1f}%" if tested_endpoints > 0 else "   Taux de réussite: 0%")
        
        print(f"\n📋 RÉSULTATS DÉTAILLÉS PAR ENDPOINT:")
        
        endpoint_names = {
            "generate": "POST /api/amazon/listings/generate",
            "validate": "POST /api/amazon/listings/validate", 
            "publish": "POST /api/amazon/listings/publish",
            "status": "GET /api/amazon/listings/status/{sku}",
            "history": "GET /api/amazon/listings/history",
            "update": "PUT /api/amazon/listings/update/{sku}"
        }
        
        for endpoint_key, result in self.endpoint_results.items():
            endpoint_name = endpoint_names.get(endpoint_key, endpoint_key)
            
            if not result["tested"]:
                status = "⏭️ NON TESTÉ"
            elif result["success"]:
                status = "✅ RÉUSSI"
            else:
                status = "❌ ÉCHEC"
            
            print(f"\n{status} - {endpoint_name}")
            
            if result["tested"]:
                details = result.get("details", {})
                if details:
                    for key, value in details.items():
                        if key != "error":
                            print(f"   └─ {key}: {value}")
                    
                    if "error" in details:
                        print(f"   └─ Erreur: {details['error']}")
        
        # Analyse des fonctionnalités critiques
        print(f"\n🔍 ANALYSE DES FONCTIONNALITÉS CRITIQUES:")
        
        # 1. Génération IA
        if self.endpoint_results["generate"]["success"]:
            gen_details = self.endpoint_results["generate"]["details"]
            optimization_score = gen_details.get("optimization_score", 0)
            print(f"✅ Génération IA: Score d'optimisation {optimization_score}%")
            print(f"   └─ Titre: {gen_details.get('title_length', 0)} caractères")
            print(f"   └─ Bullets: {gen_details.get('bullets_count', 0)} points")
            print(f"   └─ Description: {gen_details.get('description_length', 0)} caractères")
        else:
            print("❌ Génération IA: Non fonctionnelle")
        
        # 2. Validation A9/A10
        if self.endpoint_results["validate"]["success"]:
            val_details = self.endpoint_results["validate"]["details"]
            validation_score = val_details.get("validation_score", 0)
            overall_status = val_details.get("overall_status", "unknown")
            print(f"✅ Validation A9/A10: {overall_status} ({validation_score}%)")
            print(f"   └─ Erreurs: {val_details.get('errors_count', 0)}")
            print(f"   └─ Avertissements: {val_details.get('warnings_count', 0)}")
        else:
            print("❌ Validation A9/A10: Non fonctionnelle")
        
        # 3. Publication SP-API
        if self.endpoint_results["publish"]["success"]:
            pub_details = self.endpoint_results["publish"]["details"]
            pub_status = pub_details.get("publication_status", "unknown")
            print(f"✅ Publication SP-API: {pub_status}")
            print(f"   └─ SKU généré: {pub_details.get('sku', 'N/A')}")
            print(f"   └─ URL listing: {'Oui' if pub_details.get('has_listing_url') else 'Non'}")
        else:
            print("❌ Publication SP-API: Non fonctionnelle")
        
        # 4. Gestion d'erreurs
        error_handling_score = 0
        total_error_tests = 0
        
        for result in self.endpoint_results.values():
            if result["tested"]:
                total_error_tests += 1
                if "error" in result.get("details", {}):
                    error_type = result["details"]["error"]
                    if "No Amazon connection" in error_type or "HTTP 412" in error_type:
                        error_handling_score += 1  # Gestion d'erreur appropriée
                elif result["success"]:
                    error_handling_score += 1  # Pas d'erreur
        
        error_handling_rate = (error_handling_score / total_error_tests * 100) if total_error_tests > 0 else 0
        print(f"✅ Gestion d'erreurs: {error_handling_rate:.1f}% appropriée")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if successful_endpoints == total_endpoints:
            print("🎉 Tous les endpoints fonctionnent correctement!")
            print("   └─ Phase 2 Amazon Listings est prête pour la production")
        elif successful_endpoints >= total_endpoints * 0.8:
            print("✅ La plupart des endpoints fonctionnent")
            print("   └─ Corriger les endpoints en échec pour finaliser Phase 2")
        else:
            print("⚠️ Plusieurs endpoints nécessitent des corrections")
            print("   └─ Réviser l'implémentation avant mise en production")
        
        # Prochaines étapes
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print("1. Connecter un compte Amazon réel pour tests complets")
        print("2. Tester la publication avec de vraies données produit")
        print("3. Valider le workflow end-to-end avec utilisateur final")
        print("4. Optimiser les performances et la gestion d'erreurs")
        
        print("="*80)
        
        return successful_endpoints, total_endpoints

    async def run_complete_phase2_testing(self):
        """Exécute tous les tests de la Phase 2"""
        print("🚀 DÉMARRAGE - Tests complets Amazon Listings Phase 2")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📱 Produit test: {SAMPLE_PRODUCT_DATA['product_name']}")
        print("-"*80)
        
        start_time = time.time()
        
        # 1. Configuration de l'environnement
        setup_ok = await self.setup_test_environment()
        if not setup_ok:
            print("❌ ARRÊT: Impossible de configurer l'environnement de test")
            return
        
        # 2. Vérification prérequis Amazon
        await self.test_amazon_connection_status()
        
        # 3. Tests des endpoints Phase 2
        print("\n" + "="*60)
        print("🧪 TESTS DES ENDPOINTS AMAZON LISTINGS PHASE 2")
        print("="*60)
        
        await self.test_generate_listing_endpoint()
        await self.test_validate_listing_endpoint()
        await self.test_publish_listing_endpoint()
        await self.test_status_endpoint()
        await self.test_history_endpoint()
        await self.test_update_endpoint()
        
        # 4. Résumé final
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Durée totale des tests: {duration:.2f} secondes")
        
        successful_endpoints, total_endpoints = self.print_comprehensive_summary()
        
        # Sauvegarde des résultats
        results_summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "backend_url": BACKEND_URL,
            "test_product": SAMPLE_PRODUCT_DATA,
            "endpoint_results": self.endpoint_results,
            "successful_endpoints": successful_endpoints,
            "total_endpoints": total_endpoints,
            "success_rate": (successful_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0,
            "generated_listing": self.generated_listing,
            "validation_result": self.validation_result
        }
        
        # Écrire les résultats dans un fichier
        try:
            with open('/app/amazon_listings_phase2_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results_summary, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Résultats sauvegardés: /app/amazon_listings_phase2_test_results.json")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde résultats: {e}")
        
        return results_summary

async def main():
    """Fonction principale de test"""
    try:
        async with AmazonListingsPhase2Tester() as tester:
            results = await tester.run_complete_phase2_testing()
            
            # Code de sortie basé sur le succès
            if results and results.get('success_rate', 0) >= 80:
                sys.exit(0)  # Succès
            else:
                sys.exit(1)  # Échec
                
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        sys.exit(3)

if __name__ == "__main__":
    print("🎯 ECOMSIMPLY - Tests Amazon Listings Phase 2 Backend")
    print("="*80)
    asyncio.run(main())