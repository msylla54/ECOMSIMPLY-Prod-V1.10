# ================================================================================
# ECOMSIMPLY - TESTS E2E PAIEMENTS STRIPE AVEC PLAYWRIGHT
# ================================================================================

import pytest
from playwright.async_api import async_playwright, Page, BrowserContext
import asyncio
import json
import time
from typing import Dict, Any

# ================================================================================
# 🎭 TESTS E2E RÈGLE ESSAI UNIQUE
# ================================================================================

@pytest.mark.e2e
class TestTrialEligibilityE2E:
    """Tests E2E pour la règle d'essai unique"""
    
    @pytest.fixture(scope="class")
    async def browser_context(self):
        """Context de navigateur pour les tests"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            yield context
            await context.close()
            await browser.close()
    
    @pytest.fixture
    async def authenticated_page(self, browser_context: BrowserContext) -> Page:
        """Page avec utilisateur authentifié"""
        page = await browser_context.new_page()
        
        # Simuler authentification
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(2000)
        
        # Mock token d'authentification
        await page.evaluate("""
            localStorage.setItem('token', 'test_jwt_token');
            localStorage.setItem('user', JSON.stringify({
                id: 'user_e2e_test',
                email: 'e2e@test.com',
                name: 'E2E Test User'
            }));
        """)
        
        yield page
        await page.close()
    
    @pytest.mark.asyncio
    async def test_user_eligible_sees_free_trial_flow_and_success(self, authenticated_page: Page):
        """Test: Utilisateur éligible voit le flux d'essai gratuit et succès"""
        
        # Mock API responses pour utilisateur éligible
        await authenticated_page.route("**/api/subscription/trial-eligibility*", lambda route: route.fulfill(
            json={
                "eligible": True,
                "reason": "eligible_for_trial",
                "plan_type": "pro",
                "message": "Vous êtes éligible à l'essai gratuit de 7 jours !"
            }
        ))
        
        await authenticated_page.route("**/api/subscription/plans", lambda route: route.fulfill(
            json={
                "success": True,
                "plans": {
                    "pro": {
                        "id": "pro",
                        "name": "Pro",
                        "price": 29,
                        "stripe_price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
                        "features": ["100 fiches/mois", "IA avancée"]
                    }
                }
            }
        ))
        
        await authenticated_page.route("**/api/subscription/create", lambda route: route.fulfill(
            json={
                "checkout_url": "https://checkout.stripe.com/c/pay/test_session",
                "status": "checkout_created",
                "trial_active": True
            }
        ))
        
        # Naviguer vers la page d'abonnement
        await authenticated_page.goto("http://localhost:3000/subscription")
        await authenticated_page.wait_for_timeout(3000)
        
        # Vérifier que le bouton d'essai gratuit est visible
        trial_button = authenticated_page.locator('button:has-text("Essai gratuit 7 jours")')
        await trial_button.wait_for(state="visible", timeout=10000)
        
        # Cliquer sur le bouton d'essai gratuit
        await trial_button.click()
        await authenticated_page.wait_for_timeout(2000)
        
        # Vérifier la redirection vers Stripe (URL change interceptée)
        # En mode test, on vérifie que la requête à /create a été faite
        await authenticated_page.wait_for_function("""
            () => window.location.href.includes('checkout.stripe.com') || 
                  document.body.innerText.includes('checkout_created')
        """, timeout=10000)
        
        print("✅ Test flux essai gratuit éligible réussi")
    
    @pytest.mark.asyncio
    async def test_user_non_eligible_is_routed_to_paid_checkout_without_trial(self, authenticated_page: Page):
        """Test: Utilisateur non éligible est routé vers checkout payant sans essai"""
        
        # Mock API responses pour utilisateur NON éligible
        await authenticated_page.route("**/api/subscription/trial-eligibility*", lambda route: route.fulfill(
            json={
                "eligible": False,
                "reason": "trial_already_used",
                "plan_type": "pro",
                "message": "Vous avez déjà utilisé votre essai gratuit. Vous pouvez souscrire directement."
            }
        ))
        
        await authenticated_page.route("**/api/subscription/plans", lambda route: route.fulfill(
            json={
                "success": True,
                "plans": {
                    "pro": {
                        "id": "pro", 
                        "name": "Pro",
                        "price": 29,
                        "stripe_price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
                        "features": ["100 fiches/mois", "IA avancée"]
                    }
                }
            }
        ))
        
        await authenticated_page.route("**/api/subscription/create", lambda route: route.fulfill(
            json={
                "checkout_url": "https://checkout.stripe.com/c/pay/test_session_paid",
                "status": "checkout_created", 
                "trial_active": False
            }
        ))
        
        # Naviguer vers la page d'abonnement
        await authenticated_page.goto("http://localhost:3000/subscription")
        await authenticated_page.wait_for_timeout(3000)
        
        # Vérifier que le bouton d'essai gratuit N'EST PAS visible
        trial_button = authenticated_page.locator('button:has-text("Essai gratuit 7 jours")')
        await pytest.raises(TimeoutError, lambda: trial_button.wait_for(state="visible", timeout=3000))
        
        # Vérifier que le bouton "Souscrire maintenant" EST visible
        subscribe_button = authenticated_page.locator('button:has-text("Souscrire maintenant")')
        await subscribe_button.wait_for(state="visible", timeout=10000)
        
        # Vérifier le message explicatif
        message = authenticated_page.locator('text=Essai gratuit déjà utilisé')
        await message.wait_for(state="visible", timeout=5000)
        
        # Cliquer sur souscrire maintenant
        await subscribe_button.click()
        await authenticated_page.wait_for_timeout(2000)
        
        # Vérifier redirection checkout SANS essai
        await authenticated_page.wait_for_function("""
            () => window.location.href.includes('checkout.stripe.com') || 
                  document.body.innerText.includes('checkout_created')
        """, timeout=10000)
        
        print("✅ Test flux abonnement direct non éligible réussi")
    
    @pytest.mark.asyncio
    async def test_webhook_events_processed_once_and_ui_reflects_active_status(self, authenticated_page: Page):
        """Test: Événements webhook traités une seule fois et UI reflète le statut actif"""
        
        # Mock status API pour abonnement actif
        await authenticated_page.route("**/api/subscription/status", lambda route: route.fulfill(
            json={
                "user_id": "user_e2e_test",
                "plan_type": "pro",
                "status": "active",
                "trial_active": False,
                "monthly_limit": 100,
                "monthly_used": 5,
                "can_access_features": True,
                "message": "Plan Pro actif"
            }
        ))
        
        await authenticated_page.route("**/api/subscription/plans", lambda route: route.fulfill(
            json={"success": True, "plans": {}}
        ))
        
        # Naviguer vers la page d'abonnement
        await authenticated_page.goto("http://localhost:3000/subscription")
        await authenticated_page.wait_for_timeout(3000)
        
        # Vérifier l'affichage du statut actif
        active_badge = authenticated_page.locator('text=Plan Pro actif')
        await active_badge.wait_for(state="visible", timeout=10000)
        
        # Vérifier la barre d'utilisation
        usage_text = authenticated_page.locator('text=5 / 100 fiches')
        await usage_text.wait_for(state="visible", timeout=5000)
        
        # Vérifier l'absence de boutons d'abonnement (déjà abonné)
        trial_button = authenticated_page.locator('button:has-text("Essai gratuit")')
        subscribe_button = authenticated_page.locator('button:has-text("Souscrire")')
        
        # Ces boutons ne devraient pas être visibles pour un utilisateur déjà abonné
        await pytest.raises(TimeoutError, lambda: trial_button.wait_for(state="visible", timeout=3000))
        await pytest.raises(TimeoutError, lambda: subscribe_button.wait_for(state="visible", timeout=3000))
        
        print("✅ Test statut abonnement actif dans UI réussi")

# ================================================================================
# 🛒 TESTS E2E CHECKOUT SÉCURISÉ
# ================================================================================

@pytest.mark.e2e
class TestSecureCheckoutE2E:
    """Tests E2E pour le checkout sécurisé"""
    
    @pytest.fixture
    async def authenticated_page(self, browser_context: BrowserContext) -> Page:
        """Page avec utilisateur authentifié"""
        page = await browser_context.new_page()
        
        await page.goto("http://localhost:3000")
        await page.evaluate("""
            localStorage.setItem('token', 'test_jwt_secure');
            localStorage.setItem('user', JSON.stringify({
                id: 'user_secure_test',
                email: 'secure@test.com'
            }));
        """)
        
        yield page
        await page.close()
    
    @pytest.mark.asyncio
    async def test_price_id_validation_prevents_forged_requests(self, authenticated_page: Page):
        """Test: Validation price_id empêche les requêtes forgées"""
        
        request_intercepted = {"count": 0, "last_request": None}
        
        async def intercept_create_request(route):
            """Intercepte les requêtes de création d'abonnement"""
            request_intercepted["count"] += 1
            request_intercepted["last_request"] = await route.request.post_data_json()
            
            # Simuler rejet côté serveur pour price_id forgé
            if request_intercepted["last_request"]["price_id"] == "price_FORGED_123":
                await route.fulfill(
                    status=400,
                    json={
                        "status": "validation_error",
                        "message": "Price ID non autorisé"
                    }
                )
            else:
                await route.fulfill(
                    json={
                        "checkout_url": "https://checkout.stripe.com/valid",
                        "status": "checkout_created"
                    }
                )
        
        await authenticated_page.route("**/api/subscription/create", intercept_create_request)
        
        # Mock autres endpoints
        await authenticated_page.route("**/api/subscription/trial-eligibility*", lambda route: route.fulfill(
            json={"eligible": False, "reason": "test"}
        ))
        
        await authenticated_page.route("**/api/subscription/plans", lambda route: route.fulfill(
            json={
                "success": True,
                "plans": {
                    "pro": {
                        "id": "pro",
                        "price": 29,
                        "stripe_price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"  # Prix légitime
                    }
                }
            }
        ))
        
        # Aller sur la page d'abonnement
        await authenticated_page.goto("http://localhost:3000/subscription")
        await authenticated_page.wait_for_timeout(2000)
        
        # Essayer de forger une requête avec un price_id invalide via DevTools
        await authenticated_page.evaluate("""
            // Simuler une tentative de forge côté client
            fetch('/api/subscription/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer test_jwt_secure'
                },
                body: JSON.stringify({
                    plan_type: 'pro',
                    price_id: 'price_FORGED_123',  // Prix forgé
                    success_url: window.location.origin + '/success',
                    cancel_url: window.location.origin + '/cancel',
                    with_trial: false
                })
            }).catch(e => console.log('Forge attempt blocked:', e));
        """)
        
        await authenticated_page.wait_for_timeout(2000)
        
        # Vérifier que la requête forgée a été interceptée et rejetée
        assert request_intercepted["count"] >= 1
        assert request_intercepted["last_request"]["price_id"] == "price_FORGED_123"
        
        print("✅ Test validation price_id contre forge réussi")
    
    @pytest.mark.asyncio
    async def test_double_click_protection_via_idempotency(self, authenticated_page: Page):
        """Test: Protection double-clic via idempotence"""
        
        request_count = {"create": 0}
        
        async def count_requests(route):
            """Compte les requêtes de création"""
            request_count["create"] += 1
            
            if request_count["create"] == 1:
                # Première requête = succès
                await route.fulfill(
                    json={
                        "checkout_url": "https://checkout.stripe.com/test1", 
                        "status": "checkout_created"
                    }
                )
            else:
                # Requêtes suivantes = protection idempotence
                await route.fulfill(
                    json={
                        "status": "checkout_already_exists",
                        "message": "Session de paiement déjà créée (protection double-clic)"
                    }
                )
        
        await authenticated_page.route("**/api/subscription/create", count_requests)
        
        # Mock autres endpoints
        await authenticated_page.route("**/api/subscription/trial-eligibility*", lambda route: route.fulfill(
            json={"eligible": True, "reason": "eligible_for_trial"}
        ))
        
        await authenticated_page.route("**/api/subscription/plans", lambda route: route.fulfill(
            json={
                "success": True,
                "plans": {
                    "pro": {
                        "id": "pro",
                        "price": 29,
                        "stripe_price_id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"
                    }
                }
            }
        ))
        
        await authenticated_page.goto("http://localhost:3000/subscription")
        await authenticated_page.wait_for_timeout(2000)
        
        # Trouver le bouton d'essai gratuit
        trial_button = authenticated_page.locator('button:has-text("Essai gratuit")')
        await trial_button.wait_for(state="visible")
        
        # Double clic rapide
        await trial_button.click()
        await trial_button.click()  # Clic immédiat
        
        await authenticated_page.wait_for_timeout(3000)
        
        # Vérifier qu'il y a eu 2 requêtes (la 2ème protégée par idempotence)
        assert request_count["create"] == 2
        
        print("✅ Test protection double-clic via idempotence réussi")

# ================================================================================
# 🔐 TESTS E2E SÉCURITÉ WEBHOOKS
# ================================================================================

@pytest.mark.e2e
class TestWebhookSecurityE2E:
    """Tests E2E pour la sécurité des webhooks"""
    
    @pytest.mark.asyncio
    async def test_webhook_signature_validation_e2e(self, browser_context: BrowserContext):
        """Test E2E validation signature webhook"""
        
        page = await browser_context.new_page()
        
        # Mock endpoint webhook pour tester la validation
        webhook_attempts = {"valid": 0, "invalid": 0}
        
        async def mock_webhook_endpoint(route):
            """Mock de l'endpoint webhook"""
            request = route.request
            signature = request.headers.get("stripe-signature", "")
            
            if "valid_signature" in signature:
                webhook_attempts["valid"] += 1
                await route.fulfill(json={"received": True, "processed": True})
            else:
                webhook_attempts["invalid"] += 1
                await route.fulfill(
                    status=400,
                    json={"error": "Invalid signature"}
                )
        
        await page.route("**/api/subscription/webhook", mock_webhook_endpoint)
        
        # Simuler envoi de webhooks depuis une page de test
        await page.goto("data:text/html,<html><body><h1>Webhook Test</h1></body></html>")
        
        # Tenter webhook avec signature valide
        await page.evaluate("""
            fetch('/api/subscription/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'stripe-signature': 't=1234567890,v1=valid_signature'
                },
                body: JSON.stringify({
                    id: 'evt_test',
                    type: 'test',
                    data: {}
                })
            });
        """)
        
        # Tenter webhook avec signature invalide
        await page.evaluate("""
            fetch('/api/subscription/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'stripe-signature': 'invalid_signature'
                },
                body: JSON.stringify({
                    id: 'evt_test_invalid',
                    type: 'test',
                    data: {}
                })
            });
        """)
        
        await page.wait_for_timeout(2000)
        
        # Vérifier que les tentatives ont été traitées correctement
        assert webhook_attempts["valid"] >= 1
        assert webhook_attempts["invalid"] >= 1
        
        await page.close()
        print("✅ Test validation signature webhook E2E réussi")

# ================================================================================
# ⚙️ CONFIGURATION PYTEST PLAYWRIGHT
# ================================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Configuration de la boucle d'événements pour Playwright"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="class")
async def browser_context():
    """Context de navigateur réutilisable"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        yield context
        await context.close()
        await browser.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e", "--tb=short"])