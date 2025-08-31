#!/usr/bin/env python3
"""
Fix Autonome Amazon OAuth SP-API avec Tests Automatiques
Exécute corrections → tests → corrections → tests jusqu'à conformité totale
"""

import subprocess
import sys
import os
import time
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class AutonomousAmazonOAuthFixer:
    """Correcteur autonome avec tests automatiques jusqu'à CI verte"""
    
    def __init__(self):
        self.app_root = Path('/app')
        self.max_fix_iterations = 5
        self.current_iteration = 0
        self.test_results = {}
        self.corrections_applied = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log avec timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARN": "⚠️",
            "FIX": "🔧"
        }.get(level, "ℹ️")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def run_unit_tests(self) -> Tuple[bool, Dict]:
        """Exécuter tests unitaires"""
        self.log("Exécution des tests unitaires...", "INFO")
        
        try:
            # Tests backend
            result_backend = subprocess.run([
                'python', '-m', 'pytest', 
                'tests/unit/test_amazon_oauth_service.py',
                '-v', '--tb=short'
            ], capture_output=True, text=True, cwd=self.app_root)
            
            # Tests frontend  
            result_frontend = subprocess.run([
                'python', '-m', 'pytest',
                'tests/unit/test_frontend_oauth.py', 
                '-v', '--tb=short'
            ], capture_output=True, text=True, cwd=self.app_root)
            
            backend_success = result_backend.returncode == 0
            frontend_success = result_frontend.returncode == 0
            overall_success = backend_success and frontend_success
            
            results = {
                'backend': {
                    'success': backend_success,
                    'stdout': result_backend.stdout,
                    'stderr': result_backend.stderr
                },
                'frontend': {
                    'success': frontend_success,
                    'stdout': result_frontend.stdout,
                    'stderr': result_frontend.stderr
                },
                'overall_success': overall_success
            }
            
            if overall_success:
                self.log("Tests unitaires: RÉUSSIS", "SUCCESS")
            else:
                self.log("Tests unitaires: ÉCHOUÉS", "ERROR")
                if not backend_success:
                    self.log(f"Backend échec: {result_backend.stderr[:200]}", "ERROR")
                if not frontend_success:
                    self.log(f"Frontend échec: {result_frontend.stderr[:200]}", "ERROR")
            
            return overall_success, results
            
        except Exception as e:
            self.log(f"Erreur tests unitaires: {e}", "ERROR")
            return False, {'error': str(e)}
    
    def run_integration_tests(self) -> Tuple[bool, Dict]:
        """Exécuter tests d'intégration"""
        self.log("Exécution des tests d'intégration...", "INFO")
        
        try:
            result = subprocess.run([
                'python', '-m', 'pytest',
                'tests/integration/test_amazon_oauth_callback.py',
                '-v', '--tb=short'
            ], capture_output=True, text=True, cwd=self.app_root)
            
            success = result.returncode == 0
            
            results = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if success:
                self.log("Tests d'intégration: RÉUSSIS", "SUCCESS")
            else:
                self.log("Tests d'intégration: ÉCHOUÉS", "ERROR")
                self.log(f"Détails: {result.stderr[:200]}", "ERROR")
            
            return success, results
            
        except Exception as e:
            self.log(f"Erreur tests intégration: {e}", "ERROR")
            return False, {'error': str(e)}
    
    def run_backend_validation(self) -> Tuple[bool, Dict]:
        """Validation backend live"""
        self.log("Validation backend en cours...", "INFO")
        
        try:
            # Import et test direct du service OAuth
            sys.path.append('/app/backend')
            
            # Test 1: Import et initialisation
            try:
                from services.amazon_oauth_service import AmazonOAuthService
                from models.amazon_spapi import SPAPIRegion
                
                # Mock des variables d'environnement
                test_env = {
                    'AMAZON_LWA_CLIENT_ID': 'test_client_id',
                    'AMAZON_LWA_CLIENT_SECRET': 'test_client_secret',
                    'AMAZON_APP_ID': 'amzn1.sellerapps.app.test-app-id',
                    'APP_BASE_URL': 'https://app.test.com',
                    'AMAZON_REDIRECT_URI': 'https://api.test.com/api/amazon/callback'
                }
                
                for key, value in test_env.items():
                    os.environ[key] = value
                
                oauth_service = AmazonOAuthService()
                self.log("Service OAuth initialisé avec succès", "SUCCESS")
                
                # Test 2: Endpoints EU corrigés
                eu_endpoint = oauth_service._oauth_endpoints[SPAPIRegion.EU]['token']
                if eu_endpoint == 'https://api.amazon.com/auth/o2/token':
                    self.log("Endpoint EU corrigé: ✅", "SUCCESS")
                else:
                    self.log(f"Endpoint EU incorrect: {eu_endpoint}", "ERROR")
                    return False, {'error': 'EU endpoint not corrected'}
                
                # Test 3: AMAZON_APP_ID utilisé
                if hasattr(oauth_service, 'app_id') and oauth_service.app_id == test_env['AMAZON_APP_ID']:
                    self.log("AMAZON_APP_ID configuré: ✅", "SUCCESS")
                else:
                    self.log("AMAZON_APP_ID manquant", "ERROR")
                    return False, {'error': 'AMAZON_APP_ID not configured'}
                
                # Test 4: Build authorization URL
                state = oauth_service.generate_oauth_state("user123", "conn456")
                auth_url = oauth_service.build_authorization_url(
                    state=state,
                    marketplace_id="A13V1IB3VIYZZH",
                    region=SPAPIRegion.EU
                )
                
                if 'amzn1.sellerapps.app.test-app-id' in auth_url:
                    self.log("application_id utilise AMAZON_APP_ID: ✅", "SUCCESS")
                else:
                    self.log("application_id n'utilise pas AMAZON_APP_ID", "ERROR")
                    return False, {'error': 'application_id not using AMAZON_APP_ID'}
                
                if 'https://api.test.com/api/amazon/callback' in auth_url:
                    self.log("AMAZON_REDIRECT_URI prioritaire: ✅", "SUCCESS")
                else:
                    self.log("AMAZON_REDIRECT_URI pas prioritaire", "ERROR")
                    return False, {'error': 'AMAZON_REDIRECT_URI not prioritized'}
                
                return True, {
                    'oauth_service_init': True,
                    'eu_endpoint_corrected': True,
                    'app_id_configured': True,
                    'authorization_url_correct': True
                }
                
            except Exception as e:
                self.log(f"Erreur validation service: {e}", "ERROR")
                return False, {'error': f'Service validation failed: {e}'}
            
        except Exception as e:
            self.log(f"Erreur validation backend: {e}", "ERROR") 
            return False, {'error': str(e)}
    
    def apply_missing_corrections(self, test_failures: List[str]) -> bool:
        """Appliquer corrections manquantes basées sur échecs de tests"""
        self.log("Application des corrections automatiques...", "FIX")
        
        corrections_applied = []
        
        for failure in test_failures:
            if 'AMAZON_APP_ID' in failure or 'application_id' in failure:
                # Correction AMAZON_APP_ID manquante
                self.log("Application correction AMAZON_APP_ID...", "FIX")
                
                # Vérifier le fichier de service
                service_file = self.app_root / 'backend/services/amazon_oauth_service.py'
                if service_file.exists():
                    content = service_file.read_text()
                    
                    if 'self.app_id = os.environ[\'AMAZON_APP_ID\']' not in content:
                        # Ajouter app_id dans __init__
                        content = content.replace(
                            'self.client_secret = os.environ[\'AMAZON_LWA_CLIENT_SECRET\']',
                            'self.client_secret = os.environ[\'AMAZON_LWA_CLIENT_SECRET\']\n        self.app_id = os.environ[\'AMAZON_APP_ID\']  # SP-API App ID'
                        )
                        service_file.write_text(content)
                        corrections_applied.append("Added AMAZON_APP_ID to service init")
                    
                    if '\'application_id\': self.app_id' not in content:
                        # Corriger application_id
                        content = content.replace(
                            '\'application_id\': self.client_id',
                            '\'application_id\': self.app_id  # Use AMAZON_APP_ID instead of client_id'
                        )
                        service_file.write_text(content)
                        corrections_applied.append("Fixed application_id to use app_id")
            
            if 'EU endpoint' in failure or 'token endpoint' in failure:
                # Correction endpoint EU
                self.log("Application correction endpoint EU...", "FIX")
                
                service_file = self.app_root / 'backend/services/amazon_oauth_service.py'
                if service_file.exists():
                    content = service_file.read_text()
                    content = content.replace(
                        'https://api.amazon.co.uk/auth/o2/token',
                        'https://api.amazon.com/auth/o2/token'
                    )
                    service_file.write_text(content)
                    corrections_applied.append("Fixed EU token endpoint")
            
            if 'allowedOrigins' in failure or 'backend origin' in failure:
                # Correction allowedOrigins frontend
                self.log("Application correction allowedOrigins...", "FIX")
                
                app_js_file = self.app_root / 'frontend/src/App.js'
                if app_js_file.exists():
                    content = app_js_file.read_text()
                    
                    if 'new URL(process.env.REACT_APP_BACKEND_URL' not in content:
                        # Ajouter backend origin
                        old_origins = """        const allowedOrigins = [
          window.location.origin,
          'https://sellercentral-europe.amazon.com', 
          'https://sellercentral.amazon.com'
        ];"""
                        
                        new_origins = """        const allowedOrigins = [
          window.location.origin,
          'https://sellercentral-europe.amazon.com', 
          'https://sellercentral.amazon.com',
          new URL(process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL).origin  // Include backend origin
        ];"""
                        
                        content = content.replace(old_origins, new_origins)
                        app_js_file.write_text(content)
                        corrections_applied.append("Extended allowedOrigins with backend origin")
        
        self.corrections_applied.extend(corrections_applied)
        
        if corrections_applied:
            self.log(f"Corrections appliquées: {len(corrections_applied)}", "SUCCESS")
            for correction in corrections_applied:
                self.log(f"  • {correction}", "INFO")
            return True
        else:
            self.log("Aucune correction automatique disponible", "WARN")
            return False
    
    def run_full_test_suite(self) -> Tuple[bool, Dict]:
        """Exécuter suite complète de tests""" 
        self.log("=== EXÉCUTION SUITE COMPLÈTE DE TESTS ===", "INFO")
        
        results = {}
        
        # 1. Tests unitaires
        unit_success, unit_results = self.run_unit_tests()
        results['unit'] = unit_results
        
        # 2. Validation backend
        backend_success, backend_results = self.run_backend_validation()
        results['backend_validation'] = backend_results
        
        # 3. Tests intégration
        integration_success, integration_results = self.run_integration_tests()
        results['integration'] = integration_results
        
        overall_success = unit_success and backend_success and integration_success
        results['overall_success'] = overall_success
        
        self.log(f"RÉSULTATS: Unit={unit_success} Backend={backend_success} Integration={integration_success}", "INFO")
        
        return overall_success, results
    
    def run_autonomous_fix_cycle(self) -> Dict:
        """Cycle autonome: tests → corrections → tests jusqu'à succès"""
        self.log("🚀 DÉMARRAGE CYCLE AUTONOME AMAZON OAUTH", "INFO")
        self.log("=" * 60, "INFO")
        
        while self.current_iteration < self.max_fix_iterations:
            self.current_iteration += 1
            self.log(f"=== ITÉRATION {self.current_iteration}/{self.max_fix_iterations} ===", "INFO")
            
            # Exécuter tests
            test_success, test_results = self.run_full_test_suite()
            self.test_results[f'iteration_{self.current_iteration}'] = test_results
            
            if test_success:
                self.log("🎉 TOUS LES TESTS RÉUSSIS - CONFORMITÉ TOTALE ATTEINTE!", "SUCCESS")
                
                return {
                    'success': True,
                    'iterations': self.current_iteration,
                    'corrections_applied': self.corrections_applied,
                    'final_test_results': test_results,
                    'message': 'Amazon OAuth SP-API fix completed successfully'
                }
            
            else:
                self.log(f"Tests échoués à l'itération {self.current_iteration}", "ERROR")
                
                # Identifier échecs et appliquer corrections
                failures = []
                
                if not test_results.get('backend_validation', {}).get('success', True):
                    backend_error = test_results['backend_validation'].get('error', '')
                    failures.append(backend_error)
                
                if not test_results.get('unit', {}).get('overall_success', True):
                    unit_stderr = test_results['unit'].get('backend', {}).get('stderr', '')
                    unit_stderr += test_results['unit'].get('frontend', {}).get('stderr', '')
                    failures.append(unit_stderr)
                
                if failures:
                    corrections_made = self.apply_missing_corrections(failures)
                    
                    if not corrections_made:
                        self.log("Aucune correction automatique possible", "WARN")
                        break
                else:
                    self.log("Impossible d'identifier les échecs à corriger", "ERROR")
                    break
                
                # Pause entre itérations
                time.sleep(2)
        
        # Échec après max itérations
        self.log(f"❌ ÉCHEC APRÈS {self.max_fix_iterations} ITÉRATIONS", "ERROR")
        
        return {
            'success': False,
            'iterations': self.current_iteration,
            'corrections_applied': self.corrections_applied,
            'final_test_results': self.test_results.get(f'iteration_{self.current_iteration}', {}),
            'message': f'Failed to achieve conformity after {self.max_fix_iterations} iterations'
        }
    
    def generate_final_report(self, results: Dict) -> str:
        """Générer rapport final"""
        report = [
            "\n" + "=" * 80,
            "🎯 RAPPORT FINAL - FIX AUTONOME AMAZON OAUTH SP-API",
            "=" * 80,
            f"✅ Succès global: {'OUI' if results['success'] else 'NON'}",
            f"🔄 Itérations exécutées: {results['iterations']}",
            f"🔧 Corrections appliquées: {len(results['corrections_applied'])}",
            ""
        ]
        
        if results['corrections_applied']:
            report.append("📝 CORRECTIONS APPLIQUÉES:")
            for i, correction in enumerate(results['corrections_applied'], 1):
                report.append(f"   {i}. {correction}")
            report.append("")
        
        if results['success']:
            report.extend([
                "🎉 CRITÈRES D'ACCEPTATION VALIDÉS:",
                "   ✅ Endpoints OAuth EU/NA/FE corrigés",
                "   ✅ AMAZON_APP_ID utilisé pour application_id",
                "   ✅ AMAZON_REDIRECT_URI prioritaire",
                "   ✅ Logs sécurisés sans secrets",
                "   ✅ Frontend allowedOrigins étendu",
                "   ✅ postMessage AMAZON_CONNECTED géré",
                "   ✅ Tests unitaires, intégration et backend VERTS",
                "",
                "🚀 STATUS: PRÊT POUR PRODUCTION"
            ])
        else:
            report.extend([
                "❌ ÉCHECS RESTANTS:",
                f"   • {results.get('message', 'Unknown failure')}",
                "",
                "⚠️ STATUS: CORRECTIONS MANUELLES REQUISES"
            ])
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Point d'entrée du correcteur autonome"""
    fixer = AutonomousAmazonOAuthFixer()
    
    try:
        # Exécuter cycle autonome
        results = fixer.run_autonomous_fix_cycle()
        
        # Générer et afficher rapport
        report = fixer.generate_final_report(results)
        print(report)
        
        # Code de sortie
        exit_code = 0 if results['success'] else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        fixer.log("Interruption utilisateur", "WARN")
        sys.exit(130)
    except Exception as e:
        fixer.log(f"Erreur fatale: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()