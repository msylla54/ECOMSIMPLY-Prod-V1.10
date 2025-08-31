"""
Test Environment Template Validation - ECOMSIMPLY
Vérifie que le template .env.example contient toutes les clés requises
"""

import pytest
import json
import os
from pathlib import Path

def load_required_integrations():
    """Charge la configuration des intégrations requises"""
    config_path = Path(__file__).parent.parent / "required_integrations.json"
    with open(config_path, 'r') as f:
        return json.load(f)

def load_env_template():
    """Charge le template .env.example"""
    template_path = Path(__file__).parent.parent / ".env.example"
    with open(template_path, 'r') as f:
        return f.read()

@pytest.fixture
def required_integrations():
    """Fixture pour les intégrations requises"""
    return load_required_integrations()

@pytest.fixture
def env_template():
    """Fixture pour le template d'environnement"""
    return load_env_template()

def test_env_template_exists():
    """Vérifie que le template .env.example existe"""
    template_path = Path(__file__).parent.parent / ".env.example"
    assert template_path.exists(), ".env.example file must exist"

def test_required_integrations_json_exists():
    """Vérifie que required_integrations.json existe"""
    config_path = Path(__file__).parent.parent / "required_integrations.json"
    assert config_path.exists(), "required_integrations.json file must exist"

def test_required_integrations_json_schema(required_integrations):
    """Vérifie la structure du JSON des intégrations requises"""
    assert isinstance(required_integrations, list), "Required integrations must be a list"
    
    for integration in required_integrations:
        # Champs obligatoires
        required_fields = ["domain", "provider", "service", "env", "files", "required_in_real", "status"]
        for field in required_fields:
            assert field in integration, f"Integration must have '{field}' field"
        
        # Vérifications de types
        assert isinstance(integration["env"], list), "env field must be a list"
        assert isinstance(integration["files"], list), "files field must be a list"
        assert isinstance(integration["status"], dict), "status field must be a dict"
        
        # Status doit avoir les champs requis
        status_fields = ["present", "missing", "configured"]
        for field in status_fields:
            assert field in integration["status"], f"Status must have '{field}' field"

def test_all_required_env_vars_in_template(required_integrations, env_template):
    """Vérifie que toutes les variables d'environnement requises sont dans le template"""
    
    # Extraire toutes les variables d'environnement requises
    all_required_vars = set()
    for integration in required_integrations:
        all_required_vars.update(integration["env"])
    
    # Variables manquantes dans le template
    missing_vars = []
    for var in all_required_vars:
        if var not in env_template:
            missing_vars.append(var)
    
    assert len(missing_vars) == 0, f"Missing environment variables in template: {missing_vars}"

def test_critical_integrations_marked_correctly(required_integrations):
    """Vérifie que les intégrations critiques sont marquées P0"""
    
    critical_services = ["openai", "stripe", "fal_ai", "mongodb", "security"]
    
    for integration in required_integrations:
        if integration["provider"] in critical_services:
            assert integration["required_in_real"] == True, f"{integration['provider']} should be required in real mode"
            assert integration.get("priority", "P2") == "P0", f"{integration['provider']} should be P0 priority"

def test_mock_integrations_have_fallback(required_integrations):
    """Vérifie que les intégrations mock ont des fallbacks disponibles"""
    
    mock_services = ["shopify", "woocommerce", "prestashop", "proxy_services"]
    
    for integration in required_integrations:
        if integration["provider"] in mock_services:
            assert "fallback_available" in integration, f"{integration['provider']} should specify fallback availability"
            assert integration["fallback_available"] == True, f"{integration['provider']} should have fallback available"

def test_healthcheck_endpoints_specified(required_integrations):
    """Vérifie que les endpoints de healthcheck sont spécifiés"""
    
    for integration in required_integrations:
        healthcheck = integration.get("healthcheck")
        
        # Les intégrations critiques doivent avoir un healthcheck
        if integration["required_in_real"] and integration.get("priority") == "P0":
            # Exception: les intégrations frontend n'ont pas besoin d'healthcheck backend séparé
            if integration["domain"].endswith("_frontend"):
                continue
                
            assert healthcheck is not None, f"{integration['provider']} (P0) must have healthcheck endpoint"
            
            # Si ce n'est pas "integrated", ça doit être un endpoint API
            if healthcheck and healthcheck != "integrated" and healthcheck is not None:
                assert healthcheck.startswith("/api/status/"), f"Healthcheck must be API endpoint: {healthcheck}"

def test_env_template_has_documentation():
    """Vérifie que le template .env.example est bien documenté"""
    env_template = load_env_template()
    
    # Vérifier la présence de sections importantes
    required_sections = [
        "SECURITY & AUTHENTICATION", 
        "AI & CONTENT GENERATION",
        "PAYMENTS & SUBSCRIPTIONS",
        "E-COMMERCE PUBLICATION",
        "EMAIL & NOTIFICATIONS"
    ]
    
    for section in required_sections:
        assert section in env_template, f"Template must document section: {section}"

def test_no_hardcoded_secrets_in_template():
    """Vérifie qu'il n'y a pas de secrets hardcodés dans le template"""
    env_template = load_env_template()
    
    # Patterns suspects à éviter
    suspicious_patterns = [
        "sk-",  # OpenAI/Stripe real keys
        "pk_live_",  # Stripe live publishable
        "shpat_",  # Shopify access tokens
        "mongodb://admin:",  # MongoDB avec credentials
    ]
    
    for pattern in suspicious_patterns:
        # Autoriser les exemples explicites
        if pattern in env_template and "your_" not in env_template.lower():
            assert False, f"Template should not contain real credentials pattern: {pattern}"

def test_required_vs_optional_vars_documented():
    """Vérifie que les variables requises vs optionnelles sont documentées"""
    env_template = load_env_template()
    
    # Vérifier que le template indique la criticité
    assert "CRITICAL" in env_template, "Template must indicate critical variables"
    assert "OPTIONAL" in env_template, "Template must indicate optional variables"

def test_integration_files_exist(required_integrations):
    """Vérifie que les fichiers référencés dans les intégrations existent"""
    
    project_root = Path(__file__).parent.parent
    
    for integration in required_integrations:
        for file_info in integration["files"]:
            file_path = project_root / file_info["path"].lstrip('/')
            assert file_path.exists(), f"Referenced file must exist: {file_info['path']}"

def test_env_validation_script_executable():
    """Vérifie que le script de validation est exécutable"""
    script_path = Path(__file__).parent.parent / "scripts" / "check_real_mode_env.py"
    
    assert script_path.exists(), "Validation script must exist"
    assert os.access(script_path, os.X_OK), "Validation script must be executable"

def test_mock_mode_flag_documented():
    """Vérifie que MOCK_MODE est documenté dans le template"""
    env_template = load_env_template()
    
    assert "MOCK_MODE" in env_template, "Template must document MOCK_MODE flag"
    assert "Mock-first architecture" in env_template, "Template must explain mock-first concept"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])