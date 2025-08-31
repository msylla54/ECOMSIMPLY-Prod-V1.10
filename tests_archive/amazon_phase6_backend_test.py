#!/usr/bin/env python3
"""
Backend Test Amazon Phase 6 - Optimisations avancées ECOMSIMPLY
Test complet des services et API Phase 6: A/B Testing, A+ Content, Variations Builder, Compliance Scanner
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://ecomsimply.com"
API_BASE = f"{BACKEND_URL}/api"

class AmazonPhase6BackendTester:
    """Testeur complet Phase 6 Amazon - Optimisations avancées"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Enregistrer résultat de test"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Faire une requête HTTP avec gestion d'erreur"""
        url = f"{API_BASE}{endpoint}"
        headers = {}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {'raw_response': response_text}
                
                return {
                    'status': response.status,
                    'data': response_data,
                    'success': 200 <= response.status < 300
                }
                
        except Exception as e:
            return {
                'status': 0,
                'data': {'error': str(e)},
                'success': False
            }
    
    async def authenticate(self) -> bool:
        """Authentification utilisateur test"""
        print("🔐 Testing Authentication...")
        
        # Créer un utilisateur test
        register_data = {
            "email": f"phase6test_{int(time.time())}@test.com",
            "name": "Phase 6 Test User",
            "password": "TestPassword123!"
        }
        
        response = await self.make_request('POST', '/auth/register', register_data)
        
        if response['success'] and 'token' in response['data']:
            # Registration returns token directly
            self.auth_token = response['data']['token']
            self.log_test("Authentication", True, "User registered and authenticated successfully")
            return True
        elif response['success']:
            # Login separately if needed
            login_data = {
                "email": register_data['email'],
                "password": register_data['password']
            }
            
            login_response = await self.make_request('POST', '/auth/login', login_data)
            
            if login_response['success'] and 'access_token' in login_response['data']:
                self.auth_token = login_response['data']['access_token']
                self.log_test("Authentication", True, "User authenticated successfully")
                return True
            elif login_response['success'] and 'token' in login_response['data']:
                self.auth_token = login_response['data']['token']
                self.log_test("Authentication", True, "User authenticated successfully")
                return True
        
        self.log_test("Authentication", False, "Failed to authenticate user")
        return False
    
    # ==================== PHASE 6 DASHBOARD TESTS ====================
    
    async def test_phase6_dashboard(self):
        """Test du dashboard Phase 6"""
        print("\n📊 Testing Phase 6 Dashboard...")
        
        marketplace_id = "A13V1IB3VIYZZH"  # Amazon France
        
        response = await self.make_request(
            'GET', 
            '/amazon/phase6/dashboard',
            params={'marketplace_id': marketplace_id}
        )
        
        if response['success']:
            data = response['data'].get('data', {})
            
            # Vérifier la structure des données dashboard
            required_fields = [
                'active_experiments', 'completed_experiments', 'avg_lift_rate',
                'published_content', 'pending_approval', 'avg_engagement_rate',
                'variation_families', 'total_child_products', 'sync_success_rate',
                'compliance_score', 'critical_issues', 'auto_fixes_applied_24h'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_test(
                    "Phase 6 Dashboard Structure", 
                    True, 
                    f"All required fields present: {len(required_fields)} fields"
                )
                
                # Vérifier les valeurs
                metrics_valid = (
                    isinstance(data.get('compliance_score'), (int, float)) and
                    0 <= data.get('compliance_score') <= 100 and
                    isinstance(data.get('active_experiments'), int) and
                    isinstance(data.get('variation_families'), int)
                )
                
                self.log_test(
                    "Phase 6 Dashboard Metrics", 
                    metrics_valid, 
                    f"Compliance: {data.get('compliance_score')}%, Experiments: {data.get('active_experiments')}"
                )
            else:
                self.log_test(
                    "Phase 6 Dashboard Structure", 
                    False, 
                    f"Missing fields: {missing_fields}"
                )
        else:
            self.log_test(
                "Phase 6 Dashboard Access", 
                False, 
                f"Status: {response['status']}, Error: {response['data']}"
            )
    
    # ==================== A/B TESTING TESTS ====================
    
    async def test_ab_testing_workflow(self):
        """Test du workflow complet A/B Testing"""
        print("\n🧪 Testing A/B Testing Workflow...")
        
        # Test 1: Créer une expérimentation A/B
        experiment_data = {
            "sku": "TEST-PHASE6-AB-001",
            "marketplace_id": "A13V1IB3VIYZZH",
            "name": "Test Titre Optimisation Phase 6",
            "description": "Test d'optimisation du titre produit",
            "experiment_type": "title",
            "duration_days": 14,
            "primary_metric": "conversion_rate",
            "confidence_level": 95.0,
            "auto_apply_winner": False,
            "variants": [
                {
                    "name": "Titre Original",
                    "content": {"title": "Produit Test Original"},
                    "traffic_percentage": 50.0
                },
                {
                    "name": "Titre Optimisé",
                    "content": {"title": "Produit Test Optimisé SEO Premium"},
                    "traffic_percentage": 50.0
                }
            ]
        }
        
        create_response = await self.make_request(
            'POST', 
            '/amazon/phase6/experiments', 
            experiment_data
        )
        
        if create_response['success']:
            experiment = create_response['data'].get('experiment')
            if experiment:
                experiment_id = experiment.get('id')
                
                self.log_test(
                    "A/B Test Creation", 
                    True, 
                    f"Experiment created: {experiment_id}"
                )
                
                # Test 2: Démarrer l'expérimentation
                start_response = await self.make_request(
                    'POST', 
                    f'/amazon/phase6/experiments/{experiment_id}/start'
                )
                
                self.log_test(
                    "A/B Test Start", 
                    start_response['success'], 
                    f"Start status: {start_response['status']}"
                )
                
                # Test 3: Collecter les métriques
                metrics_response = await self.make_request(
                    'GET', 
                    f'/amazon/phase6/experiments/{experiment_id}/metrics'
                )
                
                self.log_test(
                    "A/B Test Metrics Collection", 
                    metrics_response['success'], 
                    f"Metrics status: {metrics_response['status']}"
                )
                
                # Test 4: Analyser les résultats
                analysis_response = await self.make_request(
                    'GET', 
                    f'/amazon/phase6/experiments/{experiment_id}/analysis'
                )
                
                self.log_test(
                    "A/B Test Statistical Analysis", 
                    analysis_response['success'], 
                    f"Analysis status: {analysis_response['status']}"
                )
                
                # Test 5: Lister les expérimentations utilisateur
                list_response = await self.make_request(
                    'GET', 
                    '/amazon/phase6/experiments',
                    params={'marketplace_id': 'A13V1IB3VIYZZH'}
                )
                
                if list_response['success']:
                    experiments = list_response['data'].get('data', [])
                    self.log_test(
                        "A/B Test User Experiments List", 
                        True, 
                        f"Found {len(experiments)} experiments"
                    )
                else:
                    self.log_test(
                        "A/B Test User Experiments List", 
                        False, 
                        f"Status: {list_response['status']}"
                    )
            else:
                self.log_test(
                    "A/B Test Creation", 
                    False, 
                    "No experiment data in response"
                )
        else:
            self.log_test(
                "A/B Test Creation", 
                False, 
                f"Status: {create_response['status']}, Error: {create_response['data']}"
            )
    
    # ==================== A+ CONTENT TESTS ====================
    
    async def test_aplus_content_workflow(self):
        """Test du workflow complet A+ Content"""
        print("\n🎨 Testing A+ Content Workflow...")
        
        # Test 1: Créer un contenu A+
        aplus_data = {
            "sku": "TEST-PHASE6-APLUS-001",
            "marketplace_id": "A13V1IB3VIYZZH",
            "name": "Contenu A+ Test Phase 6",
            "description": "Contenu A+ généré pour test Phase 6",
            "language": "fr-FR",
            "use_ai_generation": True,
            "modules_types": ["STANDARD_SINGLE_IMAGE_TEXT", "STANDARD_MULTIPLE_IMAGE_TEXT"],
            "style_preferences": {
                "tone": "professional",
                "style": "premium"
            }
        }
        
        create_response = await self.make_request(
            'POST', 
            '/amazon/phase6/aplus-content', 
            aplus_data
        )
        
        if create_response['success']:
            content = create_response['data'].get('content')
            if content:
                content_id = content.get('id')
                
                self.log_test(
                    "A+ Content Creation", 
                    True, 
                    f"Content created: {content_id}"
                )
                
                # Test 2: Publier le contenu A+
                publish_response = await self.make_request(
                    'POST', 
                    f'/amazon/phase6/aplus-content/{content_id}/publish'
                )
                
                self.log_test(
                    "A+ Content Publication", 
                    publish_response['success'], 
                    f"Publish status: {publish_response['status']}"
                )
                
                # Test 3: Vérifier le statut d'approbation
                status_response = await self.make_request(
                    'GET', 
                    f'/amazon/phase6/aplus-content/{content_id}/status'
                )
                
                self.log_test(
                    "A+ Content Approval Status", 
                    status_response['success'], 
                    f"Status check: {status_response['status']}"
                )
                
                # Test 4: Récupérer les métriques de performance
                metrics_response = await self.make_request(
                    'GET', 
                    f'/amazon/phase6/aplus-content/{content_id}/metrics'
                )
                
                self.log_test(
                    "A+ Content Performance Metrics", 
                    metrics_response['success'], 
                    f"Metrics status: {metrics_response['status']}"
                )
                
                # Test 5: Lister les contenus A+ utilisateur
                list_response = await self.make_request(
                    'GET', 
                    '/amazon/phase6/aplus-content',
                    params={'marketplace_id': 'A13V1IB3VIYZZH'}
                )
                
                if list_response['success']:
                    contents = list_response['data'].get('data', [])
                    self.log_test(
                        "A+ Content User Contents List", 
                        True, 
                        f"Found {len(contents)} A+ contents"
                    )
                else:
                    self.log_test(
                        "A+ Content User Contents List", 
                        False, 
                        f"Status: {list_response['status']}"
                    )
            else:
                self.log_test(
                    "A+ Content Creation", 
                    False, 
                    "No content data in response"
                )
        else:
            self.log_test(
                "A+ Content Creation", 
                False, 
                f"Status: {create_response['status']}, Error: {create_response['data']}"
            )
    
    # ==================== VARIATIONS BUILDER TESTS ====================
    
    async def test_variations_builder_workflow(self):
        """Test du workflow complet Variations Builder"""
        print("\n🏗️ Testing Variations Builder Workflow...")
        
        # Test 1: Détecter les familles de variations
        detect_response = await self.make_request(
            'GET', 
            '/amazon/phase6/variations/detect',
            params={
                'marketplace_id': 'A13V1IB3VIYZZH',
                'sku_list': 'TEST-SHIRT-RED-M,TEST-SHIRT-RED-L,TEST-SHIRT-BLUE-M,TEST-SHIRT-BLUE-L'
            }
        )
        
        if detect_response['success']:
            families = detect_response['data'].get('data', [])
            self.log_test(
                "Variations Detection", 
                True, 
                f"Detected {len(families)} variation families"
            )
        else:
            self.log_test(
                "Variations Detection", 
                False, 
                f"Status: {detect_response['status']}"
            )
        
        # Test 2: Créer une famille de variations
        family_data = {
            "marketplace_id": "A13V1IB3VIYZZH",
            "parent_sku": "PARENT-PHASE6-TEST-001",
            "family_name": "T-Shirts Collection Phase 6 Test",
            "variation_theme": "Size-Color",
            "child_skus": ["CHILD-PHASE6-001-S-RED", "CHILD-PHASE6-001-M-RED", "CHILD-PHASE6-001-L-BLUE"],
            "auto_manage": True,
            "sync_pricing": False,
            "sync_inventory": False,
            "children": [
                {
                    "sku": "CHILD-PHASE6-001-S-RED",
                    "variation_attributes": {"size": "S", "color": "Red"}
                },
                {
                    "sku": "CHILD-PHASE6-001-M-RED",
                    "variation_attributes": {"size": "M", "color": "Red"}
                },
                {
                    "sku": "CHILD-PHASE6-001-L-BLUE",
                    "variation_attributes": {"size": "L", "color": "Blue"}
                }
            ]
        }
        
        create_response = await self.make_request(
            'POST', 
            '/amazon/phase6/variations', 
            family_data
        )
        
        if create_response['success']:
            family = create_response['data'].get('family')
            if family:
                family_id = family.get('id')
                
                self.log_test(
                    "Variation Family Creation", 
                    True, 
                    f"Family created: {family_id}"
                )
                
                # Test 3: Synchroniser la famille
                sync_response = await self.make_request(
                    'POST', 
                    f'/amazon/phase6/variations/{family_id}/sync'
                )
                
                self.log_test(
                    "Variation Family Sync", 
                    sync_response['success'], 
                    f"Sync status: {sync_response['status']}"
                )
                
                # Test 4: Lister les familles de variations
                list_response = await self.make_request(
                    'GET', 
                    '/amazon/phase6/variations',
                    params={'marketplace_id': 'A13V1IB3VIYZZH'}
                )
                
                if list_response['success']:
                    families = list_response['data'].get('data', [])
                    self.log_test(
                        "Variation Families List", 
                        True, 
                        f"Found {len(families)} variation families"
                    )
                else:
                    self.log_test(
                        "Variation Families List", 
                        False, 
                        f"Status: {list_response['status']}"
                    )
            else:
                self.log_test(
                    "Variation Family Creation", 
                    False, 
                    "No family data in response"
                )
        else:
            self.log_test(
                "Variation Family Creation", 
                False, 
                f"Status: {create_response['status']}, Error: {create_response['data']}"
            )
    
    # ==================== COMPLIANCE SCANNER TESTS ====================
    
    async def test_compliance_scanner_workflow(self):
        """Test du workflow complet Compliance Scanner"""
        print("\n🔍 Testing Compliance Scanner Workflow...")
        
        # Test 1: Scanner la conformité
        scan_data = {
            "marketplace_id": "A13V1IB3VIYZZH",
            "sku_list": ["TEST-COMPLIANCE-001", "TEST-COMPLIANCE-002", "TEST-COMPLIANCE-003"],
            "scan_types": ["battery", "images", "dimensions", "content_policy"]
        }
        
        scan_response = await self.make_request(
            'POST', 
            '/amazon/phase6/compliance/scan', 
            scan_data
        )
        
        if scan_response['success']:
            report = scan_response['data'].get('report')
            if report:
                report_id = report.get('id')
                compliance_score = report.get('compliance_score', 0)
                issues_found = report.get('issues_found', 0)
                
                self.log_test(
                    "Compliance Scan", 
                    True, 
                    f"Report: {report_id}, Score: {compliance_score}%, Issues: {issues_found}"
                )
                
                # Test 2: Appliquer les corrections automatiques (dry run)
                if issues_found > 0:
                    fix_data = {
                        "report_id": report_id,
                        "dry_run": True
                    }
                    
                    fix_response = await self.make_request(
                        'POST', 
                        '/amazon/phase6/compliance/auto-fix', 
                        fix_data
                    )
                    
                    if fix_response['success']:
                        fix_results = fix_response['data'].get('data', {})
                        fixed_count = fix_results.get('fixed', 0)
                        
                        self.log_test(
                            "Compliance Auto-Fix (Dry Run)", 
                            True, 
                            f"Would fix {fixed_count} issues"
                        )
                    else:
                        self.log_test(
                            "Compliance Auto-Fix (Dry Run)", 
                            False, 
                            f"Status: {fix_response['status']}"
                        )
                
                # Test 3: Dashboard de conformité
                dashboard_response = await self.make_request(
                    'GET', 
                    '/amazon/phase6/compliance/dashboard',
                    params={'marketplace_id': 'A13V1IB3VIYZZH'}
                )
                
                if dashboard_response['success']:
                    dashboard_data = dashboard_response['data'].get('data', {})
                    self.log_test(
                        "Compliance Dashboard", 
                        True, 
                        f"Dashboard data retrieved with score: {dashboard_data.get('compliance_score', 'N/A')}"
                    )
                else:
                    self.log_test(
                        "Compliance Dashboard", 
                        False, 
                        f"Status: {dashboard_response['status']}"
                    )
            else:
                self.log_test(
                    "Compliance Scan", 
                    False, 
                    "No report data in response"
                )
        else:
            self.log_test(
                "Compliance Scan", 
                False, 
                f"Status: {scan_response['status']}, Error: {scan_response['data']}"
            )
    
    # ==================== INTEGRATION TESTS ====================
    
    async def test_phase6_integration_workflow(self):
        """Test du workflow d'intégration Phase 6 complet"""
        print("\n🔄 Testing Phase 6 Integration Workflow...")
        
        # Test d'intégration: Dashboard → A/B Test → Compliance → A+ Content
        marketplace_id = "A13V1IB3VIYZZH"
        
        # 1. Vérifier le dashboard initial
        dashboard_response = await self.make_request(
            'GET', 
            '/amazon/phase6/dashboard',
            params={'marketplace_id': marketplace_id}
        )
        
        initial_dashboard_success = dashboard_response['success']
        
        # 2. Créer une expérimentation A/B simple
        experiment_data = {
            "sku": "INTEGRATION-TEST-001",
            "marketplace_id": marketplace_id,
            "name": "Integration Test Experiment",
            "experiment_type": "title",
            "variants": [
                {"name": "Control", "content": {"title": "Original Title"}, "traffic_percentage": 50.0},
                {"name": "Treatment", "content": {"title": "Optimized Title"}, "traffic_percentage": 50.0}
            ]
        }
        
        experiment_response = await self.make_request(
            'POST', 
            '/amazon/phase6/experiments', 
            experiment_data
        )
        
        experiment_success = experiment_response['success']
        
        # 3. Scanner la conformité
        scan_data = {
            "marketplace_id": marketplace_id,
            "sku_list": ["INTEGRATION-TEST-001"],
            "scan_types": ["images", "content_policy"]
        }
        
        scan_response = await self.make_request(
            'POST', 
            '/amazon/phase6/compliance/scan', 
            scan_data
        )
        
        scan_success = scan_response['success']
        
        # 4. Créer du contenu A+
        aplus_data = {
            "sku": "INTEGRATION-TEST-001",
            "marketplace_id": marketplace_id,
            "name": "Integration A+ Content",
            "use_ai_generation": True,
            "modules_types": ["STANDARD_SINGLE_IMAGE_TEXT"]
        }
        
        aplus_response = await self.make_request(
            'POST', 
            '/amazon/phase6/aplus-content', 
            aplus_data
        )
        
        aplus_success = aplus_response['success']
        
        # Évaluer l'intégration globale
        integration_success = all([
            initial_dashboard_success,
            experiment_success,
            scan_success,
            aplus_success
        ])
        
        successful_components = sum([
            initial_dashboard_success,
            experiment_success,
            scan_success,
            aplus_success
        ])
        
        self.log_test(
            "Phase 6 Integration Workflow", 
            integration_success, 
            f"Integration success: {successful_components}/4 components working"
        )
        
        # Test de cohérence des données
        if initial_dashboard_success:
            # Vérifier le dashboard après les opérations
            final_dashboard_response = await self.make_request(
                'GET', 
                '/amazon/phase6/dashboard',
                params={'marketplace_id': marketplace_id}
            )
            
            if final_dashboard_response['success']:
                self.log_test(
                    "Phase 6 Dashboard Consistency", 
                    True, 
                    "Dashboard remains accessible after operations"
                )
            else:
                self.log_test(
                    "Phase 6 Dashboard Consistency", 
                    False, 
                    "Dashboard became inaccessible after operations"
                )
    
    # ==================== PERFORMANCE TESTS ====================
    
    async def test_phase6_performance(self):
        """Test des performances des endpoints Phase 6"""
        print("\n⚡ Testing Phase 6 Performance...")
        
        performance_tests = [
            ('Dashboard', 'GET', '/amazon/phase6/dashboard', {'marketplace_id': 'A13V1IB3VIYZZH'}),
            ('Experiments List', 'GET', '/amazon/phase6/experiments', {'marketplace_id': 'A13V1IB3VIYZZH'}),
            ('A+ Contents List', 'GET', '/amazon/phase6/aplus-content', {'marketplace_id': 'A13V1IB3VIYZZH'}),
            ('Variations List', 'GET', '/amazon/phase6/variations', {'marketplace_id': 'A13V1IB3VIYZZH'}),
            ('Compliance Dashboard', 'GET', '/amazon/phase6/compliance/dashboard', {'marketplace_id': 'A13V1IB3VIYZZH'})
        ]
        
        performance_results = []
        
        for test_name, method, endpoint, params in performance_tests:
            start_time = time.time()
            
            response = await self.make_request(method, endpoint, params=params)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # en millisecondes
            
            performance_results.append({
                'test': test_name,
                'response_time_ms': response_time,
                'success': response['success'],
                'status': response['status']
            })
            
            # Critère de performance: < 3000ms
            performance_ok = response_time < 3000
            
            self.log_test(
                f"Performance - {test_name}", 
                performance_ok and response['success'], 
                f"Response time: {response_time:.0f}ms (target: <3000ms)"
            )
        
        # Statistiques globales de performance
        successful_tests = [r for r in performance_results if r['success']]
        if successful_tests:
            avg_response_time = sum(r['response_time_ms'] for r in successful_tests) / len(successful_tests)
            max_response_time = max(r['response_time_ms'] for r in successful_tests)
            
            self.log_test(
                "Phase 6 Overall Performance", 
                avg_response_time < 2000 and max_response_time < 3000, 
                f"Avg: {avg_response_time:.0f}ms, Max: {max_response_time:.0f}ms"
            )
    
    # ==================== MAIN TEST EXECUTION ====================
    
    async def run_all_tests(self):
        """Exécuter tous les tests Phase 6"""
        print("🚀 AMAZON PHASE 6 BACKEND TESTING - OPTIMISATIONS AVANCÉES")
        print("=" * 80)
        
        # Authentification
        if not await self.authenticate():
            print("❌ Authentication failed. Stopping tests.")
            return
        
        # Tests principaux
        await self.test_phase6_dashboard()
        await self.test_ab_testing_workflow()
        await self.test_aplus_content_workflow()
        await self.test_variations_builder_workflow()
        await self.test_compliance_scanner_workflow()
        await self.test_phase6_integration_workflow()
        await self.test_phase6_performance()
        
        # Résumé des résultats
        await self.print_summary()
    
    async def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 80)
        print("📋 AMAZON PHASE 6 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        execution_time = time.time() - self.start_time
        print(f"⏱️ Execution Time: {execution_time:.1f}s")
        
        # Détail des échecs
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test_name']}: {result['details']}")
        
        # Critères de succès Phase 6
        print(f"\n🎯 PHASE 6 SUCCESS CRITERIA:")
        print(f"  • Routes Phase 6 registered: {'✅' if success_rate > 50 else '❌'}")
        print(f"  • Core functionality working: {'✅' if success_rate >= 70 else '❌'}")
        print(f"  • Integration workflow: {'✅' if success_rate >= 60 else '❌'}")
        print(f"  • Performance acceptable: {'✅' if success_rate >= 80 else '❌'}")
        
        # Statut final
        if success_rate >= 90:
            print(f"\n🎉 PHASE 6 STATUS: EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 75:
            print(f"\n✅ PHASE 6 STATUS: GOOD ({success_rate:.1f}%)")
        elif success_rate >= 50:
            print(f"\n⚠️ PHASE 6 STATUS: PARTIAL ({success_rate:.1f}%)")
        else:
            print(f"\n❌ PHASE 6 STATUS: NEEDS WORK ({success_rate:.1f}%)")
        
        print("=" * 80)


async def main():
    """Point d'entrée principal"""
    try:
        async with AmazonPhase6BackendTester() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())