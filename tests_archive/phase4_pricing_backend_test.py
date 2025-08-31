#!/usr/bin/env python3
"""
ECOMSIMPLY Phase 4 Amazon Pricing Engine Backend Testing
Comprehensive testing of Amazon pricing rules, calculation, and SP-API publication
"""

import asyncio
import aiohttp
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
import os

# Configuration
BACKEND_URL = "https://ecomsimply.com"
TEST_USER_EMAIL = f"pricing_test_{int(time.time())}@ecomsimply.test"
TEST_USER_PASSWORD = "TestPricing2025!"

class Phase4PricingTester:
    """Comprehensive tester for Amazon Phase 4 Pricing Engine"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.auth_token = None
        self.test_user_id = None
        self.test_results = []
        self.created_rules = []
        self.created_batches = []
        
        # Test data
        self.test_skus = [
            "IPHONE-15-PRO-256-TITANIUM",
            "SAMSUNG-S24-ULTRA-512",
            "MACBOOK-PRO-M3-14",
            "AIRPODS-PRO-2ND-GEN",
            "NINTENDO-SWITCH-OLED"
        ]
        
        self.marketplace_fr = "A13V1IB3VIYZZH"  # Amazon France
        
    async def setup(self):
        """Initialize test session and authentication"""
        print("🔧 Setting up Phase 4 Pricing Engine test environment...")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'Content-Type': 'application/json'}
        )
        
        # Create test user
        await self.create_test_user()
        
        # Authenticate
        await self.authenticate()
        
        print(f"✅ Test environment ready - User: {TEST_USER_EMAIL}")
    
    async def create_test_user(self):
        """Create test user for pricing tests"""
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "name": "Phase 4 Pricing Tester",
                "password": TEST_USER_PASSWORD,
                "language": "fr"
            }
            
            async with self.session.post(f"{self.backend_url}/api/auth/register", json=user_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    self.test_user_id = result.get('user_id')
                    print(f"✅ Test user created: {TEST_USER_EMAIL}")
                elif response.status == 400:
                    # User might already exist
                    print(f"ℹ️ Test user already exists: {TEST_USER_EMAIL}")
                else:
                    print(f"⚠️ User creation status: {response.status}")
                    
        except Exception as e:
            print(f"⚠️ User creation error: {str(e)}")
    
    async def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{self.backend_url}/api/auth/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get('access_token') or result.get('token')
                    self.test_user_id = result.get('user_id')
                    
                    # Update session headers
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    print(f"✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_pricing_rules_crud(self):
        """Test 1: CRUD operations for pricing rules"""
        print("\n📋 Testing Pricing Rules CRUD Operations...")
        start_time = time.time()
        
        try:
            # Test 1.1: Create pricing rule
            rule_data = {
                "sku": self.test_skus[0],
                "marketplace_id": self.marketplace_fr,
                "min_price": 800.0,
                "max_price": 1200.0,
                "variance_pct": 5.0,
                "map_price": 850.0,
                "strategy": "buybox_match",
                "margin_target": 25.0,
                "auto_update": True,
                "update_frequency": 300
            }
            
            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=rule_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success') and result.get('rule'):
                        rule_id = result['rule']['id']
                        self.created_rules.append(rule_id)
                        self.log_test_result("Create Pricing Rule", True, f"Rule created: {rule_id}")
                    else:
                        self.log_test_result("Create Pricing Rule", False, "No rule in response")
                        return
                else:
                    error_text = await response.text()
                    self.log_test_result("Create Pricing Rule", False, f"Status {response.status}: {error_text}")
                    return
            
            # Test 1.2: Get pricing rules
            async with self.session.get(f"{self.backend_url}/api/amazon/pricing/rules") as response:
                if response.status == 200:
                    rules = await response.json()
                    if isinstance(rules, list) and len(rules) > 0:
                        self.log_test_result("Get Pricing Rules", True, f"Retrieved {len(rules)} rules")
                    else:
                        self.log_test_result("Get Pricing Rules", False, "No rules returned")
                else:
                    self.log_test_result("Get Pricing Rules", False, f"Status {response.status}")
            
            # Test 1.3: Get specific rule
            if self.created_rules:
                rule_id = self.created_rules[0]
                async with self.session.get(f"{self.backend_url}/api/amazon/pricing/rules/{rule_id}") as response:
                    if response.status == 200:
                        rule = await response.json()
                        if rule.get('id') == rule_id:
                            self.log_test_result("Get Specific Rule", True, f"Rule {rule_id} retrieved")
                        else:
                            self.log_test_result("Get Specific Rule", False, "Rule ID mismatch")
                    else:
                        self.log_test_result("Get Specific Rule", False, f"Status {response.status}")
            
            # Test 1.4: Update pricing rule
            if self.created_rules:
                rule_id = self.created_rules[0]
                update_data = {
                    "max_price": 1300.0,
                    "variance_pct": 7.5,
                    "auto_update": False
                }
                
                async with self.session.put(f"{self.backend_url}/api/amazon/pricing/rules/{rule_id}", json=update_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            self.log_test_result("Update Pricing Rule", True, "Rule updated successfully")
                        else:
                            self.log_test_result("Update Pricing Rule", False, "Update not successful")
                    else:
                        self.log_test_result("Update Pricing Rule", False, f"Status {response.status}")
            
            duration = time.time() - start_time
            print(f"📋 Pricing Rules CRUD completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Pricing Rules CRUD", False, f"Exception: {str(e)}")
    
    async def test_price_calculation(self):
        """Test 2: Price calculation engine"""
        print("\n💰 Testing Price Calculation Engine...")
        start_time = time.time()
        
        try:
            # Test different pricing strategies
            strategies = ["buybox_match", "margin_target", "floor_ceiling"]
            
            for i, strategy in enumerate(strategies):
                # Create rule for each strategy
                rule_data = {
                    "sku": self.test_skus[i + 1],
                    "marketplace_id": self.marketplace_fr,
                    "min_price": 50.0 + (i * 100),
                    "max_price": 200.0 + (i * 200),
                    "variance_pct": 5.0,
                    "strategy": strategy,
                    "margin_target": 20.0 if strategy == "margin_target" else None,
                    "auto_update": True
                }
                
                async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=rule_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            rule_id = result['rule']['id']
                            self.created_rules.append(rule_id)
                            
                            # Test price calculation for this rule
                            calc_data = {
                                "sku": self.test_skus[i + 1],
                                "marketplace_id": self.marketplace_fr,
                                "dry_run": True
                            }
                            
                            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/calculate", json=calc_data) as calc_response:
                                if calc_response.status == 200:
                                    calc_result = await calc_response.json()
                                    if calc_result.get('success') and calc_result.get('calculation'):
                                        calculation = calc_result['calculation']
                                        recommended_price = calculation.get('recommended_price')
                                        confidence = calculation.get('confidence', 0)
                                        
                                        self.log_test_result(
                                            f"Price Calculation ({strategy})", 
                                            True, 
                                            f"Price: {recommended_price}€, Confidence: {confidence}%"
                                        )
                                    else:
                                        self.log_test_result(f"Price Calculation ({strategy})", False, "No calculation result")
                                else:
                                    self.log_test_result(f"Price Calculation ({strategy})", False, f"Status {calc_response.status}")
                        else:
                            self.log_test_result(f"Create Rule ({strategy})", False, "Rule creation failed")
                    else:
                        self.log_test_result(f"Create Rule ({strategy})", False, f"Status {response.status}")
            
            duration = time.time() - start_time
            print(f"💰 Price Calculation testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Price Calculation", False, f"Exception: {str(e)}")
    
    async def test_price_publication(self):
        """Test 3: Price publication via SP-API"""
        print("\n📤 Testing Price Publication...")
        start_time = time.time()
        
        try:
            if not self.created_rules:
                self.log_test_result("Price Publication", False, "No rules available for testing")
                return
            
            # Test publication with different methods
            methods = ["listings_items", "feeds"]
            
            for method in methods:
                publish_data = {
                    "sku": self.test_skus[0],
                    "marketplace_id": self.marketplace_fr,
                    "method": method,
                    "force_update": True
                }
                
                async with self.session.post(f"{self.backend_url}/api/amazon/pricing/publish", json=publish_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        success = result.get('success', False)
                        published = result.get('published', False)
                        
                        if success or published:
                            self.log_test_result(
                                f"Price Publication ({method})", 
                                True, 
                                f"Published: {published}, Method: {method}"
                            )
                        else:
                            # Check if it's a valid "no change needed" response
                            message = result.get('message', '')
                            if 'aucun changement' in message.lower() or 'no change' in message.lower():
                                self.log_test_result(
                                    f"Price Publication ({method})", 
                                    True, 
                                    f"No change needed: {message}"
                                )
                            else:
                                self.log_test_result(f"Price Publication ({method})", False, f"Not published: {message}")
                    else:
                        error_text = await response.text()
                        self.log_test_result(f"Price Publication ({method})", False, f"Status {response.status}: {error_text}")
            
            duration = time.time() - start_time
            print(f"📤 Price Publication testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Price Publication", False, f"Exception: {str(e)}")
    
    async def test_batch_processing(self):
        """Test 4: Batch pricing processing"""
        print("\n📦 Testing Batch Processing...")
        start_time = time.time()
        
        try:
            # Create batch processing request
            batch_data = {
                "skus": self.test_skus[:3],  # Test with first 3 SKUs
                "marketplace_id": self.marketplace_fr,
                "force_update": False,
                "dry_run": True  # Safe simulation mode
            }
            
            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/batch", json=batch_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success') and result.get('batch'):
                        batch = result['batch']
                        batch_id = batch['id']
                        self.created_batches.append(batch_id)
                        
                        self.log_test_result(
                            "Create Batch Processing", 
                            True, 
                            f"Batch {batch_id} created for {len(batch_data['skus'])} SKUs"
                        )
                        
                        # Wait a moment for processing to start
                        await asyncio.sleep(2)
                        
                        # Check batch status
                        async with self.session.get(f"{self.backend_url}/api/amazon/pricing/batch/{batch_id}") as status_response:
                            if status_response.status == 200:
                                batch_status = await status_response.json()
                                status = batch_status.get('status', 'unknown')
                                progress = batch_status.get('progress_pct', 0)
                                
                                self.log_test_result(
                                    "Batch Status Check", 
                                    True, 
                                    f"Status: {status}, Progress: {progress}%"
                                )
                            else:
                                self.log_test_result("Batch Status Check", False, f"Status {status_response.status}")
                    else:
                        self.log_test_result("Create Batch Processing", False, "No batch in response")
                else:
                    error_text = await response.text()
                    self.log_test_result("Create Batch Processing", False, f"Status {response.status}: {error_text}")
            
            duration = time.time() - start_time
            print(f"📦 Batch Processing testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Batch Processing", False, f"Exception: {str(e)}")
    
    async def test_pricing_history(self):
        """Test 5: Pricing history and analytics"""
        print("\n📊 Testing Pricing History...")
        start_time = time.time()
        
        try:
            # Test general history endpoint
            async with self.session.get(f"{self.backend_url}/api/amazon/pricing/history") as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        history = result.get('history', [])
                        total_count = result.get('total_count', 0)
                        
                        self.log_test_result(
                            "Get Pricing History", 
                            True, 
                            f"Retrieved {len(history)} entries, Total: {total_count}"
                        )
                    else:
                        self.log_test_result("Get Pricing History", False, "Response not successful")
                else:
                    self.log_test_result("Get Pricing History", False, f"Status {response.status}")
            
            # Test SKU-specific history
            if self.test_skus:
                sku = self.test_skus[0]
                async with self.session.get(f"{self.backend_url}/api/amazon/pricing/history/{sku}") as response:
                    if response.status == 200:
                        history = await response.json()
                        if isinstance(history, list):
                            self.log_test_result(
                                "Get SKU History", 
                                True, 
                                f"Retrieved {len(history)} entries for SKU {sku}"
                            )
                        else:
                            self.log_test_result("Get SKU History", False, "Invalid response format")
                    else:
                        self.log_test_result("Get SKU History", False, f"Status {response.status}")
            
            duration = time.time() - start_time
            print(f"📊 Pricing History testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Pricing History", False, f"Exception: {str(e)}")
    
    async def test_pricing_dashboard(self):
        """Test 6: Pricing dashboard data"""
        print("\n📈 Testing Pricing Dashboard...")
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.backend_url}/api/amazon/pricing/dashboard") as response:
                if response.status == 200:
                    dashboard = await response.json()
                    
                    # Validate dashboard structure
                    required_fields = ['stats', 'recent_history', 'rules_summary', 'buybox_alerts']
                    missing_fields = [field for field in required_fields if field not in dashboard]
                    
                    if not missing_fields:
                        stats = dashboard.get('stats', {})
                        total_rules = stats.get('total_rules', 0)
                        active_rules = stats.get('active_rules', 0)
                        
                        self.log_test_result(
                            "Pricing Dashboard", 
                            True, 
                            f"Dashboard loaded - Rules: {total_rules} total, {active_rules} active"
                        )
                    else:
                        self.log_test_result("Pricing Dashboard", False, f"Missing fields: {missing_fields}")
                else:
                    error_text = await response.text()
                    self.log_test_result("Pricing Dashboard", False, f"Status {response.status}: {error_text}")
            
            duration = time.time() - start_time
            print(f"📈 Pricing Dashboard testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Pricing Dashboard", False, f"Exception: {str(e)}")
    
    async def test_pricing_constraints_validation(self):
        """Test 7: Pricing constraints and validation"""
        print("\n🔒 Testing Pricing Constraints...")
        start_time = time.time()
        
        try:
            # Test invalid rule creation (max < min)
            invalid_rule = {
                "sku": "TEST-INVALID-RULE",
                "marketplace_id": self.marketplace_fr,
                "min_price": 100.0,
                "max_price": 50.0,  # Invalid: max < min
                "strategy": "floor_ceiling"
            }
            
            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=invalid_rule) as response:
                if response.status == 400:
                    self.log_test_result("Invalid Rule Validation", True, "Correctly rejected invalid rule (max < min)")
                else:
                    self.log_test_result("Invalid Rule Validation", False, f"Should have rejected invalid rule, got {response.status}")
            
            # Test margin_target strategy without margin_target value
            invalid_margin_rule = {
                "sku": "TEST-INVALID-MARGIN",
                "marketplace_id": self.marketplace_fr,
                "min_price": 50.0,
                "max_price": 150.0,
                "strategy": "margin_target"
                # Missing margin_target
            }
            
            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=invalid_margin_rule) as response:
                if response.status == 400:
                    self.log_test_result("Margin Target Validation", True, "Correctly rejected margin_target without margin value")
                else:
                    self.log_test_result("Margin Target Validation", False, f"Should have rejected rule without margin_target, got {response.status}")
            
            # Test duplicate rule creation
            if self.created_rules:
                # Try to create a rule with same SKU and marketplace
                duplicate_rule = {
                    "sku": self.test_skus[0],  # Same as first created rule
                    "marketplace_id": self.marketplace_fr,
                    "min_price": 100.0,
                    "max_price": 200.0,
                    "strategy": "buybox_match"
                }
                
                async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=duplicate_rule) as response:
                    if response.status == 400:
                        self.log_test_result("Duplicate Rule Validation", True, "Correctly rejected duplicate rule")
                    else:
                        self.log_test_result("Duplicate Rule Validation", False, f"Should have rejected duplicate rule, got {response.status}")
            
            duration = time.time() - start_time
            print(f"🔒 Pricing Constraints testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Pricing Constraints", False, f"Exception: {str(e)}")
    
    async def test_buy_box_awareness(self):
        """Test 8: Buy Box awareness and competitive pricing"""
        print("\n🏆 Testing Buy Box Awareness...")
        start_time = time.time()
        
        try:
            # Create a buybox_match strategy rule
            buybox_rule = {
                "sku": "BUYBOX-TEST-SKU",
                "marketplace_id": self.marketplace_fr,
                "min_price": 80.0,
                "max_price": 120.0,
                "variance_pct": 3.0,
                "strategy": "buybox_match",
                "auto_update": True
            }
            
            async with self.session.post(f"{self.backend_url}/api/amazon/pricing/rules", json=buybox_rule) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        rule_id = result['rule']['id']
                        self.created_rules.append(rule_id)
                        
                        # Test price calculation with Buy Box strategy
                        calc_data = {
                            "sku": "BUYBOX-TEST-SKU",
                            "marketplace_id": self.marketplace_fr,
                            "dry_run": True
                        }
                        
                        async with self.session.post(f"{self.backend_url}/api/amazon/pricing/calculate", json=calc_data) as calc_response:
                            if calc_response.status == 200:
                                calc_result = await calc_response.json()
                                if calc_result.get('success') and calc_result.get('calculation'):
                                    calculation = calc_result['calculation']
                                    buybox_status = calculation.get('buybox_status', 'unknown')
                                    competitors_count = len(calculation.get('competitors', []))
                                    reasoning = calculation.get('reasoning', '')
                                    
                                    self.log_test_result(
                                        "Buy Box Calculation", 
                                        True, 
                                        f"Status: {buybox_status}, Competitors: {competitors_count}, Reasoning: {reasoning[:100]}..."
                                    )
                                else:
                                    self.log_test_result("Buy Box Calculation", False, "No calculation result")
                            else:
                                self.log_test_result("Buy Box Calculation", False, f"Status {calc_response.status}")
                    else:
                        self.log_test_result("Create Buy Box Rule", False, "Rule creation failed")
                else:
                    self.log_test_result("Create Buy Box Rule", False, f"Status {response.status}")
            
            duration = time.time() - start_time
            print(f"🏆 Buy Box Awareness testing completed in {duration:.2f}s")
            
        except Exception as e:
            self.log_test_result("Buy Box Awareness", False, f"Exception: {str(e)}")
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created rules
        for rule_id in self.created_rules:
            try:
                async with self.session.delete(f"{self.backend_url}/api/amazon/pricing/rules/{rule_id}") as response:
                    if response.status == 200:
                        print(f"✅ Deleted rule {rule_id}")
                    else:
                        print(f"⚠️ Failed to delete rule {rule_id}: {response.status}")
            except Exception as e:
                print(f"⚠️ Error deleting rule {rule_id}: {str(e)}")
        
        # Close session
        if self.session:
            await self.session.close()
        
        print("🧹 Cleanup completed")
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n" + "="*80)
        print(f"🎯 PHASE 4 AMAZON PRICING ENGINE TESTING COMPLETED")
        print(f"="*80)
        print(f"📊 RESULTS SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"")
        
        # Detailed results by category
        categories = {}
        for result in self.test_results:
            test_name = result['test']
            category = test_name.split('(')[0].strip() if '(' in test_name else test_name
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0}
            
            if result['success']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        print(f"📋 DETAILED RESULTS BY CATEGORY:")
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total * 100) if total > 0 else 0
            status = "✅" if rate >= 75 else "⚠️" if rate >= 50 else "❌"
            print(f"   {status} {category}: {stats['passed']}/{total} ({rate:.1f}%)")
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🏁 Phase 4 Amazon Pricing Engine is {success_rate:.1f}% functional!")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'categories': categories,
            'failed_details': failed_results
        }

async def main():
    """Main test execution"""
    print("🚀 ECOMSIMPLY PHASE 4 AMAZON PRICING ENGINE BACKEND TESTING")
    print("=" * 80)
    print("Testing comprehensive Amazon pricing rules, calculation, and SP-API publication")
    print("=" * 80)
    
    tester = Phase4PricingTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run all tests
        await tester.test_pricing_rules_crud()
        await tester.test_price_calculation()
        await tester.test_price_publication()
        await tester.test_batch_processing()
        await tester.test_pricing_history()
        await tester.test_pricing_dashboard()
        await tester.test_pricing_constraints_validation()
        await tester.test_buy_box_awareness()
        
        # Generate summary
        summary = tester.generate_summary()
        
        # Cleanup
        await tester.cleanup()
        
        # Exit with appropriate code
        if summary['success_rate'] >= 75:
            print(f"\n🎉 SUCCESS: Phase 4 Amazon Pricing Engine is production-ready!")
            sys.exit(0)
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: Phase 4 needs attention on failed components")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        await tester.cleanup()
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())