"""
Test Required Integrations JSON Schema - ECOMSIMPLY
Validation complète du schéma et de la cohérence des intégrations
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any

def load_required_integrations():
    """Charge la configuration des intégrations requises"""
    config_path = Path(__file__).parent.parent / "required_integrations.json"
    with open(config_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def integrations():
    """Fixture pour les intégrations"""
    return load_required_integrations()

def test_json_is_valid(integrations):
    """Vérifie que le JSON est valide et parsable"""
    assert isinstance(integrations, list), "Root should be a list"
    assert len(integrations) > 0, "Should contain at least one integration"

def test_integration_schema_compliance(integrations):
    """Vérifie que chaque intégration respecte le schéma"""
    
    required_fields = {
        "domain": str,
        "provider": str, 
        "service": str,
        "env": list,
        "files": list,
        "required_in_real": bool,
        "status": dict,
        "priority": str,
        "fallback_available": bool
    }
    
    optional_fields = {
        "mode_flag": (str, type(None)),
        "healthcheck": (str, type(None)),
        "risks": list
    }
    
    for i, integration in enumerate(integrations):
        assert isinstance(integration, dict), f"Integration {i} must be a dictionary"
        
        # Vérifier champs obligatoires
        for field, expected_type in required_fields.items():
            assert field in integration, f"Integration {i} missing required field: {field}"
            assert isinstance(integration[field], expected_type), \
                f"Integration {i} field '{field}' must be {expected_type.__name__}"
        
        # Vérifier champs optionnels si présents
        for field, expected_types in optional_fields.items():
            if field in integration:
                if isinstance(expected_types, tuple):
                    assert isinstance(integration[field], expected_types), \
                        f"Integration {i} field '{field}' must be one of {expected_types}"
                else:
                    assert isinstance(integration[field], expected_types), \
                        f"Integration {i} field '{field}' must be {expected_types.__name__}"

def test_status_field_structure(integrations):
    """Vérifie la structure du champ status"""
    
    required_status_fields = {
        "present": bool,
        "missing": list,
        "configured": str
    }
    
    for integration in integrations:
        status = integration["status"]
        
        for field, expected_type in required_status_fields.items():
            assert field in status, f"Status missing field: {field} in {integration['provider']}"
            assert isinstance(status[field], expected_type), \
                f"Status field '{field}' must be {expected_type.__name__} in {integration['provider']}"

def test_files_field_structure(integrations):
    """Vérifie la structure du champ files"""
    
    for integration in integrations:
        for file_info in integration["files"]:
            assert isinstance(file_info, dict), f"File info must be dict in {integration['provider']}"
            assert "path" in file_info, f"File info missing path in {integration['provider']}"
            assert "lines" in file_info, f"File info missing lines in {integration['provider']}"
            
            assert isinstance(file_info["path"], str), "File path must be string"
            assert isinstance(file_info["lines"], list), "File lines must be list"
            
            # Vérifier que les numéros de ligne sont des entiers
            for line_num in file_info["lines"]:
                assert isinstance(line_num, int), f"Line number must be integer: {line_num}"

def test_priority_values(integrations):
    """Vérifie que les priorités sont valides"""
    valid_priorities = {"P0", "P1", "P2"}
    
    for integration in integrations:
        priority = integration["priority"]
        assert priority in valid_priorities, \
            f"Invalid priority '{priority}' in {integration['provider']}. Must be one of {valid_priorities}"

def test_configured_status_values(integrations):
    """Vérifie que les valeurs de status.configured sont valides"""
    valid_configured = {"yes", "no", "mock_only", "not_configured", "optional"}
    
    for integration in integrations:
        configured = integration["status"]["configured"]
        assert configured in valid_configured, \
            f"Invalid configured status '{configured}' in {integration['provider']}. Must be one of {valid_configured}"

def test_domain_categories(integrations):
    """Vérifie que les domaines sont cohérents"""
    expected_domains = {
        "ai_content", "image_generation", "payments", "payments_frontend", 
        "ecommerce_publication", "email", "scraping_proxy", "database", 
        "security", "cache", "backup", "monitoring"
    }
    
    found_domains = {integration["domain"] for integration in integrations}
    
    # Vérifier qu'on a au moins les domaines critiques
    critical_domains = {"ai_content", "payments", "database", "security"}
    for domain in critical_domains:
        assert domain in found_domains, f"Critical domain missing: {domain}"

def test_env_vars_not_empty(integrations):
    """Vérifie que les variables d'environnement ne sont pas vides"""
    
    for integration in integrations:
        env_vars = integration["env"]
        
        if integration["required_in_real"]:
            assert len(env_vars) > 0, f"Required integration {integration['provider']} must have env vars"
        
        for var in env_vars:
            assert isinstance(var, str), f"Env var must be string: {var}"
            assert len(var) > 0, f"Env var cannot be empty in {integration['provider']}"
            assert var.isupper(), f"Env var should be uppercase: {var}"

def test_consistency_priority_vs_required(integrations):
    """Vérifie la cohérence entre priorité et required_in_real"""
    
    for integration in integrations:
        priority = integration["priority"]
        required = integration["required_in_real"]
        provider = integration["provider"]
        
        if priority == "P0":
            assert required == True, f"P0 integration {provider} must be required in real mode"
        
        # Les intégrations non requises ne devraient pas être P0
        if not required:
            assert priority != "P0", f"Non-required integration {provider} should not be P0"

def test_healthcheck_consistency(integrations):
    """Vérifie la cohérence des healthcheck endpoints"""
    
    healthchecks = {}
    
    for integration in integrations:
        healthcheck = integration.get("healthcheck")
        
        if healthcheck and healthcheck != "integrated" and healthcheck is not None:
            if healthcheck in healthchecks:
                # Plusieurs services peuvent partager le même healthcheck (ex: publications)
                healthchecks[healthcheck].append(integration["provider"])
            else:
                healthchecks[healthcheck] = [integration["provider"]]
    
    # Vérifier format des endpoints
    for endpoint, providers in healthchecks.items():
        assert endpoint.startswith("/api/status/"), f"Healthcheck must start with /api/status/: {endpoint}"

def test_fallback_logic(integrations):
    """Vérifie la logique des fallbacks"""
    
    for integration in integrations:
        fallback = integration["fallback_available"]
        required = integration["required_in_real"]
        provider = integration["provider"]
        
        # Les intégrations mock-first devraient avoir un fallback
        if integration.get("mode_flag") == "MOCK_MODE":
            assert fallback == True, f"Mock integration {provider} should have fallback"
        
        # Les intégrations critiques sans fallback sont plus risquées
        if required and not fallback and integration["priority"] == "P0":
            risks = integration.get("risks", [])
            assert len(risks) > 0, f"Critical integration {provider} without fallback should document risks"

def test_no_duplicate_providers(integrations):
    """Vérifie qu'il n'y a pas de providers dupliqués (sauf cas légitimes)"""
    
    # Certains providers peuvent avoir plusieurs intégrations (ex: stripe backend/frontend)
    provider_domains = {}
    
    for integration in integrations:
        provider = integration["provider"]
        domain = integration["domain"]
        
        if provider not in provider_domains:
            provider_domains[provider] = []
        provider_domains[provider].append(domain)
    
    # Vérifier les duplicatas légitimes
    legitimate_duplicates = {
        "stripe": {"payments", "payments_frontend"}
    }
    
    for provider, domains in provider_domains.items():
        if len(domains) > 1:
            assert provider in legitimate_duplicates, f"Unexpected duplicate provider: {provider}"
            expected_domains = legitimate_duplicates[provider]
            assert set(domains) == expected_domains, \
                f"Provider {provider} has unexpected domains: {domains}"

def test_risks_field_quality(integrations):
    """Vérifie la qualité du champ risks"""
    
    for integration in integrations:
        risks = integration.get("risks", [])
        
        if integration["required_in_real"] and integration["priority"] == "P0":
            assert len(risks) > 0, f"P0 required integration {integration['provider']} should document risks"
        
        for risk in risks:
            assert isinstance(risk, str), f"Risk must be string in {integration['provider']}"
            assert len(risk) > 10, f"Risk description too short in {integration['provider']}: {risk}"

def test_missing_vars_logic(integrations):
    """Vérifie la logique des variables manquantes"""
    
    for integration in integrations:
        status = integration["status"]
        present = status["present"]
        missing = status["missing"]
        env_vars = integration["env"]
        
        if present:
            assert len(missing) == 0, f"Present integration {integration['provider']} should not have missing vars"
        else:
            # Si not present, il devrait y avoir des variables manquantes
            if len(env_vars) > 0:  # Seulement si l'intégration a des env vars
                assert len(missing) > 0, f"Non-present integration {integration['provider']} should list missing vars"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])