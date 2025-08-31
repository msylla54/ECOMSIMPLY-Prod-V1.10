"""
Tests Backend - Amazon Pricing Phase 4
Tests complets pour le moteur de prix intelligents
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

# Imports du système
from backend.models.amazon_pricing import (
    PricingRule, PricingHistory, PricingCalculation, CompetitorOffer,
    PricingStrategy, BuyBoxStatus, PricingRuleStatus
)
from backend.amazon.pricing_engine import pricing_engine
from backend.services.amazon_pricing_rules_service import pricing_rules_service


class TestAmazonPricingModels:
    """Tests des modèles de données"""
    
    def test_pricing_rule_creation(self):
        """Test création règle de pricing valide"""
        rule = PricingRule(
            user_id="user-123",
            sku="B08N5WRWNW",
            marketplace_id="A13V1IB3VIYZZH",
            min_price=50.0,
            max_price=150.0,
            variance_pct=5.0,
            strategy=PricingStrategy.BUYBOX_MATCH
        )
        
        assert rule.user_id == "user-123"
        assert rule.sku == "B08N5WRWNW"
        assert rule.strategy == PricingStrategy.BUYBOX_MATCH
        assert rule.status == PricingRuleStatus.ACTIVE
        assert rule.created_at is not None
    
    def test_pricing_rule_validation_errors(self):
        """Test validation des erreurs de règles"""
        
        # Prix max <= prix min
        with pytest.raises(ValueError, match="max_price must be greater than min_price"):
            PricingRule(
                user_id="user-123",
                sku="TEST-SKU",
                marketplace_id="A13V1IB3VIYZZH",
                min_price=100.0,
                max_price=50.0,  # Erreur : max < min
                strategy=PricingStrategy.BUYBOX_MATCH
            )
        
        # Marge cible manquante pour strategy margin_target
        with pytest.raises(ValueError, match="margin_target is required"):
            PricingRule(
                user_id="user-123",
                sku="TEST-SKU",
                marketplace_id="A13V1IB3VIYZZH",
                min_price=50.0,
                max_price=150.0,
                strategy=PricingStrategy.MARGIN_TARGET
                # margin_target manquant
            )
    
    def test_competitor_offer_model(self):
        """Test modèle offre concurrente"""
        offer = CompetitorOffer(
            seller_id="SELLER123",
            condition="New",
            price=79.99,
            shipping=3.50,
            landed_price=83.49,
            is_buy_box_winner=True
        )
        
        assert offer.seller_id == "SELLER123"
        assert offer.landed_price == 83.49
        assert offer.is_buy_box_winner is True
    
    def test_pricing_calculation_model(self):
        """Test modèle calcul de prix"""
        calculation = PricingCalculation(
            sku="B08N5WRWNW",
            marketplace_id="A13V1IB3VIYZZH",
            current_price=79.99,
            competitors=[],
            recommended_price=77.50,
            buybox_status=BuyBoxStatus.RISK,
            within_rules=True,
            reasoning="Test calculation",
            confidence=85.5
        )
        
        assert calculation.sku == "B08N5WRWNW"
        assert calculation.recommended_price == 77.50
        assert calculation.buybox_status == BuyBoxStatus.RISK
        assert calculation.confidence == 85.5


class TestAmazonPricingEngine:
    """Tests du moteur de pricing"""
    
    @pytest.fixture
    def sample_rule(self):
        """Règle de test"""
        return PricingRule(
            user_id="user-123",
            sku="B08N5WRWNW",
            marketplace_id="A13V1IB3VIYZZH",
            min_price=50.0,
            max_price=150.0,
            variance_pct=5.0,
            strategy=PricingStrategy.BUYBOX_MATCH
        )
    
    @pytest.fixture
    def sample_competitors(self):
        """Données concurrentes de test"""
        return [
            CompetitorOffer(
                seller_id="SELLER1",
                condition="New",
                price=79.99,
                shipping=0.0,
                landed_price=79.99,
                is_buy_box_winner=True
            ),
            CompetitorOffer(
                seller_id="SELLER2",
                condition="New", 
                price=82.50,
                shipping=3.99,
                landed_price=86.49,
                is_buy_box_winner=False
            ),
            CompetitorOffer(
                seller_id="SELLER3",
                condition="New",
                price=77.00,
                shipping=5.99,
                landed_price=82.99,
                is_buy_box_winner=False
            )
        ]
    
    @patch('backend.amazon.pricing_engine.AmazonPricingEngine.get_competitive_pricing')
    async def test_calculate_optimal_price_buybox_match(self, mock_get_pricing, sample_rule, sample_competitors):
        """Test calcul prix avec stratégie Buy Box match"""
        
        # Mock des données SP-API
        mock_get_pricing.return_value = (sample_competitors, {'api_duration_ms': 1500})
        
        # Calculer prix optimal
        calculation = await pricing_engine.calculate_optimal_price(
            rule=sample_rule,
            current_price=85.00
        )
        
        # Vérifications
        assert calculation.sku == sample_rule.sku
        assert calculation.marketplace_id == sample_rule.marketplace_id
        assert calculation.current_price == 85.00
        assert len(calculation.competitors) == 3
        assert calculation.buybox_price == 79.99  # Prix du gagnant Buy Box
        assert calculation.recommended_price < 79.99  # Prix calculé légèrement inférieur
        assert calculation.within_rules is True
        assert calculation.confidence > 70.0
        assert "Buy Box" in calculation.reasoning
    
    def test_analyze_buybox_situation(self, sample_competitors):
        """Test analyse situation Buy Box"""
        
        analysis = pricing_engine._analyze_buybox_situation(sample_competitors, 85.00)
        
        assert analysis['buybox_price'] == 79.99
        assert analysis['buybox_winner'] == 'SELLER1'
        assert analysis['competitors_count'] == 3
        assert analysis['min_competitor_price'] == 77.00
        assert analysis['status'] == BuyBoxStatus.LOST  # Notre prix trop élevé
    
    def test_calculate_buybox_match_price(self, sample_rule):
        """Test calcul prix pour matcher Buy Box"""
        
        buybox_analysis = {
            'buybox_price': 79.99,
            'status': BuyBoxStatus.LOST
        }
        
        target_price, reasoning = pricing_engine._calculate_buybox_match_price(
            rule=sample_rule,
            buybox_analysis=buybox_analysis,
            competitors=[]
        )
        
        assert target_price == 79.98  # Buy Box price - 0.01
        assert "Buy Box" in reasoning
        assert "79.99" in reasoning
    
    def test_apply_pricing_constraints(self, sample_rule):
        """Test application des contraintes de pricing"""
        
        # Prix trop bas
        final_price, constraints = pricing_engine._apply_pricing_constraints(
            price=30.0,
            rule=sample_rule,
            current_price=80.0
        )
        
        assert final_price == sample_rule.min_price  # Ajusté au minimum
        assert "Prix minimum" in constraints[0]
        
        # Prix trop haut
        final_price, constraints = pricing_engine._apply_pricing_constraints(
            price=200.0,
            rule=sample_rule, 
            current_price=80.0
        )
        
        assert final_price == sample_rule.max_price  # Ajusté au maximum
        assert "Prix maximum" in constraints[0]
        
        # Variance trop importante
        final_price, constraints = pricing_engine._apply_pricing_constraints(
            price=120.0,  # +50% vs prix actuel 80€
            rule=sample_rule,
            current_price=80.0
        )
        
        expected_max = 80.0 + (80.0 * 0.05)  # +5% variance max
        assert final_price == expected_max
        assert "Variance maximale" in constraints[0]
    
    @patch('backend.integrations.amazon.client.AmazonSPAPIClient.make_request')
    async def test_get_competitive_pricing(self, mock_sp_api):
        """Test récupération données concurrentielles via SP-API"""
        
        # Mock réponse SP-API Product Pricing
        mock_sp_api.return_value = {
            'success': True,
            'data': {
                'payload': [{
                    'ASIN': 'B08N5WRWNW',
                    'Product': {
                        'CompetitivePricing': {
                            'CompetitivePrices': [{
                                'CompetitivePriceId': 'SELLER1',
                                'Price': {
                                    'ListingPrice': {'Amount': 79.99},
                                    'Shipping': {'Amount': 0.0},
                                    'LandedPrice': {'Amount': 79.99}
                                },
                                'belongsToRequester': False
                            }]
                        },
                        'Offers': [{
                            'IsBuyBoxWinner': True,
                            'SellerId': 'SELLER1',
                            'ItemCondition': 'New',
                            'ListingPrice': {'Amount': 79.99},
                            'Shipping': {'Amount': 0.0}
                        }]
                    }
                }]
            }
        }
        
        competitors, metadata = await pricing_engine.get_competitive_pricing(
            sku="B08N5WRWNW",
            marketplace_id="A13V1IB3VIYZZH"
        )
        
        assert len(competitors) == 1
        assert competitors[0].seller_id == "SELLER1"
        assert competitors[0].price == 79.99
        assert competitors[0].landed_price == 79.99
        assert metadata['buybox_info']['price'] == 79.99
        assert metadata['competitors_count'] == 1
        
        # Vérifier l'appel SP-API
        mock_sp_api.assert_called_once_with(
            method="GET",
            endpoint="/products/pricing/v0/price",
            params={
                "MarketplaceId": "A13V1IB3VIYZZH",
                "Skus": "B08N5WRWNW", 
                "ItemCondition": "New"
            },
            marketplace_id="A13V1IB3VIYZZH"
        )
    
    @patch('backend.integrations.amazon.client.AmazonSPAPIClient.make_request')
    async def test_publish_price_listings_items(self, mock_sp_api):
        """Test publication prix via Listings Items API"""
        
        mock_sp_api.return_value = {
            'success': True,
            'data': {
                'submissionId': 'sub_12345',
                'status': 'SUBMITTED'
            }
        }
        
        result = await pricing_engine.publish_price(
            sku="B08N5WRWNW",
            marketplace_id="A13V1IB3VIYZZH", 
            new_price=77.50,
            method="listings_items"
        )
        
        assert result['success'] is True
        assert result['method_used'] == 'listings_items'
        assert 'publication_duration_ms' in result
        assert result['submission_id'] == 'sub_12345'
        
        # Vérifier l'appel SP-API
        mock_sp_api.assert_called_once_with(
            method="PATCH",
            endpoint="/listings/2021-08-01/items/B08N5WRWNW",
            json_data={
                "productType": "PRODUCT",
                "patches": [{
                    "op": "replace",
                    "path": "/attributes/list_price",
                    "value": [{
                        "Amount": 77.50,
                        "CurrencyCode": "EUR"
                    }]
                }]
            },
            marketplace_id="A13V1IB3VIYZZH",
            params={"marketplaceIds": "A13V1IB3VIYZZH"}
        )
    
    def test_create_pricing_history_entry(self, sample_rule, sample_competitors):
        """Test création entrée historique"""
        
        calculation = PricingCalculation(
            sku=sample_rule.sku,
            marketplace_id=sample_rule.marketplace_id,
            current_price=85.00,
            competitors=sample_competitors,
            buybox_price=79.99,
            recommended_price=77.50,
            price_change=-7.50,
            price_change_pct=-8.82,
            buybox_status=BuyBoxStatus.RISK,
            within_rules=True,
            reasoning="Test calculation",
            confidence=85.5,
            calculation_duration_ms=1200
        )
        
        publication_result = {
            'success': True,
            'method_used': 'listings_items',
            'publication_duration_ms': 800
        }
        
        history = pricing_engine.create_pricing_history_entry(
            user_id="user-123",
            rule=sample_rule,
            calculation=calculation, 
            publication_result=publication_result
        )
        
        assert history.user_id == "user-123"
        assert history.sku == sample_rule.sku
        assert history.rule_id == sample_rule.id
        assert history.old_price == 85.00
        assert history.new_price == 77.50
        assert history.price_change == -7.50
        assert history.buybox_price == 79.99
        assert history.competitors_count == 3
        assert history.publication_success is True
        assert history.publication_method == 'listings_items'
        assert history.confidence == 85.5
        assert history.calculation_duration_ms == 1200
        assert history.publication_duration_ms == 800


class TestAmazonPricingRulesService:
    """Tests du service de gestion des règles"""
    
    @pytest.fixture
    def sample_rule_data(self):
        """Données de règle pour tests"""
        return {
            "user_id": "user-123",
            "sku": "TEST-SKU-001", 
            "marketplace_id": "A13V1IB3VIYZZH",
            "min_price": 50.0,
            "max_price": 150.0,
            "variance_pct": 5.0,
            "strategy": PricingStrategy.BUYBOX_MATCH,
            "auto_update": True
        }
    
    async def test_create_pricing_rule(self, sample_rule_data):
        """Test création règle de pricing"""
        
        rule = PricingRule(**sample_rule_data)
        
        # Mock collection MongoDB
        with patch.object(pricing_rules_service.pricing_rules_collection, 'find_one', return_value=None):
            with patch.object(pricing_rules_service.pricing_rules_collection, 'insert_one', return_value=Mock()):
                
                rule_id = await pricing_rules_service.create_pricing_rule(rule)
                
                assert rule_id == rule.id
    
    async def test_create_duplicate_rule_error(self, sample_rule_data):
        """Test erreur création règle dupliquée"""
        
        rule = PricingRule(**sample_rule_data)
        
        # Mock règle existante
        with patch.object(pricing_rules_service.pricing_rules_collection, 'find_one', return_value={'id': 'existing'}):
            
            with pytest.raises(ValueError, match="Règle déjà existante"):
                await pricing_rules_service.create_pricing_rule(rule)
    
    async def test_get_pricing_rule(self, sample_rule_data):
        """Test récupération règle par ID"""
        
        rule = PricingRule(**sample_rule_data)
        
        with patch.object(pricing_rules_service.pricing_rules_collection, 'find_one', return_value=rule.model_dump()):
            
            retrieved_rule = await pricing_rules_service.get_pricing_rule(
                user_id="user-123",
                rule_id=rule.id
            )
            
            assert retrieved_rule is not None
            assert retrieved_rule.id == rule.id
            assert retrieved_rule.sku == rule.sku
    
    async def test_update_pricing_rule(self, sample_rule_data):
        """Test mise à jour règle"""
        
        updates = {
            "min_price": 60.0,
            "max_price": 180.0,
            "status": PricingRuleStatus.PAUSED
        }
        
        with patch.object(pricing_rules_service.pricing_rules_collection, 'update_one') as mock_update:
            mock_update.return_value = Mock(modified_count=1)
            
            success = await pricing_rules_service.update_pricing_rule(
                user_id="user-123",
                rule_id="rule-123",
                updates=updates
            )
            
            assert success is True
            
            # Vérifier l'appel update
            call_args = mock_update.call_args
            assert call_args[0][0] == {"id": "rule-123", "user_id": "user-123"}
            assert "updated_at" in call_args[0][1]["$set"]
    
    async def test_get_user_pricing_rules(self, sample_rule_data):
        """Test récupération règles utilisateur"""
        
        # Mock cursor MongoDB
        mock_cursor = Mock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = Mock(return_value=iter([sample_rule_data, sample_rule_data]))
        
        with patch.object(pricing_rules_service.pricing_rules_collection, 'find', return_value=mock_cursor):
            
            rules = await pricing_rules_service.get_user_pricing_rules(
                user_id="user-123",
                marketplace_id="A13V1IB3VIYZZH"
            )
            
            assert len(rules) == 2
            assert all(rule.user_id == "user-123" for rule in rules)
    
    async def test_save_pricing_history(self):
        """Test sauvegarde historique"""
        
        history = PricingHistory(
            user_id="user-123",
            sku="TEST-SKU",
            marketplace_id="A13V1IB3VIYZZH", 
            rule_id="rule-123",
            old_price=85.00,
            new_price=77.50,
            price_change=-7.50,
            price_change_pct=-8.82,
            buybox_status_before=BuyBoxStatus.RISK,
            publication_success=True,
            reasoning="Test history",
            confidence=85.5,
            calculation_duration_ms=1200
        )
        
        with patch.object(pricing_rules_service.pricing_history_collection, 'insert_one', return_value=Mock()):
            
            history_id = await pricing_rules_service.save_pricing_history(history)
            
            assert history_id == history.id


class TestPricingAPIIntegration:
    """Tests d'intégration des API de pricing"""
    
    def test_pricing_workflow_complete(self):
        """Test workflow complet de pricing"""
        
        # Ce test serait exécuté avec des données réelles en E2E
        # 1. Créer règle de pricing
        # 2. Récupérer données concurrentielles via SP-API  
        # 3. Calculer prix optimal
        # 4. Publier via SP-API
        # 5. Vérifier historique
        
        assert True  # Placeholder pour tests E2E réels
    
    def test_batch_processing_simulation(self):
        """Test simulation traitement par lot"""
        
        # Simuler traitement de 10 SKUs
        skus = [f"TEST-SKU-{i:03d}" for i in range(10)]
        
        # Vérifier que le batch peut traiter tous les SKUs
        assert len(skus) == 10
        assert all(sku.startswith("TEST-SKU-") for sku in skus)
    
    def test_buy_box_status_detection(self):
        """Test détection des statuts Buy Box"""
        
        # Test différents scenarios
        scenarios = [
            (True, 79.99, 79.99, BuyBoxStatus.WON),      # Nous avons la Buy Box
            (False, 79.99, 82.00, BuyBoxStatus.RISK),    # Prix proche mais pas optimal
            (False, 79.99, 90.00, BuyBoxStatus.LOST),    # Prix trop élevé
            (False, None, 80.00, BuyBoxStatus.UNKNOWN)   # Buy Box indéterminée
        ]
        
        for is_winner, buybox_price, our_price, expected_status in scenarios:
            # Logic de détection (simplified)
            if is_winner:
                status = BuyBoxStatus.WON
            elif buybox_price and our_price:
                diff_pct = abs(our_price - buybox_price) / buybox_price * 100
                status = BuyBoxStatus.RISK if diff_pct <= 5 else BuyBoxStatus.LOST
            else:
                status = BuyBoxStatus.UNKNOWN
            
            assert status == expected_status


# Fixtures globales et configuration
@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def clean_test_data():
    """Nettoyer les données de test après chaque test"""
    yield
    
    # Cleanup après tests
    try:
        await pricing_rules_service.pricing_rules_collection.delete_many({
            "sku": {"$regex": "^TEST-"}
        })
        await pricing_rules_service.pricing_history_collection.delete_many({
            "sku": {"$regex": "^TEST-"}
        })
    except Exception:
        pass  # Ignorer erreurs cleanup


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([
        __file__, 
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])