# ================================================================================
# ECOMSIMPLY - TESTS UNITAIRES RENFORCEMENT STRIPE + RÈGLE ESSAI UNIQUE
# ================================================================================

import pytest
import asyncio
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import stripe
from fastapi import Request, HTTPException

# Imports du système
from backend.services.stripe_service import stripe_service, validate_price_id, get_authorized_price_id, STRIPE_PRICE_ALLOWLIST
from backend.services.trial_eligibility_service import trial_eligibility_service, TrialEligibilityService
from backend.webhooks.stripe_webhooks import webhook_handler, StripeWebhookHandler
from backend.models.subscription import User, PlanType, CreateSubscriptionRequest

# ================================================================================
# 🔐 TESTS SÉCURITÉ WEBHOOKS
# ================================================================================

class TestWebhookSecurity:
    """Tests pour la sécurité des webhooks Stripe"""
    
    @pytest.fixture
    def mock_request(self):
        """Mock d'une requête webhook Stripe"""
        request = Mock(spec=Request)
        request.body = AsyncMock()
        request.headers = {}
        return request
    
    @pytest.fixture
    def mock_db(self):
        """Mock de la base de données"""
        db = Mock()
        db.webhook_events = Mock()
        db.webhook_events.find_one = AsyncMock(return_value=None)
        db.webhook_events.insert_one = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_webhook_signature_raw_ok(self, mock_request, mock_db):
        """Test vérification signature webhook avec raw body - OK"""
        # Prepare - timestamp récent
        current_time = int(datetime.utcnow().timestamp())
        raw_payload = f'{{"id": "evt_test", "type": "checkout.session.completed", "created": {current_time}}}'.encode()
        valid_signature = f"t={current_time},v1=valid_signature"
        
        mock_request.body.return_value = raw_payload
        mock_request.headers = {"stripe-signature": valid_signature}
        
        mock_event = {
            "id": "evt_test_12345",
            "type": "checkout.session.completed", 
            "created": current_time,  # Timestamp récent
            "data": {"object": {"id": "cs_test"}}
        }
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            # Execute
            result = await webhook_handler.verify_webhook_signature(mock_request, mock_db)
            
            # Assert
            assert result["event"]["id"] == "evt_test_12345"
            assert result["duplicate"] == False
            assert "Valid webhook event" in result["message"]
    
    @pytest.mark.asyncio
    async def test_webhook_signature_raw_ko(self, mock_request, mock_db):
        """Test vérification signature webhook - ÉCHEC"""
        # Prepare
        raw_payload = b'{"id": "evt_test", "type": "test"}'
        invalid_signature = "invalid_signature"
        
        mock_request.body.return_value = raw_payload
        mock_request.headers = {"stripe-signature": invalid_signature}
        
        with patch('stripe.Webhook.construct_event', side_effect=stripe.error.SignatureVerificationError("Invalid signature", "sig")):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await webhook_handler.verify_webhook_signature(mock_request, mock_db)
            
            assert exc_info.value.status_code == 400
            assert "Invalid signature" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_webhook_antireplay_blocks_duplicate_event(self, mock_request, mock_db):
        """Test anti-replay bloque les événements dupliqués"""
        # Prepare - timestamp récent
        current_time = int(datetime.utcnow().timestamp())
        raw_payload = f'{{"id": "evt_duplicate", "type": "test", "created": {current_time}}}'.encode()
        valid_signature = f"t={current_time},v1=valid_signature"
        
        mock_request.body.return_value = raw_payload
        mock_request.headers = {"stripe-signature": valid_signature}
        
        mock_event = {
            "id": "evt_duplicate_12345",
            "type": "test",
            "created": current_time,
            "data": {}
        }
        
        # Simuler événement déjà existant
        mock_db.webhook_events.find_one.return_value = {"event_id": "evt_duplicate_12345"}
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            # Execute
            result = await webhook_handler.verify_webhook_signature(mock_request, mock_db)
            
            # Assert
            assert result["duplicate"] == True
            assert "Duplicate event ignored" in result["message"]
    
    @pytest.mark.asyncio
    async def test_webhook_event_too_old(self, mock_request, mock_db):
        """Test rejet des événements trop anciens"""
        # Prepare - événement vieux de 10 minutes
        old_timestamp = int((datetime.utcnow() - timedelta(minutes=10)).timestamp())
        raw_payload = f'{{"id": "evt_old", "type": "test", "created": {old_timestamp}}}'.encode()
        
        mock_request.body.return_value = raw_payload
        mock_request.headers = {"stripe-signature": "valid"}
        
        mock_event = {
            "id": "evt_old_12345",
            "type": "test", 
            "created": old_timestamp,
            "data": {}
        }
        
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            # Execute & Assert
            with pytest.raises(HTTPException) as exc_info:
                await webhook_handler.verify_webhook_signature(mock_request, mock_db)
            
            assert exc_info.value.status_code == 400
            assert "Event too old" in str(exc_info.value.detail)

# ================================================================================
# 🔐 TESTS ALLOWLIST PRIX
# ================================================================================

class TestPriceAllowlist:
    """Tests pour l'allowlist des prix Stripe"""
    
    def test_allowlist_price_rejects_forged_price(self):
        """Test rejet des price_id forgés"""
        # Test price_id valides
        assert validate_price_id("price_1Rrw3UGK8qzu5V5Wu8PnvKzK", PlanType.PRO) == True
        assert validate_price_id("price_1RrxgjGK8qzu5V5WvOSb4uPd", PlanType.PREMIUM) == True
        
        # Test price_id forgés
        assert validate_price_id("price_FORGED123", PlanType.PRO) == False
        assert validate_price_id("price_1Rrw3UGK8qzu5V5Wu8PnvKzK", PlanType.PREMIUM) == False  # Mauvais plan
        assert validate_price_id("", PlanType.PRO) == False
        assert validate_price_id(None, PlanType.PRO) == False
    
    def test_get_authorized_price_id(self):
        """Test récupération des price_id autorisés"""
        assert get_authorized_price_id(PlanType.PRO) == "price_1Rrw3UGK8qzu5V5Wu8PnvKzK"
        assert get_authorized_price_id(PlanType.PREMIUM) == "price_1RrxgjGK8qzu5V5WvOSb4uPd"
        assert get_authorized_price_id(PlanType.GRATUIT) == None
    
    def test_allowlist_completeness(self):
        """Test complétude de l'allowlist"""
        # Vérifier que tous les plans payants ont un price_id
        for plan_type in [PlanType.PRO, PlanType.PREMIUM]:
            price_id = get_authorized_price_id(plan_type)
            assert price_id is not None, f"Missing price_id for {plan_type}"
            assert price_id.startswith("price_"), f"Invalid price_id format for {plan_type}"

# ================================================================================
# 🔑 TESTS IDEMPOTENCE
# ================================================================================

class TestIdempotency:
    """Tests pour l'idempotence Stripe"""
    
    def test_idempotency_key_generation(self):
        """Test génération des clés d'idempotence"""
        # Test génération de base
        key1 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        key2 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        
        # Même window temporelle = même clé
        assert key1 == key2
        assert key1.startswith("checkout_")
        assert len(key1) <= 255  # Limite Stripe
    
    def test_idempotency_key_different_users(self):
        """Test clés différentes pour utilisateurs différents"""
        key1 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        key2 = stripe_service._generate_idempotency_key("checkout", "user456", "pro")
        
        assert key1 != key2
    
    def test_idempotency_key_different_plans(self):
        """Test clés différentes pour plans différents"""
        key1 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        key2 = stripe_service._generate_idempotency_key("checkout", "user123", "premium")
        
        assert key1 != key2
    
    @patch('time.time')
    def test_idempotency_key_different_time_windows(self, mock_time):
        """Test clés différentes pour windows temporelles différentes"""
        # Window 1
        mock_time.return_value = 1000
        key1 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        
        # Window 2 (5+ minutes plus tard)
        mock_time.return_value = 1000 + 400  # 6 minutes 40s
        key2 = stripe_service._generate_idempotency_key("checkout", "user123", "pro")
        
        assert key1 != key2

# ================================================================================
# 🎯 TESTS ÉLIGIBILITÉ ESSAI
# ================================================================================

class TestTrialEligibility:
    """Tests pour l'éligibilité à l'essai gratuit"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock utilisateur pour tests"""
        return User(
            id="user_test_123",
            email="test@example.com",
            password_hash="hashed",
            has_used_trial=False,
            trial_used_at=None
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock base de données pour tests"""
        db = Mock()
        db.trial_fingerprints = Mock()
        db.trial_fingerprints.find_one = AsyncMock(return_value=None)
        db.users = Mock()
        db.users.find_one = AsyncMock(return_value=None)
        db.trial_ip_usage = Mock()
        db.trial_ip_usage.count_documents = AsyncMock(return_value=0)
        return db
    
    @pytest.mark.asyncio
    async def test_trial_eligibility_true_new_user(self, mock_user, mock_db):
        """Test éligibilité TRUE pour nouvel utilisateur"""
        # Execute
        result = await trial_eligibility_service.check_trial_eligibility(
            user=mock_user,
            plan_type=PlanType.PRO,
            client_ip="192.168.1.1",
            db=mock_db
        )
        
        # Assert
        assert result["eligible"] == True
        assert result["reason"] == "eligible_for_trial"
        assert result["plan_type"] == PlanType.PRO
    
    @pytest.mark.asyncio
    async def test_trial_eligibility_false_by_user_flag(self, mock_user, mock_db):
        """Test éligibilité FALSE par flag utilisateur"""
        # Prepare
        mock_user.has_used_trial = True
        
        # Execute
        result = await trial_eligibility_service.check_trial_eligibility(
            user=mock_user,
            plan_type=PlanType.PRO,
            db=mock_db
        )
        
        # Assert
        assert result["eligible"] == False
        assert result["reason"] == "trial_already_used_legacy"
    
    @pytest.mark.asyncio
    async def test_trial_eligibility_false_by_timestamp(self, mock_user, mock_db):
        """Test éligibilité FALSE par timestamp trial_used_at"""
        # Prepare
        mock_user.trial_used_at = datetime.utcnow() - timedelta(days=100)
        
        # Execute
        result = await trial_eligibility_service.check_trial_eligibility(
            user=mock_user,
            plan_type=PlanType.PRO,
            db=mock_db
        )
        
        # Assert
        assert result["eligible"] == False
        assert result["reason"] == "trial_already_used"
    
    @pytest.mark.asyncio
    async def test_trial_eligibility_false_by_fingerprint(self, mock_user, mock_db):
        """Test éligibilité FALSE par fingerprint de paiement"""
        # Prepare
        mock_db.trial_fingerprints.find_one.return_value = {
            "fingerprint_hash": "hash123",
            "trial_used": True,
            "used_at": datetime.utcnow()
        }
        
        # Execute
        result = await trial_eligibility_service.check_trial_eligibility(
            user=mock_user,
            plan_type=PlanType.PRO,
            payment_fingerprint="test_fingerprint",
            db=mock_db
        )
        
        # Assert
        assert result["eligible"] == False
        assert result["reason"] == "payment_fingerprint_already_used"
    
    @pytest.mark.asyncio
    async def test_trial_eligibility_record_usage(self, mock_user, mock_db):
        """Test enregistrement utilisation essai"""
        # Mock des opérations DB
        mock_db.trial_fingerprints.insert_one = AsyncMock()
        mock_db.trial_ip_usage.insert_one = AsyncMock()
        mock_db.users.update_one = AsyncMock()
        
        # Execute
        result = await trial_eligibility_service.record_trial_usage(
            user=mock_user,
            payment_fingerprint="test_fingerprint",
            client_ip="192.168.1.1",
            plan_type=PlanType.PRO,
            db=mock_db
        )
        
        # Assert
        assert result == True
        assert mock_user.trial_used_at is not None
        assert mock_user.has_used_trial == True
        mock_db.trial_fingerprints.insert_one.assert_called_once()
        mock_db.trial_ip_usage.insert_one.assert_called_once()
        mock_db.users.update_one.assert_called_once()

# ================================================================================
# 🛒 TESTS CHECKOUT SÉCURISÉ
# ================================================================================

class TestSecureCheckout:
    """Tests pour la création de checkout sécurisée"""
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="user_test_123",
            email="test@example.com",
            password_hash="hashed",
            has_used_trial=False
        )
    
    @pytest.fixture
    def mock_request(self):
        return CreateSubscriptionRequest(
            plan_type=PlanType.PRO,
            price_id="price_1Rrw3UGK8qzu5V5Wu8PnvKzK",  # Prix autorisé
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            with_trial=True
        )
    
    @patch('backend.services.stripe_service.stripe.checkout.Session.create')
    @patch('backend.services.trial_eligibility_service.trial_eligibility_service.check_trial_eligibility')
    @pytest.mark.asyncio
    async def test_checkout_with_valid_price_and_eligible_trial(self, mock_eligibility, mock_stripe_create, mock_user, mock_request):
        """Test checkout avec prix valide et essai éligible"""
        # Prepare
        mock_eligibility.return_value = {"eligible": True, "reason": "eligible_for_trial"}
        mock_stripe_create.return_value = Mock(id="cs_test", url="https://checkout.stripe.com/test")
        
        # Execute
        result = await stripe_service.create_subscription_checkout(mock_user, mock_request, "192.168.1.1", None)
        
        # Assert
        assert result.status == "checkout_created"
        assert result.trial_active == True
        mock_stripe_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_checkout_rejects_invalid_price_id(self, mock_user):
        """Test rejet price_id non autorisé"""
        # Prepare
        invalid_request = CreateSubscriptionRequest(
            plan_type=PlanType.PRO,
            price_id="price_FORGED_INVALID",  # Prix non autorisé
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            with_trial=False
        )
        
        # Execute
        result = await stripe_service.create_subscription_checkout(mock_user, invalid_request, "192.168.1.1", None)
        
        # Assert
        assert result.status == "validation_error"
        assert "Price ID non autorisé" in result.message
    
    @patch('backend.services.trial_eligibility_service.trial_eligibility_service.check_trial_eligibility')
    @patch('backend.services.stripe_service.stripe.checkout.Session.create')
    @pytest.mark.asyncio
    async def test_checkout_forces_paid_when_trial_not_eligible(self, mock_stripe_create, mock_eligibility, mock_user, mock_request):
        """Test que le checkout force un abonnement payant quand essai non éligible"""
        # Prepare
        mock_eligibility.return_value = {"eligible": False, "reason": "trial_already_used"}
        mock_stripe_create.return_value = Mock(id="cs_test", url="https://checkout.stripe.com/test")
        
        # Execute - demander essai mais être non éligible
        result = await stripe_service.create_subscription_checkout(mock_user, mock_request, "192.168.1.1", None)
        
        # Assert
        assert result.status == "checkout_created"
        assert result.trial_active == False  # Forcé à False côté serveur
        
        # Vérifier que Stripe est appelé SANS trial_period_days
        call_args = mock_stripe_create.call_args[1]
        assert "subscription_data" not in call_args or "trial_period_days" not in call_args.get("subscription_data", {})

# ================================================================================
# 🧪 TESTS HASH ET SÉCURITÉ
# ================================================================================

class TestHashingSecurity:
    """Tests pour les fonctions de hashage sécurisées"""
    
    def test_email_hashing_consistency(self):
        """Test cohérence du hashage d'email"""
        email = "Test@Example.COM"
        hash1 = trial_eligibility_service._hash_email(email)
        hash2 = trial_eligibility_service._hash_email(email)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex
    
    def test_email_hashing_normalization(self):
        """Test normalisation email avant hashage"""
        hash1 = trial_eligibility_service._hash_email("test@example.com")
        hash2 = trial_eligibility_service._hash_email("TEST@EXAMPLE.COM")
        hash3 = trial_eligibility_service._hash_email("  Test@Example.COM  ")
        
        assert hash1 == hash2 == hash3
    
    def test_fingerprint_hashing(self):
        """Test hashage fingerprint paiement"""
        fingerprint = "test_fingerprint_123"
        hash1 = trial_eligibility_service._hash_fingerprint(fingerprint)
        hash2 = trial_eligibility_service._hash_fingerprint(fingerprint)
        
        assert hash1 == hash2
        assert hash1 != fingerprint  # Hash ≠ donnée originale
        assert len(hash1) == 64
    
    def test_no_pii_in_hashes(self):
        """Test absence de PII dans les hash"""
        email = "user@company.com"
        ip = "192.168.1.100"
        user_id = "user_12345"
        
        email_hash = trial_eligibility_service._hash_email(email)
        ip_hash = trial_eligibility_service._hash_ip(ip)
        user_hash = trial_eligibility_service._hash_user_id(user_id)
        
        # Les hash ne doivent pas contenir les données originales
        assert email not in email_hash
        assert ip not in ip_hash
        assert user_id not in user_hash
        
        # Les hash doivent être de longueur fixe
        assert len(email_hash) == 64
        assert len(ip_hash) == 64
        assert len(user_hash) == 64

# ================================================================================
# ⚡ CONFIGURATION PYTEST
# ================================================================================

if __name__ == "__main__":
    # Lancer les tests avec : python -m pytest test_stripe_hardening.py -v
    pytest.main([__file__, "-v", "--tb=short"])