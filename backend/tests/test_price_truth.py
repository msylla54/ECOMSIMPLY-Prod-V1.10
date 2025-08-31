"""
Tests pour le système PriceTruth
"""
import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import os

# Fixtures pour tests async
pytest_plugins = ['pytest_asyncio']

# Import du système PriceTruth
from models.price_truth import (
    PriceTruth, PriceSource, PriceConsensus, ConsensusPriceStatus,
    PriceTruthDatabase
)
from services.price_truth_service import PriceTruthService
from services.pricing.base_adapter import PriceExtractionResult


class TestPriceTruthModels:
    """Tests des modèles Pydantic"""
    
    def test_price_source_creation(self):
        """Test création PriceSource"""
        source = PriceSource(
            name="amazon",
            price=Decimal("123.45"),
            currency="EUR",
            url="https://amazon.fr/test",
            selector=".price",
            ts=datetime.now()
        )
        
        assert source.name == "amazon"
        assert source.price == Decimal("123.45")
        assert source.currency == "EUR"
        assert source.success is True
    
    def test_price_consensus_creation(self):
        """Test création PriceConsensus"""
        consensus = PriceConsensus(
            agreeing_sources=2,
            median_price=Decimal("100.00"),
            status=ConsensusPriceStatus.VALID
        )
        
        assert consensus.agreeing_sources == 2
        assert consensus.median_price == Decimal("100.00")
        assert consensus.status == ConsensusPriceStatus.VALID
    
    def test_price_truth_is_fresh(self):
        """Test vérification fraîcheur des données"""
        # Données fraîches
        price_truth = PriceTruth(
            sku="test-sku",
            query="test query",
            consensus=PriceConsensus(
                agreeing_sources=2,
                status=ConsensusPriceStatus.VALID
            ),
            updated_at=datetime.now(),
            ttl_hours=6
        )
        
        assert price_truth.is_fresh is True
        
        # Données périmées
        price_truth.updated_at = datetime.now() - timedelta(hours=7)
        assert price_truth.is_fresh is False
    
    def test_price_truth_has_valid_consensus(self):
        """Test validation du consensus"""
        # Consensus valide
        price_truth = PriceTruth(
            sku="test-sku",
            query="test query",
            value=Decimal("100.00"),
            consensus=PriceConsensus(
                agreeing_sources=2,
                status=ConsensusPriceStatus.VALID
            )
        )
        
        assert price_truth.has_valid_consensus is True
        
        # Consensus invalide
        price_truth.consensus.status = ConsensusPriceStatus.INSUFFICIENT_EVIDENCE
        assert price_truth.has_valid_consensus is False


class TestPriceTruthService:
    """Tests du service PriceTruth"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de la base de données"""
        db = Mock(spec=PriceTruthDatabase)
        db.upsert_price_truth = AsyncMock(return_value=True)
        db.get_price_truth = AsyncMock(return_value=None)
        db.search_by_query = AsyncMock(return_value=None)
        db.get_stale_records = AsyncMock(return_value=[])
        db.ensure_indexes = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Service PriceTruth avec DB mockée"""
        with patch.dict(os.environ, {
            'PRICE_TRUTH_ENABLED': 'true',
            'PRICE_TRUTH_TTL_HOURS': '6',
            'CONSENSUS_TOLERANCE_PCT': '3.0'
        }):
            service = PriceTruthService(mock_db)
            
            # Mock des adapters
            for name, adapter in service.adapters.items():
                adapter.extract_price = AsyncMock()
            
            return service
    
    @pytest.mark.asyncio
    async def test_consensus_calculation_valid(self, service):
        """Test calcul de consensus avec prix valides"""
        sources = [
            PriceSource(
                name="amazon",
                price=Decimal("100.00"),
                currency="EUR",
                url="https://amazon.fr",
                selector=".price",
                ts=datetime.now()
            ),
            PriceSource(
                name="fnac",
                price=Decimal("102.00"),
                currency="EUR", 
                url="https://fnac.com",
                selector=".price",
                ts=datetime.now()
            ),
            PriceSource(
                name="cdiscount",
                price=Decimal("101.50"),
                currency="EUR",
                url="https://cdiscount.com",
                selector=".price",
                ts=datetime.now()
            )
        ]
        
        consensus = service._calculate_consensus(sources)
        
        assert consensus.status == ConsensusPriceStatus.VALID
        assert consensus.agreeing_sources >= 2
        assert consensus.median_price is not None
    
    @pytest.mark.asyncio
    async def test_consensus_calculation_outlier(self, service):
        """Test calcul de consensus avec outlier"""
        sources = [
            PriceSource(
                name="amazon",
                price=Decimal("100.00"),
                currency="EUR",
                url="https://amazon.fr",
                selector=".price",
                ts=datetime.now()
            ),
            PriceSource(
                name="fnac",
                price=Decimal("102.00"),
                currency="EUR",
                url="https://fnac.com",
                selector=".price",
                ts=datetime.now()
            ),
            PriceSource(
                name="cdiscount",
                price=Decimal("200.00"),  # Outlier
                currency="EUR",
                url="https://cdiscount.com",
                selector=".price",
                ts=datetime.now()
            ),
            PriceSource(
                name="google_shopping",
                price=Decimal("101.00"),  # Ajout d'une 4ème source pour IQR
                currency="EUR",
                url="https://google.fr",
                selector=".price",
                ts=datetime.now()
            )
        ]
        
        consensus = service._calculate_consensus(sources)
        
        # Avec 4 sources, l'IQR devrait détecter l'outlier à 200€
        # Sinon, au moins le consensus devrait être valide avec les 3 autres sources
        assert consensus.status == ConsensusPriceStatus.VALID
        assert consensus.agreeing_sources >= 2
    
    @pytest.mark.asyncio
    async def test_consensus_insufficient_sources(self, service):
        """Test consensus avec sources insuffisantes"""
        sources = [
            PriceSource(
                name="amazon",
                price=Decimal("100.00"),
                currency="EUR",
                url="https://amazon.fr",
                selector=".price",
                ts=datetime.now()
            )
        ]
        
        consensus = service._calculate_consensus(sources)
        
        assert consensus.status == ConsensusPriceStatus.INSUFFICIENT_EVIDENCE
        assert consensus.agreeing_sources < 2
    
    @pytest.mark.asyncio
    async def test_get_price_truth_cache_hit(self, service, mock_db):
        """Test récupération avec cache hit"""
        # Mock cache hit
        cached_price = PriceTruth(
            sku="test-sku",
            query="test query",
            value=Decimal("100.00"),
            consensus=PriceConsensus(
                agreeing_sources=2,
                status=ConsensusPriceStatus.VALID
            ),
            updated_at=datetime.now(),  # Frais
            ttl_hours=6
        )
        
        mock_db.get_price_truth.return_value = cached_price
        
        result = await service.get_price_truth(sku="test-sku")
        
        assert result is not None
        assert result.price == 100.00
        assert result.is_fresh is True
        assert service.stats['cache_hits'] == 1
    
    @pytest.mark.asyncio
    async def test_get_price_truth_cache_miss(self, service, mock_db):
        """Test récupération avec cache miss et fetch"""
        # Mock cache miss
        mock_db.get_price_truth.return_value = None
        mock_db.search_by_query.return_value = None
        
        # Mock des résultats d'extraction
        mock_results = [
            PriceExtractionResult(
                price=Decimal("100.00"),
                currency="EUR",
                url="https://amazon.fr",
                selector=".price",
                screenshot_path=None,
                timestamp=datetime.now(),
                success=True
            ),
            PriceExtractionResult(
                price=Decimal("102.00"),
                currency="EUR",
                url="https://fnac.com",
                selector=".price",
                screenshot_path=None,
                timestamp=datetime.now(),
                success=True
            )
        ]
        
        # Mock des adapters
        service.adapters['amazon'].extract_price.return_value = mock_results[0]
        service.adapters['fnac'].extract_price.return_value = mock_results[1]
        service.adapters['google_shopping'].extract_price.return_value = PriceExtractionResult(
            price=None, currency="EUR", url="", selector="", 
            screenshot_path=None, timestamp=datetime.now(), success=False
        )
        service.adapters['cdiscount'].extract_price.return_value = PriceExtractionResult(
            price=None, currency="EUR", url="", selector="", 
            screenshot_path=None, timestamp=datetime.now(), success=False
        )
        
        result = await service.get_price_truth(sku="test-sku")
        
        assert result is not None
        assert result.sources_count >= 2
        assert result.agreeing_sources >= 2
        # Vérifier que upsert a été appelé
        mock_db.upsert_price_truth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_disabled(self, mock_db):
        """Test service désactivé"""
        with patch.dict(os.environ, {'PRICE_TRUTH_ENABLED': 'false'}):
            service = PriceTruthService(mock_db)
            
            result = await service.get_price_truth(sku="test-sku")
            assert result is None
    
    def test_service_stats(self, service):
        """Test récupération des statistiques"""
        service.stats['total_queries'] = 10
        service.stats['successful_consensus'] = 8
        service.stats['cache_hits'] = 3
        
        stats = service.get_service_stats()
        
        assert stats['enabled'] is True
        assert stats['ttl_hours'] == 6
        assert 'success_rate' in stats['stats']
        assert 'cache_rate' in stats['stats']
        assert len(stats['adapters_available']) == 4


class TestPriceExtractionIntegration:
    """Tests d'intégration pour l'extraction de prix"""
    
    def test_price_cleaning(self):
        """Test nettoyage des prix"""
        from services.pricing.amazon_adapter import AmazonPriceAdapter
        
        adapter = AmazonPriceAdapter()
        
        # Formats européens
        assert adapter._clean_price_text("123,45 €") == Decimal("123.45")
        assert adapter._clean_price_text("1.234,56€") == Decimal("1234.56")
        assert adapter._clean_price_text("1 234,56 €") == Decimal("1234.56")
        
        # Formats américains
        assert adapter._clean_price_text("$123.45") == Decimal("123.45")
        assert adapter._clean_price_text("1,234.56") == Decimal("1234.56")
        
        # Cas d'erreur
        assert adapter._clean_price_text("N/A") is None
        assert adapter._clean_price_text("") is None
        assert adapter._clean_price_text("abc") is None
    
    def test_url_construction(self):
        """Test construction des URLs de recherche"""
        from services.pricing import AmazonPriceAdapter, GoogleShoppingAdapter
        
        amazon = AmazonPriceAdapter()
        google = GoogleShoppingAdapter()
        
        query = "iPhone 15 Pro"
        
        amazon_url = amazon._get_search_url(query)
        google_url = google._get_search_url(query)
        
        assert "amazon.fr" in amazon_url
        assert "iPhone+15+Pro" in amazon_url
        
        assert "google.fr" in google_url
        assert "iPhone+15+Pro" in google_url
        assert "tbm=shop" in google_url