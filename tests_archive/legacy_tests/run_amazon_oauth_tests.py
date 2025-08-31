#!/usr/bin/env python3
"""
Script d'exécution des tests Amazon OAuth SP-API
Validation complète des critères d'acceptation
"""

import subprocess
import sys
import os
import pytest
from typing import Dict, List, Tuple


class AmazonOAuthTestRunner:
    """Runner pour tous les tests Amazon OAuth"""
    
    def __init__(self):
        self.test_results = {}
        self.coverage_threshold = 85.0
    
    def run_unit_tests(self) -> Tuple[bool, Dict]:
        """Exécuter les tests unitaires"""
        print("🧪 Exécution des tests unitaires Amazon OAuth...")
        
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', 
                'tests/unit/test_amazon_oauth_service.py',
                '-v', '--tb=short', '--durations=10'
            ], capture_output=True, text=True, cwd='/app')
            
            success = result.returncode == 0
            
            test_info = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': success
            }
            
            if success:
                print("✅ Tests unitaires: RÉUSSIS")
            else:
                print("❌ Tests unitaires: ÉCHOUÉS")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
            
            return success, test_info
            
        except Exception as e:
            print(f"❌ Erreur lors des tests unitaires: {e}")
            return False, {'error': str(e)}
    
    def run_integration_tests(self) -> Tuple[bool, Dict]:
        """Exécuter les tests d'intégration"""
        print("🔗 Exécution des tests d'intégration Amazon OAuth...")
        
        try:
            result = subprocess.run([
                'python', '-m', 'pytest',
                'tests/integration/test_amazon_oauth_callback.py',
                '-v', '--tb=short', '--durations=10'
            ], capture_output=True, text=True, cwd='/app')
            
            success = result.returncode == 0
            
            test_info = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': success
            }
            
            if success:
                print("✅ Tests d'intégration: RÉUSSIS")
            else:
                print("❌ Tests d'intégration: ÉCHOUÉS")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
            
            return success, test_info
            
        except Exception as e:
            print(f"❌ Erreur lors des tests d'intégration: {e}")
            return False, {'error': str(e)}
    
    def run_e2e_tests(self) -> Tuple[bool, Dict]:
        """Exécuter les tests E2E"""
        print("🌐 Exécution des tests E2E Amazon OAuth...")
        
        # Vérifier que Playwright est installé
        try:
            subprocess.run(['playwright', 'install', 'chromium'], 
                         capture_output=True, check=True)
        except:
            print("⚠️ Installation de Playwright...")
            subprocess.run(['pip', 'install', 'playwright'], check=True)
            subprocess.run(['playwright', 'install', 'chromium'], check=True)
        
        try:
            result = subprocess.run([
                'python', '-m', 'pytest',
                'tests/e2e/test_amazon_oauth_e2e.py',
                '-v', '--tb=short', '--durations=10'
            ], capture_output=True, text=True, cwd='/app')
            
            success = result.returncode == 0
            
            test_info = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': success
            }
            
            if success:
                print("✅ Tests E2E: RÉUSSIS")
            else:
                print("❌ Tests E2E: ÉCHOUÉS")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
            
            return success, test_info
            
        except Exception as e:
            print(f"❌ Erreur lors des tests E2E: {e}")
            return False, {'error': str(e)}
    
    def check_coverage(self) -> Tuple[bool, Dict]:
        """Vérifier la couverture de code"""
        print("📊 Vérification de la couverture de code...")
        
        try:
            result = subprocess.run([
                'python', '-m', 'pytest',
                'tests/unit/test_amazon_oauth_service.py',
                'tests/integration/test_amazon_oauth_callback.py',
                '--cov=backend/services/amazon_oauth_service',
                '--cov=backend/routes/amazon_routes',
                '--cov-report=term-missing',
                f'--cov-fail-under={self.coverage_threshold}'
            ], capture_output=True, text=True, cwd='/app')
            
            success = result.returncode == 0
            
            coverage_info = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': success,
                'threshold': self.coverage_threshold
            }
            
            if success:
                print(f"✅ Couverture: ≥ {self.coverage_threshold}%")
            else:
                print(f"❌ Couverture: < {self.coverage_threshold}%")
                print(f"Détails: {result.stdout}")
            
            return success, coverage_info
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification de couverture: {e}")
            return False, {'error': str(e)}
    
    def validate_acceptance_criteria(self) -> Dict:
        """Valider les critères d'acceptation"""
        print("\n📋 VALIDATION DES CRITÈRES D'ACCEPTATION")
        print("=" * 60)
        
        criteria = {
            "1. En EU comme NA/FE, l'échange retourne un refresh_token et le stocke chiffré": False,
            "2. En préprod, AMAZON_REDIRECT_URI permet la connexion avec 'Connecté ✅'": False,
            "3. En cas de mauvaise redirect_uri, l'erreur est visible dans les logs": False,
            "4. CI verte, couverture tests ≥ 85% sur modules modifiés": False
        }
        
        # Vérification 1: Tests unitaires endpoints EU/NA/FE
        unit_success, unit_info = self.test_results.get('unit', (False, {}))
        if unit_success and 'test_oauth_endpoints_mapping_conforme PASSED' in unit_info.get('stdout', ''):
            criteria["1. En EU comme NA/FE, l'échange retourne un refresh_token et le stocke chiffré"] = True
        
        # Vérification 2: Tests E2E connexion réussie
        e2e_success, e2e_info = self.test_results.get('e2e', (False, {}))
        if e2e_success and 'test_amazon_oauth_complete_flow_success PASSED' in e2e_info.get('stdout', ''):
            criteria["2. En préprod, AMAZON_REDIRECT_URI permet la connexion avec 'Connecté ✅'"] = True
        
        # Vérification 3: Tests intégration gestion d'erreurs
        integration_success, integration_info = self.test_results.get('integration', (False, {}))
        if integration_success and 'test_callback_redirect_uri_mismatch_error PASSED' in integration_info.get('stdout', ''):
            criteria["3. En cas de mauvaise redirect_uri, l'erreur est visible dans les logs"] = True
        
        # Vérification 4: Couverture de code
        coverage_success, coverage_info = self.test_results.get('coverage', (False, {}))
        if coverage_success:
            criteria["4. CI verte, couverture tests ≥ 85% sur modules modifiés"] = True
        
        # Affichage des résultats
        for criterion, passed in criteria.items():
            status = "✅ VALIDÉ" if passed else "❌ ÉCHEC"
            print(f"{status} {criterion}")
        
        all_passed = all(criteria.values())
        overall_status = "✅ TOUS CRITÈRES VALIDÉS" if all_passed else "❌ CERTAINS CRITÈRES ÉCHOUÉS"
        print(f"\n🎯 RÉSULTAT GLOBAL: {overall_status}")
        
        return {
            'criteria': criteria,
            'all_passed': all_passed,
            'success_rate': sum(criteria.values()) / len(criteria) * 100
        }
    
    def run_all_tests(self) -> Dict:
        """Exécuter tous les tests et valider les critères"""
        print("🚀 DÉMARRAGE DES TESTS AMAZON OAUTH SP-API")
        print("=" * 60)
        
        # 1. Tests unitaires
        unit_success, unit_info = self.run_unit_tests()
        self.test_results['unit'] = (unit_success, unit_info)
        
        # 2. Tests d'intégration  
        integration_success, integration_info = self.run_integration_tests()
        self.test_results['integration'] = (integration_success, integration_info)
        
        # 3. Tests E2E
        e2e_success, e2e_info = self.run_e2e_tests()
        self.test_results['e2e'] = (e2e_success, e2e_info)
        
        # 4. Couverture de code
        coverage_success, coverage_info = self.check_coverage()
        self.test_results['coverage'] = (coverage_success, coverage_info)
        
        # 5. Validation des critères d'acceptation
        validation_results = self.validate_acceptance_criteria()
        
        # Résumé final
        print("\n📊 RÉSUMÉ COMPLET")
        print("=" * 60)
        print(f"Tests unitaires: {'✅' if unit_success else '❌'}")
        print(f"Tests intégration: {'✅' if integration_success else '❌'}")
        print(f"Tests E2E: {'✅' if e2e_success else '❌'}")
        print(f"Couverture: {'✅' if coverage_success else '❌'}")
        print(f"Critères d'acceptation: {validation_results['success_rate']:.1f}%")
        
        overall_success = (unit_success and integration_success and 
                          e2e_success and coverage_success and 
                          validation_results['all_passed'])
        
        final_status = "🎉 TOUS LES TESTS RÉUSSIS - PRÊT POUR PRODUCTION" if overall_success else "⚠️ CERTAINS TESTS ÉCHOUÉS - CORRECTIONS NÉCESSAIRES"
        print(f"\n{final_status}")
        
        return {
            'overall_success': overall_success,
            'unit_tests': unit_success,
            'integration_tests': integration_success,
            'e2e_tests': e2e_success,
            'coverage': coverage_success,
            'acceptance_criteria': validation_results,
            'test_results': self.test_results
        }


def main():
    """Point d'entrée principal"""
    runner = AmazonOAuthTestRunner()
    results = runner.run_all_tests()
    
    # Exit code basé sur le succès global
    exit_code = 0 if results['overall_success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()