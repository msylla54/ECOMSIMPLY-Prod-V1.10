#!/usr/bin/env python3
"""
ECOMSIMPLY - Environment Variables Validation Script
Vérifie que toutes les clés API requises sont présentes pour le mode REAL
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load backend .env file
    backend_env_path = Path(__file__).parent.parent / "backend" / ".env"
    if backend_env_path.exists():
        load_dotenv(backend_env_path)
        print(f"✅ Loaded environment from {backend_env_path}")
    
    # Load frontend .env file
    frontend_env_path = Path(__file__).parent.parent / "frontend" / ".env"
    if frontend_env_path.exists():
        load_dotenv(frontend_env_path)
        print(f"✅ Loaded environment from {frontend_env_path}")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment only")

# Configuration des variables par domaine et priorité
INTEGRATIONS_CONFIG = {
    "P0_CRITICAL": {
        "description": "Services critiques - échec = service indisponible",
        "integrations": {
            "openai": {
                "name": "OpenAI GPT Content Generation",
                "required_vars": ["OPENAI_API_KEY"],
                "optional_vars": [],
                "validation_func": "validate_openai_key",
                "healthcheck": "/api/status/ai"
            },
            "fal_ai": {
                "name": "FAL.ai Flux Pro Image Generation", 
                "required_vars": ["FAL_KEY"],
                "optional_vars": [],
                "validation_func": "validate_fal_key",
                "healthcheck": "/api/status/images"
            },
            "stripe": {
                "name": "Stripe Payments & Subscriptions",
                "required_vars": ["STRIPE_API_KEY"],
                "optional_vars": ["STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID_PRO", "STRIPE_PRICE_ID_PREMIUM"],
                "validation_func": "validate_stripe_key",
                "healthcheck": "/api/status/payments"
            },
            "stripe_frontend": {
                "name": "Stripe Frontend Publishable Key",
                "required_vars": ["REACT_APP_STRIPE_PUBLISHABLE_KEY"],
                "optional_vars": [],
                "validation_func": "validate_stripe_publishable_key",
                "healthcheck": None
            },
            "database": {
                "name": "MongoDB Primary Database",
                "required_vars": ["MONGO_URL"],
                "optional_vars": ["DB_NAME"],
                "validation_func": "validate_mongo_url",
                "healthcheck": "integrated"
            },
            "security": {
                "name": "JWT & Encryption Security",
                "required_vars": ["JWT_SECRET", "ENCRYPTION_KEY"],
                "optional_vars": [],
                "validation_func": "validate_security_keys",
                "healthcheck": "integrated"
            }
        }
    },
    "P1_MAJOR": {
        "description": "Services majeurs - échec = fonctionnalité dégradée",
        "integrations": {
            "email": {
                "name": "SMTP Email Service",
                "required_vars": ["SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD"],
                "optional_vars": ["SMTP_PORT", "SMTP_USE_SSL", "SENDER_EMAIL"],
                "validation_func": "validate_smtp_config",
                "healthcheck": "/api/status/email"
            },
            "shopify": {
                "name": "Shopify Publication API",
                "required_vars": ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN"],
                "optional_vars": [],
                "validation_func": "validate_shopify_config",
                "healthcheck": "/api/status/publication"
            },
            "woocommerce": {
                "name": "WooCommerce Publication API", 
                "required_vars": ["WOO_STORE_URL", "WOO_CONSUMER_KEY", "WOO_CONSUMER_SECRET"],
                "optional_vars": [],
                "validation_func": "validate_woocommerce_config",
                "healthcheck": "/api/status/publication"
            },
            "prestashop": {
                "name": "PrestaShop Publication API",
                "required_vars": ["PRESTA_STORE_URL", "PRESTA_API_KEY"],
                "optional_vars": [],
                "validation_func": "validate_prestashop_config", 
                "healthcheck": "/api/status/publication"
            }
        }
    },
    "P2_OPTIONAL": {
        "description": "Services optionnels - échec = performance dégradée",
        "integrations": {
            "redis": {
                "name": "Redis Cache & Sessions",
                "required_vars": [],
                "optional_vars": ["REDIS_URL", "REDIS_PASSWORD"],
                "validation_func": "validate_redis_config",
                "healthcheck": "/api/status/redis"
            },
            "proxy_scraping": {
                "name": "Proxy Services for Scraping",
                "required_vars": [],
                "optional_vars": ["PROXY_PROVIDER", "SCRAPERAPI_KEY", "BRIGHT_DATA_KEY"],
                "validation_func": "validate_proxy_config",
                "healthcheck": "/api/status/scraping"
            },
            "backup": {
                "name": "AWS S3 External Backups",
                "required_vars": [],
                "optional_vars": ["BACKUP_S3_BUCKET", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                "validation_func": "validate_backup_config",
                "healthcheck": "/api/status/backup"
            },
            "monitoring": {
                "name": "External Monitoring & Analytics",
                "required_vars": [],
                "optional_vars": ["MONITORING_ENDPOINT", "SENTRY_DSN", "DATADOG_API_KEY"],
                "validation_func": "validate_monitoring_config",
                "healthcheck": "/api/status/monitoring"
            }
        }
    }
}

class EnvironmentValidator:
    """Validateur pour les variables d'environnement ECOMSIMPLY"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.issues = []
        self.warnings = []
        self.success = []
        
    def validate_all(self, mode: str = "production") -> Dict[str, Any]:
        """Valide toutes les intégrations selon le mode"""
        
        print(f"🔍 ECOMSIMPLY Environment Validation - Mode: {mode.upper()}")
        print("=" * 60)
        
        results = {
            "mode": mode,
            "strict": self.strict_mode,
            "timestamp": self._get_timestamp(),
            "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
            "details": {},
            "missing_critical": [],
            "missing_optional": []
        }
        
        # Vérification du mode Mock vs Real
        mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
        print(f"📋 Mock Mode: {'Enabled' if mock_mode else 'Disabled'}")
        
        if mock_mode and mode == "production":
            self.warnings.append("MOCK_MODE is enabled but production mode requested")
        
        # Validation par priorité
        for priority, config in INTEGRATIONS_CONFIG.items():
            print(f"\n📊 {priority}: {config['description']}")
            print("-" * 40)
            
            results["details"][priority] = {}
            
            for service_key, service_config in config["integrations"].items():
                result = self._validate_integration(service_key, service_config, mode, mock_mode)
                results["details"][priority][service_key] = result
                results["summary"]["total"] += 1
                
                if result["status"] == "passed":
                    results["summary"]["passed"] += 1
                    print(f"✅ {service_config['name']}: OK")
                elif result["status"] == "warning":
                    results["summary"]["warnings"] += 1 
                    print(f"⚠️  {service_config['name']}: {result['message']}")
                else:
                    results["summary"]["failed"] += 1
                    print(f"❌ {service_config['name']}: {result['message']}")
                    
                    if priority == "P0_CRITICAL":
                        results["missing_critical"].extend(result["missing_vars"])
                    else:
                        results["missing_optional"].extend(result["missing_vars"])
        
        # Résumé final
        self._print_summary(results)
        return results
    
    def _validate_integration(self, service_key: str, config: Dict, mode: str, mock_mode: bool) -> Dict[str, Any]:
        """Valide une intégration spécifique"""
        
        result = {
            "service": config["name"],
            "status": "passed",
            "message": "All variables present",
            "missing_vars": [],
            "optional_missing": [],
            "validation_details": {}
        }
        
        # Vérifier les variables requises
        missing_required = []
        for var in config["required_vars"]:
            if not os.environ.get(var):
                missing_required.append(var)
        
        # Vérifier les variables optionnelles
        missing_optional = []
        for var in config["optional_vars"]:
            if not os.environ.get(var):
                missing_optional.append(var)
        
        # Logique de validation selon le service et le mode
        if service_key in ["shopify", "woocommerce", "prestashop", "proxy_scraping"] and mock_mode:
            # Services avec mock disponible - pas critique si mode mock
            if missing_required:
                result["status"] = "warning"
                result["message"] = f"Mock mode enabled - missing real API keys: {', '.join(missing_required)}"
        elif missing_required:
            # Variables critiques manquantes
            result["status"] = "failed"
            result["message"] = f"Missing required variables: {', '.join(missing_required)}"
            result["missing_vars"] = missing_required
        elif missing_optional:
            # Variables optionnelles manquantes - warning seulement
            result["status"] = "warning" if self.strict_mode else "passed"
            result["message"] = f"Missing optional variables: {', '.join(missing_optional)}"
            result["optional_missing"] = missing_optional
        
        # Validation spécialisée si disponible
        if hasattr(self, config["validation_func"]):
            validator = getattr(self, config["validation_func"])
            validation_result = validator(config)
            result["validation_details"] = validation_result
        
        return result
    
    def validate_openai_key(self, config: Dict) -> Dict[str, Any]:
        """Validation spécifique OpenAI"""
        key = os.environ.get('OPENAI_API_KEY', '')
        
        if not key:
            return {"valid": False, "reason": "Key missing"}
        
        if not key.startswith('sk-'):
            return {"valid": False, "reason": "Invalid key format (should start with sk-)"}
        
        if len(key) < 20:
            return {"valid": False, "reason": "Key too short"}
            
        return {"valid": True, "key_length": len(key), "prefix": "sk-***"}
    
    def validate_fal_key(self, config: Dict) -> Dict[str, Any]:
        """Validation spécifique FAL.ai"""
        key = os.environ.get('FAL_KEY', '')
        
        if not key:
            return {"valid": False, "reason": "Key missing"}
        
        if ':' not in key:
            return {"valid": False, "reason": "Invalid key format (should contain :)"}
            
        return {"valid": True, "format": "valid"}
    
    def validate_stripe_key(self, config: Dict) -> Dict[str, Any]:
        """Validation spécifique Stripe"""
        key = os.environ.get('STRIPE_API_KEY', '')
        
        if not key:
            return {"valid": False, "reason": "Key missing"}
        
        if not key.startswith('sk_'):
            return {"valid": False, "reason": "Invalid secret key format"}
        
        is_live = key.startswith('sk_live_')
        is_test = key.startswith('sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        
        return {
            "valid": True,
            "environment": "live" if is_live else "test" if is_test else "unknown",
            "recommendation": "Use live keys in production" if not is_live else None
        }
    
    def validate_stripe_publishable_key(self, config: Dict) -> Dict[str, Any]:
        """Validation clé publishable Stripe"""
        key = os.environ.get('REACT_APP_STRIPE_PUBLISHABLE_KEY', '')
        
        if not key:
            return {"valid": False, "reason": "Key missing"}
        
        if not key.startswith('pk_'):
            return {"valid": False, "reason": "Invalid publishable key format"}
            
        return {"valid": True, "environment": "live" if 'live' in key else "test"}
    
    def validate_mongo_url(self, config: Dict) -> Dict[str, Any]:
        """Validation MongoDB URL"""
        url = os.environ.get('MONGO_URL', '')
        
        if not url:
            return {"valid": False, "reason": "URL missing"}
        
        if not url.startswith('mongodb://') and not url.startswith('mongodb+srv://'):
            return {"valid": False, "reason": "Invalid MongoDB URL format"}
            
        return {"valid": True, "protocol": "srv" if "srv" in url else "standard"}
    
    def validate_security_keys(self, config: Dict) -> Dict[str, Any]:
        """Validation clés de sécurité"""
        jwt_secret = os.environ.get('JWT_SECRET', '')
        encryption_key = os.environ.get('ENCRYPTION_KEY', '')
        
        issues = []
        
        if len(jwt_secret) < 32:
            issues.append("JWT_SECRET too short (minimum 32 characters)")
        
        if not encryption_key:
            issues.append("ENCRYPTION_KEY missing")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_smtp_config(self, config: Dict) -> Dict[str, Any]:
        """Validation configuration SMTP"""
        server = os.environ.get('SMTP_SERVER', '')
        username = os.environ.get('SMTP_USERNAME', '')
        password = os.environ.get('SMTP_PASSWORD', '')
        
        if not all([server, username, password]):
            return {"valid": False, "reason": "Missing SMTP credentials"}
            
        return {"valid": True, "server": server}
    
    def validate_shopify_config(self, config: Dict) -> Dict[str, Any]:
        """Validation Shopify"""
        url = os.environ.get('SHOPIFY_STORE_URL', '')
        token = os.environ.get('SHOPIFY_ACCESS_TOKEN', '')
        
        if url and not url.endswith('.myshopify.com'):
            return {"valid": False, "reason": "Invalid Shopify store URL format"}
            
        return {"valid": bool(url and token)}
    
    def validate_woocommerce_config(self, config: Dict) -> Dict[str, Any]:
        """Validation WooCommerce"""
        url = os.environ.get('WOO_STORE_URL', '')
        key = os.environ.get('WOO_CONSUMER_KEY', '')
        secret = os.environ.get('WOO_CONSUMER_SECRET', '')
        
        return {"valid": bool(url and key and secret)}
    
    def validate_prestashop_config(self, config: Dict) -> Dict[str, Any]:
        """Validation PrestaShop"""
        url = os.environ.get('PRESTA_STORE_URL', '')
        key = os.environ.get('PRESTA_API_KEY', '')
        
        return {"valid": bool(url and key)}
    
    def validate_redis_config(self, config: Dict) -> Dict[str, Any]:
        """Validation Redis"""
        url = os.environ.get('REDIS_URL', '')
        return {"valid": url.startswith('redis://') if url else True, "configured": bool(url)}
    
    def validate_proxy_config(self, config: Dict) -> Dict[str, Any]:
        """Validation services proxy"""
        provider = os.environ.get('PROXY_PROVIDER', 'none')
        return {"valid": True, "provider": provider, "configured": provider != 'none'}
    
    def validate_backup_config(self, config: Dict) -> Dict[str, Any]:
        """Validation sauvegarde AWS S3"""
        bucket = os.environ.get('BACKUP_S3_BUCKET', '')
        access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        
        return {"valid": True, "configured": bool(bucket and access_key and secret_key)}
    
    def validate_monitoring_config(self, config: Dict) -> Dict[str, Any]:
        """Validation monitoring externe"""
        endpoint = os.environ.get('MONITORING_ENDPOINT', '')
        sentry = os.environ.get('SENTRY_DSN', '')
        datadog = os.environ.get('DATADOG_API_KEY', '')
        
        return {
            "valid": True, 
            "services": {
                "monitoring": bool(endpoint),
                "sentry": bool(sentry),
                "datadog": bool(datadog)
            }
        }
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Affiche le résumé final"""
        
        summary = results["summary"]
        print(f"\n{'='*60}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Integrations: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        
        if results["missing_critical"]:
            print(f"\n🚨 CRITICAL MISSING VARIABLES:")
            for var in set(results["missing_critical"]):
                print(f"   - {var}")
        
        if results["missing_optional"]:
            print(f"\n📝 OPTIONAL MISSING VARIABLES:")
            for var in set(results["missing_optional"]):
                print(f"   - {var}")
        
        # Exit code logic
        if results["missing_critical"]:
            print(f"\n❌ VALIDATION FAILED: Critical variables missing")
            print("🔧 Add missing variables and run validation again")
            return 1
        elif summary["failed"] > 0:
            print(f"\n⚠️  VALIDATION ISSUES: Some integrations have problems")
            return 2 if self.strict_mode else 0
        else:
            print(f"\n✅ VALIDATION SUCCESSFUL: All integrations ready")
            return 0
    
    def _get_timestamp(self) -> str:
        """Timestamp pour les résultats"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

def main():
    parser = argparse.ArgumentParser(
        description="ECOMSIMPLY Environment Variables Validation Script"
    )
    parser.add_argument(
        "--mode", 
        choices=["development", "staging", "production"], 
        default="production",
        help="Validation mode (default: production)"
    )
    parser.add_argument(
        "--strict", 
        action="store_true",
        help="Strict mode - warnings become errors"
    )
    parser.add_argument(
        "--output", 
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🚀 ECOMSIMPLY Environment Validation")
        print(f"Mode: {args.mode}, Strict: {args.strict}")
        print()
    
    validator = EnvironmentValidator(strict_mode=args.strict)
    results = validator.validate_all(mode=args.mode)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {args.output}")
    
    # Determine exit code
    if results["missing_critical"]:
        sys.exit(1)  # Critical failure
    elif results["summary"]["failed"] > 0:
        sys.exit(2 if args.strict else 0)  # Issues found
    else:
        sys.exit(0)  # All good

if __name__ == "__main__":
    main()