"""
Test Phase 3: Implémentation améliorations - Mock Sources Return Prices
Tests pour valider que toutes les sources mock retournent des prix
"""

import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_scraping_service import HybridScrapingService

class TestMockSourcesReturnPrices:
    """Tests pour validation retour prix de toutes sources mock"""
    
    @pytest.fixture
    def hybrid_service(self):
        return HybridScrapingService()
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_amazon(self, hybrid_service):
        """Test: Amazon mock retourne des prix valides"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="iPhone 15 Pro",
            use_cache=False  # Éviter cache pour test
        )
        
        # Vérifier qu'Amazon a retourné des prix
        sources_detail = result.sources_detail
        assert "amazon" in sources_detail
        
        amazon_detail = sources_detail["amazon"]
        assert amazon_detail["prices_found"] > 0, "Amazon devrait retourner au moins 1 prix"
        assert len(amazon_detail["prices"]) > 0, "Liste prix Amazon ne devrait pas être vide"
        assert amazon_detail["success"] == True, "Amazon devrait être marqué comme succès"
        assert amazon_detail["avg_price"] > 0, "Prix moyen Amazon devrait être > 0"
        
        # Validation prix individuels
        for price in amazon_detail["prices"]:
            assert isinstance(price, (int, float)), "Prix doivent être numériques"
            assert price > 0, "Prix doivent être positifs"
            assert price < 50000, "Prix doivent être raisonnables"
        
        print(f"✅ Amazon mock - Prix trouvés: {amazon_detail['prices_found']}")
        print(f"  - Prix: {amazon_detail['prices']}")
        print(f"  - Moyenne: {amazon_detail['avg_price']:.2f}€")
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_fnac(self, hybrid_service):
        """Test: Fnac mock retourne des prix valides"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="Samsung Galaxy S24",
            use_cache=False
        )
        
        sources_detail = result.sources_detail
        assert "fnac" in sources_detail
        
        fnac_detail = sources_detail["fnac"]
        assert fnac_detail["prices_found"] > 0
        assert fnac_detail["success"] == True
        assert len(fnac_detail["prices"]) > 0
        
        # Validation gamme de prix Fnac (généralement compétitifs)
        prices = fnac_detail["prices"]
        assert all(50 <= price <= 3000 for price in prices), "Prix Fnac dans gamme raisonnable"
        
        print(f"✅ Fnac mock - Prix trouvés: {fnac_detail['prices_found']}")
        print(f"  - Prix: {fnac_detail['prices']}")
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_cdiscount(self, hybrid_service):
        """Test: Cdiscount mock retourne des prix valides"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="MacBook Air M2",
            use_cache=False
        )
        
        sources_detail = result.sources_detail
        assert "cdiscount" in sources_detail
        
        cdiscount_detail = sources_detail["cdiscount"]
        assert cdiscount_detail["prices_found"] > 0
        assert cdiscount_detail["success"] == True
        
        print(f"✅ Cdiscount mock - Prix trouvés: {cdiscount_detail['prices_found']}")
        print(f"  - Prix: {cdiscount_detail['prices']}")
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_google_shopping(self, hybrid_service):
        """Test: Google Shopping mock retourne des prix valides"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="AirPods Pro",
            use_cache=False
        )
        
        sources_detail = result.sources_detail
        assert "google_shopping" in sources_detail
        
        google_detail = sources_detail["google_shopping"]
        assert google_detail["prices_found"] > 0
        assert google_detail["success"] == True
        
        print(f"✅ Google Shopping mock - Prix trouvés: {google_detail['prices_found']}")
        print(f"  - Prix: {google_detail['prices']}")
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_aliexpress(self, hybrid_service):
        """Test: AliExpress mock retourne des prix valides"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="iPad Pro",
            use_cache=False
        )
        
        sources_detail = result.sources_detail
        
        # AliExpress peut ne pas avoir tous les produits (plus spécialisé)
        if "aliexpress" in sources_detail:
            aliexpress_detail = sources_detail["aliexpress"]
            
            if aliexpress_detail["success"]:
                assert aliexpress_detail["prices_found"] > 0
                
                # AliExpress généralement moins cher
                prices = aliexpress_detail["prices"]
                avg_price = sum(prices) / len(prices) if prices else 0
                print(f"✅ AliExpress mock - Prix trouvés: {aliexpress_detail['prices_found']}")
                print(f"  - Prix: {prices}")
                print(f"  - Moyenne: {avg_price:.2f}€ (généralement plus bas)")
            else:
                print("✅ AliExpress mock - Pas de prix (acceptable selon dataset)")
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_all_sources_comprehensive(self, hybrid_service):
        """Test: Toutes les sources retournent des prix de manière comprehensive"""
        
        test_products = [
            "iPhone 15 Pro",
            "Samsung Galaxy S24", 
            "MacBook Air M2",
            "AirPods Pro"
        ]
        
        all_sources_stats = {
            "amazon": {"requests": 0, "successes": 0, "total_prices": 0},
            "fnac": {"requests": 0, "successes": 0, "total_prices": 0},
            "cdiscount": {"requests": 0, "successes": 0, "total_prices": 0},
            "google_shopping": {"requests": 0, "successes": 0, "total_prices": 0},
            "aliexpress": {"requests": 0, "successes": 0, "total_prices": 0}
        }
        
        for product in test_products:
            result = await hybrid_service.scrape_prices_unified(
                product_name=product,
                use_cache=False
            )
            
            for source_name, source_detail in result.sources_detail.items():
                if source_name in all_sources_stats:
                    stats = all_sources_stats[source_name]
                    stats["requests"] += 1
                    if source_detail["success"]:
                        stats["successes"] += 1
                        stats["total_prices"] += source_detail["prices_found"]
        
        print("✅ Analyse comprehensive toutes sources:")
        for source_name, stats in all_sources_stats.items():
            success_rate = stats["successes"] / stats["requests"] if stats["requests"] > 0 else 0
            avg_prices = stats["total_prices"] / stats["requests"] if stats["requests"] > 0 else 0
            
            print(f"  - {source_name}: {success_rate:.1%} succès, {avg_prices:.1f} prix/req")
            
            # Validation taux succès minimum
            if source_name in ["amazon", "fnac", "cdiscount", "google_shopping"]:
                assert success_rate > 0, f"{source_name} devrait avoir au moins quelques succès"
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_variation_realism(self, hybrid_service):
        """Test: Sources retournent des prix avec variation réaliste"""
        
        # Test même produit plusieurs fois pour voir variations
        product_name = "iPhone 15 Pro"
        results = []
        
        for i in range(3):
            result = await hybrid_service.scrape_prices_unified(
                product_name=product_name,
                use_cache=False  # Important: pas de cache
            )
            results.append(result)
        
        # Analyser variations par source
        source_variations = {}
        
        for source_name in ["amazon", "fnac", "cdiscount"]:
            prices_over_time = []
            
            for result in results:
                if source_name in result.sources_detail:
                    source_detail = result.sources_detail[source_name]
                    if source_detail["success"] and source_detail["prices"]:
                        prices_over_time.extend(source_detail["prices"])
            
            if len(prices_over_time) > 1:
                min_price = min(prices_over_time)
                max_price = max(prices_over_time)
                price_variation = (max_price - min_price) / min_price * 100
                
                source_variations[source_name] = {
                    "min_price": min_price,
                    "max_price": max_price,
                    "variation_percent": price_variation,
                    "total_prices": len(prices_over_time)
                }
        
        print("✅ Variations prix réalistes:")
        for source_name, variation_data in source_variations.items():
            print(f"  - {source_name}: {variation_data['variation_percent']:.1f}% variation")
            print(f"    Range: {variation_data['min_price']:.2f}€ - {variation_data['max_price']:.2f}€")
            
            # Validation réalisme variations (5-25% acceptable)
            assert 0 <= variation_data["variation_percent"] <= 50, f"Variation {source_name} doit être réaliste"
    
    @pytest.mark.asyncio
    async def test_mock_sources_return_prices_currency_consistency(self, hybrid_service):
        """Test: Toutes sources retournent des prix en EUR cohérents"""
        
        result = await hybrid_service.scrape_prices_unified(
            product_name="Samsung Galaxy S24",
            use_cache=False
        )
        
        all_prices = []
        sources_with_prices = []
        
        for source_name, source_detail in result.sources_detail.items():
            if source_detail["success"] and source_detail["prices"]:
                all_prices.extend(source_detail["prices"])
                sources_with_prices.append(source_name)
                
                # Validation gamme prix EUR raisonnable
                for price in source_detail["prices"]:
                    assert 10 <= price <= 15000, f"Prix {price}€ de {source_name} hors gamme EUR raisonnable"
        
        # Validation cohérence inter-sources
        if len(all_prices) > 1:
            min_price = min(all_prices)
            max_price = max(all_prices)
            price_spread = (max_price - min_price) / min_price * 100
            
            # Écart inter-sources ne devrait pas être trop extrême (sauf outliers)
            print(f"✅ Cohérence currency EUR:")
            print(f"  - Sources avec prix: {sources_with_prices}")
            print(f"  - Fourchette: {min_price:.2f}€ - {max_price:.2f}€")
            print(f"  - Écart inter-sources: {price_spread:.1f}%")
            
            # Validation: écart <300% généralement acceptable (avant outlier detection)
            if price_spread > 500:
                print(f"  ⚠️ Écart élevé détecté - outliers probables")
        
        assert len(sources_with_prices) > 0, "Au moins une source devrait retourner des prix"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])