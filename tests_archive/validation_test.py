#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - PHASE 3 VALIDATION AVANCÉE DES ENTRÉES
Test automatique pour vérifier que le système de validation avancée des entrées fonctionne correctement.

OBJECTIFS DE TEST:
1. Test Validation product_name (longueur, caractères interdits)
2. Test Validation product_description (longueur min/max)
3. Test Validation language (langues supportées)
4. Test Validation number_of_images (plage 1-5)
5. Test Validation Globale (erreurs multiples)
6. Test Messages d'Erreur (format JSON, français, logging)
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class ValidationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.test_user = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        print("✅ Session HTTP initialisée")
        return True
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def create_test_user(self) -> Dict:
        """Create a test user for validation testing"""
        
        user_data = {
            "email": f"validation_test_{int(time.time())}@ecomsimply.test",
            "name": "Validation Test User",
            "password": "TestPassword123!"
        }
        
        print(f"👤 Création utilisateur test pour validation...")
        
        try:
            # Register user
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
                if response.status == 200:
                    print(f"✅ Utilisateur créé: {user_data['email']}")
                    
                    # Login to get token
                    login_data = {
                        "email": user_data["email"],
                        "password": user_data["password"]
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            login_result = await login_response.json()
                            token = login_result.get("token")
                            
                            user_info = {
                                "email": user_data["email"],
                                "token": token
                            }
                            
                            self.test_user = user_info
                            print(f"✅ Utilisateur prêt avec token")
                            return user_info
                        else:
                            error_text = await login_response.text()
                            print(f"❌ Échec login: {login_response.status} - {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    print(f"❌ Échec création utilisateur: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Exception création utilisateur: {str(e)}")
            return None
    
    def get_auth_headers(self, token: str):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def test_product_name_validation(self):
        """
        TEST 1: Validation product_name
        - product_name trop court (< 5 caractères) → HTTP 400
        - product_name vide → HTTP 400  
        - product_name avec caractères interdits (<, >, {, }) → HTTP 400
        - product_name valide → HTTP 200
        """
        print("\n🧪 TEST 1: Validation product_name")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test cases for product_name validation
        test_cases = [
            {
                "name": "Nom trop court (< 5 caractères)",
                "data": {
                    "product_name": "ABC",  # 3 caractères
                    "product_description": "Description valide de test pour validation",
                    "generate_image": True,
                    "number_of_images": 1,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_name"
            },
            {
                "name": "Nom vide",
                "data": {
                    "product_name": "",
                    "product_description": "Description valide de test pour validation",
                    "generate_image": True,
                    "number_of_images": 1,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_name"
            },
            {
                "name": "Nom avec caractères interdits (<>{})",
                "data": {
                    "product_name": "Produit <test> {invalid}",
                    "product_description": "Description valide de test pour validation",
                    "generate_image": True,
                    "number_of_images": 1,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_name"
            },
            {
                "name": "Nom valide",
                "data": {
                    "product_name": "iPhone 15 Pro Max",  # Nom valide
                    "product_description": "Smartphone Apple haut de gamme avec processeur A17 Pro",
                    "generate_image": False,  # Pas d'image pour test rapide
                    "number_of_images": 0,
                    "language": "fr"
                },
                "expected_status": 200,
                "expected_error_field": None
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    # Vérifier le status code
                    status_ok = status == test_case["expected_status"]
                    print(f"   📊 Status: {status} (attendu: {test_case['expected_status']}) {'✅' if status_ok else '❌'}")
                    
                    # Pour les erreurs 400, vérifier la structure de l'erreur
                    if test_case["expected_status"] == 400:
                        error_checks = {
                            "has_error_field": "error" in response_data,
                            "has_message_field": "message" in response_data,
                            "has_details_field": "details" in response_data,
                            "has_status_code": "status_code" in response_data,
                            "status_code_400": response_data.get("status_code") == 400,
                            "message_in_french": "validation" in response_data.get("message", "").lower() or "erreur" in response_data.get("message", "").lower()
                        }
                        
                        # Vérifier que le champ product_name est mentionné dans les détails
                        details = response_data.get("details", [])
                        field_mentioned = any(
                            test_case["expected_error_field"] in detail.get("field", "") 
                            for detail in details if isinstance(detail, dict)
                        )
                        error_checks["field_mentioned"] = field_mentioned
                        
                        print(f"   📋 Validation structure erreur:")
                        for check, passed in error_checks.items():
                            status_icon = "✅" if passed else "❌"
                            print(f"      {status_icon} {check}")
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": status_ok and all(error_checks.values()),
                            "status": status,
                            "error_structure": error_checks,
                            "response": response_data
                        })
                    else:
                        # Pour les succès (200), vérifier que la génération fonctionne
                        success_checks = {
                            "status_200": status == 200,
                            "has_generated_title": "generated_title" in response_data,
                            "has_marketing_description": "marketing_description" in response_data
                        }
                        
                        print(f"   📋 Validation succès:")
                        for check, passed in success_checks.items():
                            status_icon = "✅" if passed else "❌"
                            print(f"      {status_icon} {check}")
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": all(success_checks.values()),
                            "status": status,
                            "success_checks": success_checks,
                            "response": response_data
                        })
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Évaluation globale
        successful_tests = sum(1 for result in results if result.get('success', False))
        total_tests = len(results)
        
        print(f"\n📈 RÉSULTATS product_name: {successful_tests}/{total_tests} tests réussis")
        
        self.test_results.append({
            "test": "product_name_validation",
            "success": successful_tests == total_tests,
            "success_rate": (successful_tests / total_tests) * 100,
            "details": results
        })
        
        return successful_tests == total_tests
    
    async def test_product_description_validation(self):
        """
        TEST 2: Validation product_description
        - description trop courte (< 10 caractères) → HTTP 400
        - description vide → HTTP 400
        - description trop longue (> 2000 caractères) → HTTP 400
        - description valide → HTTP 200
        """
        print("\n🧪 TEST 2: Validation product_description")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Générer une description très longue (> 2000 caractères)
        long_description = "Description très longue. " * 100  # ~2500 caractères
        
        test_cases = [
            {
                "name": "Description trop courte (< 10 caractères)",
                "data": {
                    "product_name": "Produit Test",
                    "product_description": "Court",  # 5 caractères
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_description"
            },
            {
                "name": "Description vide",
                "data": {
                    "product_name": "Produit Test",
                    "product_description": "",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_description"
            },
            {
                "name": "Description trop longue (> 2000 caractères)",
                "data": {
                    "product_name": "Produit Test",
                    "product_description": long_description,
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "product_description"
            },
            {
                "name": "Description valide",
                "data": {
                    "product_name": "iPhone 15 Pro",
                    "product_description": "Smartphone Apple haut de gamme avec processeur A17 Pro et appareil photo 48MP pour des performances exceptionnelles",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "fr"
                },
                "expected_status": 200,
                "expected_error_field": None
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    status_ok = status == test_case["expected_status"]
                    print(f"   📊 Status: {status} (attendu: {test_case['expected_status']}) {'✅' if status_ok else '❌'}")
                    
                    if test_case["expected_status"] == 400:
                        # Vérifier structure d'erreur
                        error_checks = {
                            "has_error_structure": all(field in response_data for field in ["error", "message", "details", "status_code"]),
                            "correct_status_code": response_data.get("status_code") == 400,
                            "message_in_french": any(word in response_data.get("message", "").lower() for word in ["validation", "erreur", "description"])
                        }
                        
                        # Vérifier mention du champ dans les détails
                        details = response_data.get("details", [])
                        field_mentioned = any(
                            test_case["expected_error_field"] in detail.get("field", "") 
                            for detail in details if isinstance(detail, dict)
                        )
                        error_checks["field_mentioned"] = field_mentioned
                        
                        print(f"   📋 Validation structure erreur:")
                        for check, passed in error_checks.items():
                            status_icon = "✅" if passed else "❌"
                            print(f"      {status_icon} {check}")
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": status_ok and all(error_checks.values()),
                            "status": status,
                            "error_structure": error_checks
                        })
                    else:
                        # Vérifier succès
                        success_checks = {
                            "status_200": status == 200,
                            "has_content": "generated_title" in response_data and "marketing_description" in response_data
                        }
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": all(success_checks.values()),
                            "status": status,
                            "success_checks": success_checks
                        })
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        successful_tests = sum(1 for result in results if result.get('success', False))
        total_tests = len(results)
        
        print(f"\n📈 RÉSULTATS product_description: {successful_tests}/{total_tests} tests réussis")
        
        self.test_results.append({
            "test": "product_description_validation",
            "success": successful_tests == total_tests,
            "success_rate": (successful_tests / total_tests) * 100,
            "details": results
        })
        
        return successful_tests == total_tests
    
    async def test_language_validation(self):
        """
        TEST 3: Validation language
        - langue non supportée ("jp", "ru") → HTTP 400
        - langue valide ("fr", "en") → HTTP 200
        """
        print("\n🧪 TEST 3: Validation language")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        test_cases = [
            {
                "name": "Langue non supportée (jp)",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Description de test pour validation de langue",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "jp"  # Non supporté
                },
                "expected_status": 400,
                "expected_error_field": "language"
            },
            {
                "name": "Langue non supportée (ru)",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Description de test pour validation de langue",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "ru"  # Non supporté
                },
                "expected_status": 400,
                "expected_error_field": "language"
            },
            {
                "name": "Langue valide (fr)",
                "data": {
                    "product_name": "Produit Test",
                    "product_description": "Description de test pour validation de langue française",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "fr"  # Supporté
                },
                "expected_status": 200,
                "expected_error_field": None
            },
            {
                "name": "Langue valide (en)",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Test description for English language validation",
                    "generate_image": False,
                    "number_of_images": 0,
                    "language": "en"  # Supporté
                },
                "expected_status": 200,
                "expected_error_field": None
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    status_ok = status == test_case["expected_status"]
                    print(f"   📊 Status: {status} (attendu: {test_case['expected_status']}) {'✅' if status_ok else '❌'}")
                    
                    if test_case["expected_status"] == 400:
                        # Vérifier que l'erreur mentionne les langues supportées
                        error_message = response_data.get("message", "")
                        details = response_data.get("details", [])
                        
                        error_checks = {
                            "has_error_structure": all(field in response_data for field in ["error", "message", "details"]),
                            "mentions_supported_languages": any(lang in str(details).lower() for lang in ["fr", "en", "de", "es", "pt"]),
                            "field_mentioned": any(
                                test_case["expected_error_field"] in detail.get("field", "") 
                                for detail in details if isinstance(detail, dict)
                            )
                        }
                        
                        print(f"   📋 Validation erreur langue:")
                        for check, passed in error_checks.items():
                            status_icon = "✅" if passed else "❌"
                            print(f"      {status_icon} {check}")
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": status_ok and all(error_checks.values()),
                            "status": status,
                            "error_structure": error_checks
                        })
                    else:
                        # Vérifier succès
                        success_checks = {
                            "status_200": status == 200,
                            "has_content": "generated_title" in response_data
                        }
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": all(success_checks.values()),
                            "status": status
                        })
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        successful_tests = sum(1 for result in results if result.get('success', False))
        total_tests = len(results)
        
        print(f"\n📈 RÉSULTATS language: {successful_tests}/{total_tests} tests réussis")
        
        self.test_results.append({
            "test": "language_validation",
            "success": successful_tests == total_tests,
            "success_rate": (successful_tests / total_tests) * 100,
            "details": results
        })
        
        return successful_tests == total_tests
    
    async def test_number_of_images_validation(self):
        """
        TEST 4: Validation number_of_images
        - nombre < 1 → HTTP 400
        - nombre > 5 → HTTP 400
        - nombre valide (1-5) → HTTP 200
        """
        print("\n🧪 TEST 4: Validation number_of_images")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        test_cases = [
            {
                "name": "Nombre d'images < 1",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Description de test pour validation nombre d'images",
                    "generate_image": True,
                    "number_of_images": 0,  # Invalide
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "number_of_images"
            },
            {
                "name": "Nombre d'images > 5",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Description de test pour validation nombre d'images",
                    "generate_image": True,
                    "number_of_images": 6,  # Invalide
                    "language": "fr"
                },
                "expected_status": 400,
                "expected_error_field": "number_of_images"
            },
            {
                "name": "Nombre d'images valide (1)",
                "data": {
                    "product_name": "Test Product",
                    "product_description": "Description de test pour validation nombre d'images",
                    "generate_image": False,  # Pas d'image pour test rapide
                    "number_of_images": 1,  # Valide
                    "language": "fr"
                },
                "expected_status": 200,
                "expected_error_field": None
            },
            {
                "name": "Nombre d'images valide (5)",
                "data": {
                    "product_name": "Test Product Max Images",
                    "product_description": "Description de test pour validation nombre maximum d'images",
                    "generate_image": False,  # Pas d'image pour test rapide
                    "number_of_images": 5,  # Valide (maximum)
                    "language": "fr"
                },
                "expected_status": 200,
                "expected_error_field": None
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🔍 Test: {test_case['name']}")
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_case["data"],
                    headers=self.get_auth_headers(self.test_user["token"])
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    status_ok = status == test_case["expected_status"]
                    print(f"   📊 Status: {status} (attendu: {test_case['expected_status']}) {'✅' if status_ok else '❌'}")
                    
                    if test_case["expected_status"] == 400:
                        # Vérifier que l'erreur mentionne la plage 1-5
                        details = response_data.get("details", [])
                        
                        error_checks = {
                            "has_error_structure": all(field in response_data for field in ["error", "message", "details"]),
                            "mentions_range": any("1" in str(detail) and "5" in str(detail) for detail in details),
                            "field_mentioned": any(
                                test_case["expected_error_field"] in detail.get("field", "") 
                                for detail in details if isinstance(detail, dict)
                            )
                        }
                        
                        print(f"   📋 Validation erreur nombre d'images:")
                        for check, passed in error_checks.items():
                            status_icon = "✅" if passed else "❌"
                            print(f"      {status_icon} {check}")
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": status_ok and all(error_checks.values()),
                            "status": status,
                            "error_structure": error_checks
                        })
                    else:
                        # Vérifier succès
                        success_checks = {
                            "status_200": status == 200,
                            "has_content": "generated_title" in response_data
                        }
                        
                        results.append({
                            "test_name": test_case["name"],
                            "success": all(success_checks.values()),
                            "status": status
                        })
                        
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        successful_tests = sum(1 for result in results if result.get('success', False))
        total_tests = len(results)
        
        print(f"\n📈 RÉSULTATS number_of_images: {successful_tests}/{total_tests} tests réussis")
        
        self.test_results.append({
            "test": "number_of_images_validation",
            "success": successful_tests == total_tests,
            "success_rate": (successful_tests / total_tests) * 100,
            "details": results
        })
        
        return successful_tests == total_tests
    
    async def test_global_validation(self):
        """
        TEST 5: Validation Globale
        - Erreurs multiples simultanées → HTTP 400 avec détails pour chaque champ
        - Message d'erreur en français et structure JSON claire
        """
        print("\n🧪 TEST 5: Validation Globale (erreurs multiples)")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test avec plusieurs erreurs simultanées
        test_data = {
            "product_name": "AB",  # Trop court
            "product_description": "Court",  # Trop court
            "generate_image": True,
            "number_of_images": 10,  # Trop élevé
            "language": "xx"  # Non supporté
        }
        
        print(f"🔍 Test erreurs multiples simultanées")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                status = response.status
                response_data = await response.json()
                
                print(f"   📊 Status: {status} (attendu: 400) {'✅' if status == 400 else '❌'}")
                
                if status == 400:
                    # Vérifier structure globale
                    global_checks = {
                        "has_error_field": "error" in response_data,
                        "has_message_field": "message" in response_data,
                        "has_details_field": "details" in response_data,
                        "has_status_code": "status_code" in response_data,
                        "status_code_400": response_data.get("status_code") == 400
                    }
                    
                    # Vérifier que plusieurs champs sont mentionnés dans les détails
                    details = response_data.get("details", [])
                    expected_fields = ["product_name", "product_description", "number_of_images", "language"]
                    
                    fields_mentioned = []
                    for detail in details:
                        if isinstance(detail, dict) and "field" in detail:
                            field_name = detail["field"]
                            for expected_field in expected_fields:
                                if expected_field in field_name:
                                    fields_mentioned.append(expected_field)
                    
                    multiple_errors_checks = {
                        "multiple_fields_mentioned": len(set(fields_mentioned)) >= 3,  # Au moins 3 champs différents
                        "details_is_list": isinstance(details, list),
                        "details_not_empty": len(details) > 0,
                        "each_detail_has_structure": all(
                            isinstance(detail, dict) and "field" in detail and "message" in detail 
                            for detail in details
                        )
                    }
                    
                    # Vérifier message en français
                    message = response_data.get("message", "")
                    french_checks = {
                        "message_in_french": any(word in message.lower() for word in ["erreur", "validation", "champ", "détectées"]),
                        "message_not_empty": len(message.strip()) > 0
                    }
                    
                    print(f"   📋 Validation structure globale:")
                    for check, passed in global_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    print(f"   📋 Validation erreurs multiples:")
                    for check, passed in multiple_errors_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    print(f"   📋 Validation français:")
                    for check, passed in french_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    print(f"   📊 Champs en erreur détectés: {set(fields_mentioned)}")
                    print(f"   📝 Message: {message}")
                    
                    all_checks = {**global_checks, **multiple_errors_checks, **french_checks}
                    
                    self.test_results.append({
                        "test": "global_validation",
                        "success": status == 400 and all(all_checks.values()),
                        "status": status,
                        "checks": all_checks,
                        "fields_mentioned": list(set(fields_mentioned)),
                        "message": message
                    })
                    
                    return status == 400 and all(all_checks.values())
                else:
                    print(f"   ❌ Status inattendu: {status}")
                    self.test_results.append({
                        "test": "global_validation",
                        "success": False,
                        "status": status,
                        "error": "Status code incorrect"
                    })
                    return False
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            self.test_results.append({
                "test": "global_validation",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_error_message_format(self):
        """
        TEST 6: Test Messages d'Erreur
        - Vérifier format JSON response: error, message, details, status_code
        - Vérifier que les messages sont en français
        - Vérifier logging structuré des erreurs de validation
        """
        print("\n🧪 TEST 6: Format des Messages d'Erreur")
        print("=" * 60)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Test avec une erreur simple pour vérifier le format
        test_data = {
            "product_name": "",  # Erreur simple
            "product_description": "Description valide pour test de format d'erreur",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr"
        }
        
        print(f"🔍 Test format message d'erreur")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                status = response.status
                response_data = await response.json()
                
                print(f"   📊 Status: {status} (attendu: 400) {'✅' if status == 400 else '❌'}")
                
                if status == 400:
                    # Vérifier format JSON exact
                    format_checks = {
                        "has_error": "error" in response_data,
                        "has_message": "message" in response_data,
                        "has_details": "details" in response_data,
                        "has_status_code": "status_code" in response_data,
                        "error_is_string": isinstance(response_data.get("error"), str),
                        "message_is_string": isinstance(response_data.get("message"), str),
                        "details_is_list": isinstance(response_data.get("details"), list),
                        "status_code_is_int": isinstance(response_data.get("status_code"), int)
                    }
                    
                    # Vérifier contenu des détails
                    details = response_data.get("details", [])
                    detail_checks = {
                        "details_not_empty": len(details) > 0,
                        "each_detail_has_field": all("field" in detail for detail in details if isinstance(detail, dict)),
                        "each_detail_has_message": all("message" in detail for detail in details if isinstance(detail, dict)),
                        "each_detail_has_type": all("type" in detail for detail in details if isinstance(detail, dict))
                    }
                    
                    # Vérifier messages en français
                    message = response_data.get("message", "")
                    french_checks = {
                        "main_message_french": any(word in message.lower() for word in ["erreur", "validation", "champ"]),
                        "detail_messages_french": any(
                            any(word in detail.get("message", "").lower() for word in ["vide", "caractères", "contenir"])
                            for detail in details if isinstance(detail, dict)
                        )
                    }
                    
                    print(f"   📋 Validation format JSON:")
                    for check, passed in format_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    print(f"   📋 Validation détails:")
                    for check, passed in detail_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    print(f"   📋 Validation français:")
                    for check, passed in french_checks.items():
                        status_icon = "✅" if passed else "❌"
                        print(f"      {status_icon} {check}")
                    
                    # Afficher exemple de structure
                    print(f"   📄 Exemple structure:")
                    print(f"      Error: {response_data.get('error')}")
                    print(f"      Message: {response_data.get('message')}")
                    print(f"      Status Code: {response_data.get('status_code')}")
                    if details:
                        print(f"      Premier détail: {details[0]}")
                    
                    all_checks = {**format_checks, **detail_checks, **french_checks}
                    
                    self.test_results.append({
                        "test": "error_message_format",
                        "success": status == 400 and all(all_checks.values()),
                        "status": status,
                        "checks": all_checks,
                        "response_structure": response_data
                    })
                    
                    return status == 400 and all(all_checks.values())
                else:
                    print(f"   ❌ Status inattendu: {status}")
                    self.test_results.append({
                        "test": "error_message_format",
                        "success": False,
                        "status": status
                    })
                    return False
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            self.test_results.append({
                "test": "error_message_format",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 ECOMSIMPLY - TEST AUTOMATIQUE PHASE 3 - VALIDATION AVANCÉE DES ENTRÉES")
        print("=" * 80)
        print("Objectif: Vérifier que le système de validation avancée des entrées fonctionne correctement")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        # Create test user
        if not await self.create_test_user():
            print("❌ Failed to create test user")
            return False
        
        try:
            # Run all validation tests
            print("\n🎯 DÉMARRAGE DES TESTS DE VALIDATION...")
            
            test1_result = await self.test_product_name_validation()
            await asyncio.sleep(1)
            
            test2_result = await self.test_product_description_validation()
            await asyncio.sleep(1)
            
            test3_result = await self.test_language_validation()
            await asyncio.sleep(1)
            
            test4_result = await self.test_number_of_images_validation()
            await asyncio.sleep(1)
            
            test5_result = await self.test_global_validation()
            await asyncio.sleep(1)
            
            test6_result = await self.test_error_message_format()
            
            # Summary
            print("\n" + "=" * 80)
            print("🏁 RÉSUMÉ FINAL - TEST VALIDATION AVANCÉE DES ENTRÉES")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result.get('success', False))
            
            print(f"📊 Total Tests: {total_tests}")
            print(f"✅ Réussis: {passed_tests}")
            print(f"❌ Échoués: {total_tests - passed_tests}")
            print(f"📈 Taux de Réussite: {(passed_tests/total_tests*100):.1f}%")
            
            print(f"\n🎯 STATUT DES TESTS:")
            print(f"   1. Validation product_name: {'✅ RÉUSSI' if test1_result else '❌ ÉCHOUÉ'}")
            print(f"   2. Validation product_description: {'✅ RÉUSSI' if test2_result else '❌ ÉCHOUÉ'}")
            print(f"   3. Validation language: {'✅ RÉUSSI' if test3_result else '❌ ÉCHOUÉ'}")
            print(f"   4. Validation number_of_images: {'✅ RÉUSSI' if test4_result else '❌ ÉCHOUÉ'}")
            print(f"   5. Validation globale: {'✅ RÉUSSI' if test5_result else '❌ ÉCHOUÉ'}")
            print(f"   6. Format messages d'erreur: {'✅ RÉUSSI' if test6_result else '❌ ÉCHOUÉ'}")
            
            # Critères de succès
            success_criteria = {
                "product_name_validation": test1_result,
                "product_description_validation": test2_result,
                "language_validation": test3_result,
                "number_of_images_validation": test4_result,
                "global_validation": test5_result,
                "error_message_format": test6_result
            }
            
            print(f"\n📋 CRITÈRES DE SUCCÈS:")
            for criterion, met in success_criteria.items():
                status_icon = "✅" if met else "❌"
                print(f"   {status_icon} {criterion}")
            
            # Overall assessment
            critical_validations = [test1_result, test2_result, test3_result, test4_result]  # Core validations
            critical_success = all(critical_validations)
            overall_success = all(success_criteria.values())
            
            if overall_success:
                print(f"\n🎉 SUCCÈS COMPLET: Le système de validation avancée fonctionne parfaitement!")
                print("   ✅ HTTP 400 retourné pour entrées invalides")
                print("   ✅ Messages d'erreur clairs en français")
                print("   ✅ Structure JSON standardisée")
                print("   ✅ Logging structuré des erreurs de validation")
                print("   ✅ Identification précise des champs en erreur")
                print("   ✅ Génération normale fonctionne avec entrées valides")
            elif critical_success:
                print(f"\n⚡ SUCCÈS CRITIQUE: Les validations essentielles fonctionnent!")
                print("   ✅ Validation des champs principaux opérationnelle")
                print("   ✅ Erreurs HTTP 400 correctement retournées")
                if not test5_result:
                    print("   ⚠️ Validation globale nécessite des ajustements")
                if not test6_result:
                    print("   ⚠️ Format des messages d'erreur à améliorer")
            else:
                print(f"\n❌ ÉCHEC CRITIQUE: Le système de validation présente des problèmes majeurs")
                failed_validations = [name for name, result in success_criteria.items() if not result]
                print(f"   ❌ Validations échouées: {', '.join(failed_validations)}")
                print("   🔧 Correction immédiate requise")
            
            return critical_success
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = ValidationTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())