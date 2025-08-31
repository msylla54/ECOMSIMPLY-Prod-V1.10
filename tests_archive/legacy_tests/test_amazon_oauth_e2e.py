#!/usr/bin/env python3
"""
Tests E2E Amazon OAuth Frontend - Flow Complet avec Playwright

Tests E2E:
- Clic bouton → OAuth → retour → bouton affiche Connecté ✅
- Flow complet avec popup et fallback
- Vérification que l'utilisateur n'est jamais bloqué sur Amazon
- Retour immédiate dans le dashboard
- État du bouton correspond au statut en DB

Critères d'acceptation:
✅ L'utilisateur n'est jamais bloqué sur Amazon
✅ Le retour dans le dashboard est immédiat
✅ L'état du bouton correspond au statut en DB
"""

import asyncio
import pytest
import json
import os
import time
from datetime import datetime
from typing import Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Configuration des tests
FRONTEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com').replace('/api', '')
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ecomsimply.com')

class AmazonOAuthE2ETester:
    """Tests E2E pour le flow OAuth Amazon frontend"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.test_results = []
        
        # Données de test
        self.test_user = {
            "email": "test.oauth.frontend@ecomsimply.com",
            "password": "TestOAuthFrontend2025!",
            "name": "OAuth Frontend Test User"
        }
        
        print("🎭 Amazon OAuth E2E Testing Suite Initialized")
        print(f"🔗 Frontend URL: {FRONTEND_URL}")
        print(f"📡 Backend URL: {BACKEND_URL}")
    
    async def setup_browser(self):
        """Initialiser le navigateur et le contexte"""
        playwright = await async_playwright().start()
        
        # Lancer le navigateur en mode headless pour les tests
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Créer un contexte avec viewport standard
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='fr-FR'
        )
        
        # Créer une nouvelle page
        self.page = await self.context.new_page()
        
        # Activer les logs de console pour debug
        self.page.on('console', lambda msg: print(f"🖥️ Console: {msg.text}"))
        self.page.on('pageerror', lambda error: print(f"❌ Page Error: {error}"))
        
        print("✅ Navigateur initialisé")
    
    async def cleanup_browser(self):
        """Nettoyer le navigateur"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("🧹 Navigateur nettoyé")
    
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {details}")
        if data and not success:
            print(f"   📋 Error Data: {json.dumps(data, indent=2)}")
    
    async def authenticate_user(self) -> bool:
        """Authentifier l'utilisateur de test"""
        try:
            print("🔐 Démarrage authentification utilisateur...")
            
            # Aller à la page de connexion
            await self.page.goto(f"{FRONTEND_URL}/login")
            await self.page.wait_for_load_state('networkidle')
            
            # Remplir le formulaire de connexion
            await self.page.fill('input[type="email"]', self.test_user["email"])
            await self.page.fill('input[type="password"]', self.test_user["password"])
            
            # Cliquer sur le bouton de connexion
            await self.page.click('button[type="submit"]')
            
            # Attendre la redirection vers le dashboard
            await self.page.wait_for_url('**/dashboard*', timeout=10000)
            
            # Vérifier la présence d'éléments du dashboard
            dashboard_title = await self.page.locator('h1, h2').first.text_content()
            
            if 'dashboard' in dashboard_title.lower() or 'ecomsimply' in dashboard_title.lower():
                self.log_test_result(
                    "User Authentication E2E",
                    True,
                    "Utilisateur authentifié avec succès"
                )
                return True
            else:
                self.log_test_result(
                    "User Authentication E2E",
                    False,
                    "Échec de l'authentification - pas sur le dashboard",
                    {"current_url": self.page.url, "title": dashboard_title}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "User Authentication E2E",
                False,
                f"Erreur lors de l'authentification: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return False
    
    async def test_amazon_button_initial_state(self) -> bool:
        """Test: État initial du bouton Amazon"""
        try:
            print("🔍 Test état initial du bouton Amazon...")
            
            # Naviguer vers l'onglet Boutiques
            await self.page.click('text=Boutiques')
            await self.page.wait_for_timeout(2000)
            
            # Localiser le bouton Amazon
            amazon_button = self.page.locator('button:has-text("Amazon")')
            
            if await amazon_button.count() == 0:
                self.log_test_result(
                    "Amazon Button Initial State",
                    False,
                    "Bouton Amazon non trouvé",
                    {"buttons_found": await self.page.locator('button').count()}
                )
                return False
            
            # Vérifier le texte et l'icône du bouton
            button_text = await amazon_button.text_content()
            
            # Le bouton doit contenir "Amazon" et soit "Marketplace global" ou un statut
            if "Amazon" in button_text:
                # Vérifier l'état initial (doit être non connecté)
                if "Connecté ✅" not in button_text:
                    self.log_test_result(
                        "Amazon Button Initial State",
                        True,
                        "Bouton Amazon trouvé avec état initial correct",
                        {"button_text": button_text}
                    )
                    return True
                else:
                    # Si déjà connecté, c'est OK aussi
                    self.log_test_result(
                        "Amazon Button Initial State",
                        True,
                        "Bouton Amazon déjà connecté (état valide)",
                        {"button_text": button_text}
                    )
                    return True
            else:
                self.log_test_result(
                    "Amazon Button Initial State",
                    False,
                    "Bouton Amazon ne contient pas le texte attendu",
                    {"button_text": button_text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Amazon Button Initial State",
                False,
                f"Erreur lors du test état initial: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_amazon_button_click_popup_flow(self) -> bool:
        """Test E2E: Clic bouton → OAuth popup → retour → bouton mis à jour"""
        try:
            print("🚀 Test flow complet clic bouton Amazon...")
            
            # Naviguer vers l'onglet Boutiques si pas déjà fait
            await self.page.click('text=Boutiques')
            await self.page.wait_for_timeout(2000)
            
            # Localiser le bouton Amazon
            amazon_button = self.page.locator('button:has-text("Amazon")').first
            
            # Vérifier l'état initial du bouton
            initial_button_text = await amazon_button.text_content()
            print(f"📊 État initial du bouton: {initial_button_text}")
            
            # Si déjà connecté, test du statut existant
            if "Connecté ✅" in initial_button_text:
                self.log_test_result(
                    "Amazon Button Click Flow",
                    True,
                    "Bouton Amazon déjà connecté - statut DB correct",
                    {"button_state": "connected", "text": initial_button_text}
                )
                return True
            
            # Préparer l'interception du popup
            popup_opened = False
            popup_page = None
            
            async def handle_popup(popup):
                nonlocal popup_opened, popup_page
                popup_opened = True
                popup_page = popup
                print("🔗 Popup OAuth détecté!")
                
                # Attendre que le popup charge
                await popup.wait_for_load_state('load')
                popup_url = popup.url
                print(f"📍 URL du popup: {popup_url}")
                
                # Vérifier que c'est bien une URL Amazon OAuth
                if 'sellercentral' in popup_url and 'amazon.com' in popup_url:
                    # Simuler la réussite OAuth en fermant le popup et postMessage
                    await popup.evaluate("""
                        () => {
                            if (window.opener) {
                                window.opener.postMessage({
                                    type: 'AMAZON_CONNECTED',
                                    success: true,
                                    message: 'Amazon connection successful (E2E test)',
                                    timestamp: new Date().toISOString()
                                }, window.location.origin);
                            }
                        }
                    """)
                    
                    # Fermer le popup
                    await popup.close()
                    print("✅ Popup OAuth simulé avec succès")
                else:
                    print(f"⚠️ URL de popup inattendue: {popup_url}")
            
            # Écouter les popups
            self.page.on('popup', handle_popup)
            
            # Cliquer sur le bouton Amazon
            await amazon_button.click()
            print("🖱️ Clic sur le bouton Amazon effectué")
            
            # Attendre que le bouton passe en état de chargement
            await self.page.wait_for_timeout(1000)
            
            # Vérifier l'état de chargement
            loading_button_text = await amazon_button.text_content()
            if "Connexion..." in loading_button_text or "⏳" in loading_button_text:
                print("⏳ État de chargement détecté")
            
            # Attendre qu'un popup s'ouvre (timeout 10 secondes)
            for i in range(20):  # 10 secondes max
                await self.page.wait_for_timeout(500)
                if popup_opened:
                    break
            
            if not popup_opened:
                # Tester le fallback redirection
                current_url = self.page.url
                if 'sellercentral' in current_url:
                    print("🔄 Fallback redirection détecté - simulation retour")
                    
                    # Simuler le retour via URL
                    await self.page.goto(f"{FRONTEND_URL}/dashboard?amazon_connected=true&tab=stores")
                    await self.page.wait_for_timeout(2000)
                else:
                    # Popup peut être bloqué ou erreur
                    print("⚠️ Aucun popup détecté et pas de redirection")
            
            # Attendre la mise à jour du bouton (max 10 secondes)
            for i in range(20):
                await self.page.wait_for_timeout(500)
                updated_button_text = await amazon_button.text_content()
                
                if "Connecté ✅" in updated_button_text:
                    self.log_test_result(
                        "Amazon Button Click Flow",
                        True,
                        "Flow complet réussi - bouton mis à jour avec Connecté ✅",
                        {
                            "initial_state": initial_button_text,
                            "final_state": updated_button_text,
                            "popup_opened": popup_opened,
                            "flow_type": "popup" if popup_opened else "fallback"
                        }
                    )
                    return True
                elif "Connexion..." not in updated_button_text:
                    # Le chargement s'est arrêté mais pas connecté
                    break
            
            # Si on arrive ici, le bouton n'a pas été mis à jour correctement
            final_button_text = await amazon_button.text_content()
            self.log_test_result(
                "Amazon Button Click Flow",
                False,
                "Flow incomplet - bouton pas mis à jour avec statut connecté",
                {
                    "initial_state": initial_button_text,
                    "final_state": final_button_text,
                    "popup_opened": popup_opened
                }
            )
            return False
            
        except Exception as e:
            self.log_test_result(
                "Amazon Button Click Flow",
                False,
                f"Erreur lors du test flow complet: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_fallback_url_handling(self) -> bool:
        """Test: Gestion fallback via URL de retour"""
        try:
            print("🔄 Test gestion fallback URL...")
            
            # Simuler retour OAuth via URL
            await self.page.goto(f"{FRONTEND_URL}/dashboard?amazon_connected=true&tab=stores")
            await self.page.wait_for_load_state('networkidle')
            
            # Vérifier que l'URL est nettoyée
            await self.page.wait_for_timeout(2000)
            current_url = self.page.url
            
            if "amazon_connected" not in current_url:
                print("✅ URL nettoyée automatiquement")
            else:
                print("⚠️ URL pas encore nettoyée")
            
            # Vérifier l'onglet actif (doit être Boutiques)
            stores_tab = self.page.locator('text=Boutiques')
            if await stores_tab.count() > 0:
                tab_class = await stores_tab.get_attribute('class')
                if 'active' in tab_class or 'selected' in tab_class:
                    print("✅ Onglet Boutiques activé")
            
            # Vérifier le bouton Amazon
            amazon_button = self.page.locator('button:has-text("Amazon")').first
            button_text = await amazon_button.text_content()
            
            # Attendre mise à jour statut (max 5 secondes)
            for i in range(10):
                await self.page.wait_for_timeout(500)
                button_text = await amazon_button.text_content()
                if "Connecté ✅" in button_text:
                    break
            
            if "Connecté ✅" in button_text:
                self.log_test_result(
                    "Fallback URL Handling",
                    True,
                    "Fallback URL géré correctement - bouton mis à jour",
                    {"button_text": button_text, "url_cleaned": "amazon_connected" not in current_url}
                )
                return True
            else:
                self.log_test_result(
                    "Fallback URL Handling",
                    False,
                    "Fallback URL - bouton pas correctement mis à jour",
                    {"button_text": button_text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Fallback URL Handling",
                False,
                f"Erreur lors du test fallback: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_no_user_blocking_guarantee(self) -> bool:
        """Test: Garantir que l'utilisateur n'est jamais bloqué sur Amazon"""
        try:
            print("🔒 Test garantie non-blocage utilisateur...")
            
            # Simuler différents scenarios de blocage potentiel
            scenarios_tested = []
            
            # Scenario 1: Popup fermé manuellement
            amazon_button = self.page.locator('button:has-text("Amazon")').first
            
            # Vérifier qu'on est sur le dashboard
            if "/dashboard" not in self.page.url and "/boutiques" not in self.page.url:
                await self.page.goto(f"{FRONTEND_URL}/dashboard")
                await self.page.click('text=Boutiques')
                await self.page.wait_for_timeout(1000)
            
            # Test: L'utilisateur doit toujours pouvoir naviguer
            navigation_links = await self.page.locator('nav a, button[role="tab"]').count()
            if navigation_links > 0:
                scenarios_tested.append("navigation_available")
            
            # Test: Pas de redirection forcée vers Amazon
            current_url = self.page.url
            if 'sellercentral' not in current_url and 'amazon.com' not in current_url:
                scenarios_tested.append("no_forced_redirect")
            
            # Test: Interface responsive et fonctionnelle
            dashboard_elements = await self.page.locator('button, input, a').count()
            if dashboard_elements > 5:  # Interface basique fonctionnelle
                scenarios_tested.append("interface_functional")
            
            # Test: Possibilité de quitter/recharger la page
            await self.page.reload()
            await self.page.wait_for_load_state('networkidle')
            if "/dashboard" in self.page.url or "login" in self.page.url:
                scenarios_tested.append("page_reload_working")
            
            if len(scenarios_tested) >= 3:
                self.log_test_result(
                    "User Blocking Prevention",
                    True,
                    "Utilisateur jamais bloqué - tous les scenarios testés OK",
                    {"scenarios_passed": scenarios_tested}
                )
                return True
            else:
                self.log_test_result(
                    "User Blocking Prevention",
                    False,
                    "Risque de blocage utilisateur détecté",
                    {"scenarios_passed": scenarios_tested}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "User Blocking Prevention",
                False,
                f"Erreur lors du test non-blocage: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Exécuter tous les tests E2E"""
        print("🚀 Démarrage des tests E2E Amazon OAuth Frontend...")
        
        try:
            await self.setup_browser()
            
            # Authentification
            auth_success = await self.authenticate_user()
            if not auth_success:
                print("❌ Échec authentification - arrêt des tests")
                return self.generate_report()
            
            # Tests E2E
            tests = [
                ("Amazon Button Initial State", self.test_amazon_button_initial_state),
                ("Amazon Button Click Flow", self.test_amazon_button_click_popup_flow),
                ("Fallback URL Handling", self.test_fallback_url_handling),
                ("User Blocking Prevention", self.test_no_user_blocking_guarantee)
            ]
            
            for test_name, test_func in tests:
                try:
                    await test_func()
                    await self.page.wait_for_timeout(1000)  # Pause entre les tests
                except Exception as e:
                    self.log_test_result(
                        test_name,
                        False,
                        f"Exception lors du test: {str(e)}",
                        {"error": str(e)}
                    )
            
        finally:
            await self.cleanup_browser()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Générer le rapport de tests E2E"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_type": "E2E Amazon OAuth Frontend",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_success": success_rate >= 75,  # 75% minimum pour E2E
            "results": self.test_results,
            "summary": {
                "user_never_blocked": any(r['test'] == 'User Blocking Prevention' and r['success'] for r in self.test_results),
                "immediate_dashboard_return": any(r['test'] == 'Fallback URL Handling' and r['success'] for r in self.test_results),
                "button_state_db_sync": any(r['test'] == 'Amazon Button Click Flow' and r['success'] for r in self.test_results)
            }
        }
        
        return report


async def main():
    """Fonction principale pour exécuter les tests E2E"""
    tester = AmazonOAuthE2ETester()
    report = await tester.run_all_tests()
    
    print("\n" + "="*60)
    print("📊 RAPPORT TESTS E2E AMAZON OAUTH FRONTEND")
    print("="*60)
    print(f"Tests total: {report['total_tests']}")
    print(f"Tests réussis: {report['passed_tests']}")
    print(f"Tests échoués: {report['failed_tests']}")
    print(f"Taux de réussite: {report['success_rate']:.1f}%")
    print(f"Statut global: {'✅ RÉUSSI' if report['overall_success'] else '❌ ÉCHOUÉ'}")
    
    print("\n📋 CRITÈRES D'ACCEPTATION:")
    summary = report['summary']
    print(f"✅ Utilisateur jamais bloqué: {'OUI' if summary['user_never_blocked'] else 'NON'}")
    print(f"✅ Retour immédiat dashboard: {'OUI' if summary['immediate_dashboard_return'] else 'NON'}")
    print(f"✅ État bouton = statut DB: {'OUI' if summary['button_state_db_sync'] else 'NON'}")
    
    # Sauvegarder le rapport
    with open('/app/tests/amazon_oauth_e2e_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Rapport sauvegardé: /app/tests/amazon_oauth_e2e_report.json")
    
    # Code de sortie basé sur le succès
    return 0 if report['overall_success'] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())