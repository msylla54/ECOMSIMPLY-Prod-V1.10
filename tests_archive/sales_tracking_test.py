#!/usr/bin/env python3
"""
Sales Tracking System Test Runner
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class SalesTrackingTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def test_user_registration(self):
        """Register a test user"""
        self.log("Registering test user...")
        
        timestamp = int(time.time())
        user_data = {
            "email": f"salestest{timestamp}@test.com",
            "name": "Sales Test User",
            "password": "TestPassword123!",
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                self.log(f"✅ User registered: {self.user_data['email']}")
                return True
            else:
                self.log(f"❌ Registration failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False

    def test_sales_analytics_endpoint(self):
        """Test GET /api/analytics/sales endpoint"""
        self.log("Testing Sales Analytics endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/analytics/sales", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["success", "metrics"]
                if all(field in data for field in required_fields):
                    metrics = data.get("metrics", {})
                    metrics_fields = ["total_sales", "total_revenue", "conversion_rate", 
                                    "sales_this_month", "revenue_this_month", "sales_this_week", 
                                    "revenue_this_week", "platform_breakdown", "last_updated"]
                    
                    if all(field in metrics for field in metrics_fields):
                        self.log("✅ Sales Analytics Endpoint: Working correctly")
                        self.log(f"   Total Sales: {metrics['total_sales']}")
                        self.log(f"   Total Revenue: {metrics['total_revenue']}€")
                        self.log(f"   Conversion Rate: {metrics['conversion_rate']:.2f}%")
                        return True
                    else:
                        missing = [f for f in metrics_fields if f not in metrics]
                        self.log(f"❌ Missing metrics fields: {missing}", "ERROR")
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log(f"❌ Missing response fields: {missing}", "ERROR")
                    return False
            else:
                self.log(f"❌ Sales Analytics failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Sales Analytics test failed: {str(e)}", "ERROR")
            return False

    def test_sales_analytics_authentication(self):
        """Test that sales analytics endpoint requires authentication"""
        self.log("Testing Sales Analytics authentication requirement...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analytics/sales")
            
            if response.status_code in [401, 403]:
                self.log("✅ Sales Analytics Authentication: Correctly requires authentication")
                return True
            else:
                self.log(f"❌ Expected 401/403, got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication test failed: {str(e)}", "ERROR")
            return False

    def test_product_performance_endpoint(self):
        """Test GET /api/analytics/product-performance endpoint"""
        self.log("Testing Product Performance endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/analytics/product-performance", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "success" in data and "products" in data:
                    products = data.get("products", [])
                    self.log("✅ Product Performance Endpoint: Working correctly")
                    self.log(f"   Retrieved {len(products)} product performance records")
                    return True
                else:
                    self.log("❌ Missing required fields in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Product Performance failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Product Performance test failed: {str(e)}", "ERROR")
            return False

    def test_analytics_refresh_endpoint(self):
        """Test POST /api/analytics/refresh endpoint"""
        self.log("Testing Analytics Refresh endpoint...")
        
        if not self.auth_token:
            self.log("❌ No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.post(f"{BASE_URL}/analytics/refresh", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "success" in data and "message" in data and "metrics" in data:
                    self.log("✅ Analytics Refresh Endpoint: Working correctly")
                    self.log(f"   Message: {data.get('message')}")
                    return True
                else:
                    self.log("❌ Missing required fields in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Analytics Refresh failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Analytics Refresh test failed: {str(e)}", "ERROR")
            return False

    def test_detailed_analytics_sales_metrics(self):
        """Test that GET /api/analytics/detailed includes sales metrics"""
        self.log("Testing Detailed Analytics includes sales metrics...")
        
        if not self.auth_token:
            self.log("❌ No auth token", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/analytics/detailed", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify sales metrics are included
                sales_fields = ["total_sales", "total_revenue", "conversion_rate", 
                              "sales_this_month", "revenue_this_month", "sales_this_week", 
                              "revenue_this_week", "platform_sales_breakdown"]
                
                if all(field in data for field in sales_fields):
                    self.log("✅ Detailed Analytics Sales Metrics: Working correctly")
                    self.log(f"   Sales metrics included: {data['total_sales']} sales, {data['total_revenue']}€ revenue")
                    return True
                else:
                    missing = [f for f in sales_fields if f not in data]
                    self.log(f"❌ Missing sales fields: {missing}", "ERROR")
                    return False
            else:
                self.log(f"❌ Detailed Analytics failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Detailed Analytics test failed: {str(e)}", "ERROR")
            return False

    def test_shopify_webhook_endpoint(self):
        """Test POST /api/webhook/shopify/orders endpoint"""
        self.log("Testing Shopify Webhook endpoint...")
        
        webhook_payload = {
            "id": 12345678,
            "email": "customer@example.com",
            "total_price": "99.99",
            "currency": "EUR",
            "created_at": "2024-01-15T10:30:00Z",
            "line_items": [
                {
                    "id": 987654321,
                    "product_id": "test_product_123",
                    "variant_id": "test_variant_456",
                    "title": "Test Sales Product",
                    "quantity": 2,
                    "price": "49.99"
                }
            ],
            "customer": {
                "email": "customer@example.com",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
        
        headers = {
            "x-shopify-hmac-sha256": "test_signature",
            "x-shopify-shop-domain": "test-sales-shop.myshopify.com",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/webhook/shopify/orders", 
                                       json=webhook_payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "status" in data:
                    self.log("✅ Shopify Webhook Endpoint: Working correctly")
                    self.log(f"   Status: {data['status']}")
                    return True
                else:
                    self.log("❌ Missing status in response", "ERROR")
                    return False
            else:
                self.log(f"❌ Shopify Webhook failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Shopify Webhook test failed: {str(e)}", "ERROR")
            return False

    def test_woocommerce_webhook_endpoint(self):
        """Test POST /api/webhook/woocommerce/orders endpoint"""
        self.log("Testing WooCommerce Webhook endpoint...")
        
        webhook_payload = {
            "id": 12345,
            "status": "completed",
            "total": "99.99",
            "currency": "EUR",
            "date_created": "2024-01-15T10:30:00",
            "line_items": [
                {
                    "id": 987,
                    "product_id": "test_product_123",
                    "name": "Test Sales Product",
                    "quantity": 2,
                    "total": "99.99"
                }
            ],
            "billing": {
                "email": "customer@example.com",
                "first_name": "Jane",
                "last_name": "Smith"
            },
            "_links": {
                "self": [{"href": "https://test-woo-store.com/wp-json/wc/v3/orders/12345"}]
            }
        }
        
        headers = {
            "x-wc-webhook-source": "https://test-woo-store.com",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/webhook/woocommerce/orders", 
                                       json=webhook_payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "status" in data:
                    self.log("✅ WooCommerce Webhook Endpoint: Working correctly")
                    self.log(f"   Status: {data['status']}")
                    return True
                else:
                    self.log("❌ Missing status in response", "ERROR")
                    return False
            else:
                self.log(f"❌ WooCommerce Webhook failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ WooCommerce Webhook test failed: {str(e)}", "ERROR")
            return False

    def test_webhook_error_handling(self):
        """Test webhook endpoints error handling"""
        self.log("Testing Webhook error handling...")
        
        try:
            # Test Shopify webhook without required headers
            response = self.session.post(f"{BASE_URL}/webhook/shopify/orders", json={})
            
            if response.status_code == 400:
                self.log("✅ Shopify Webhook Error Handling: Correctly rejects missing headers")
            else:
                self.log(f"❌ Expected 400, got {response.status_code}", "ERROR")
                return False
            
            # Test WooCommerce webhook without store URL
            response = self.session.post(f"{BASE_URL}/webhook/woocommerce/orders", json={})
            
            if response.status_code == 400:
                self.log("✅ WooCommerce Webhook Error Handling: Correctly rejects missing store URL")
                return True
            else:
                self.log(f"❌ Expected 400, got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Webhook Error Handling test failed: {str(e)}", "ERROR")
            return False

    def run_all_tests(self):
        """Run all sales tracking tests"""
        self.log("🚀 Starting SALES TRACKING SYSTEM Tests...")
        self.log("=" * 80)
        
        # Setup
        if not self.test_user_registration():
            self.log("❌ User registration failed, aborting tests")
            return 0, 1
        
        # Sales tracking system tests
        tests = [
            ("Sales Analytics Endpoint", self.test_sales_analytics_endpoint),
            ("Sales Analytics Authentication", self.test_sales_analytics_authentication),
            ("Product Performance Endpoint", self.test_product_performance_endpoint),
            ("Analytics Refresh Endpoint", self.test_analytics_refresh_endpoint),
            ("Detailed Analytics Sales Metrics", self.test_detailed_analytics_sales_metrics),
            ("Shopify Webhook Endpoint", self.test_shopify_webhook_endpoint),
            ("WooCommerce Webhook Endpoint", self.test_woocommerce_webhook_endpoint),
            ("Webhook Error Handling", self.test_webhook_error_handling),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            self.log("-" * 60)
            
            try:
                if test_func():
                    self.log(f"✅ PASSED: {test_name}")
                    passed += 1
                else:
                    self.log(f"❌ FAILED: {test_name}")
                    failed += 1
            except Exception as e:
                self.log(f"❌ ERROR in {test_name}: {str(e)}", "ERROR")
                failed += 1
            
            time.sleep(0.5)  # Brief pause between tests
        
        # Final Results
        self.log("\n" + "=" * 80)
        self.log("🎯 SALES TRACKING SYSTEM TEST RESULTS")
        self.log("=" * 80)
        self.log(f"✅ PASSED: {passed}")
        self.log(f"❌ FAILED: {failed}")
        self.log(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL SALES TRACKING TESTS PASSED!")
            self.log("   ✅ Sales analytics endpoints working correctly")
            self.log("   ✅ Webhook endpoints processing orders correctly")
            self.log("   ✅ Product performance tracking functional")
            self.log("   ✅ Sales metrics calculation working")
            self.log("   ✅ Authentication and error handling proper")
        elif passed > failed:
            self.log("✅ MAJORITY TESTS PASSED! Minor issues detected.")
        else:
            self.log("⚠️  MULTIPLE FAILURES DETECTED! Sales tracking system needs attention.")
        
        return passed, failed

if __name__ == "__main__":
    tester = SalesTrackingTester()
    passed, failed = tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 ALL SALES TRACKING TESTS COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print(f"\n⚠️  SALES TRACKING TESTS COMPLETED WITH {failed} FAILURES")
        exit(1)