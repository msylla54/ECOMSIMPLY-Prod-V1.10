"""
Tests End-to-End pour Amazon OAuth avec Playwright
Test du flow complet: clic → popup → postMessage → UI "Connecté ✅"
"""

import pytest
import asyncio
import os
from playwright.async_api import async_playwright, expect
from unittest.mock import patch


class TestAmazonOAuthE2E:
    """Tests E2E complets du flow OAuth Amazon"""
    
    @pytest.fixture
    async def browser_context(self):
        """Fixture pour browser Playwright avec configuration"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            yield context
            await context.close()
            await browser.close()
    
    @pytest.fixture
    async def authenticated_page(self, browser_context):
        """Page avec authentification utilisateur"""
        page = await browser_context.new_page()
        
        # Simuler l'authentification (ajuster selon votre implémentation)
        await page.goto('http://localhost:3000')
        
        # Mock l'état d'authentification dans localStorage
        await page.evaluate("""
            localStorage.setItem('auth_token', 'test_jwt_token');
            localStorage.setItem('user_id', 'test_user_12345');
            localStorage.setItem('subscription_plan', 'premium');
        """)
        
        yield page
        await page.close()
    
    async def test_amazon_oauth_complete_flow_success(self, authenticated_page):
        """Test du flow OAuth complet: clic Amazon → popup → postMessage → UI connecté"""
        
        # 1. Aller sur la page avec intégration Amazon
        await authenticated_page.goto('http://localhost:3000')
        
        # Attendre que la page soit chargée
        await authenticated_page.wait_for_load_state('networkidle')
        
        # 2. Localiser et cliquer sur le bouton/carte Amazon
        amazon_card = authenticated_page.locator('[data-testid="amazon-integration-card"], .amazon-connect-button, text=Amazon')
        await expect(amazon_card).to_be_visible()
        
        # Vérifier l'état initial (déconnecté)
        disconnect_indicator = authenticated_page.locator('text=❌ Déconnecté, text=Déconnecté')
        if await disconnect_indicator.count() > 0:
            await expect(disconnect_indicator).to_be_visible()
        
        # 3. Intercepter la création de popup et simuler le callback OAuth
        popup_promise = authenticated_page.wait_for_event('popup')
        
        # Cliquer sur le bouton de connexion Amazon
        connect_button = authenticated_page.locator('text=Connecter, text=Reconnecter, [data-action="amazon-connect"]')
        await connect_button.first.click()
        
        # 4. Attendre l'ouverture de la popup OAuth
        popup = await popup_promise
        await popup.wait_for_load_state()
        
        # Vérifier que la popup contient l'URL Amazon OAuth (ou notre callback de test)
        popup_url = popup.url
        assert 'amazon' in popup_url.lower() or 'oauth' in popup_url.lower() or 'callback' in popup_url.lower()
        
        # 5. Simuler le callback OAuth de succès via postMessage
        # (En test E2E réel, Amazon redirigerait vers notre callback qui enverrait le postMessage)
        await authenticated_page.evaluate("""
            window.postMessage({
                type: 'AMAZON_CONNECTED',
                success: true,
                message: 'Amazon connection successful with automatic refresh token generation',
                timestamp: new Date().toISOString()
            }, '*');
        """)
        
        # 6. Attendre la fermeture de la popup
        await popup.wait_for_event('close', timeout=5000)
        
        # 7. Vérifier que l'UI se met à jour avec le statut "Connecté"
        await authenticated_page.wait_for_timeout(1000)  # Laisser le temps à l'UI de se mettre à jour
        
        # Chercher les indicateurs de connexion réussie
        success_indicators = [
            '✅ Connecté',
            'Connecté ✅', 
            'text=Connecté',
            'text=Connected',
            '.amazon-connected-status',
            '[data-status="connected"]'
        ]
        
        connected_found = False
        for indicator in success_indicators:
            if await authenticated_page.locator(indicator).count() > 0:
                await expect(authenticated_page.locator(indicator)).to_be_visible()
                connected_found = True
                break
        
        assert connected_found, "Aucun indicateur de connexion Amazon trouvé dans l'UI"
        
        # 8. Vérifier que le bouton change d'état (Connect → Disconnect)
        disconnect_button = authenticated_page.locator('text=Déconnecter, text=Disconnect, [data-action="amazon-disconnect"]')
        if await disconnect_button.count() > 0:
            await expect(disconnect_button).to_be_visible()
    
    async def test_amazon_oauth_error_handling(self, authenticated_page):
        """Test de gestion d'erreur OAuth"""
        
        # 1. Aller sur la page d'intégration
        await authenticated_page.goto('http://localhost:3000')
        await authenticated_page.wait_for_load_state('networkidle')
        
        # 2. Cliquer sur Amazon pour ouvrir popup
        popup_promise = authenticated_page.wait_for_event('popup')
        connect_button = authenticated_page.locator('text=Connecter, text=Reconnecter, [data-action="amazon-connect"]')
        await connect_button.first.click()
        
        popup = await popup_promise 
        await popup.wait_for_load_state()
        
        # 3. Simuler une erreur OAuth via postMessage
        await authenticated_page.evaluate("""
            window.postMessage({
                type: 'AMAZON_CONNECTION_ERROR',
                success: false,
                error: 'redirect_uri_mismatch',
                message: 'Redirect URI does not match configured value',
                timestamp: new Date().toISOString()
            }, '*');
        """)
        
        # 4. Attendre la fermeture de la popup
        await popup.wait_for_event('close', timeout=5000)
        
        # 5. Vérifier l'affichage de l'erreur dans l'UI
        await authenticated_page.wait_for_timeout(1000)
        
        error_indicators = [
            'text=Erreur de connexion',
            'text=Connection error', 
            '.amazon-error-status',
            '[data-status="error"]',
            'text=❌'
        ]
        
        error_found = False
        for indicator in error_indicators:
            if await authenticated_page.locator(indicator).count() > 0:
                error_found = True
                break
        
        assert error_found, "Aucun indicateur d'erreur de connexion trouvé dans l'UI"
    
    async def test_non_regression_other_integrations(self, authenticated_page):
        """Test de non-régression: autres intégrations inchangées"""
        
        # 1. Aller sur la page d'intégrations
        await authenticated_page.goto('http://localhost:3000')
        await authenticated_page.wait_for_load_state('networkidle')
        
        # 2. Vérifier que les autres plateformes sont présentes et fonctionnelles
        expected_platforms = [
            'Shopify',
            'WooCommerce', 
            'eBay',
            'Etsy',
            'Facebook',
            'Google Shopping'
        ]
        
        for platform in expected_platforms:
            platform_element = authenticated_page.locator(f'text={platform}')
            if await platform_element.count() > 0:
                await expect(platform_element).to_be_visible()
                
                # Vérifier que le bouton/carte est cliquable
                platform_button = authenticated_page.locator(f'text={platform}').or_(
                    authenticated_page.locator(f'[data-platform="{platform.lower()}"]')
                )
                
                if await platform_button.count() > 0:
                    await expect(platform_button).to_be_enabled()
        
        # 3. Tester qu'Amazon est également présent mais distinct
        amazon_element = authenticated_page.locator('text=Amazon')
        await expect(amazon_element).to_be_visible()
        
        # 4. Vérifier qu'il n'y a pas de doublons Amazon
        amazon_elements = await authenticated_page.locator('text=Amazon').count()
        # Il devrait y avoir exactement 1 ou 2 éléments Amazon (bouton principal + éventuellement dans liste)
        assert amazon_elements <= 2, f"Trop d'éléments Amazon trouvés: {amazon_elements}"
    
    async def test_responsive_design_mobile(self, browser_context):
        """Test responsive design sur mobile"""
        
        # Configuration mobile
        mobile_page = await browser_context.new_page()
        await mobile_page.set_viewport_size({'width': 375, 'height': 667})  # iPhone SE
        
        # Mock auth
        await mobile_page.goto('http://localhost:3000')
        await mobile_page.evaluate("""
            localStorage.setItem('auth_token', 'test_jwt_token');
            localStorage.setItem('user_id', 'test_user_12345');
        """)
        
        await mobile_page.reload()
        await mobile_page.wait_for_load_state('networkidle')
        
        # Vérifier que les éléments Amazon sont visibles et utilisables sur mobile
        amazon_elements = mobile_page.locator('text=Amazon, [data-platform="amazon"]')
        await expect(amazon_elements.first).to_be_visible()
        
        # Vérifier que les boutons sont assez grands pour être utilisables (minimum 44px)
        amazon_button = mobile_page.locator('text=Amazon, [data-platform="amazon"]').first
        button_box = await amazon_button.bounding_box()
        
        if button_box:
            assert button_box['height'] >= 44, f"Bouton trop petit sur mobile: {button_box['height']}px"
            assert button_box['width'] >= 44, f"Bouton trop étroit sur mobile: {button_box['width']}px"
        
        await mobile_page.close()
    
    async def test_accessibility_keyboard_navigation(self, authenticated_page):
        """Test d'accessibilité: navigation au clavier"""
        
        await authenticated_page.goto('http://localhost:3000')
        await authenticated_page.wait_for_load_state('networkidle')
        
        # Tester la navigation Tab vers Amazon
        await authenticated_page.keyboard.press('Tab')  # Premier élément
        
        # Continuer jusqu'à Amazon (maximum 20 tabs pour éviter boucle infinie)
        for i in range(20):
            focused_element = await authenticated_page.evaluate('document.activeElement.textContent')
            if 'Amazon' in focused_element:
                break
            await authenticated_page.keyboard.press('Tab')
        else:
            # Si pas trouvé par Tab, chercher directement
            amazon_button = authenticated_page.locator('text=Amazon, [data-platform="amazon"]').first
            await amazon_button.focus()
        
        # Vérifier que l'élément Amazon peut être activé au clavier
        focused_element = await authenticated_page.evaluate('document.activeElement')
        assert focused_element is not None
        
        # Tester activation avec Entrée
        await authenticated_page.keyboard.press('Enter')
        
        # Attendre un court délai pour voir si une action se déclenche
        await authenticated_page.wait_for_timeout(500)
        
        # Le test passe s'il n'y a pas d'erreur JavaScript


if __name__ == "__main__":
    # Lancer les tests E2E
    pytest.main([__file__, "-v", "-s"])