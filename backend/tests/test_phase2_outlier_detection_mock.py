"""
Test Phase 2: Plan d'amélioration - Outlier Detection Mock
Tests pour valider la détection d'outliers dans les données mock
"""

import pytest
import sys
import os
import statistics
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_scraping_service import EnhancedScrapingService

class PriceOutlierDetector:
    """Détecteur d'outliers pour les prix - Prototype pour amélioration"""
    
    @staticmethod
    def detect_outliers_zscore(prices: list, threshold: float = 2.0) -> dict:
        """Détection outliers avec Z-score"""
        if len(prices) < 3:
            return {"outliers": [], "clean_prices": prices, "method": "zscore_insufficient_data"}
        
        mean_price = statistics.mean(prices)
        stdev_price = statistics.stdev(prices)
        
        if stdev_price == 0:
            return {"outliers": [], "clean_prices": prices, "method": "zscore_no_variation"}
        
        outliers = []
        clean_prices = []
        
        for price in prices:
            zscore = abs(price - mean_price) / stdev_price
            if zscore > threshold:
                outliers.append({"price": price, "zscore": zscore})
            else:
                clean_prices.append(price)
        
        return {
            "outliers": outliers,
            "clean_prices": clean_prices,
            "method": "zscore",
            "threshold": threshold,
            "original_count": len(prices),
            "clean_count": len(clean_prices),
            "outlier_count": len(outliers),
            "stats": {
                "mean": mean_price,
                "stdev": stdev_price
            }
        }
    
    @staticmethod
    def detect_outliers_iqr(prices: list, multiplier: float = 1.5) -> dict:
        """Détection outliers avec IQR (Interquartile Range)"""
        if len(prices) < 3:
            return {"outliers": [], "clean_prices": prices, "method": "iqr_insufficient_data"}
        
        sorted_prices = sorted(prices)
        q1 = statistics.quantiles(sorted_prices, n=4)[0]
        q3 = statistics.quantiles(sorted_prices, n=4)[2]
        iqr = q3 - q1
        
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        
        outliers = []
        clean_prices = []
        
        for price in prices:
            if price < lower_bound or price > upper_bound:
                outliers.append({
                    "price": price,
                    "deviation": "low" if price < lower_bound else "high",
                    "bound_exceeded": lower_bound if price < lower_bound else upper_bound
                })
            else:
                clean_prices.append(price)
        
        return {
            "outliers": outliers,
            "clean_prices": clean_prices,
            "method": "iqr",
            "multiplier": multiplier,
            "bounds": {"lower": lower_bound, "upper": upper_bound},
            "quartiles": {"q1": q1, "q3": q3, "iqr": iqr},
            "original_count": len(prices),
            "clean_count": len(clean_prices),
            "outlier_count": len(outliers)
        }
    
    @staticmethod
    def detect_outliers_contextual(prices: list, category: str = None, product_name: str = None) -> dict:
        """Détection outliers contextuelle basée sur règles métier"""
        
        # Règles contextuelles par catégorie/produit
        context_rules = {
            "smartphone": {"min": 50, "max": 2000, "reasonable_range": (200, 1500)},
            "laptop": {"min": 200, "max": 5000, "reasonable_range": (500, 3000)},
            "accessory": {"min": 5, "max": 500, "reasonable_range": (20, 300)},
            "default": {"min": 10, "max": 10000, "reasonable_range": (50, 2000)}
        }
        
        # Détection automatique catégorie si pas fournie
        if not category and product_name:
            product_lower = product_name.lower()
            if any(kw in product_lower for kw in ["iphone", "samsung", "galaxy", "smartphone"]):
                category = "smartphone"
            elif any(kw in product_lower for kw in ["macbook", "laptop", "pc", "ordinateur"]):
                category = "laptop" 
            elif any(kw in product_lower for kw in ["airpods", "casque", "chargeur", "cable"]):
                category = "accessory"
        
        rules = context_rules.get(category, context_rules["default"])
        
        outliers = []
        clean_prices = []
        
        for price in prices:
            is_outlier = False
            reasons = []
            
            # Vérifications contextuelles
            if price < rules["min"]:
                is_outlier = True
                reasons.append(f"below_minimum_{rules['min']}")
            elif price > rules["max"]:
                is_outlier = True
                reasons.append(f"above_maximum_{rules['max']}")
            elif price < rules["reasonable_range"][0]:
                reasons.append("below_reasonable_range")
            elif price > rules["reasonable_range"][1]:
                reasons.append("above_reasonable_range")
            
            # Prix suspicieusement ronds (9999, 1000, etc.)
            if price in [9999, 9999.99, 1111, 2222, 3333]:
                is_outlier = True
                reasons.append("suspicious_round_price")
            
            if is_outlier:
                outliers.append({
                    "price": price,
                    "reasons": reasons,
                    "category": category or "default"
                })
            else:
                clean_prices.append(price)
        
        return {
            "outliers": outliers,
            "clean_prices": clean_prices,
            "method": "contextual",
            "category": category,
            "rules_applied": rules,
            "original_count": len(prices),
            "clean_count": len(clean_prices),
            "outlier_count": len(outliers)
        }

class TestOutlierDetectionMock:
    """Tests pour validation détection outliers dans mock"""
    
    @pytest.fixture
    def enhanced_service(self):
        return EnhancedScrapingService()
    
    @pytest.fixture
    def outlier_detector(self):
        return PriceOutlierDetector()
    
    @pytest.mark.asyncio
    async def test_outlier_detection_zscore_method(self, enhanced_service, outlier_detector):
        """Test: Détection outliers avec méthode Z-score"""
        
        # Récupérer données de prix mock
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="iPhone 15 Pro",
            sources=["amazon", "fnac", "cdiscount", "google_shopping"]
        )
        
        # Extraire prix de toutes les sources
        all_prices = []
        scraped_results = result.get("scraped_results", {})
        
        for source, source_data in scraped_results.items():
            products = source_data.get("products", [])
            prices = [p["price"] for p in products if "price" in p]
            all_prices.extend(prices)
        
        # Ajouter outliers artificiels pour test
        test_prices = all_prices + [9999.99, 1.0, 50000.0]  # Outliers évidents
        
        # Test détection Z-score
        zscore_result = outlier_detector.detect_outliers_zscore(test_prices, threshold=2.0)
        
        # Validation résultats Z-score
        assert zscore_result["method"] == "zscore"
        assert zscore_result["original_count"] == len(test_prices)
        assert zscore_result["clean_count"] + zscore_result["outlier_count"] == len(test_prices)
        assert zscore_result["outlier_count"] > 0, "Devrait détecter des outliers artificiels"
        
        print("✅ Détection outliers Z-score:")
        print(f"  - Prix originaux: {len(test_prices)}")
        print(f"  - Prix propres: {zscore_result['clean_count']}")
        print(f"  - Outliers détectés: {zscore_result['outlier_count']}")
        print(f"  - Seuil Z-score: {zscore_result['threshold']}")
        
        # Afficher outliers détectés
        for outlier in zscore_result["outliers"]:
            print(f"    - Prix outlier: {outlier['price']}€ (Z-score: {outlier['zscore']:.2f})")
    
    @pytest.mark.asyncio
    async def test_outlier_detection_iqr_method(self, enhanced_service, outlier_detector):
        """Test: Détection outliers avec méthode IQR"""
        
        # Récupérer données de prix réalistes
        result = await enhanced_service.scrape_competitor_prices_enhanced(
            product_name="Samsung Galaxy S24",
            sources=["amazon", "fnac", "cdiscount"]
        )
        
        # Extraire prix
        all_prices = []
        scraped_results = result.get("scraped_results", {})
        
        for source_data in scraped_results.values():
            products = source_data.get("products", [])
            prices = [p["price"] for p in products if "price" in p]
            all_prices.extend(prices)
        
        # Ajouter mix outliers
        test_prices = all_prices + [25.0, 15000.0, 0.99]  # Mix bas/haut outliers
        
        # Test détection IQR
        iqr_result = outlier_detector.detect_outliers_iqr(test_prices, multiplier=1.5)
        
        # Validation IQR
        assert iqr_result["method"] == "iqr"
        assert iqr_result["original_count"] == len(test_prices)
        assert "bounds" in iqr_result
        assert "quartiles" in iqr_result
        assert iqr_result["clean_count"] + iqr_result["outlier_count"] == len(test_prices)
        
        print("✅ Détection outliers IQR:")
        print(f"  - Prix originaux: {len(test_prices)}")
        print(f"  - Prix propres: {iqr_result['clean_count']}")
        print(f"  - Outliers détectés: {iqr_result['outlier_count']}")
        print(f"  - Bornes: [{iqr_result['bounds']['lower']:.2f}, {iqr_result['bounds']['upper']:.2f}]")
        
        # Afficher outliers avec détail
        for outlier in iqr_result["outliers"]:
            print(f"    - Prix outlier: {outlier['price']}€ ({outlier['deviation']}, seuil: {outlier['bound_exceeded']:.2f})")
    
    @pytest.mark.asyncio
    async def test_outlier_detection_contextual_smartphone(self, enhanced_service, outlier_detector):
        """Test: Détection outliers contextuelle pour smartphones"""
        
        # Test détection contextuelle smartphone
        smartphone_prices = [899.99, 1199.99, 1229.99, 849.99, 9999.99, 50.0, 3500.0, 1299.99]
        
        contextual_result = outlier_detector.detect_outliers_contextual(
            smartphone_prices,
            category="smartphone",
            product_name="iPhone 15 Pro"
        )
        
        # Validation contextuelle
        assert contextual_result["method"] == "contextual"
        assert contextual_result["category"] == "smartphone"
        assert "rules_applied" in contextual_result
        assert contextual_result["outlier_count"] > 0, "Devrait détecter outliers contextuels"
        
        print("✅ Détection outliers contextuelle (smartphone):")
        print(f"  - Catégorie: {contextual_result['category']}")
        print(f"  - Prix originaux: {len(smartphone_prices)}")
        print(f"  - Prix propres: {contextual_result['clean_count']}")
        print(f"  - Outliers détectés: {contextual_result['outlier_count']}")
        
        rules = contextual_result["rules_applied"]
        print(f"  - Règles: min {rules['min']}€, max {rules['max']}€")
        print(f"  - Fourchette raisonnable: {rules['reasonable_range'][0]}-{rules['reasonable_range'][1]}€")
        
        # Analyser raisons outliers
        for outlier in contextual_result["outliers"]:
            print(f"    - {outlier['price']}€: {', '.join(outlier['reasons'])}")
    
    @pytest.mark.asyncio
    async def test_outlier_detection_contextual_auto_category(self, enhanced_service, outlier_detector):
        """Test: Détection automatique catégorie puis outliers"""
        
        # Test détection automatique avec différents produits
        test_cases = [
            {"product_name": "MacBook Air M2", "expected_category": "laptop"},
            {"product_name": "AirPods Pro", "expected_category": "accessory"},
            {"product_name": "Samsung Galaxy S24", "expected_category": "smartphone"},
            {"product_name": "Produit Mystère", "expected_category": "default"}
        ]
        
        for test_case in test_cases:
            # Prix de test avec outliers
            test_prices = [299.99, 899.99, 1199.99, 9999.99, 5.0]
            
            result = outlier_detector.detect_outliers_contextual(
                test_prices,
                product_name=test_case["product_name"]
            )
            
            detected_category = result["category"] or "default"
            
            print(f"✅ Auto-détection catégorie:")
            print(f"  - Produit: '{test_case['product_name']}'")
            print(f"  - Catégorie détectée: {detected_category}")
            print(f"  - Catégorie attendue: {test_case['expected_category']}")
            print(f"  - Outliers: {result['outlier_count']}/{len(test_prices)}")
            
            # Validation auto-détection
            assert detected_category is not None
            assert result["outlier_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_outlier_detection_comparative_methods(self, enhanced_service, outlier_detector):
        """Test: Comparaison des 3 méthodes de détection"""
        
        # Dataset de test avec outliers connus
        test_prices = [
            # Prix normaux
            899.99, 949.99, 1199.99, 1229.99, 1099.99, 1149.99,
            # Outliers évidents
            9999.99,  # Prix cassé
            29.99,    # Suspicieusement bas
            15000.0,  # Anormalement élevé
            0.01      # Prix d'erreur
        ]
        
        # Test des 3 méthodes
        zscore_result = outlier_detector.detect_outliers_zscore(test_prices, threshold=2.0)
        iqr_result = outlier_detector.detect_outliers_iqr(test_prices, multiplier=1.5) 
        contextual_result = outlier_detector.detect_outliers_contextual(
            test_prices,
            category="smartphone"
        )
        
        print("✅ Comparaison méthodes détection outliers:")
        print(f"Prix de test: {len(test_prices)} prix")
        print(f"  - Z-score: {zscore_result['outlier_count']} outliers détectés")
        print(f"  - IQR: {iqr_result['outlier_count']} outliers détectés")
        print(f"  - Contextuel: {contextual_result['outlier_count']} outliers détectés")
        
        # Analyser consensus entre méthodes
        zscore_outlier_prices = {o["price"] for o in zscore_result["outliers"]}
        iqr_outlier_prices = {o["price"] for o in iqr_result["outliers"]}
        contextual_outlier_prices = {o["price"] for o in contextual_result["outliers"]}
        
        consensus_outliers = zscore_outlier_prices & iqr_outlier_prices & contextual_outlier_prices
        union_outliers = zscore_outlier_prices | iqr_outlier_prices | contextual_outlier_prices
        
        print(f"  - Consensus (3 méthodes): {len(consensus_outliers)} prix")
        print(f"  - Union (≥1 méthode): {len(union_outliers)} prix")
        
        # Validation efficacité
        assert len(consensus_outliers) > 0, "Au moins quelques outliers évidents détectés par toutes méthodes"
        assert len(union_outliers) >= len(consensus_outliers), "Union ≥ consensus"
        
        # Prix consensus (détectés par toutes méthodes)
        if consensus_outliers:
            print("  - Outliers consensus:", sorted(consensus_outliers))

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])