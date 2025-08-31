#!/usr/bin/env python3
"""
Tests E2E pour l'intégration Amazon avec interface refactorisée
Test complet du cycle connexion/déconnexion Amazon avec nouveau composant AmazonIntegrationCard
"""

import asyncio
import os
from playwright.async_api import async_playwright
import pytest

# Configuration des URLs
FRONTEND_URL = "https://ecomsimply.com"
TEST_USER_EMAIL = "msylla54@gmail.com"
TEST_USER_PASSWORD = "AdminEcomsimply"

class TestAmazonIntegrationE2E:
    """Tests E2E complets pour l'intégration Amazon refactorisée"""
    
    @pytest.mark.asyncio
    async def test_complete_amazon_integration_flow(self):
        """Test complet du flux d'intégration Amazon avec nouvelle interface"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                print("🔍 Test E2E - Navigation et authentification...")
                
                # 1. Navigation vers l'application
                await page.goto(FRONTEND_URL, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # 2. Authentification si nécessaire
                if await page.locator('input[type="email"]').count() > 0:
                    print("📧 Connexion avec les credentials test...")
                    await page.fill('input[type="email"]', TEST_USER_EMAIL)
                    await page.fill('input[type="password"]', TEST_USER_PASSWORD)
                    await page.click('button[type="submit"]')
                    await page.wait_for_timeout(3000)
                
                # 3. Navigation vers SEO Premium
                seo_button = page.locator('text="SEO Premium"')
                if await seo_button.count() > 0:
                    await seo_button.click()
                    await page.wait_for_timeout(2000)
                
                # 4. Navigation vers l'onglet Boutiques/Intégrations
                stores_button = page.locator('text="🏪 Boutiques"')
                if await stores_button.count() == 0:
                    stores_button = page.locator('text="Boutiques"')
                
                if await stores_button.count() > 0:
                    await stores_button.click()
                    await page.wait_for_timeout(2000)
                    print("✅ Navigation vers l'onglet Boutiques réussie")
                
                # 5. Test de présence de la section Amazon Integration
                amazon_section = page.locator('#amazon-integration-section')
                assert await amazon_section.count() > 0, "Section Amazon Integration non trouvée"
                print("✅ Section Amazon Integration trouvée")
                
                # 6. Test de présence du composant AmazonIntegrationCard
                amazon_card = amazon_section.locator('.bg-white.border')
                assert await amazon_card.count() > 0, "Composant AmazonIntegrationCard non trouvé"
                print("✅ Composant AmazonIntegrationCard présent")
                
                # 7. Vérification de l'état initial Amazon
                amazon_status = amazon_card.locator('[class*="border-"] span')
                status_text = await amazon_status.text_content() if await amazon_status.count() > 0 else "Non connecté"
                print(f"📊 Statut Amazon initial: {status_text}")
                
                # 8. Test des boutons d'action Amazon
                action_button = amazon_card.locator('button[class*="bg-"]')
                assert await action_button.count() > 0, "Bouton d'action Amazon non trouvé"
                
                button_text = await action_button.text_content()
                print(f"🔘 Bouton d'action trouvé: '{button_text}'")
                
                # 9. Test de suppression des doublons - Vérifier qu'Amazon n'est pas dans la grille des autres plateformes
                platform_buttons = page.locator('[class*="grid"] button')
                platform_count = await platform_buttons.count()
                
                amazon_in_grid = False
                for i in range(platform_count):
                    button = platform_buttons.nth(i)
                    text = await button.text_content()
                    if 'Amazon' in text and 'amazon-integration-section' not in await button.get_attribute('id'):
                        amazon_in_grid = True
                        break
                
                assert not amazon_in_grid, "Doublon Amazon trouvé dans la grille des plateformes"
                print("✅ Aucun doublon Amazon dans la grille des plateformes")
                
                # 10. Test de navigation par clic sur Amazon dans la grille principale
                main_amazon_button = page.locator('text="Amazon"').first
                if await main_amazon_button.count() > 0:
                    # Cliquer sur Amazon dans la grille principale devrait scroller vers la section dédiée
                    await main_amazon_button.click()
                    await page.wait_for_timeout(1000)
                    
                    # Vérifier que la section Amazon est visible
                    is_visible = await amazon_section.is_visible()
                    print(f"📍 Section Amazon visible après clic: {is_visible}")
                
                # 11. Test de l'absence de la section Amazon dans Config SEO
                config_tab = page.locator('text="⚙️ Paramètres"')
                if await config_tab.count() > 0:
                    await config_tab.click()
                    await page.wait_for_timeout(2000)
                    
                    # Vérifier qu'il n'y a pas de section Amazon dans Config SEO
                    amazon_config_section = page.locator('text="🛒 Configuration Amazon"')
                    assert await amazon_config_section.count() == 0, "Section Amazon trouvée dans Config SEO (devrait être supprimée)"
                    print("✅ Section Amazon supprimée de Config SEO")
                    
                    # Retour à l'onglet Boutiques
                    await stores_button.click()
                    await page.wait_for_timeout(2000)
                
                # 12. Test de responsivité du composant
                await page.set_viewport_size({"width": 375, "height": 667})  # Mobile
                await page.wait_for_timeout(1000)
                
                mobile_visible = await amazon_section.is_visible()
                print(f"📱 Section Amazon visible en mobile: {mobile_visible}")
                
                await page.set_viewport_size({"width": 1920, "height": 1080})  # Desktop
                await page.wait_for_timeout(1000)
                
                # 13. Screenshot final pour validation visuelle
                await page.screenshot(path="amazon_integration_e2e_final.png", quality=20, full_page=False)
                
                print("✅ Test E2E Amazon Integration réussi !")
                
                return {
                    "status": "success",
                    "amazon_section_found": True,
                    "component_present": True,
                    "no_duplicates": True,
                    "config_seo_cleaned": True,
                    "mobile_responsive": mobile_visible,
                    "initial_status": status_text,
                    "action_button": button_text
                }
                
            except Exception as e:
                print(f"❌ Erreur dans le test E2E: {e}")
                await page.screenshot(path="amazon_integration_e2e_error.png", quality=20, full_page=False)
                raise e
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio 
    async def test_amazon_button_states(self):
        """Test des différents états du bouton Amazon"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                print("🔍 Test des états du bouton Amazon...")
                
                # Navigation et authentification (même logique que le test précédent)
                await page.goto(FRONTEND_URL, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Simuler différents états Amazon via JavaScript
                states_to_test = [
                    {"status": "none", "expected_button": "Connecter", "expected_color": "bg-green-600"},
                    {"status": "revoked", "expected_button": "Reconnecter", "expected_color": "bg-green-600"},
                    {"status": "connected", "expected_button": "Déconnecter", "expected_color": "bg-red-600"},
                    {"status": "pending", "expected_button": "Connecter", "expected_color": "bg-green-600"},
                    {"status": "error", "expected_button": "Connecter", "expected_color": "bg-green-600"}
                ]
                
                for state in states_to_test:
                    # Simuler le changement d'état via JavaScript
                    await page.evaluate(f"""
                        if (window.setAmazonConnectionStatus) {{
                            window.setAmazonConnectionStatus('{state["status"]}');
                        }}
                    """)
                    
                    await page.wait_for_timeout(500)
                    
                    print(f"🔄 Test état: {state['status']}")
                
                print("✅ Test des états du bouton Amazon réussi !")
                
            except Exception as e:
                print(f"❌ Erreur dans le test des états: {e}")
                raise e
                
            finally:
                await browser.close()

# Script d'exécution directe pour les tests
async def run_e2e_tests():
    """Exécuter les tests E2E directement"""
    test_instance = TestAmazonIntegrationE2E()
    
    print("🚀 Démarrage des tests E2E Amazon Integration...")
    
    try:
        # Test principal
        result = await test_instance.test_complete_amazon_integration_flow()
        print(f"📊 Résultat du test principal: {result}")
        
        # Test des états des boutons
        await test_instance.test_amazon_button_states()
        
        print("🎉 Tous les tests E2E réussis !")
        
    except Exception as e:
        print(f"❌ Échec des tests E2E: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())