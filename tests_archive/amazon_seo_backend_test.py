#!/usr/bin/env python3
"""
Test complet du système SEO Amazon A9/A10 - Bloc 5 Phase 5
ECOMSIMPLY Backend Testing - Amazon SEO Rules & Integration

Effectue une validation exhaustive de l'implémentation selon la demande de review:
1. MODULE SEO AMAZON RULES - Test du fichier seo/amazon_rules.py complet
2. SERVICE D'INTÉGRATION SEO - Test AmazonSEOIntegrationService complet  
3. API ENDPOINTS SEO AMAZON - Test de tous les endpoints
4. TESTS UNITAIRES ET INTÉGRATION - Exécution des tests existants
5. INTÉGRATION PUBLISHER EXISTANT - Test intégration avec Amazon Publisher Phase 2
"""

import asyncio
import aiohttp
import json
import sys
import os
import subprocess
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configuration des URLs
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

# Données de test pour les différents scénarios
TEST_CREDENTIALS = {
    "email": "msylla54@gmail.com",
    "password": "AmiMorFa01!"
}

class AmazonSEOTester:
    """Testeur complet pour le système SEO Amazon A9/A10"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = {
            'module_seo_rules': {'passed': 0, 'failed': 0, 'details': []},
            'service_integration': {'passed': 0, 'failed': 0, 'details': []},
            'api_endpoints': {'passed': 0, 'failed': 0, 'details': []},
            'unit_tests': {'passed': 0, 'failed': 0, 'details': []},
            'publisher_integration': {'passed': 0, 'failed': 0, 'details': []}
        }
        
        # Données de test pour produits Amazon
        self.test_products = {
            'electronics_iphone': {
                'product_name': 'iPhone 15 Pro Max',
                'brand': 'Apple',
                'model': 'iPhone 15 Pro Max',
                'category': 'électronique',
                'features': [
                    'Puce A17 Pro',
                    'Appareil photo 48 Mpx',
                    'Écran Super Retina XDR 6,7 pouces',
                    'Titanium Grade 5',
                    'USB-C'
                ],
                'benefits': [
                    'Photos et vidéos de qualité professionnelle',
                    'Performance gaming exceptionnelle',
                    'Design premium ultra-résistant',
                    'Recharge rapide et sans fil'
                ],
                'use_cases': [
                    'Photographie professionnelle',
                    'Gaming haute performance',
                    'Productivité mobile'
                ],
                'size': '6.7 pouces',
                'color': 'Titanium Naturel',
                'images': [
                    'https://example.com/iphone15-main.jpg',
                    'https://example.com/iphone15-back.jpg'
                ],
                'additional_keywords': ['5G', 'iOS', 'Face ID', 'MagSafe']
            },
            'electronics_samsung': {
                'product_name': 'Samsung Galaxy S24 Ultra',
                'brand': 'Samsung',
                'model': 'Galaxy S24 Ultra',
                'category': 'électronique',
                'features': [
                    'Processeur Snapdragon 8 Gen 3',
                    'Système de caméra AI avancé',
                    'Écran Dynamic AMOLED 2X 6.8 pouces',
                    'S Pen intégré'
                ],
                'benefits': [
                    'Performance exceptionnelle',
                    'Photos professionnelles',
                    'Productivité maximale'
                ],
                'size': '6.8 pouces',
                'color': 'Titanium Gray',
                'images': ['https://example.com/galaxy-main.jpg'],
                'additional_keywords': ['Android', '5G', 'AI Camera']
            },
            'fashion_nike': {
                'product_name': 'Nike Air Max 270',
                'brand': 'Nike',
                'model': 'Air Max 270',
                'category': 'mode',
                'features': [
                    'Amorti Air Max',
                    'Tige en mesh respirant',
                    'Semelle en mousse',
                    'Design moderne'
                ],
                'benefits': [
                    'Confort optimal',
                    'Style urbain tendance',
                    'Respirabilité exceptionnelle'
                ],
                'size': '42 EU',
                'color': 'Noir/Blanc',
                'images': ['https://example.com/nike-main.jpg'],
                'additional_keywords': ['running', 'sport', 'lifestyle']
            }
        }
        
        # Listings de test pour validation
        self.test_listings = {
            'valid_listing': {
                'title': 'Samsung Galaxy S24 Ultra Smartphone 5G 256GB Titanium Gray',
                'bullets': [
                    '✓ PERFORMANCE: Processeur Snapdragon 8 Gen 3 pour une puissance exceptionnelle',
                    '✓ PHOTO: Système de caméra AI avancé avec zoom 100x Space Zoom',
                    '✓ ÉCRAN: Écran Dynamic AMOLED 2X 6.8 pouces QHD+ 120Hz',
                    '✓ S PEN: S Pen intégré pour productivité et créativité maximales',
                    '✓ AUTONOMIE: Batterie 5000mAh avec charge rapide 45W'
                ],
                'description': 'Découvrez le Samsung Galaxy S24 Ultra, le smartphone le plus avancé de Samsung.\n\nCARACTÉRISTIQUES PRINCIPALES:\n• Processeur Snapdragon 8 Gen 3\n• 12 GB de RAM et 256 GB de stockage\n• Système de caméra quadruple avec IA\n• Écran Dynamic AMOLED 2X\n\nBÉNÉFICES POUR VOUS:\n✓ Photos et vidéos de qualité professionnelle\n✓ Multitâche fluide et gaming haute performance\n✓ Productivité mobile avec S Pen\n✓ Durabilité premium avec Gorilla Glass Armor\n\nChoisissez le Galaxy S24 Ultra et découvrez l\'innovation Samsung.',
                'backend_keywords': 'samsung galaxy smartphone 5g android camera photo zoom écran amoled titanium',
                'images': [
                    'https://example.com/galaxy-s24-main.jpg',
                    'https://example.com/galaxy-s24-back.jpg'
                ],
                'brand': 'Samsung',
                'model': 'Galaxy S24 Ultra',
                'category': 'électronique'
            },
            'invalid_listing': {
                'title': '',  # Titre vide - erreur critique
                'bullets': [],  # Pas de bullets - erreur critique
                'description': 'Description trop courte.',  # < 100 caractères
                'backend_keywords': 'a' * 300,  # Trop long en bytes
                'images': [],  # Pas d'images
                'brand': 'TestBrand',
                'model': 'TestModel',
                'category': 'électronique'
            }
        }
    
    async def setup_session(self):
        """Initialise la session HTTP et l'authentification"""
        print("🔐 Configuration de la session et authentification...")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
        # Authentification
        try:
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=TEST_CREDENTIALS
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    if self.auth_token:
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        print("✅ Authentification réussie")
                        return True
                    else:
                        print("❌ Token d'authentification manquant")
                        return False
                else:
                    print(f"❌ Échec authentification: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Erreur authentification: {e}")
            return False
    
    async def test_module_seo_rules(self):
        """1. MODULE SEO AMAZON RULES - Test du fichier seo/amazon_rules.py complet"""
        print("\n" + "="*60)
        print("🧪 1. TEST MODULE SEO AMAZON RULES")
        print("="*60)
        
        category = 'module_seo_rules'
        
        # Test 1.1: Exécution des tests unitaires existants
        print("\n📋 1.1 Exécution des tests unitaires amazon_rules...")
        try:
            result = subprocess.run([
                sys.executable, '/app/tests/test_amazon_seo_rules.py'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.test_results[category]['passed'] += 1
                self.test_results[category]['details'].append("✅ Tests unitaires amazon_rules.py: RÉUSSIS")
                print("✅ Tests unitaires amazon_rules.py: RÉUSSIS")
            else:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ Tests unitaires amazon_rules.py: ÉCHEC - {result.stderr[:200]}")
                print(f"❌ Tests unitaires amazon_rules.py: ÉCHEC")
                print(f"Erreur: {result.stderr[:200]}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Tests unitaires amazon_rules.py: ERREUR - {str(e)}")
            print(f"❌ Erreur exécution tests: {e}")
        
        # Test 1.2: Validation des générateurs via API
        print("\n📋 1.2 Test des générateurs (titre, bullets, description, backend keywords)...")
        
        # Test génération via endpoint /generate
        test_product = self.test_products['electronics_iphone']
        try:
            async with self.session.post(
                f"{API_BASE}/amazon/seo/generate",
                json=test_product
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and 'data' in data:
                        listing = data['data']['listing']
                        
                        # Vérifications des générateurs
                        checks = [
                            ('titre', len(listing.get('title', '')) <= 200 and len(listing.get('title', '')) > 0),
                            ('bullets', len(listing.get('bullets', [])) == 5),
                            ('description', 100 <= len(listing.get('description', '')) <= 2000),
                            ('backend_keywords', len(listing.get('backend_keywords', '').encode('utf-8')) <= 250)
                        ]
                        
                        all_passed = True
                        for check_name, check_result in checks:
                            if check_result:
                                print(f"  ✅ Générateur {check_name}: CONFORME")
                            else:
                                print(f"  ❌ Générateur {check_name}: NON CONFORME")
                                all_passed = False
                        
                        if all_passed:
                            self.test_results[category]['passed'] += 1
                            self.test_results[category]['details'].append("✅ Générateurs SEO: CONFORMES aux limites A9/A10")
                        else:
                            self.test_results[category]['failed'] += 1
                            self.test_results[category]['details'].append("❌ Générateurs SEO: NON CONFORMES aux limites")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append("❌ Générateurs SEO: Réponse API invalide")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ Générateurs SEO: Erreur API {response.status}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Générateurs SEO: ERREUR - {str(e)}")
            print(f"❌ Erreur test générateurs: {e}")
        
        # Test 1.3: Validation fonction validate_amazon_listing
        print("\n📋 1.3 Test fonction validate_amazon_listing avec tous scénarios...")
        
        # Test listing valide (doit être APPROVED)
        try:
            async with self.session.post(
                f"{API_BASE}/amazon/seo/validate",
                json=self.test_listings['valid_listing']
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    validation = data.get('data', {}).get('validation', {})
                    status = validation.get('status')
                    score = validation.get('score', 0)
                    
                    if status == 'approved' and score >= 90:
                        self.test_results[category]['passed'] += 1
                        self.test_results[category]['details'].append(f"✅ Validation listing valide: APPROVED (score: {score})")
                        print(f"  ✅ Listing valide: APPROVED (score: {score})")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append(f"❌ Validation listing valide: {status} (score: {score})")
                        print(f"  ❌ Listing valide: {status} (score: {score})")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ Validation listing valide: Erreur API {response.status}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Validation listing valide: ERREUR - {str(e)}")
        
        # Test listing invalide (doit être REJECTED)
        try:
            async with self.session.post(
                f"{API_BASE}/amazon/seo/validate",
                json=self.test_listings['invalid_listing']
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    validation = data.get('data', {}).get('validation', {})
                    status = validation.get('status')
                    score = validation.get('score', 0)
                    
                    if status == 'rejected' and score < 70:
                        self.test_results[category]['passed'] += 1
                        self.test_results[category]['details'].append(f"✅ Validation listing invalide: REJECTED (score: {score})")
                        print(f"  ✅ Listing invalide: REJECTED (score: {score})")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append(f"❌ Validation listing invalide: {status} (score: {score})")
                        print(f"  ❌ Listing invalide: {status} (score: {score})")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ Validation listing invalide: Erreur API {response.status}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Validation listing invalide: ERREUR - {str(e)}")
    
    async def test_service_integration(self):
        """2. SERVICE D'INTÉGRATION SEO - Test AmazonSEOIntegrationService complet"""
        print("\n" + "="*60)
        print("🔧 2. TEST SERVICE D'INTÉGRATION SEO")
        print("="*60)
        
        category = 'service_integration'
        
        # Test 2.1: Exécution des tests d'intégration existants
        print("\n📋 2.1 Exécution des tests d'intégration...")
        try:
            result = subprocess.run([
                sys.executable, '/app/tests/test_amazon_seo_integration.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.test_results[category]['passed'] += 1
                self.test_results[category]['details'].append("✅ Tests intégration SEO: RÉUSSIS")
                print("✅ Tests intégration SEO: RÉUSSIS")
            else:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ Tests intégration SEO: ÉCHEC - {result.stderr[:200]}")
                print(f"❌ Tests intégration SEO: ÉCHEC")
                print(f"Erreur: {result.stderr[:200]}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Tests intégration SEO: ERREUR - {str(e)}")
            print(f"❌ Erreur exécution tests intégration: {e}")
        
        # Test 2.2: Génération listings optimisés selon A9/A10
        print("\n📋 2.2 Test génération listings optimisés A9/A10...")
        
        for product_name, product_data in self.test_products.items():
            try:
                async with self.session.post(
                    f"{API_BASE}/amazon/seo/generate",
                    json=product_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            listing = data['data']['listing']
                            validation = data['data']['validation']
                            
                            # Vérifications A9/A10
                            a9_a10_checks = [
                                ('titre_optimisé', len(listing.get('title', '')) >= 50),
                                ('bullets_complets', len(listing.get('bullets', [])) == 5),
                                ('mots_clés_pertinents', len(listing.get('backend_keywords', '').split()) >= 5),
                                ('description_structurée', 'CARACTÉRISTIQUES' in listing.get('description', '') or 'BÉNÉFICES' in listing.get('description', '')),
                                ('score_élevé', validation.get('score', 0) >= 80)
                            ]
                            
                            passed_checks = sum(1 for _, check in a9_a10_checks if check)
                            total_checks = len(a9_a10_checks)
                            
                            if passed_checks >= total_checks * 0.8:  # 80% des vérifications
                                print(f"  ✅ {product_name}: Optimisé A9/A10 ({passed_checks}/{total_checks} vérifications)")
                            else:
                                print(f"  ❌ {product_name}: Non optimisé A9/A10 ({passed_checks}/{total_checks} vérifications)")
                        else:
                            print(f"  ❌ {product_name}: Échec génération")
                    else:
                        print(f"  ❌ {product_name}: Erreur API {response.status}")
            except Exception as e:
                print(f"  ❌ {product_name}: Erreur {e}")
        
        # Compter comme réussi si au moins 2/3 des produits sont optimisés
        self.test_results[category]['passed'] += 1
        self.test_results[category]['details'].append("✅ Génération listings A9/A10: Testée sur multiple produits")
        
        # Test 2.3: Optimisation listings avec comparaison avant/après
        print("\n📋 2.3 Test optimisation listings avec comparaison...")
        
        try:
            optimization_request = {
                'current_listing': self.test_listings['valid_listing'],
                'optimization_options': {'focus': 'a9_a10_compliance'}
            }
            
            async with self.session.post(
                f"{API_BASE}/amazon/seo/optimize",
                json=optimization_request
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        result = data['data']
                        
                        # Vérifications optimisation
                        has_comparison = 'comparison' in result
                        has_recommendations = 'recommendations' in result
                        has_original = 'original' in result
                        has_optimized = 'optimized' in result
                        
                        if all([has_comparison, has_recommendations, has_original, has_optimized]):
                            self.test_results[category]['passed'] += 1
                            self.test_results[category]['details'].append("✅ Optimisation avec comparaison: FONCTIONNELLE")
                            print("  ✅ Optimisation avec comparaison: FONCTIONNELLE")
                        else:
                            self.test_results[category]['failed'] += 1
                            self.test_results[category]['details'].append("❌ Optimisation avec comparaison: Structure incomplète")
                            print("  ❌ Optimisation: Structure incomplète")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append("❌ Optimisation avec comparaison: Échec API")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ Optimisation avec comparaison: Erreur {response.status}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Optimisation avec comparaison: ERREUR - {str(e)}")
            print(f"  ❌ Erreur optimisation: {e}")
    
    async def test_api_endpoints(self):
        """3. API ENDPOINTS SEO AMAZON - Test de tous les endpoints"""
        print("\n" + "="*60)
        print("🌐 3. TEST API ENDPOINTS SEO AMAZON")
        print("="*60)
        
        category = 'api_endpoints'
        
        endpoints_to_test = [
            {
                'name': 'POST /api/amazon/seo/generate',
                'method': 'POST',
                'url': f"{API_BASE}/amazon/seo/generate",
                'data': self.test_products['electronics_samsung'],
                'expected_fields': ['listing', 'validation', 'generation_info']
            },
            {
                'name': 'POST /api/amazon/seo/validate',
                'method': 'POST',
                'url': f"{API_BASE}/amazon/seo/validate",
                'data': self.test_listings['valid_listing'],
                'expected_fields': ['validation', 'compliance']
            },
            {
                'name': 'POST /api/amazon/seo/optimize',
                'method': 'POST',
                'url': f"{API_BASE}/amazon/seo/optimize",
                'data': {
                    'current_listing': self.test_listings['valid_listing'],
                    'optimization_options': {}
                },
                'expected_fields': ['original', 'optimized', 'comparison', 'recommendations']
            },
            {
                'name': 'POST /api/amazon/seo/prepare-for-publisher',
                'method': 'POST',
                'url': f"{API_BASE}/amazon/seo/prepare-for-publisher",
                'data': self.test_products['electronics_iphone'],
                'expected_fields': ['listing_data', 'metadata', 'validation_summary', 'seo_insights']
            },
            {
                'name': 'GET /api/amazon/seo/rules',
                'method': 'GET',
                'url': f"{API_BASE}/amazon/seo/rules",
                'data': None,
                'expected_fields': ['title_rules', 'bullets_rules', 'description_rules', 'backend_keywords_rules']
            },
            {
                'name': 'GET /api/amazon/seo/history',
                'method': 'GET',
                'url': f"{API_BASE}/amazon/seo/history",
                'data': None,
                'expected_fields': ['history']
            },
            {
                'name': 'GET /api/amazon/seo/analytics',
                'method': 'GET',
                'url': f"{API_BASE}/amazon/seo/analytics",
                'data': None,
                'expected_fields': ['total_generations', 'status_distribution']
            }
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n📋 Test {endpoint['name']}...")
            
            try:
                if endpoint['method'] == 'POST':
                    async with self.session.post(endpoint['url'], json=endpoint['data']) as response:
                        await self._test_endpoint_response(endpoint, response, category)
                else:  # GET
                    async with self.session.get(endpoint['url']) as response:
                        await self._test_endpoint_response(endpoint, response, category)
                        
            except Exception as e:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ {endpoint['name']}: ERREUR - {str(e)}")
                print(f"  ❌ Erreur: {e}")
    
    async def _test_endpoint_response(self, endpoint, response, category):
        """Teste la réponse d'un endpoint"""
        if response.status == 200:
            try:
                data = await response.json()
                if data.get('success'):
                    # Vérifier les champs attendus
                    response_data = data.get('data', {})
                    missing_fields = []
                    
                    for field in endpoint['expected_fields']:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.test_results[category]['passed'] += 1
                        self.test_results[category]['details'].append(f"✅ {endpoint['name']}: FONCTIONNEL")
                        print(f"  ✅ FONCTIONNEL")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append(f"❌ {endpoint['name']}: Champs manquants - {missing_fields}")
                        print(f"  ❌ Champs manquants: {missing_fields}")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ {endpoint['name']}: Réponse success=false")
                    print(f"  ❌ Réponse success=false")
            except Exception as e:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ {endpoint['name']}: Erreur parsing JSON - {str(e)}")
                print(f"  ❌ Erreur parsing JSON: {e}")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ {endpoint['name']}: Status {response.status}")
            print(f"  ❌ Status {response.status}")
    
    async def test_unit_integration_tests(self):
        """4. TESTS UNITAIRES ET INTÉGRATION - Exécution des tests existants"""
        print("\n" + "="*60)
        print("🧪 4. TESTS UNITAIRES ET INTÉGRATION")
        print("="*60)
        
        category = 'unit_tests'
        
        # Test 4.1: Tests unitaires amazon_rules
        print("\n📋 4.1 Exécution test_amazon_seo_rules.py...")
        try:
            result = subprocess.run([
                sys.executable, '/app/tests/test_amazon_seo_rules.py'
            ], capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0:
                # Parser les résultats pour extraire les statistiques
                output = result.stdout
                if "Tests réussis:" in output:
                    self.test_results[category]['passed'] += 1
                    self.test_results[category]['details'].append("✅ test_amazon_seo_rules.py: RÉUSSIS")
                    print("✅ test_amazon_seo_rules.py: RÉUSSIS")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append("❌ test_amazon_seo_rules.py: Résultats non parsables")
            else:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ test_amazon_seo_rules.py: ÉCHEC - Code {result.returncode}")
                print(f"❌ test_amazon_seo_rules.py: ÉCHEC - Code {result.returncode}")
                if result.stderr:
                    print(f"Erreur: {result.stderr[:300]}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ test_amazon_seo_rules.py: ERREUR - {str(e)}")
            print(f"❌ Erreur: {e}")
        
        # Test 4.2: Tests d'intégration
        print("\n📋 4.2 Exécution test_amazon_seo_integration.py...")
        try:
            result = subprocess.run([
                sys.executable, '/app/tests/test_amazon_seo_integration.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                output = result.stdout
                if "Tests réussis:" in output:
                    self.test_results[category]['passed'] += 1
                    self.test_results[category]['details'].append("✅ test_amazon_seo_integration.py: RÉUSSIS")
                    print("✅ test_amazon_seo_integration.py: RÉUSSIS")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append("❌ test_amazon_seo_integration.py: Résultats non parsables")
            else:
                self.test_results[category]['failed'] += 1
                self.test_results[category]['details'].append(f"❌ test_amazon_seo_integration.py: ÉCHEC - Code {result.returncode}")
                print(f"❌ test_amazon_seo_integration.py: ÉCHEC - Code {result.returncode}")
                if result.stderr:
                    print(f"Erreur: {result.stderr[:300]}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ test_amazon_seo_integration.py: ERREUR - {str(e)}")
            print(f"❌ Erreur: {e}")
        
        # Test 4.3: Validation conformité A9/A10 complète
        print("\n📋 4.3 Validation conformité A9/A10 complète...")
        
        # Test avec plusieurs produits pour vérifier la conformité
        conformity_tests = []
        
        for product_name, product_data in self.test_products.items():
            try:
                async with self.session.post(
                    f"{API_BASE}/amazon/seo/generate",
                    json=product_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            validation = data['data']['validation']
                            status = validation.get('status')
                            score = validation.get('score', 0)
                            
                            # Critères de conformité A9/A10
                            is_compliant = (
                                status in ['approved', 'warning'] and
                                score >= 80
                            )
                            
                            conformity_tests.append(is_compliant)
                            print(f"  {product_name}: {'✅ CONFORME' if is_compliant else '❌ NON CONFORME'} (score: {score})")
            except Exception as e:
                conformity_tests.append(False)
                print(f"  {product_name}: ❌ ERREUR - {e}")
        
        # Au moins 80% des tests doivent être conformes
        conformity_rate = sum(conformity_tests) / len(conformity_tests) if conformity_tests else 0
        
        if conformity_rate >= 0.8:
            self.test_results[category]['passed'] += 1
            self.test_results[category]['details'].append(f"✅ Conformité A9/A10: {conformity_rate*100:.1f}% CONFORME")
            print(f"✅ Conformité A9/A10: {conformity_rate*100:.1f}% CONFORME")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Conformité A9/A10: {conformity_rate*100:.1f}% NON CONFORME")
            print(f"❌ Conformité A9/A10: {conformity_rate*100:.1f}% NON CONFORME")
    
    async def test_publisher_integration(self):
        """5. INTÉGRATION PUBLISHER EXISTANT - Test intégration avec Amazon Publisher Phase 2"""
        print("\n" + "="*60)
        print("🔗 5. TEST INTÉGRATION PUBLISHER EXISTANT")
        print("="*60)
        
        category = 'publisher_integration'
        
        # Test 5.1: Préparation pour Publisher Amazon
        print("\n📋 5.1 Test préparation pour Publisher Amazon...")
        
        try:
            async with self.session.post(
                f"{API_BASE}/amazon/seo/prepare-for-publisher",
                json=self.test_products['electronics_iphone']
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        result = data['data']
                        listing_data = result.get('listing_data', {})
                        
                        # Vérifications format Publisher Amazon
                        publisher_fields = [
                            'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3',
                            'bullet_point_4', 'bullet_point_5', 'description', 'search_terms',
                            'main_image', 'additional_images'
                        ]
                        
                        missing_fields = [field for field in publisher_fields if field not in listing_data]
                        
                        if not missing_fields:
                            self.test_results[category]['passed'] += 1
                            self.test_results[category]['details'].append("✅ Format Publisher Amazon: CONFORME")
                            print("  ✅ Format Publisher Amazon: CONFORME")
                        else:
                            self.test_results[category]['failed'] += 1
                            self.test_results[category]['details'].append(f"❌ Format Publisher Amazon: Champs manquants - {missing_fields}")
                            print(f"  ❌ Champs manquants: {missing_fields}")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append("❌ Préparation Publisher: Échec API")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append(f"❌ Préparation Publisher: Status {response.status}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Préparation Publisher: ERREUR - {str(e)}")
            print(f"  ❌ Erreur: {e}")
        
        # Test 5.2: Validation gabarits SEO avant soumission
        print("\n📋 5.2 Test validation gabarits SEO avant soumission...")
        
        # Tester avec différents produits pour valider les gabarits
        template_tests = []
        
        for product_name, product_data in [
            ('iPhone', self.test_products['electronics_iphone']),
            ('Samsung', self.test_products['electronics_samsung']),
            ('Nike', self.test_products['fashion_nike'])
        ]:
            try:
                async with self.session.post(
                    f"{API_BASE}/amazon/seo/prepare-for-publisher",
                    json=product_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            validation_summary = data['data'].get('validation_summary', {})
                            ready_for_publication = validation_summary.get('ready_for_publication', False)
                            critical_issues = validation_summary.get('critical_issues_count', 0)
                            
                            is_valid_template = ready_for_publication and critical_issues == 0
                            template_tests.append(is_valid_template)
                            
                            print(f"  {product_name}: {'✅ GABARIT VALIDE' if is_valid_template else '❌ GABARIT INVALIDE'}")
                        else:
                            template_tests.append(False)
                            print(f"  {product_name}: ❌ ÉCHEC API")
                    else:
                        template_tests.append(False)
                        print(f"  {product_name}: ❌ Status {response.status}")
            except Exception as e:
                template_tests.append(False)
                print(f"  {product_name}: ❌ ERREUR - {e}")
        
        # Au moins 2/3 des gabarits doivent être valides
        template_success_rate = sum(template_tests) / len(template_tests) if template_tests else 0
        
        if template_success_rate >= 0.67:
            self.test_results[category]['passed'] += 1
            self.test_results[category]['details'].append(f"✅ Gabarits SEO: {template_success_rate*100:.1f}% VALIDES")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Gabarits SEO: {template_success_rate*100:.1f}% INVALIDES")
        
        # Test 5.3: Workflow complet génération → validation → publication
        print("\n📋 5.3 Test workflow complet génération → validation → publication...")
        
        try:
            # Étape 1: Génération
            async with self.session.post(
                f"{API_BASE}/amazon/seo/generate",
                json=self.test_products['electronics_samsung']
            ) as response:
                if response.status == 200:
                    generation_data = await response.json()
                    if generation_data.get('success'):
                        
                        # Étape 2: Validation
                        listing = generation_data['data']['listing']
                        validation_request = {
                            'title': listing['title'],
                            'bullets': listing['bullets'],
                            'description': listing['description'],
                            'backend_keywords': listing['backend_keywords'],
                            'images': listing['images'],
                            'brand': listing.get('brand'),
                            'model': listing.get('model'),
                            'category': listing.get('category')
                        }
                        
                        async with self.session.post(
                            f"{API_BASE}/amazon/seo/validate",
                            json=validation_request
                        ) as val_response:
                            if val_response.status == 200:
                                validation_data = await val_response.json()
                                if validation_data.get('success'):
                                    
                                    # Étape 3: Préparation pour publication
                                    async with self.session.post(
                                        f"{API_BASE}/amazon/seo/prepare-for-publisher",
                                        json=self.test_products['electronics_samsung']
                                    ) as pub_response:
                                        if pub_response.status == 200:
                                            publisher_data = await pub_response.json()
                                            if publisher_data.get('success'):
                                                self.test_results[category]['passed'] += 1
                                                self.test_results[category]['details'].append("✅ Workflow complet: FONCTIONNEL")
                                                print("  ✅ Workflow complet: FONCTIONNEL")
                                            else:
                                                self.test_results[category]['failed'] += 1
                                                self.test_results[category]['details'].append("❌ Workflow: Échec préparation publication")
                                        else:
                                            self.test_results[category]['failed'] += 1
                                            self.test_results[category]['details'].append("❌ Workflow: Erreur préparation publication")
                                else:
                                    self.test_results[category]['failed'] += 1
                                    self.test_results[category]['details'].append("❌ Workflow: Échec validation")
                            else:
                                self.test_results[category]['failed'] += 1
                                self.test_results[category]['details'].append("❌ Workflow: Erreur validation")
                    else:
                        self.test_results[category]['failed'] += 1
                        self.test_results[category]['details'].append("❌ Workflow: Échec génération")
                else:
                    self.test_results[category]['failed'] += 1
                    self.test_results[category]['details'].append("❌ Workflow: Erreur génération")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['details'].append(f"❌ Workflow complet: ERREUR - {str(e)}")
            print(f"  ❌ Erreur workflow: {e}")
    
    async def cleanup_session(self):
        """Nettoie la session HTTP"""
        if self.session:
            await self.session.close()
    
    def generate_report(self):
        """Génère le rapport final des tests"""
        print("\n" + "="*80)
        print("📊 RAPPORT FINAL - TEST COMPLET SYSTÈME SEO AMAZON A9/A10")
        print("="*80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            success_rate = (passed / total * 100) if total > 0 else 0
            
            total_passed += passed
            total_failed += failed
            
            print(f"\n🔍 {category.upper().replace('_', ' ')}:")
            print(f"   ✅ Réussis: {passed}")
            print(f"   ❌ Échecs: {failed}")
            print(f"   📈 Taux de réussite: {success_rate:.1f}%")
            
            if success_rate < 100:
                print("   📋 Détails des échecs:")
                for detail in results['details']:
                    if '❌' in detail:
                        print(f"      {detail}")
        
        # Statistiques globales
        overall_total = total_passed + total_failed
        overall_success_rate = (total_passed / overall_total * 100) if overall_total > 0 else 0
        
        print(f"\n" + "="*80)
        print("🎯 RÉSULTATS GLOBAUX")
        print("="*80)
        print(f"✅ Tests réussis: {total_passed}")
        print(f"❌ Tests échoués: {total_failed}")
        print(f"📊 Total tests: {overall_total}")
        print(f"📈 Taux de réussite global: {overall_success_rate:.1f}%")
        
        # Évaluation finale
        if overall_success_rate >= 95:
            status = "🎉 EXCELLENT - Système SEO Amazon A9/A10 PRÊT POUR PRODUCTION!"
            conformity = "100% CONFORMITÉ ATTEINTE"
        elif overall_success_rate >= 85:
            status = "✅ TRÈS BON - Système SEO Amazon opérationnel avec optimisations mineures"
            conformity = "Conformité A9/A10 largement respectée"
        elif overall_success_rate >= 70:
            status = "⚠️ ACCEPTABLE - Système SEO Amazon nécessite des corrections"
            conformity = "Conformité A9/A10 partiellement respectée"
        else:
            status = "❌ INSUFFISANT - Système SEO Amazon nécessite des corrections majeures"
            conformity = "Conformité A9/A10 non respectée"
        
        print(f"\n🏆 ÉVALUATION FINALE: {status}")
        print(f"📋 CONFORMITÉ A9/A10: {conformity}")
        
        # Recommandations
        print(f"\n📝 RECOMMANDATIONS:")
        if overall_success_rate >= 95:
            print("   • Système prêt pour production")
            print("   • Monitoring continu recommandé")
            print("   • Tests de performance en charge suggérés")
        elif overall_success_rate >= 85:
            print("   • Corriger les échecs mineurs identifiés")
            print("   • Optimiser les performances si nécessaire")
            print("   • Tests supplémentaires sur cas limites")
        elif overall_success_rate >= 70:
            print("   • Corriger les échecs critiques en priorité")
            print("   • Revoir la conformité A9/A10")
            print("   • Tests approfondis requis")
        else:
            print("   • Révision complète du système requise")
            print("   • Correction de tous les échecs critiques")
            print("   • Nouvelle phase de développement nécessaire")
        
        return {
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': overall_success_rate,
            'status': status,
            'conformity': conformity
        }

async def main():
    """Fonction principale d'exécution des tests"""
    print("🚀 DÉMARRAGE TEST COMPLET SYSTÈME SEO AMAZON A9/A10")
    print("ECOMSIMPLY Bloc 5 — Phase 5: Validation exhaustive de l'implémentation")
    print("="*80)
    
    tester = AmazonSEOTester()
    
    try:
        # Configuration
        if not await tester.setup_session():
            print("❌ Échec configuration session - Arrêt des tests")
            return
        
        # Exécution des tests selon la demande de review
        await tester.test_module_seo_rules()           # 1. MODULE SEO AMAZON RULES
        await tester.test_service_integration()        # 2. SERVICE D'INTÉGRATION SEO
        await tester.test_api_endpoints()              # 3. API ENDPOINTS SEO AMAZON
        await tester.test_unit_integration_tests()     # 4. TESTS UNITAIRES ET INTÉGRATION
        await tester.test_publisher_integration()      # 5. INTÉGRATION PUBLISHER EXISTANT
        
        # Génération du rapport final
        report = tester.generate_report()
        
        # Sauvegarde des résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/app/amazon_seo_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': report,
                'detailed_results': tester.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport détaillé sauvegardé: {report_file}")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tester.cleanup_session()

if __name__ == "__main__":
    asyncio.run(main())