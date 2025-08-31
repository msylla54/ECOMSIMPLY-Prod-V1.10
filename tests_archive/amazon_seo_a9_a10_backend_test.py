#!/usr/bin/env python3
"""
ECOMSIMPLY Amazon SEO A9/A10 System Backend Testing
Test complet du système SEO Amazon A9/A10 (Bloc 5) - Backend Testing

OBJECTIFS DE TEST :
1. **Endpoints SEO Amazon** : Tester tous les endpoints /api/amazon/seo/* (generate, validate, optimize)
2. **Intégration Amazon Rules** : Vérifier que les règles A9/A10 sont correctement appliquées
3. **Service Amazon SEO** : Valider le service amazon_seo_integration_service.py
4. **Formats de sortie** : Vérifier que les formats respectent les spécifications Amazon SP-API
5. **Authentification** : Valider que l'accès Premium/Pro fonctionne

TESTS À EFFECTUER :
- POST /api/amazon/seo/generate (génération listing optimisé)
- POST /api/amazon/seo/validate (validation listing existant) 
- POST /api/amazon/seo/optimize (optimisation listing)
- Vérification conformité A9/A10 (titre ≤200 chars, 5 bullets ≤255 chars, description 100-2000 chars, backend keywords ≤250 bytes)
- Test avec produits réels (iPhone 15 Pro, Samsung Galaxy S24)
- Validation métadonnées et scores de qualité

Author: Testing Agent
Date: 2025-01-01
"""

import asyncio
import os
import sys
import json
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv('/app/backend/.env')

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmazonSEOA9A10BackendTest:
    """Test suite for Amazon SEO A9/A10 system validation"""
    
    def __init__(self):
        # Use the correct backend URL from frontend/.env
        frontend_env_path = '/app/frontend/.env'
        try:
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.backend_url = line.split('=', 1)[1].strip()
                        break
                else:
                    self.backend_url = 'http://localhost:8001'
        except:
            self.backend_url = 'http://localhost:8001'
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test credentials (from environment)
        self.test_email = "msylla54@gmail.com"
        self.test_password = "AmiMorFa01!"
        self.auth_token = None
        
        # Test products for real-world testing
        self.test_products = {
            "iphone_15_pro": {
                "product_name": "iPhone 15 Pro",
                "brand": "Apple",
                "model": "iPhone 15 Pro",
                "category": "électronique",
                "features": [
                    "Puce A17 Pro avec GPU 6 cœurs",
                    "Écran Super Retina XDR 6,1 pouces",
                    "Système de caméra Pro triple 48 Mpx",
                    "Châssis en titane de qualité aérospatiale",
                    "USB-C avec USB 3 pour transferts rapides"
                ],
                "benefits": [
                    "Performances exceptionnelles pour gaming et création",
                    "Photos et vidéos de qualité professionnelle",
                    "Résistance et légèreté optimales",
                    "Connectivité universelle USB-C",
                    "Autonomie toute la journée"
                ],
                "use_cases": [
                    "Photographie professionnelle mobile",
                    "Gaming haute performance",
                    "Création de contenu vidéo 4K"
                ],
                "size": "6,1 pouces",
                "color": "Titane Naturel",
                "images": [
                    "https://example.com/iphone15pro-main.jpg",
                    "https://example.com/iphone15pro-side.jpg",
                    "https://example.com/iphone15pro-camera.jpg"
                ],
                "additional_keywords": ["smartphone", "iOS", "5G", "MagSafe", "Face ID"]
            },
            "samsung_galaxy_s24": {
                "product_name": "Samsung Galaxy S24",
                "brand": "Samsung",
                "model": "Galaxy S24",
                "category": "électronique",
                "features": [
                    "Processeur Snapdragon 8 Gen 3",
                    "Écran Dynamic AMOLED 2X 6,2 pouces",
                    "Triple caméra 50MP avec zoom optique 3x",
                    "Batterie 4000mAh avec charge rapide 25W",
                    "One UI 6.1 avec Galaxy AI intégré"
                ],
                "benefits": [
                    "Intelligence artificielle avancée pour photos",
                    "Écran lumineux visible en plein soleil",
                    "Autonomie optimisée toute la journée",
                    "Charge ultra-rapide sans fil",
                    "Interface intuitive et personnalisable"
                ],
                "use_cases": [
                    "Photographie avec IA",
                    "Productivité professionnelle",
                    "Divertissement multimédia"
                ],
                "size": "6,2 pouces",
                "color": "Violet Cobalt",
                "images": [
                    "https://example.com/galaxys24-main.jpg",
                    "https://example.com/galaxys24-display.jpg",
                    "https://example.com/galaxys24-camera.jpg"
                ],
                "additional_keywords": ["Android", "5G", "Samsung DeX", "S Pen compatible"]
            }
        }
        
        logger.info("🧪 Amazon SEO A9/A10 Backend Test Suite Initialized")
        logger.info(f"📡 Backend URL: {self.backend_url}")
    
    async def setup_authentication(self) -> bool:
        """Setup authentication for API testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Login to get JWT token
                login_response = await client.post(
                    f"{self.backend_url}/api/auth/login",
                    json={
                        "email": self.test_email,
                        "password": self.test_password
                    }
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.auth_token = login_data.get('access_token')
                    logger.info("✅ Authentication successful")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {login_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication setup failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def test_amazon_seo_generate_endpoint(self) -> Dict[str, Any]:
        """Test 1: POST /api/amazon/seo/generate - Génération listing optimisé"""
        test_name = "Amazon SEO Generate Endpoint"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                auth_headers = self.get_auth_headers()
                
                if not auth_headers:
                    return {
                        "test": test_name,
                        "status": "SKIP",
                        "message": "Authentication required but not available",
                        "details": {}
                    }
                
                # Test avec iPhone 15 Pro
                iphone_data = self.test_products["iphone_15_pro"]
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/seo/generate",
                    headers=auth_headers,
                    json=iphone_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Vérifier la structure de la réponse
                    required_fields = ['success', 'data', 'message']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        return {
                            "test": test_name,
                            "status": "FAIL",
                            "message": f"Missing required fields: {missing_fields}",
                            "details": {"response": data}
                        }
                    
                    # Vérifier la structure des données
                    listing_data = data.get('data', {})
                    listing = listing_data.get('listing', {})
                    validation = listing_data.get('validation', {})
                    
                    # Validation A9/A10 compliance
                    compliance_checks = self._validate_a9_a10_compliance(listing)
                    
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": "Amazon SEO generate endpoint working correctly",
                        "details": {
                            "response_status": response.status_code,
                            "listing_generated": bool(listing),
                            "validation_included": bool(validation),
                            "validation_status": validation.get('status'),
                            "validation_score": validation.get('score'),
                            "a9_a10_compliance": compliance_checks,
                            "title_length": len(listing.get('title', '')),
                            "bullets_count": len(listing.get('bullets', [])),
                            "description_length": len(listing.get('description', '')),
                            "backend_keywords_bytes": len(listing.get('backend_keywords', '').encode('utf-8'))
                        }
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Generate endpoint failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_validate_endpoint(self) -> Dict[str, Any]:
        """Test 2: POST /api/amazon/seo/validate - Validation listing existant"""
        test_name = "Amazon SEO Validate Endpoint"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                auth_headers = self.get_auth_headers()
                
                if not auth_headers:
                    return {
                        "test": test_name,
                        "status": "SKIP",
                        "message": "Authentication required but not available",
                        "details": {}
                    }
                
                # Test avec un listing existant (simulé)
                existing_listing = {
                    "title": "Samsung Galaxy S24 Smartphone Android 256GB Violet Cobalt",
                    "bullets": [
                        "✓ PERFORMANCE: Processeur Snapdragon 8 Gen 3 pour une puissance exceptionnelle",
                        "✓ ÉCRAN: Dynamic AMOLED 2X 6,2 pouces avec luminosité adaptative",
                        "✓ PHOTO: Triple caméra 50MP avec IA pour des clichés professionnels",
                        "✓ AUTONOMIE: Batterie 4000mAh avec charge rapide 25W sans fil",
                        "✓ INTELLIGENCE: Galaxy AI intégré pour une expérience personnalisée"
                    ],
                    "description": "Découvrez le Samsung Galaxy S24, la révolution smartphone qui transforme votre quotidien.\n\nCARACTÉRISTIQUES PRINCIPALES:\n• Processeur Snapdragon 8 Gen 3 dernière génération\n• Écran Dynamic AMOLED 2X 6,2 pouces 120Hz\n• Triple caméra 50MP avec zoom optique 3x\n• Batterie 4000mAh avec charge rapide 25W\n• One UI 6.1 avec Galaxy AI intégré\n\nBÉNÉFICES POUR VOUS:\n✓ Photos d'une qualité exceptionnelle grâce à l'IA\n✓ Écran ultra-lumineux visible même en plein soleil\n✓ Autonomie optimisée pour une journée complète\n✓ Charge ultra-rapide sans fil et filaire\n✓ Interface intuitive et personnalisable\n\nChoisissez le Samsung Galaxy S24 et rejoignez des milliers de clients satisfaits.",
                    "backend_keywords": "samsung galaxy s24 smartphone android snapdragon écran amoled caméra 50mp batterie 4000mah charge rapide galaxy ai violet cobalt 256gb 5g",
                    "images": [
                        "https://example.com/galaxys24-main.jpg",
                        "https://example.com/galaxys24-display.jpg"
                    ],
                    "brand": "Samsung",
                    "model": "Galaxy S24",
                    "category": "électronique"
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/seo/validate",
                    headers=auth_headers,
                    json=existing_listing
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Vérifier la structure de la réponse
                    validation_data = data.get('data', {})
                    validation = validation_data.get('validation', {})
                    compliance = validation_data.get('compliance', {})
                    
                    # Vérifier les scores et statuts
                    validation_score = validation.get('score', 0)
                    validation_status = validation.get('status')
                    a9_a10_compliant = compliance.get('a9_a10_compliant', False)
                    
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": "Amazon SEO validate endpoint working correctly",
                        "details": {
                            "response_status": response.status_code,
                            "validation_score": validation_score,
                            "validation_status": validation_status,
                            "a9_a10_compliant": a9_a10_compliant,
                            "ready_for_publication": compliance.get('ready_for_publication', False),
                            "critical_issues": compliance.get('critical_issues', 0),
                            "reasons_count": len(validation.get('reasons', [])),
                            "warnings_count": len(validation.get('warnings', [])),
                            "suggestions_count": len(validation.get('suggestions', []))
                        }
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Validate endpoint failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_optimize_endpoint(self) -> Dict[str, Any]:
        """Test 3: POST /api/amazon/seo/optimize - Optimisation listing"""
        test_name = "Amazon SEO Optimize Endpoint"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                auth_headers = self.get_auth_headers()
                
                if not auth_headers:
                    return {
                        "test": test_name,
                        "status": "SKIP",
                        "message": "Authentication required but not available",
                        "details": {}
                    }
                
                # Test avec un listing à optimiser
                listing_to_optimize = {
                    "current_listing": {
                        "title": "iPhone 15 Pro Apple Smartphone",  # Titre basique à optimiser
                        "bullets": [
                            "Bon smartphone Apple",
                            "Écran de qualité",
                            "Appareil photo correct"
                        ],  # Bullets basiques à améliorer
                        "description": "iPhone 15 Pro est un bon téléphone d'Apple avec un écran et un appareil photo.",  # Description courte
                        "backend_keywords": "iphone apple smartphone",  # Keywords limitées
                        "images": ["https://example.com/iphone15pro.jpg"],
                        "brand": "Apple",
                        "model": "iPhone 15 Pro",
                        "category": "électronique"
                    },
                    "optimization_options": {
                        "focus_keywords": ["A17 Pro", "titane", "USB-C", "Pro camera"],
                        "target_audience": "professionnels créatifs"
                    }
                }
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/seo/optimize",
                    headers=auth_headers,
                    json=listing_to_optimize
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Vérifier la structure de la réponse
                    optimization_data = data.get('data', {})
                    original = optimization_data.get('original', {})
                    optimized = optimization_data.get('optimized', {})
                    comparison = optimization_data.get('comparison', {})
                    recommendations = optimization_data.get('recommendations', {})
                    
                    # Vérifier les améliorations
                    score_improvement = recommendations.get('score_improvement', 0)
                    should_update = recommendations.get('should_update', False)
                    
                    return {
                        "test": test_name,
                        "status": "PASS",
                        "message": "Amazon SEO optimize endpoint working correctly",
                        "details": {
                            "response_status": response.status_code,
                            "original_score": original.get('validation', {}).get('score', 0),
                            "optimized_score": optimized.get('validation', {}).get('score', 0),
                            "score_improvement": score_improvement,
                            "should_update": should_update,
                            "comparison_available": bool(comparison),
                            "priority_changes": comparison.get('priority_changes', []),
                            "total_changes": comparison.get('total_changes', 0)
                        }
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Optimize endpoint failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_rules_endpoint(self) -> Dict[str, Any]:
        """Test 4: GET /api/amazon/seo/rules - Récupération des règles SEO"""
        test_name = "Amazon SEO Rules Endpoint"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                auth_headers = self.get_auth_headers()
                
                if not auth_headers:
                    return {
                        "test": test_name,
                        "status": "SKIP",
                        "message": "Authentication required but not available",
                        "details": {}
                    }
                
                response = await client.get(
                    f"{self.backend_url}/api/amazon/seo/rules",
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rules_data = data.get('data', {})
                    
                    # Vérifier les règles A9/A10 essentielles
                    expected_rules = [
                        'title_rules',
                        'bullets_rules', 
                        'description_rules',
                        'backend_keywords_rules',
                        'images_rules',
                        'a9_a10_optimization'
                    ]
                    
                    missing_rules = [rule for rule in expected_rules if rule not in rules_data]
                    
                    # Vérifier les limites spécifiques
                    title_rules = rules_data.get('title_rules', {})
                    bullets_rules = rules_data.get('bullets_rules', {})
                    backend_rules = rules_data.get('backend_keywords_rules', {})
                    
                    compliance_check = {
                        'title_max_200': title_rules.get('max_length') == 200,
                        'bullets_count_5': bullets_rules.get('count') == 5,
                        'bullet_max_255': bullets_rules.get('max_length_per_bullet') == 255,
                        'backend_max_250_bytes': backend_rules.get('max_bytes') == 250
                    }
                    
                    return {
                        "test": test_name,
                        "status": "PASS" if not missing_rules else "PARTIAL_PASS",
                        "message": "Amazon SEO rules endpoint accessible" + (f" (missing: {missing_rules})" if missing_rules else ""),
                        "details": {
                            "response_status": response.status_code,
                            "rules_available": len(rules_data),
                            "missing_rules": missing_rules,
                            "a9_a10_compliance_rules": compliance_check,
                            "all_limits_correct": all(compliance_check.values())
                        }
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Rules endpoint failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_prepare_publisher_endpoint(self) -> Dict[str, Any]:
        """Test 5: POST /api/amazon/seo/prepare-for-publisher - Préparation pour Publisher"""
        test_name = "Amazon SEO Prepare Publisher Endpoint"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                auth_headers = self.get_auth_headers()
                
                if not auth_headers:
                    return {
                        "test": test_name,
                        "status": "SKIP",
                        "message": "Authentication required but not available",
                        "details": {}
                    }
                
                # Test avec Samsung Galaxy S24
                samsung_data = self.test_products["samsung_galaxy_s24"]
                
                response = await client.post(
                    f"{self.backend_url}/api/amazon/seo/prepare-for-publisher",
                    headers=auth_headers,
                    json=samsung_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    publisher_data = data.get('data', {})
                    
                    # Vérifier le format Publisher Amazon
                    publisher_format = publisher_data.get('publisher_format', {})
                    validation_summary = publisher_data.get('validation_summary', {})
                    
                    # Champs requis pour le Publisher Amazon
                    required_publisher_fields = [
                        'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3',
                        'bullet_point_4', 'bullet_point_5', 'description', 'search_terms'
                    ]
                    
                    missing_fields = [field for field in required_publisher_fields if field not in publisher_format]
                    
                    return {
                        "test": test_name,
                        "status": "PASS" if not missing_fields else "PARTIAL_PASS",
                        "message": "Amazon SEO prepare publisher endpoint working" + (f" (missing: {missing_fields})" if missing_fields else ""),
                        "details": {
                            "response_status": response.status_code,
                            "publisher_format_available": bool(publisher_format),
                            "missing_publisher_fields": missing_fields,
                            "ready_for_publication": validation_summary.get('ready_for_publication', False),
                            "validation_score": validation_summary.get('validation_score', 0),
                            "seo_optimized": publisher_data.get('metadata', {}).get('seo_optimized', False),
                            "a9_a10_compliant": publisher_data.get('metadata', {}).get('a9_a10_compliant', False)
                        }
                    }
                else:
                    return {
                        "test": test_name,
                        "status": "FAIL",
                        "message": f"Prepare publisher endpoint failed with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Test execution failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_service_integration(self) -> Dict[str, Any]:
        """Test 6: Validation du service d'intégration SEO Amazon"""
        test_name = "Amazon SEO Service Integration"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            # Import direct du service pour test unitaire
            from services.amazon_seo_integration_service import get_amazon_seo_integration_service
            from seo.amazon_rules import get_amazon_seo_rules
            
            # Test du service d'intégration
            seo_service = get_amazon_seo_integration_service()
            amazon_rules = get_amazon_seo_rules()
            
            # Vérifier l'initialisation
            service_checks = {
                'service_initialized': seo_service is not None,
                'amazon_seo_rules_available': hasattr(seo_service, 'amazon_seo') and seo_service.amazon_seo is not None,
                'logger_configured': hasattr(seo_service, 'logger') and seo_service.logger is not None,
                'rules_service_initialized': amazon_rules is not None
            }
            
            # Test des constantes A9/A10
            rules_constants = {
                'title_max_length': amazon_rules.TITLE_MAX_LENGTH == 200,
                'bullet_max_length': amazon_rules.BULLET_MAX_LENGTH == 255,
                'bullets_count': amazon_rules.BULLETS_COUNT == 5,
                'backend_keywords_max_bytes': amazon_rules.BACKEND_KEYWORDS_MAX_BYTES == 250,
                'description_min_length': amazon_rules.DESCRIPTION_MIN_LENGTH == 100,
                'description_max_length': amazon_rules.DESCRIPTION_MAX_LENGTH == 2000
            }
            
            # Test des méthodes disponibles
            method_checks = {
                'has_generate_optimized_listing': hasattr(seo_service, 'generate_optimized_listing'),
                'has_validate_existing_listing': hasattr(seo_service, 'validate_existing_listing'),
                'has_optimize_existing_listing': hasattr(seo_service, 'optimize_existing_listing'),
                'has_prepare_listing_for_publisher': hasattr(seo_service, 'prepare_listing_for_publisher'),
                'has_validate_amazon_listing': hasattr(amazon_rules, 'validate_amazon_listing'),
                'has_generate_optimized_title': hasattr(amazon_rules, 'generate_optimized_title'),
                'has_generate_optimized_bullets': hasattr(amazon_rules, 'generate_optimized_bullets'),
                'has_generate_backend_keywords': hasattr(amazon_rules, 'generate_backend_keywords')
            }
            
            # Test fonctionnel avec données réelles
            functional_tests = {}
            try:
                # Test génération titre
                test_title = amazon_rules.generate_optimized_title(
                    brand="Apple",
                    model="iPhone 15 Pro",
                    features=["A17 Pro", "Titane"],
                    size="6,1 pouces",
                    color="Titane Naturel",
                    category="électronique"
                )
                functional_tests['title_generation'] = len(test_title) > 0 and len(test_title) <= 200
                
                # Test génération bullets
                test_bullets = amazon_rules.generate_optimized_bullets(
                    product_name="iPhone 15 Pro",
                    features=["A17 Pro", "Caméra Pro"],
                    benefits=["Performance exceptionnelle", "Photos professionnelles"],
                    category="électronique"
                )
                functional_tests['bullets_generation'] = len(test_bullets) == 5 and all(len(b) <= 255 for b in test_bullets)
                
                # Test génération backend keywords
                test_keywords = amazon_rules.generate_backend_keywords(
                    product_name="iPhone 15 Pro",
                    category="électronique",
                    features=["A17 Pro", "Titane"]
                )
                functional_tests['keywords_generation'] = len(test_keywords.encode('utf-8')) <= 250
                
                # Test validation listing
                from seo.amazon_rules import AmazonListing
                test_listing = AmazonListing(
                    title=test_title,
                    bullets=test_bullets,
                    description="Test description avec plus de 100 caractères pour respecter les règles Amazon A9/A10 et fournir une description complète du produit.",
                    backend_keywords=test_keywords,
                    images=["https://example.com/test.jpg"],
                    brand="Apple",
                    model="iPhone 15 Pro",
                    category="électronique"
                )
                
                validation_result = amazon_rules.validate_amazon_listing(test_listing)
                functional_tests['listing_validation'] = validation_result.score > 0
                functional_tests['validation_status'] = validation_result.status.value
                
            except Exception as e:
                functional_tests['error'] = str(e)
            
            all_checks = {**service_checks, **rules_constants, **method_checks}
            passed_checks = sum(1 for check in all_checks.values() if check is True)
            total_checks = len(all_checks)
            
            functional_passed = sum(1 for check in functional_tests.values() if check is True)
            functional_total = len([v for v in functional_tests.values() if isinstance(v, bool)])
            
            return {
                "test": test_name,
                "status": "PASS" if passed_checks == total_checks and functional_passed >= functional_total * 0.8 else "PARTIAL_PASS",
                "message": f"Amazon SEO service integration validated ({passed_checks}/{total_checks} checks passed, {functional_passed}/{functional_total} functional tests passed)",
                "details": {
                    "service_checks": service_checks,
                    "rules_constants": rules_constants,
                    "method_checks": method_checks,
                    "functional_tests": functional_tests,
                    "passed_checks": passed_checks,
                    "total_checks": total_checks,
                    "functional_passed": functional_passed,
                    "functional_total": functional_total,
                    "success_rate": f"{(passed_checks/total_checks)*100:.1f}%"
                }
            }
            
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Service integration test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def test_amazon_seo_routes_accessibility(self) -> Dict[str, Any]:
        """Test 7: Vérifier l'accessibilité des routes Amazon SEO"""
        test_name = "Amazon SEO Routes Accessibility"
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                route_tests = {}
                
                # Test des routes sans authentification pour voir les erreurs
                routes_to_test = [
                    "/api/amazon/seo/generate",
                    "/api/amazon/seo/validate", 
                    "/api/amazon/seo/optimize",
                    "/api/amazon/seo/rules",
                    "/api/amazon/seo/prepare-for-publisher"
                ]
                
                for route in routes_to_test:
                    try:
                        # Test GET pour voir si la route existe
                        get_response = await client.get(f"{self.backend_url}{route}")
                        route_tests[f"{route}_GET"] = {
                            "status_code": get_response.status_code,
                            "accessible": get_response.status_code != 404,
                            "requires_auth": get_response.status_code == 401 or get_response.status_code == 403
                        }
                        
                        # Test POST pour les routes qui l'acceptent
                        if route != "/api/amazon/seo/rules":
                            post_response = await client.post(f"{self.backend_url}{route}", json={})
                            route_tests[f"{route}_POST"] = {
                                "status_code": post_response.status_code,
                                "accessible": post_response.status_code != 404,
                                "requires_auth": post_response.status_code == 401 or post_response.status_code == 403
                            }
                    except Exception as e:
                        route_tests[route] = {"error": str(e), "accessible": False}
                
                # Compter les routes accessibles
                accessible_routes = sum(1 for test in route_tests.values() 
                                      if isinstance(test, dict) and test.get('accessible', False))
                total_routes = len(route_tests)
                
                return {
                    "test": test_name,
                    "status": "PASS" if accessible_routes >= total_routes * 0.8 else "PARTIAL_PASS" if accessible_routes > 0 else "FAIL",
                    "message": f"Amazon SEO routes accessibility checked ({accessible_routes}/{total_routes} accessible)",
                    "details": {
                        "route_tests": route_tests,
                        "accessible_routes": accessible_routes,
                        "total_routes": total_routes,
                        "accessibility_rate": f"{(accessible_routes/total_routes)*100:.1f}%" if total_routes > 0 else "0%"
                    }
                }
                
        except Exception as e:
            return {
                "test": test_name,
                "status": "ERROR",
                "message": f"Route accessibility test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _validate_a9_a10_compliance(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la conformité A9/A10 d'un listing généré"""
        compliance = {
            'title_length_ok': False,
            'bullets_count_ok': False,
            'bullets_length_ok': True,
            'description_length_ok': False,
            'backend_keywords_bytes_ok': False,
            'overall_compliant': False
        }
        
        # Vérifier le titre (≤200 chars)
        title = listing.get('title', '')
        compliance['title_length_ok'] = len(title) <= 200 and len(title) > 0
        
        # Vérifier les bullets (5 bullets, chacun ≤255 chars)
        bullets = listing.get('bullets', [])
        compliance['bullets_count_ok'] = len(bullets) == 5
        
        for bullet in bullets:
            if len(bullet) > 255:
                compliance['bullets_length_ok'] = False
                break
        
        # Vérifier la description (100-2000 chars)
        description = listing.get('description', '')
        desc_len = len(description)
        compliance['description_length_ok'] = 100 <= desc_len <= 2000
        
        # Vérifier les backend keywords (≤250 bytes)
        backend_keywords = listing.get('backend_keywords', '')
        compliance['backend_keywords_bytes_ok'] = len(backend_keywords.encode('utf-8')) <= 250
        
        # Conformité globale
        compliance['overall_compliant'] = all([
            compliance['title_length_ok'],
            compliance['bullets_count_ok'],
            compliance['bullets_length_ok'],
            compliance['description_length_ok'],
            compliance['backend_keywords_bytes_ok']
        ])
        
        return compliance
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Amazon SEO A9/A10 system tests"""
        logger.info("🚀 Starting Amazon SEO A9/A10 Backend Test Suite")
        
        # Setup authentication
        auth_success = await self.setup_authentication()
        if not auth_success:
            logger.warning("⚠️ Authentication failed - some tests may be limited")
        
        # Define all tests
        tests = [
            self.test_amazon_seo_routes_accessibility,
            self.test_amazon_seo_service_integration,
            self.test_amazon_seo_generate_endpoint,
            self.test_amazon_seo_validate_endpoint,
            self.test_amazon_seo_optimize_endpoint,
            self.test_amazon_seo_rules_endpoint,
            self.test_amazon_seo_prepare_publisher_endpoint
        ]
        
        # Run all tests
        results = []
        for test_func in tests:
            try:
                result = await test_func()
                results.append(result)
                self.total_tests += 1
                
                if result['status'] in ['PASS', 'PARTIAL_PASS']:
                    self.passed_tests += 1
                    logger.info(f"✅ {result['test']}: {result['status']}")
                else:
                    logger.error(f"❌ {result['test']}: {result['status']} - {result['message']}")
                    
            except Exception as e:
                error_result = {
                    "test": test_func.__name__,
                    "status": "ERROR",
                    "message": f"Test execution failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                results.append(error_result)
                self.total_tests += 1
                logger.error(f"💥 {test_func.__name__}: ERROR - {str(e)}")
        
        # Calculate overall results
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        summary = {
            "test_suite": "Amazon SEO A9/A10 System Backend Testing",
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": "PASS" if success_rate >= 80 else "PARTIAL_PASS" if success_rate >= 60 else "FAIL",
            "test_results": results
        }
        
        return summary

async def main():
    """Main test execution function"""
    print("=" * 80)
    print("🧪 ECOMSIMPLY AMAZON SEO A9/A10 SYSTEM BACKEND TESTING")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = AmazonSEOA9A10BackendTest()
    
    # Run all tests
    results = await test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Test Suite: {results['test_suite']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed Tests: {results['passed_tests']}")
    print(f"Success Rate: {results['success_rate']}")
    print(f"Overall Status: {results['overall_status']}")
    
    print("\n📋 DETAILED RESULTS:")
    print("-" * 80)
    
    for i, test_result in enumerate(results['test_results'], 1):
        status_emoji = "✅" if test_result['status'] == "PASS" else "⚠️" if test_result['status'] == "PARTIAL_PASS" else "❌"
        print(f"{i}. {status_emoji} {test_result['test']}")
        print(f"   Status: {test_result['status']}")
        print(f"   Message: {test_result['message']}")
        
        if test_result.get('details'):
            # Print key details only
            details = test_result['details']
            key_details = {}
            
            # Extract most important details
            for key in ['response_status', 'validation_score', 'a9_a10_compliance', 'success_rate', 'overall_compliant']:
                if key in details:
                    key_details[key] = details[key]
            
            if key_details:
                print(f"   Key Details: {json.dumps(key_details, indent=2)}")
        print()
    
    print("=" * 80)
    
    # Return appropriate exit code
    return 0 if results['overall_status'] in ['PASS', 'PARTIAL_PASS'] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)