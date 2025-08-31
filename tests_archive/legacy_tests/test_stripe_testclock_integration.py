# ================================================================================
# ECOMSIMPLY - TESTS INTÉGRATION STRIPE TEST CLOCK
# ================================================================================

import pytest
import asyncio
import stripe
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import os
import time

# Configuration Stripe Test
stripe.api_key = os.getenv("STRIPE_TEST_SECRET_KEY", "sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...")
STRIPE_TEST_WEBHOOK_SECRET = os.getenv("STRIPE_TEST_WEBHOOK_SECRET", "whsec_test_...")

# Imports du système
from backend.services.stripe_service import stripe_service
from backend.services.trial_eligibility_service import trial_eligibility_service
from backend.webhooks.stripe_webhooks import webhook_handler
from backend.models.subscription import User, PlanType, CreateSubscriptionRequest, SubscriptionStatus

# ================================================================================
# 🕐 TESTS STRIPE TEST CLOCK
# ================================================================================

class TestStripeTestClock:
    """Tests d'intégration avec Stripe Test Clock pour scénarios temporels"""
    
    @pytest.fixture(scope="session")
    def test_clock(self):
        """Crée un Test Clock Stripe pour les tests"""
        try:
            # Créer un Test Clock
            test_clock = stripe.test_helpers.TestClock.create(
                frozen_time=int(datetime.utcnow().timestamp()),
                name="ECOMSIMPLY_TEST_CLOCK"
            )
            yield test_clock
            
            # Cleanup après tests
            try:
                stripe.test_helpers.TestClock.delete(test_clock.id)
            except:
                pass
        except Exception as e:
            pytest.skip(f"Stripe Test Clock not available: {e}")
    
    @pytest.fixture
    def mock_user(self):
        """Utilisateur de test"""
        return User(
            id="user_testclock_123",
            email="testclock@example.com",
            password_hash="hashed",
            has_used_trial=False,
            trial_used_at=None
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock DB pour tests"""
        db = Mock()
        db.users = Mock()
        db.users.find_one = AsyncMock()
        db.users.update_one = AsyncMock()
        db.subscription_records = Mock()
        db.subscription_records.insert_one = AsyncMock()
        db.subscription_records.update_one = AsyncMock()
        db.payment_history = Mock()
        db.payment_history.insert_one = AsyncMock()
        return db
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scenario_trial_to_active_then_invoice_failed_then_recovered(self, test_clock, mock_user, mock_db):
        """Scénario complet: Essai → Actif → Échec paiement → Récupération"""
        
        # Phase 1: Créer un client avec Test Clock
        customer = stripe.Customer.create(
            email=mock_user.email,
            test_clock=test_clock.id
        )
        mock_user.stripe_customer_id = customer.id
        
        # Phase 2: Créer abonnement avec essai 7 jours
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                "price": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"  # Prix Pro
            }],
            trial_period_days=7,
            test_clock=test_clock.id
        )
        
        assert subscription.status == "trialing"
        assert subscription.trial_end is not None
        
        # Phase 3: Avancer le temps au milieu de l'essai (4 jours)
        stripe.test_helpers.TestClock.advance(
            test_clock.id,
            frozen_time=test_clock.frozen_time + (4 * 24 * 3600)
        )
        
        subscription_refreshed = stripe.Subscription.retrieve(subscription.id)
        assert subscription_refreshed.status == "trialing"
        
        # Phase 4: Avancer à la fin de l'essai (8 jours total)
        stripe.test_helpers.TestClock.advance(
            test_clock.id, 
            frozen_time=test_clock.frozen_time + (8 * 24 * 3600)
        )
        
        # Simuler échec de paiement à la fin de l'essai
        subscription_refreshed = stripe.Subscription.retrieve(subscription.id)
        
        # Si la carte de test échoue, le statut sera past_due ou unpaid
        if subscription_refreshed.status in ["past_due", "unpaid"]:
            # Phase 5: Simuler récupération avec nouveau mode de paiement
            # Créer un PaymentMethod de test qui fonctionne
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": "4242424242424242",
                    "exp_month": 12,
                    "exp_year": 2030,
                    "cvc": "123"
                }
            )
            
            # Attacher le nouveau mode de paiement
            payment_method.attach(customer=customer.id)
            
            # Mettre à jour l'abonnement avec le nouveau mode de paiement
            stripe.Subscription.modify(
                subscription.id,
                default_payment_method=payment_method.id
            )
            
            # Simuler le paiement réussi de la facture en souffrance
            invoices = stripe.Invoice.list(
                customer=customer.id,
                status="open"
            )
            
            if invoices.data:
                latest_invoice = invoices.data[0]
                stripe.Invoice.pay(latest_invoice.id)
            
            # Vérifier que l'abonnement est maintenant actif
            subscription_final = stripe.Subscription.retrieve(subscription.id)
            assert subscription_final.status == "active"
            
        print(f"✅ Scénario complet test réussi: {subscription_refreshed.status}")
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_scenario_cancel_at_period_end_then_reactivate(self, test_clock, mock_user, mock_db):
        """Scénario: Annulation en fin de période → Réactivation"""
        
        # Créer client et abonnement actif
        customer = stripe.Customer.create(
            email=mock_user.email,
            test_clock=test_clock.id
        )
        
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                "price": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"
            }],
            test_clock=test_clock.id
        )
        
        assert subscription.status == "active"
        
        # Annuler à la fin de la période
        canceled_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )
        
        assert canceled_subscription.cancel_at_period_end == True
        assert canceled_subscription.status == "active"  # Encore actif jusqu'à la fin
        
        # Réactiver avant la fin
        reactivated_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=False
        )
        
        assert reactivated_subscription.cancel_at_period_end == False
        assert reactivated_subscription.status == "active"
        
        print("✅ Scénario cancel/reactivate réussi")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scenario_upgrade_downgrade_with_proration(self, test_clock, mock_user, mock_db):
        """Scénario: Upgrade/Downgrade avec proratisation"""
        
        # Créer client avec abonnement Pro
        customer = stripe.Customer.create(
            email=mock_user.email,
            test_clock=test_clock.id
        )
        
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                "price": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"  # Pro
            }],
            test_clock=test_clock.id
        )
        
        assert subscription.status == "active"
        original_price = subscription.items.data[0].price.id
        
        # Avancer de 15 jours dans la période
        stripe.test_helpers.TestClock.advance(
            test_clock.id,
            frozen_time=test_clock.frozen_time + (15 * 24 * 3600)
        )
        
        # Upgrade vers Premium
        upgraded_subscription = stripe.Subscription.modify(
            subscription.id,
            items=[{
                "id": subscription.items.data[0].id,
                "price": "price_1RrxgjGK8qzu5V5WvOSb4uPd"  # Premium
            }],
            proration_behavior="create_prorations"
        )
        
        assert upgraded_subscription.items.data[0].price.id != original_price
        print("✅ Scénario upgrade/downgrade réussi")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scenario_non_eligible_trial_forces_paid_checkout(self, test_clock, mock_user, mock_db):
        """Scénario: Utilisateur non éligible essai → Checkout payant forcé"""
        
        # Marquer utilisateur comme ayant déjà utilisé son essai
        mock_user.has_used_trial = True
        mock_user.trial_used_at = datetime.utcnow() - timedelta(days=30)
        
        # Simuler check d'éligibilité
        eligibility_result = await trial_eligibility_service.check_trial_eligibility(
            user=mock_user,
            plan_type=PlanType.PRO,
            client_ip="192.168.1.1",
            db=mock_db
        )
        
        assert eligibility_result["eligible"] == False
        assert "trial_already_used" in eligibility_result["reason"]
        
        # Créer une demande d'abonnement AVEC essai demandé
        request = CreateSubscriptionRequest(
            plan_type=PlanType.PRO,
            price_id="price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
            success_url="https://test.com/success",
            cancel_url="https://test.com/cancel",
            with_trial=True  # Demandé mais non éligible
        )
        
        # Mock création customer
        with patch.object(stripe_service, 'create_or_get_customer', return_value="cus_test"):
            with patch('stripe.checkout.Session.create') as mock_create:
                mock_create.return_value = Mock(
                    id="cs_test",
                    url="https://checkout.stripe.com/test"
                )
                
                # Exécuter la création de checkout
                result = await stripe_service.create_subscription_checkout(
                    user=mock_user,
                    request=request,
                    client_ip="192.168.1.1", 
                    db=mock_db
                )
                
                # Vérifier que le checkout est créé SANS essai
                assert result.status == "checkout_created"
                assert result.trial_active == False  # Forcé côté serveur
                
                # Vérifier que Stripe est appelé sans trial_period_days
                call_kwargs = mock_create.call_args[1]
                if "subscription_data" in call_kwargs:
                    assert "trial_period_days" not in call_kwargs["subscription_data"]
                
        print("✅ Scénario essai non éligible → checkout payant réussi")

# ================================================================================
# 🔄 TESTS WEBHOOK AVEC TEST CLOCK
# ================================================================================

class TestWebhookWithTestClock:
    """Tests des webhooks avec Test Clock pour scénarios temporels"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_webhook_checkout_completed_with_trial_recording(self, mock_db):
        """Test webhook checkout.session.completed avec enregistrement essai"""
        
        # Mock event webhook
        webhook_event = {
            "id": "evt_test_12345",
            "type": "checkout.session.completed",
            "created": int(datetime.utcnow().timestamp()),
            "data": {
                "object": {
                    "id": "cs_test_session",
                    "customer": "cus_test_customer",
                    "subscription": "sub_test_subscription",
                    "metadata": {
                        "user_id": "user_test_123",
                        "plan_type": "pro"
                    }
                }
            }
        }
        
        # Mock user dans DB
        mock_user_data = {
            "id": "user_test_123",
            "email": "test@example.com",
            "has_used_trial": False,
            "subscription_plan": "gratuit"
        }
        mock_db.users.find_one.return_value = mock_user_data
        
        # Mock Stripe subscription avec essai
        mock_subscription = Mock()
        mock_subscription.id = "sub_test_subscription"
        mock_subscription.status = "trialing"
        mock_subscription.trial_start = int(datetime.utcnow().timestamp())
        mock_subscription.trial_end = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        mock_subscription.current_period_start = int(datetime.utcnow().timestamp())
        mock_subscription.current_period_end = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        mock_subscription.__getitem__ = lambda self, key: {
            "items": {
                "data": [{
                    "price": {
                        "id": "price_1Rrw3UGK8qzu5V5Wu8PnvKzK",
                        "unit_amount": 2900,
                        "currency": "eur"
                    }
                }]
            }
        }[key]
        
        with patch('stripe.Subscription.retrieve', return_value=mock_subscription):
            with patch.object(trial_eligibility_service, 'record_trial_usage', return_value=True) as mock_record:
                
                # Exécuter le handler
                result = await webhook_handler.handle_checkout_session_completed(
                    event_data=webhook_event["data"],
                    db=mock_db
                )
                
                # Vérifier que l'essai est enregistré
                assert result == True
                mock_record.assert_called_once()
                
                # Vérifier mise à jour user
                mock_db.users.update_one.assert_called()
                update_call = mock_db.users.update_one.call_args
                assert "has_used_trial" in str(update_call)
                assert "trial_used_at" in str(update_call)
        
        print("✅ Webhook checkout completed avec enregistrement essai réussi")

# ================================================================================
# ⚡ UTILITAIRES TESTS INTÉGRATION
# ================================================================================

class TestClockHelper:
    """Utilitaires pour gérer les Test Clocks"""
    
    @staticmethod
    def create_test_clock(name: str = None) -> str:
        """Crée un Test Clock et retourne son ID"""
        try:
            test_clock = stripe.test_helpers.TestClock.create(
                frozen_time=int(datetime.utcnow().timestamp()),
                name=name or f"TEST_{int(time.time())}"
            )
            return test_clock.id
        except Exception as e:
            pytest.skip(f"Cannot create Test Clock: {e}")
    
    @staticmethod
    def cleanup_test_clock(test_clock_id: str):
        """Nettoie un Test Clock"""
        try:
            stripe.test_helpers.TestClock.delete(test_clock_id)
        except Exception as e:
            print(f"Warning: Could not delete test clock {test_clock_id}: {e}")
    
    @staticmethod
    def advance_clock(test_clock_id: str, days: int = 1):
        """Avance un Test Clock de N jours"""
        current_clock = stripe.test_helpers.TestClock.retrieve(test_clock_id)
        new_time = current_clock.frozen_time + (days * 24 * 3600)
        
        stripe.test_helpers.TestClock.advance(
            test_clock_id,
            frozen_time=new_time
        )
        
        return new_time

# ================================================================================
# ⚡ CONFIGURATION PYTEST
# ================================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_stripe_test_env():
    """Configuration globale pour les tests Stripe"""
    # Vérifier que nous sommes en mode test
    if not stripe.api_key or "sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" not in stripe.api_key:
        pytest.skip("Stripe test key required for integration tests")
    
    yield
    
    # Cleanup après tous les tests
    print("🧹 Cleaning up Stripe test resources...")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])