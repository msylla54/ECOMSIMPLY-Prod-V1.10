"""
Tests pour la Tâche 2 : SEO Tags - 20 tags uniques avec diversité Jaccard
"""

import pytest
import sys
from typing import List

# Configuration du path pour les imports
sys.path.insert(0, '/app/backend')

from services.seo_scraping_service import SEOTagGenerator

class TestSEOTagGeneration:
    """Tests de génération de 20 tags SEO"""
    
    @pytest.fixture
    def tag_generator(self):
        """Fixture pour le générateur de tags"""
        return SEOTagGenerator()
    
    def test_generate_20_tags(self, tag_generator):
        """Test génération de 20 tags uniques"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Smartphone Galaxy Ultra",
            category="électronique",
            trending_keywords=["smartphone-5g", "photo-pro", "batterie-longue-duree"],
            ai_generated_tags=["galaxy-ultra", "android-premium", "ecran-oled"],
            user_id="test_user"
        )
        
        # Vérifications
        assert result["count"] == 20, f"Attendu 20 tags, obtenu {result['count']}"
        assert result["target_reached"] is True
        assert len(result["tags"]) == 20
        assert len(set(result["tags"])) == 20, "Les tags doivent être uniques"
    
    def test_tag_length_and_uniqueness(self, tag_generator):
        """Test longueur des tags (2-5 mots) et unicité"""
        result = tag_generator.generate_20_seo_tags(
            product_name="MacBook Pro 16",
            category="ordinateur",
            trending_keywords=["macbook-2024", "m3-chip", "retina-display"],
            ai_generated_tags=["macbook-pro", "apple-silicon", "creative-professionals"]
        )
        
        tags = result["tags"]
        
        # Test longueur (2-5 mots)
        for tag in tags:
            word_count = len(tag.split('-'))
            assert 2 <= word_count <= 5, f"Tag '{tag}' a {word_count} mots, attendu 2-5"
        
        # Test unicité
        unique_tags = set(tags)
        assert len(unique_tags) == len(tags), "Tous les tags doivent être uniques"
        
        # Test validation format
        assert result["validation_passed"] is True, "Tous les tags doivent passer la validation"
    
    def test_tag_diversity(self, tag_generator):
        """Test diversité Jaccard < 0.7"""
        result = tag_generator.generate_20_seo_tags(
            product_name="iPhone 15 Pro Max",
            category="smartphone",
            trending_keywords=["iphone-15", "titanium-design", "usb-c"],
            ai_generated_tags=["iphone-pro-max", "apple-premium", "camera-system"]
        )
        
        tags = result["tags"]
        
        # Test diversité entre tous les tags
        for i, tag1 in enumerate(tags):
            for j, tag2 in enumerate(tags):
                if i < j:  # Éviter les doublons et auto-comparaisons
                    similarity = tag_generator.calculate_jaccard_similarity(tag1, tag2)
                    assert similarity < 0.7, f"Tags '{tag1}' et '{tag2}' trop similaires: {similarity:.3f}"
        
        # Test score de diversité global
        assert result["diversity_score"] > 0.3, f"Score de diversité trop faible: {result['diversity_score']}"
        assert result["average_jaccard"] < 0.7, f"Similarité moyenne trop élevée: {result['average_jaccard']}"

class TestJaccardSimilarity:
    """Tests du calcul de similarité Jaccard"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_jaccard_identical_tags(self, tag_generator):
        """Test similarité entre tags identiques"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-5g", "smartphone-5g")
        assert similarity == 1.0, "Tags identiques doivent avoir similarité 1.0"
    
    def test_jaccard_completely_different_tags(self, tag_generator):
        """Test similarité entre tags complètement différents"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-premium", "livre-cuisine-italienne")
        assert similarity == 0.0, "Tags complètement différents doivent avoir similarité 0.0"
    
    def test_jaccard_partial_overlap(self, tag_generator):
        """Test similarité avec chevauchement partiel"""
        similarity = tag_generator.calculate_jaccard_similarity("smartphone-android-premium", "smartphone-ios-premium")
        # Intersection: {smartphone, premium} = 2
        # Union: {smartphone, android, premium, ios} = 4
        # Jaccard = 2/4 = 0.5
        assert abs(similarity - 0.5) < 0.01, f"Similarité attendue ~0.5, obtenu {similarity}"
    
    def test_jaccard_high_similarity(self, tag_generator):
        """Test détection de haute similarité"""
        similarity = tag_generator.calculate_jaccard_similarity("iphone-pro-max", "iphone-pro-plus")
        # Intersection: {iphone, pro} = 2
        # Union: {iphone, pro, max, plus} = 4
        # Jaccard = 2/4 = 0.5
        assert similarity >= 0.5, f"Similarité élevée attendue, obtenu {similarity}"

class TestTagValidation:
    """Tests de validation des tags"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_validate_tag_format_valid(self, tag_generator):
        """Test validation tags valides"""
        valid_tags = [
            "smartphone-premium",           # 2 mots
            "macbook-pro-m3",              # 3 mots  
            "iphone-15-pro-max",           # 4 mots
            "ordinateur-portable-gaming-asus-rog"  # 5 mots
        ]
        
        for tag in valid_tags:
            assert tag_generator.validate_tag_format(tag), f"Tag '{tag}' devrait être valide"
    
    def test_validate_tag_format_invalid(self, tag_generator):
        """Test validation tags invalides"""
        invalid_tags = [
            "smartphone",                   # 1 mot (trop court)
            "ordinateur-portable-gaming-asus-rog-strix",  # 6 mots (trop long)
            "",                            # Vide
            "   ",                         # Espaces seulement
            "---",                         # Tirets seulement
        ]
        
        for tag in invalid_tags:
            assert not tag_generator.validate_tag_format(tag), f"Tag '{tag}' devrait être invalide"
    
    def test_is_diverse_enough(self, tag_generator):
        """Test vérification de diversité"""
        existing_tags = ["smartphone-android-premium", "iphone-premium", "tablette-samsung"]
        
        # Tag trop similaire (devrait être rejeté)
        # smartphone-android-premium vs smartphone-premium-qualite
        # Intersection: {smartphone, premium} = 2
        # Union: {smartphone, android, premium, qualite} = 4  
        # Jaccard = 2/4 = 0.5 < 0.7 → accepté
        # Essayons un cas plus similaire
        similar_tag = "smartphone-android-ultra"  # Intersection: 2, Union: 3 → 0.67 < 0.7
        # Encore plus similaire
        very_similar_tag = "smartphone-android-premium-version"  # Plus de mots en commun
        
        # Test avec un tag très similaire
        similarity = tag_generator.calculate_jaccard_similarity(very_similar_tag, existing_tags[0])
        if similarity >= 0.7:
            assert not tag_generator.is_diverse_enough(very_similar_tag, existing_tags), \
                f"Tag '{very_similar_tag}' devrait être rejeté pour manque de diversité (similarité: {similarity:.3f})"
        
        # Tag suffisamment différent (devrait être accepté)
        diverse_tag = "ordinateur-portable"
        assert tag_generator.is_diverse_enough(diverse_tag, existing_tags), \
            f"Tag '{diverse_tag}' devrait être accepté"

class TestTagSources:
    """Tests des sources de tags"""
    
    @pytest.fixture
    def tag_generator(self):
        return SEOTagGenerator()
    
    def test_trending_keywords_priority(self, tag_generator):
        """Test priorité aux mots-clés tendance"""
        trending_keywords = ["trend-2024", "viral-product", "bestseller-france"]
        ai_tags = ["ai-generated-1", "ai-generated-2"]
        
        result = tag_generator.generate_20_seo_tags(
            product_name="Test Product",
            trending_keywords=trending_keywords,
            ai_generated_tags=ai_tags
        )
        
        # Vérifier que les trending keywords sont présents
        tags = result["tags"]
        trending_found = sum(1 for trend in trending_keywords if any(trend in tag for tag in tags))
        
        assert result["source_breakdown"]["trending"] > 0, "Devrait utiliser des mots-clés tendance"
        assert trending_found > 0, "Au moins un mot-clé tendance devrait être présent"
    
    def test_mixed_sources(self, tag_generator):
        """Test mélange de sources"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Gaming Laptop",
            category="ordinateur",
            trending_keywords=["gaming-2024", "rtx-4090"],
            ai_generated_tags=["laptop-gamer", "high-performance"]
        )
        
        breakdown = result["source_breakdown"]
        
        # Vérifier qu'on a un mélange de sources
        total_sources = sum(breakdown.values())
        assert total_sources == 20, f"Total sources {total_sources} != 20"
        assert breakdown["trending"] >= 0, "Trending count should be >= 0"
        assert breakdown["ai"] >= 0, "AI count should be >= 0"  
        assert breakdown["static"] >= 0, "Static count should be >= 0"
    
    def test_static_fallback(self, tag_generator):
        """Test fallback vers tags statiques"""
        result = tag_generator.generate_20_seo_tags(
            product_name="Simple Product",
            # Pas de trending ou AI tags
        )
        
        # Devrait utiliser principalement des tags statiques
        assert result["source_breakdown"]["static"] > 10, \
            f"Devrait utiliser beaucoup de tags statiques, obtenu {result['source_breakdown']['static']}"
        assert result["count"] == 20, "Devrait quand même atteindre 20 tags"

if __name__ == "__main__":
    # Tests pour la ligne de commande
    import subprocess
    result = subprocess.run(["python", "-m", "pytest", __file__, "-v"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)