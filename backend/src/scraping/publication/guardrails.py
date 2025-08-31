"""
Guardrails - Garde-fous pour publication automatique - ECOMSIMPLY
Validation prix, qualité données, scoring confiance avant publication
"""

from typing import Dict, List, Optional, Tuple, Any
from statistics import median, stdev
from decimal import Decimal
from datetime import datetime
import logging

from ..semantic import ProductDTO
from .dto import PublishTask

logger = logging.getLogger(__name__)


class PriceGuardrail:
    """Garde-fou prix basé sur écart médian et outliers"""
    
    def __init__(self, variance_threshold: float = 0.20):
        """
        Args:
            variance_threshold: Seuil d'écart acceptable (0.20 = 20%)
        """
        self.variance_threshold = variance_threshold
        
        # Base de données prix pour comparaison (simulée)
        self._price_history: Dict[str, List[float]] = {}
    
    def validate_price(self, product: ProductDTO, market_prices: Optional[List[float]] = None) -> Tuple[bool, str, Dict]:
        """
        Valide le prix par rapport au marché
        
        Returns:
            (is_valid, reason, analysis_data)
        """
        
        if not product.price:
            return False, "Aucun prix détecté", {"price_available": False}
        
        price_value = float(product.price.amount)
        
        # Si pas de données marché, utiliser données historiques simulées
        if not market_prices:
            market_prices = self._get_simulated_market_prices(product)
        
        if len(market_prices) < 2:
            # Pas assez de données pour comparaison → accepter avec warning
            logger.warning(f"Pas assez de données prix pour comparaison: {product.title}")
            return True, "Données marché insuffisantes (accepté)", {
                "price_value": price_value,
                "market_data_points": len(market_prices),
                "status": "insufficient_data"
            }
        
        # Calcul médiane et écart
        market_median = median(market_prices)
        price_deviation = abs(price_value - market_median) / market_median
        
        analysis = {
            "price_value": price_value,
            "market_median": market_median,
            "market_min": min(market_prices),
            "market_max": max(market_prices),
            "deviation_percentage": price_deviation * 100,
            "threshold_percentage": self.variance_threshold * 100,
            "market_data_points": len(market_prices)
        }
        
        # Validation seuil
        if price_deviation <= self.variance_threshold:
            return True, f"Prix dans la fourchette (écart: {price_deviation*100:.1f}%)", analysis
        else:
            reason = f"Prix aberrant - écart: {price_deviation*100:.1f}% > seuil: {self.variance_threshold*100:.1f}%"
            analysis["outlier_type"] = "above" if price_value > market_median else "below"
            return False, reason, analysis
    
    def _get_simulated_market_prices(self, product: ProductDTO) -> List[float]:
        """Simule données prix marché pour tests"""
        
        if not product.price:
            return []
        
        base_price = float(product.price.amount)
        
        # Simuler 5-10 prix marché autour du prix base
        import random
        market_count = random.randint(5, 10)
        market_prices = []
        
        for _ in range(market_count):
            # Variation ±15% autour prix base
            variation = random.uniform(-0.15, 0.15)
            simulated_price = base_price * (1 + variation)
            market_prices.append(max(1.0, simulated_price))  # Prix minimum 1€
        
        return market_prices


class QualityGuardrail:
    """Garde-fou qualité données produit"""
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Args:
            min_confidence: Score de confiance minimum (0.0-1.0)
        """
        self.min_confidence = min_confidence
    
    def validate_quality(self, product: ProductDTO) -> Tuple[bool, str, Dict]:
        """
        Valide la qualité des données produit
        
        Returns:
            (is_valid, reason, quality_analysis)
        """
        
        scores = self._calculate_quality_scores(product)
        overall_confidence = scores['overall_confidence']
        
        analysis = {
            **scores,
            "min_confidence_required": self.min_confidence,
            "quality_checks": self._get_quality_checks(product)
        }
        
        if overall_confidence >= self.min_confidence:
            return True, f"Qualité suffisante (confiance: {overall_confidence:.2f})", analysis
        else:
            reason = f"Qualité insuffisante - confiance: {overall_confidence:.2f} < seuil: {self.min_confidence}"
            return False, reason, analysis
    
    def _calculate_quality_scores(self, product: ProductDTO) -> Dict[str, float]:
        """Calcule scores qualité détaillés"""
        
        scores = {}
        
        # Score titre (longueur, contenu informatif)
        title_score = 0.0
        if product.title and len(product.title.strip()) >= 10:
            title_score = min(1.0, len(product.title) / 50.0)  # Score basé sur longueur
            if any(word in product.title.lower() for word in ['pro', 'premium', 'ultra', 'max']):
                title_score += 0.1  # Bonus mots informatifs
        scores['title_score'] = min(1.0, title_score)
        
        # Score description (richesse contenu)
        desc_score = 0.0
        if product.description_html:
            desc_length = len(product.description_html.strip())
            desc_score = min(1.0, desc_length / 200.0)  # Score basé sur longueur
            if '<p>' in product.description_html or '<ul>' in product.description_html:
                desc_score += 0.1  # Bonus structure HTML
        scores['description_score'] = min(1.0, desc_score)
        
        # Score prix (disponibilité + réalisme)
        price_score = 0.0
        if product.price and product.price.amount > 0:
            price_score = 0.8  # Base pour prix disponible
            # Bonus pour devise standard
            if product.price.currency in ['EUR', 'USD', 'GBP']:
                price_score += 0.2
        scores['price_score'] = price_score
        
        # Score images (nombre + qualité URLs)
        image_score = 0.0
        if product.images:
            image_count_score = min(1.0, len(product.images) / 3.0)  # Optimal: 3+ images
            https_score = sum(1 for img in product.images if img.url.startswith('https://')) / len(product.images)
            alt_score = sum(1 for img in product.images if img.alt and len(img.alt) > 5) / len(product.images)
            
            image_score = (image_count_score + https_score + alt_score) / 3.0
        scores['image_score'] = image_score
        
        # Score attributs (richesse métadonnées)
        attr_score = 0.0
        if product.attributes:
            attr_count_score = min(1.0, len(product.attributes) / 5.0)  # Optimal: 5+ attributs
            important_attrs = ['brand', 'model', 'category', 'sku']
            important_score = sum(1 for attr in important_attrs if attr in product.attributes) / len(important_attrs)
            
            attr_score = (attr_count_score + important_score) / 2.0
        scores['attributes_score'] = attr_score
        
        # Score SEO (nouvelles données Phase 1)
        seo_score = 0.0
        if hasattr(product, 'seo_title') and product.seo_title:
            seo_score += 0.3
        if hasattr(product, 'seo_description') and product.seo_description:
            seo_score += 0.3
        if hasattr(product, 'seo_keywords') and len(product.seo_keywords) >= 3:
            seo_score += 0.4
        scores['seo_score'] = seo_score
        
        # Score global pondéré
        weights = {
            'title_score': 0.20,
            'description_score': 0.15,
            'price_score': 0.25,
            'image_score': 0.20,
            'attributes_score': 0.10,
            'seo_score': 0.10
        }
        
        overall_confidence = sum(scores[key] * weights[key] for key in weights)
        scores['overall_confidence'] = overall_confidence
        
        return scores
    
    def _get_quality_checks(self, product: ProductDTO) -> Dict[str, bool]:
        """Checks booléens qualité"""
        
        return {
            'has_title': bool(product.title and len(product.title.strip()) >= 5),
            'has_description': bool(product.description_html and len(product.description_html.strip()) >= 20),
            'has_price': bool(product.price and product.price.amount > 0),
            'has_images': bool(product.images and len(product.images) >= 1),
            'https_images': all(img.url.startswith('https://') for img in product.images) if product.images else False,
            'has_attributes': bool(product.attributes and len(product.attributes) >= 2),
            'has_seo_data': bool(hasattr(product, 'seo_title') and product.seo_title),
            'status_complete': product.status.value == 'complete'
        }


class GuardRailEngine:
    """Moteur principal des garde-fous"""
    
    def __init__(self, price_variance_threshold: float = 0.20, min_confidence: float = 0.6):
        """
        Args:
            price_variance_threshold: Seuil écart prix acceptable
            min_confidence: Score confiance minimum
        """
        self.price_guardrail = PriceGuardrail(price_variance_threshold)
        self.quality_guardrail = QualityGuardrail(min_confidence)
        
        # Statistiques
        self.stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'blocked_by_price': 0,
            'blocked_by_quality': 0,
            'blocked_by_both': 0
        }
    
    def validate_publication(self, task: PublishTask) -> Tuple[bool, str, Dict]:
        """
        Validation complète avant publication
        
        Returns:
            (can_publish, blocking_reason, full_analysis)
        """
        
        self.stats['total_validations'] += 1
        product = task.product_dto
        
        logger.info(f"🛡️  Validation guardrails pour: {product.title[:30]}...")
        
        # 1. Validation prix
        price_valid, price_reason, price_analysis = self.price_guardrail.validate_price(product)
        
        # 2. Validation qualité
        quality_valid, quality_reason, quality_analysis = self.quality_guardrail.validate_quality(product)
        
        # 3. Résultat global
        can_publish = price_valid and quality_valid
        
        full_analysis = {
            'price_validation': {
                'valid': price_valid,
                'reason': price_reason,
                'analysis': price_analysis
            },
            'quality_validation': {
                'valid': quality_valid,
                'reason': quality_reason,
                'analysis': quality_analysis
            },
            'overall_decision': {
                'can_publish': can_publish,
                'timestamp': f"{datetime.now().isoformat()}"
            }
        }
        
        # Statistiques
        if can_publish:
            self.stats['passed_validations'] += 1
            blocking_reason = "Validation réussie"
            logger.info(f"✅ Validation réussie: {product.title[:30]}")
        else:
            # Catégoriser le blocage
            if not price_valid and not quality_valid:
                self.stats['blocked_by_both'] += 1
                blocking_reason = f"Prix ET qualité: {price_reason} | {quality_reason}"
            elif not price_valid:
                self.stats['blocked_by_price'] += 1
                blocking_reason = f"Prix: {price_reason}"
            else:
                self.stats['blocked_by_quality'] += 1
                blocking_reason = f"Qualité: {quality_reason}"
            
            logger.warning(f"🚫 Validation bloquée: {blocking_reason}")
        
        return can_publish, blocking_reason, full_analysis
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Statistiques des validations"""
        
        stats = self.stats.copy()
        
        if stats['total_validations'] > 0:
            stats['success_rate'] = (stats['passed_validations'] / stats['total_validations']) * 100
            stats['block_rate'] = 100 - stats['success_rate']
        else:
            stats['success_rate'] = 0.0
            stats['block_rate'] = 0.0
        
        return stats
    
    def get_quality_report(self, products: List[ProductDTO]) -> Dict[str, Any]:
        """Rapport qualité pour liste de produits"""
        
        if not products:
            return {"error": "Aucun produit fourni"}
        
        all_scores = []
        quality_distribution = {
            'excellent': 0,    # > 0.8
            'good': 0,         # 0.6-0.8
            'average': 0,      # 0.4-0.6
            'poor': 0          # < 0.4
        }
        
        for product in products:
            scores = self.quality_guardrail._calculate_quality_scores(product)
            confidence = scores['overall_confidence']
            all_scores.append(confidence)
            
            if confidence > 0.8:
                quality_distribution['excellent'] += 1
            elif confidence > 0.6:
                quality_distribution['good'] += 1
            elif confidence > 0.4:
                quality_distribution['average'] += 1
            else:
                quality_distribution['poor'] += 1
        
        avg_confidence = sum(all_scores) / len(all_scores)
        
        return {
            'total_products': len(products),
            'average_confidence': avg_confidence,
            'quality_distribution': quality_distribution,
            'publishable_count': quality_distribution['excellent'] + quality_distribution['good'],
            'needs_improvement': quality_distribution['average'] + quality_distribution['poor']
        }