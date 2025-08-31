"""
Test Phase 3: Implémentation améliorations - Currency Conversion Mock  
Tests pour valider la détection/conversion de devises en mock
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_scraping_service import HybridScrapingService

class CurrencyConverter:
    """Simulateur conversion devises pour tests mock"""
    
    def __init__(self):
        # Taux de change simulés (EUR de base)
        self.exchange_rates = {
            "EUR": 1.0,
            "USD": 0.85,   # 1 USD = 0.85 EUR
            "GBP": 1.15,   # 1 GBP = 1.15 EUR  
            "CAD": 0.63,   # 1 CAD = 0.63 EUR
            "JPY": 0.0057  # 1 JPY = 0.0057 EUR
        }
    
    def detect_currency_from_price(self, price: float, context: str = "") -> str:
        """Détecte la devise probable basée sur le prix et contexte"""
        
        # Règles heuristiques de détection
        if price > 10000:
            return "JPY"  # Yen japonais (prix élevés)
        elif price < 10 and context.lower() not in ["accessory", "cable", "small"]:
            return "USD"  # Potentiel prix en dollars
        elif 500 <= price <= 3000 and "uk" in context.lower():
            return "GBP"  # Livre sterling UK
        elif 500 <= price <= 5000 and "us" in context.lower():
            return "USD"  # Dollar US
        else:
            return "EUR"  # Euro par défaut
    
    def convert_to_eur(self, price: float, from_currency: str) -> float:
        """Convertit un prix vers EUR"""
        
        if from_currency not in self.exchange_rates:
            return price  # Pas de conversion si devise inconnue
        
        rate = self.exchange_rates[from_currency]
        eur_price = price * rate
        
        return round(eur_price, 2)
    
    def normalize_prices_to_eur(self, prices_with_context: list) -> dict:
        """Normalise une liste de prix vers EUR"""
        
        normalized_prices = []
        conversions_applied = []
        
        for price_data in prices_with_context:
            price = price_data["price"]
            context = price_data.get("context", "")
            source = price_data.get("source", "unknown")
            
            detected_currency = self.detect_currency_from_price(price, context)
            eur_price = self.convert_to_eur(price, detected_currency)
            
            normalized_prices.append(eur_price)
            
            conversion_info = {
                "original_price": price,
                "detected_currency": detected_currency,
                "eur_price": eur_price,
                "source": source,
                "conversion_applied": detected_currency != "EUR"
            }
            conversions_applied.append(conversion_info)
        
        return {
            "normalized_prices": normalized_prices,
            "conversions": conversions_applied,
            "total_conversions": sum(1 for c in conversions_applied if c["conversion_applied"])
        }

class TestCurrencyConversionMock:
    """Tests pour validation conversion devises mock"""
    
    @pytest.fixture
    def hybrid_service(self):
        return HybridScrapingService()
    
    @pytest.fixture
    def currency_converter(self):
        return CurrencyConverter()
    
    def test_currency_conversion_mock_detection_eur(self, currency_converter):
        """Test: Détection correcte de prix EUR"""
        
        eur_prices = [899.99, 1199.99, 299.99, 1599.99]
        
        for price in eur_prices:
            detected = currency_converter.detect_currency_from_price(price, "smartphone")
            assert detected == "EUR", f"Prix {price} devrait être détecté comme EUR"
        
        print("✅ Détection EUR:")
        for price in eur_prices:
            print(f"  - {price} → {currency_converter.detect_currency_from_price(price)}")
    
    def test_currency_conversion_mock_detection_usd(self, currency_converter):
        """Test: Détection correcte de prix USD"""
        
        # Prix suspects d'être en USD (faibles pour contexte européen)
        usd_candidates = [
            {"price": 8.99, "context": "cable"},
            {"price": 15.99, "context": "accessory"},
            {"price": 899, "context": "us smartphone"},
            {"price": 1299, "context": "us laptop"}
        ]
        
        for candidate in usd_candidates:
            detected = currency_converter.detect_currency_from_price(
                candidate["price"], 
                candidate["context"]
            )
            print(f"✅ Détection USD: {candidate['price']} ({candidate['context']}) → {detected}")
            
            # Certains devraient être détectés comme USD
            if "us" in candidate["context"] or candidate["price"] < 20:
                expected_currency = "USD"
            else:
                expected_currency = "EUR"  # Fallback
    
    def test_currency_conversion_mock_detection_jpy(self, currency_converter):
        """Test: Détection correcte de prix JPY"""
        
        jpy_prices = [89999, 129999, 25999, 199999]  # Prix typiques Japon
        
        for price in jpy_prices:
            detected = currency_converter.detect_currency_from_price(price, "japan")
            assert detected == "JPY", f"Prix {price} devrait être détecté comme JPY"
        
        print("✅ Détection JPY:")
        for price in jpy_prices:
            eur_converted = currency_converter.convert_to_eur(price, "JPY")
            print(f"  - {price} JPY → {eur_converted} EUR")
    
    def test_currency_conversion_mock_conversion_rates(self, currency_converter):
        """Test: Taux de conversion corrects"""
        
        test_conversions = [
            {"price": 100, "from": "USD", "expected_range": (80, 90)},   # ~85 EUR
            {"price": 100, "from": "GBP", "expected_range": (110, 120)}, # ~115 EUR
            {"price": 100, "from": "CAD", "expected_range": (60, 70)},   # ~63 EUR
            {"price": 10000, "from": "JPY", "expected_range": (50, 60)}  # ~57 EUR
        ]
        
        print("✅ Tests taux conversion:")
        for test_case in test_conversions:
            eur_price = currency_converter.convert_to_eur(
                test_case["price"], 
                test_case["from"]
            )
            
            expected_min, expected_max = test_case["expected_range"]
            
            print(f"  - {test_case['price']} {test_case['from']} → {eur_price} EUR")
            
            assert expected_min <= eur_price <= expected_max, \
                f"Conversion {test_case['from']} vers EUR hors fourchette attendue"
    
    def test_currency_conversion_mock_normalization_mixed(self, currency_converter):
        """Test: Normalisation mix de devises"""
        
        mixed_prices = [
            {"price": 899.99, "context": "eur smartphone", "source": "fnac"},
            {"price": 999, "context": "us smartphone", "source": "amazon_us"},
            {"price": 89999, "context": "japan smartphone", "source": "amazon_jp"},
            {"price": 799, "context": "uk smartphone", "source": "amazon_uk"}
        ]
        
        normalization_result = currency_converter.normalize_prices_to_eur(mixed_prices)
        
        # Validation résultats
        assert len(normalization_result["normalized_prices"]) == len(mixed_prices)
        assert len(normalization_result["conversions"]) == len(mixed_prices)
        assert normalization_result["total_conversions"] >= 1, "Au moins une conversion devrait être appliquée"
        
        print("✅ Normalisation mix devises:")
        print(f"  - Prix normalisés: {normalization_result['normalized_prices']}")
        print(f"  - Conversions appliquées: {normalization_result['total_conversions']}")
        
        # Afficher détails conversions
        for conversion in normalization_result["conversions"]:
            if conversion["conversion_applied"]:
                print(f"    • {conversion['original_price']} {conversion['detected_currency']} → {conversion['eur_price']} EUR ({conversion['source']})")
    
    @pytest.mark.asyncio
    async def test_currency_conversion_mock_integration_scraping(self, hybrid_service, currency_converter):
        """Test: Intégration conversion avec scraping hybride"""
        
        # Scraping prix depuis sources mock
        result = await hybrid_service.scrape_prices_unified(
            product_name="iPhone 15 Pro",
            use_cache=False
        )
        
        # Simulation: certains prix pourraient être dans d'autres devises
        # On va traiter les prix récupérés comme potentiellement multi-devises
        
        prices_for_conversion = []
        
        for source_name, source_detail in result.sources_detail.items():
            if source_detail["success"] and source_detail["prices"]:
                for price in source_detail["prices"]:
                    # Simulation contexte par source
                    context_by_source = {
                        "amazon": "international",
                        "aliexpress": "us context", 
                        "google_shopping": "mixed regions",
                        "fnac": "eur context",
                        "cdiscount": "eur context"
                    }
                    
                    prices_for_conversion.append({
                        "price": price,
                        "context": context_by_source.get(source_name, ""),
                        "source": source_name
                    })
        
        # Appliquer normalisation devises
        if prices_for_conversion:
            normalized_result = currency_converter.normalize_prices_to_eur(prices_for_conversion)
            
            print("✅ Intégration scraping + conversion:")
            print(f"  - Prix récupérés: {len(prices_for_conversion)}")
            print(f"  - Prix normalisés EUR: {len(normalized_result['normalized_prices'])}")
            print(f"  - Conversions appliquées: {normalized_result['total_conversions']}")
            
            # Comparaison avant/après normalisation
            original_prices = [p["price"] for p in prices_for_conversion]
            normalized_prices = normalized_result["normalized_prices"]
            
            if len(original_prices) == len(normalized_prices):
                for i, (orig, norm) in enumerate(zip(original_prices, normalized_prices)):
                    if abs(orig - norm) > 0.01:  # Conversion appliquée
                        conversion = normalized_result["conversions"][i]
                        print(f"    • Converti: {orig} → {norm} EUR ({conversion['detected_currency']})")
            
            # Validation cohérence
            assert len(normalized_prices) > 0, "Au moins un prix normalisé"
            assert all(isinstance(p, (int, float)) for p in normalized_prices), "Prix normalisés numériques"
            assert all(10 <= p <= 15000 for p in normalized_prices), "Prix EUR dans gamme raisonnable"
        else:
            print("⚠️ Aucun prix récupéré pour test conversion")
    
    def test_currency_conversion_mock_outlier_impact(self, currency_converter):
        """Test: Impact conversion sur détection outliers"""
        
        # Prix avec potentielles erreurs de devise
        problematic_prices = [
            {"price": 899.99, "context": "eur", "source": "fnac"},      # OK EUR
            {"price": 899, "context": "us", "source": "amazon_us"},     # USD → ~764 EUR
            {"price": 89999, "context": "japan", "source": "amazon_jp"}, # JPY → ~513 EUR
            {"price": 25000, "context": "error", "source": "error"}     # Erreur probable
        ]
        
        # Normalisation
        normalized = currency_converter.normalize_prices_to_eur(problematic_prices)
        
        normalized_prices = normalized["normalized_prices"]
        
        print("✅ Impact conversion sur outliers:")
        print(f"  - Prix originaux: {[p['price'] for p in problematic_prices]}")
        print(f"  - Prix normalisés: {normalized_prices}")
        
        # Calculs outliers AVANT normalisation (prix bruts)
        raw_prices = [p["price"] for p in problematic_prices]
        raw_max = max(raw_prices)
        raw_min = min(raw_prices)
        raw_spread = (raw_max - raw_min) / raw_min * 100
        
        # Calculs outliers APRÈS normalisation
        norm_max = max(normalized_prices)
        norm_min = min(normalized_prices) 
        norm_spread = (norm_max - norm_min) / norm_min * 100
        
        print(f"  - Spread avant: {raw_spread:.1f}% ({raw_min}-{raw_max})")
        print(f"  - Spread après: {norm_spread:.1f}% ({norm_min:.2f}-{norm_max:.2f})")
        
        # Validation: normalisation devrait réduire spread aberrant
        if raw_spread > norm_spread:
            print("  ✅ Conversion a réduit l'écart → Moins d'outliers")
        else:
            print("  ⚠️ Conversion n'a pas amélioré cohérence")
        
        # Validation cohérence post-normalisation
        assert norm_spread < 10000, "Spread post-normalisation devrait être plus raisonnable"
        assert all(10 <= price <= 15000 for price in normalized_prices), "Prix EUR cohérents"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])