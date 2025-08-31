# Price Optimizer Service - Phase 3
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import statistics
import os

logger = logging.getLogger(__name__)

class PriceOptimizerService:
    """
    Service d'optimisation des prix Amazon
    Agrégation prix concurrents, conversion devise, règles min/max/variance
    """
    
    def __init__(self):
        self.fx_api_key = os.environ.get('FIXER_API_KEY')  # API Fixer.io pour conversion
        self.fx_api_url = 'http://data.fixer.io/api/latest'
        
        # Configuration par défaut
        self.default_config = {
            'min_margin_percent': 5,      # Marge minimum 5%
            'max_margin_percent': 40,     # Marge maximum 40%
            'competitor_weight': 0.6,     # Poids prix concurrents
            'cost_weight': 0.4,           # Poids coût produit
            'variance_threshold': 0.15,   # Seuil variance prix (15%)
            'currency_update_hours': 24   # Mise à jour taux change (24h)
        }
        
        # Cache des taux de change
        self.fx_cache = {}
        self.fx_cache_timestamp = None
    
    async def optimize_price_from_market_data(
        self,
        product_data: Dict[str, Any],
        competitor_prices: List[Dict[str, Any]],
        pricing_rules: Dict[str, Any] = None,
        target_marketplace: str = 'FR'
    ) -> Dict[str, Any]:
        """
        Optimiser le prix basé sur les données marché
        
        Args:
            product_data: Données du produit (coût, prix actuel, etc.)
            competitor_prices: Prix des concurrents
            pricing_rules: Règles de pricing spécifiques
            target_marketplace: Marketplace cible
        
        Returns:
            Dict avec prix optimisé et métadonnées
        """
        try:
            logger.info(f"🎯 Starting price optimization for {target_marketplace}")
            
            # Merge des règles avec configuration par défaut
            rules = {**self.default_config, **(pricing_rules or {})}
            
            # Analyser les prix concurrents
            competitor_analysis = await self._analyze_competitor_prices(
                competitor_prices, target_marketplace
            )
            
            # Convertir les prix si nécessaire
            normalized_prices = await self._normalize_prices_to_target_currency(
                competitor_analysis, target_marketplace
            )
            
            # Calculer le prix optimal
            optimal_price = await self._calculate_optimal_price(
                product_data, normalized_prices, rules
            )
            
            # Appliquer les contraintes min/max
            final_price = self._apply_price_constraints(
                optimal_price, product_data, rules
            )
            
            # Calculer les métriques
            metrics = self._calculate_pricing_metrics(
                final_price, product_data, normalized_prices, rules
            )
            
            result = {
                'optimized_price': final_price,
                'currency': self._get_marketplace_currency(target_marketplace),
                'competitor_analysis': competitor_analysis,
                'pricing_strategy': self._determine_pricing_strategy(final_price, normalized_prices),
                'metrics': metrics,
                'rules_applied': rules,
                'optimization_metadata': {
                    'optimized_at': datetime.utcnow().isoformat(),
                    'competitors_analyzed': len(competitor_prices),
                    'price_sources': len([p for p in normalized_prices if p.get('price')]),
                    'target_marketplace': target_marketplace,
                    'confidence_score': metrics.get('confidence_score', 0)
                }
            }
            
            logger.info(f"✅ Price optimization completed - Final price: {final_price['amount']} {final_price['currency']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Price optimization failed: {str(e)}")
            return {
                'optimized_price': None,
                'error': str(e),
                'optimization_metadata': {
                    'optimized_at': datetime.utcnow().isoformat(),
                    'success': False
                }
            }
    
    async def _analyze_competitor_prices(
        self, 
        competitor_prices: List[Dict[str, Any]], 
        marketplace: str
    ) -> Dict[str, Any]:
        """
        Analyser les prix des concurrents
        """
        if not competitor_prices:
            return {
                'count': 0,
                'average': None,
                'median': None,
                'min': None,
                'max': None,
                'variance': None,
                'outliers': []
            }
        
        # Extraire les prix valides
        valid_prices = []
        price_data = []
        
        for comp in competitor_prices:
            price = comp.get('price')
            if isinstance(price, (int, float)) and price > 0:
                valid_prices.append(price)
                price_data.append({
                    'asin': comp.get('asin'),
                    'title': comp.get('title', '')[:50],
                    'price': price,
                    'rating': comp.get('rating'),
                    'currency': comp.get('currency')
                })
        
        if not valid_prices:
            return {'count': 0, 'error': 'No valid competitor prices found'}
        
        # Statistiques de base
        avg_price = statistics.mean(valid_prices)
        median_price = statistics.median(valid_prices)
        min_price = min(valid_prices)
        max_price = max(valid_prices)
        
        # Variance et écart-type
        if len(valid_prices) > 1:
            variance = statistics.variance(valid_prices)
            std_dev = statistics.stdev(valid_prices)
        else:
            variance = 0
            std_dev = 0
        
        # Détecter les outliers (prix > 2 écarts-types)
        outliers = []
        if std_dev > 0:
            for data in price_data:
                z_score = abs(data['price'] - avg_price) / std_dev
                if z_score > 2:
                    outliers.append({
                        **data,
                        'z_score': round(z_score, 2),
                        'deviation_percent': round(((data['price'] - avg_price) / avg_price) * 100, 1)
                    })
        
        # Distribution des prix
        price_ranges = self._categorize_price_ranges(valid_prices, avg_price)
        
        analysis = {
            'count': len(valid_prices),
            'prices': price_data,
            'statistics': {
                'average': round(avg_price, 2),
                'median': round(median_price, 2),
                'min': round(min_price, 2),
                'max': round(max_price, 2),
                'variance': round(variance, 2),
                'standard_deviation': round(std_dev, 2),
                'coefficient_variation': round((std_dev / avg_price) * 100, 1) if avg_price > 0 else 0
            },
            'outliers': outliers,
            'price_distribution': price_ranges,
            'market_competitiveness': self._assess_market_competitiveness(std_dev, avg_price)
        }
        
        logger.info(f"✅ Analyzed {len(valid_prices)} competitor prices - Avg: {avg_price:.2f}")
        return analysis
    
    def _categorize_price_ranges(self, prices: List[float], avg_price: float) -> Dict[str, Any]:
        """
        Catégoriser les prix par gamme
        """
        low_threshold = avg_price * 0.8
        high_threshold = avg_price * 1.2
        
        low_price = [p for p in prices if p < low_threshold]
        mid_price = [p for p in prices if low_threshold <= p <= high_threshold]
        high_price = [p for p in prices if p > high_threshold]
        
        return {
            'low_price': {
                'count': len(low_price),
                'percentage': round((len(low_price) / len(prices)) * 100, 1),
                'range': f"< {low_threshold:.2f}"
            },
            'mid_price': {
                'count': len(mid_price),
                'percentage': round((len(mid_price) / len(prices)) * 100, 1),
                'range': f"{low_threshold:.2f} - {high_threshold:.2f}"
            },
            'high_price': {
                'count': len(high_price),
                'percentage': round((len(high_price) / len(prices)) * 100, 1),
                'range': f"> {high_threshold:.2f}"
            }
        }
    
    def _assess_market_competitiveness(self, std_dev: float, avg_price: float) -> str:
        """
        Évaluer la compétitivité du marché basé sur la variance des prix
        """
        if avg_price == 0:
            return 'unknown'
        
        cv = (std_dev / avg_price) * 100  # Coefficient de variation
        
        if cv < 10:
            return 'highly_competitive'  # Prix très serrés
        elif cv < 25:
            return 'competitive'
        elif cv < 50:
            return 'moderately_competitive'
        else:
            return 'fragmented'  # Marché fragmenté avec grandes différences
    
    async def _normalize_prices_to_target_currency(
        self, 
        competitor_analysis: Dict[str, Any], 
        target_marketplace: str
    ) -> List[Dict[str, Any]]:
        """
        Normaliser tous les prix vers la devise du marketplace cible
        """
        target_currency = self._get_marketplace_currency(target_marketplace)
        prices = competitor_analysis.get('prices', [])
        
        if not prices:
            return []
        
        # Obtenir les taux de change
        fx_rates = await self._get_exchange_rates()
        
        normalized_prices = []
        for price_data in prices:
            original_currency = price_data.get('currency', target_currency)
            original_price = price_data.get('price', 0)
            
            if original_currency == target_currency:
                # Pas de conversion nécessaire
                normalized_price = original_price
                conversion_rate = 1.0
            else:
                # Conversion nécessaire
                conversion_rate = self._get_conversion_rate(
                    original_currency, target_currency, fx_rates
                )
                normalized_price = original_price * conversion_rate
            
            normalized_data = {
                **price_data,
                'original_price': original_price,
                'original_currency': original_currency,
                'normalized_price': round(normalized_price, 2),
                'target_currency': target_currency,
                'conversion_rate': round(conversion_rate, 4),
                'converted': original_currency != target_currency
            }
            
            normalized_prices.append(normalized_data)
        
        logger.info(f"✅ Normalized {len(normalized_prices)} prices to {target_currency}")
        return normalized_prices
    
    async def _get_exchange_rates(self) -> Dict[str, float]:
        """
        Obtenir les taux de change actuels
        """
        # Vérifier le cache
        if (self.fx_cache_timestamp and 
            datetime.utcnow() - self.fx_cache_timestamp < timedelta(hours=self.default_config['currency_update_hours'])):
            return self.fx_cache
        
        if not self.fx_api_key:
            logger.warning("⚠️ No FX API key, using default rates")
            return self._get_default_exchange_rates()
        
        try:
            params = {
                'access_key': self.fx_api_key,
                'base': 'EUR',  # Base EUR pour avoir tous les taux
                'symbols': 'USD,GBP,EUR'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.fx_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            rates = data.get('rates', {})
                            # Ajouter EUR = 1 (base)
                            rates['EUR'] = 1.0
                            
                            self.fx_cache = rates
                            self.fx_cache_timestamp = datetime.utcnow()
                            
                            logger.info(f"✅ Updated FX rates: {rates}")
                            return rates
            
            logger.warning("⚠️ FX API failed, using default rates")
            return self._get_default_exchange_rates()
            
        except Exception as e:
            logger.error(f"❌ Error fetching FX rates: {str(e)}")
            return self._get_default_exchange_rates()
    
    def _get_default_exchange_rates(self) -> Dict[str, float]:
        """
        Taux de change par défaut (approximatifs)
        """
        return {
            'EUR': 1.0,
            'USD': 1.08,
            'GBP': 0.85
        }
    
    def _get_conversion_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        fx_rates: Dict[str, float]
    ) -> float:
        """
        Calculer le taux de conversion entre deux devises
        """
        if from_currency == to_currency:
            return 1.0
        
        from_rate = fx_rates.get(from_currency, 1.0)
        to_rate = fx_rates.get(to_currency, 1.0)
        
        # Conversion via EUR (base)
        # from_currency -> EUR -> to_currency
        conversion_rate = to_rate / from_rate
        
        return conversion_rate
    
    async def _calculate_optimal_price(
        self,
        product_data: Dict[str, Any],
        normalized_prices: List[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculer le prix optimal basé sur la concurrence et les coûts
        """
        # Extraire les données produit
        cost_price = product_data.get('cost_price', 0)
        current_price = product_data.get('current_price', 0)
        target_margin = product_data.get('target_margin_percent', rules['min_margin_percent'])
        
        # Prix concurrents normalisés
        competitor_prices = [p['normalized_price'] for p in normalized_prices if p.get('normalized_price')]
        
        if not competitor_prices:
            # Pas de concurrence, basé sur coût + marge
            if cost_price > 0:
                optimal_price = cost_price * (1 + target_margin / 100)
            else:
                optimal_price = current_price or 10.0
        else:
            # Calculer prix basé sur concurrence
            competitor_avg = statistics.mean(competitor_prices)
            competitor_median = statistics.median(competitor_prices)
            
            # Pondération entre prix concurrents et coût
            competitor_weight = rules['competitor_weight']
            cost_weight = rules['cost_weight']
            
            # Prix basé coût
            if cost_price > 0:
                cost_based_price = cost_price * (1 + target_margin / 100)
            else:
                cost_based_price = competitor_median
            
            # Prix optimal pondéré
            optimal_price = (
                competitor_median * competitor_weight + 
                cost_based_price * cost_weight
            )
            
            # Ajustement selon stratégie
            strategy = product_data.get('pricing_strategy', 'competitive')
            
            if strategy == 'premium':
                # Positionnement premium (+10-20% du marché)
                optimal_price = competitor_avg * 1.15
            elif strategy == 'aggressive':
                # Prix agressif (-5-10% du marché)
                optimal_price = competitor_median * 0.95
            elif strategy == 'value':
                # Rapport qualité/prix
                optimal_price = competitor_median * 1.05
        
        return {
            'amount': round(optimal_price, 2),
            'calculation_method': 'weighted_competitor_cost',
            'competitor_influence': rules['competitor_weight'],
            'cost_influence': rules['cost_weight'],
            'strategy_applied': product_data.get('pricing_strategy', 'competitive'),
            'base_competitor_price': statistics.median(competitor_prices) if competitor_prices else None,
            'base_cost_price': cost_price
        }
    
    def _apply_price_constraints(
        self,
        optimal_price: Dict[str, Any],
        product_data: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Appliquer les contraintes min/max au prix optimal
        """
        price = optimal_price['amount']
        cost_price = product_data.get('cost_price', 0)
        
        # Contraintes absolues
        min_price = product_data.get('min_price')
        max_price = product_data.get('max_price')
        
        # Contraintes basées sur les marges
        if cost_price > 0:
            min_margin_price = cost_price * (1 + rules['min_margin_percent'] / 100)
            max_margin_price = cost_price * (1 + rules['max_margin_percent'] / 100)
        else:
            min_margin_price = None
            max_margin_price = None
        
        # Appliquer les contraintes
        original_price = price
        constraints_applied = []
        
        # Minimum
        if min_price and price < min_price:
            price = min_price
            constraints_applied.append(f'min_price: {min_price}')
        
        if min_margin_price and price < min_margin_price:
            price = min_margin_price
            constraints_applied.append(f'min_margin: {rules["min_margin_percent"]}%')
        
        # Maximum
        if max_price and price > max_price:
            price = max_price
            constraints_applied.append(f'max_price: {max_price}')
        
        if max_margin_price and price > max_margin_price:
            price = max_margin_price
            constraints_applied.append(f'max_margin: {rules["max_margin_percent"]}%')
        
        return {
            **optimal_price,
            'amount': round(price, 2),
            'original_amount': round(original_price, 2),
            'constraints_applied': constraints_applied,
            'constrained': len(constraints_applied) > 0
        }
    
    def _calculate_pricing_metrics(
        self,
        final_price: Dict[str, Any],
        product_data: Dict[str, Any],
        normalized_prices: List[Dict[str, Any]],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculer les métriques de pricing
        """
        price = final_price['amount']
        cost_price = product_data.get('cost_price', 0)
        current_price = product_data.get('current_price', 0)
        
        metrics = {}
        
        # Marge
        if cost_price > 0:
            margin_amount = price - cost_price
            margin_percent = (margin_amount / cost_price) * 100
            metrics['margin'] = {
                'amount': round(margin_amount, 2),
                'percentage': round(margin_percent, 1),
                'target_met': margin_percent >= rules['min_margin_percent']
            }
        
        # Comparaison avec prix actuel
        if current_price > 0:
            price_change = price - current_price
            price_change_percent = (price_change / current_price) * 100
            metrics['price_change'] = {
                'amount': round(price_change, 2),
                'percentage': round(price_change_percent, 1),
                'direction': 'increase' if price_change > 0 else 'decrease' if price_change < 0 else 'unchanged'
            }
        
        # Position concurrentielle
        if normalized_prices:
            competitor_prices = [p['normalized_price'] for p in normalized_prices]
            
            # Percentile dans la concurrence
            sorted_prices = sorted(competitor_prices + [price])
            position = sorted_prices.index(price) + 1
            percentile = (position / len(sorted_prices)) * 100
            
            metrics['competitive_position'] = {
                'percentile': round(percentile, 1),
                'rank': position,
                'total_competitors': len(competitor_prices),
                'vs_average': round(((price / statistics.mean(competitor_prices)) - 1) * 100, 1),
                'vs_median': round(((price / statistics.median(competitor_prices)) - 1) * 100, 1),
                'positioning': self._determine_price_positioning(percentile)
            }
        
        # Score de confiance
        confidence_factors = []
        
        if len(normalized_prices) >= 3:
            confidence_factors.append(30)  # Échantillon concurrentiel suffisant
        elif len(normalized_prices) >= 1:
            confidence_factors.append(15)
        
        if cost_price > 0:
            confidence_factors.append(25)  # Données de coût disponibles
        
        if not final_price.get('constrained', False):
            confidence_factors.append(20)  # Pas de contraintes appliquées
        
        if current_price > 0:
            confidence_factors.append(15)  # Référence prix actuel
        
        if len(final_price.get('constraints_applied', [])) == 0:
            confidence_factors.append(10)  # Optimisation libre
        
        confidence_score = min(100, sum(confidence_factors))
        metrics['confidence_score'] = confidence_score
        
        return metrics
    
    def _determine_price_positioning(self, percentile: float) -> str:
        """
        Déterminer le positionnement prix basé sur le percentile
        """
        if percentile >= 80:
            return 'premium'
        elif percentile >= 60:
            return 'above_average'
        elif percentile >= 40:
            return 'competitive'
        elif percentile >= 20:
            return 'value'
        else:
            return 'budget'
    
    def _determine_pricing_strategy(
        self, 
        final_price: Dict[str, Any], 
        normalized_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Déterminer la stratégie de pricing recommandée
        """
        if not normalized_prices:
            return {
                'strategy': 'cost_plus',
                'rationale': 'No competitor data available',
                'confidence': 'low'
            }
        
        price = final_price['amount']
        competitor_prices = [p['normalized_price'] for p in normalized_prices]
        avg_price = statistics.mean(competitor_prices)
        
        price_vs_avg = (price / avg_price - 1) * 100
        
        if price_vs_avg > 15:
            strategy = 'premium'
            rationale = f'Prix {price_vs_avg:.1f}% au-dessus du marché - positionnement premium'
        elif price_vs_avg > 5:
            strategy = 'value_plus'
            rationale = f'Prix {price_vs_avg:.1f}% au-dessus du marché - qualité supérieure'
        elif price_vs_avg > -5:
            strategy = 'competitive'
            rationale = f'Prix aligné sur le marché (±{abs(price_vs_avg):.1f}%)'
        elif price_vs_avg > -15:
            strategy = 'aggressive'
            rationale = f'Prix {abs(price_vs_avg):.1f}% sous le marché - acquisition client'
        else:
            strategy = 'penetration'
            rationale = f'Prix {abs(price_vs_avg):.1f}% sous le marché - pénétration marché'
        
        # Confiance basée sur l'échantillon concurrentiel
        if len(competitor_prices) >= 5:
            confidence = 'high'
        elif len(competitor_prices) >= 3:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'strategy': strategy,
            'rationale': rationale,
            'confidence': confidence,
            'price_vs_market_avg': round(price_vs_avg, 1)
        }
    
    def _get_marketplace_currency(self, marketplace: str) -> str:
        """
        Obtenir la devise du marketplace
        """
        currency_map = {
            'FR': 'EUR',
            'DE': 'EUR', 
            'IT': 'EUR',
            'ES': 'EUR',
            'UK': 'GBP',
            'US': 'USD'
        }
        return currency_map.get(marketplace, 'EUR')
    
    async def validate_price_rules(
        self, 
        price: float, 
        product_data: Dict[str, Any],
        rules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Valider un prix contre les règles définies
        """
        rules = rules or self.default_config
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        cost_price = product_data.get('cost_price', 0)
        min_price = product_data.get('min_price')
        max_price = product_data.get('max_price')
        
        # Validation marge minimum
        if cost_price > 0:
            margin_percent = ((price - cost_price) / cost_price) * 100
            min_margin = rules['min_margin_percent']
            
            if margin_percent < min_margin:
                validation['valid'] = False
                validation['errors'].append(f'Marge insuffisante: {margin_percent:.1f}% < {min_margin}%')
            
            validation['details']['margin'] = {
                'current': round(margin_percent, 1),
                'minimum_required': min_margin,
                'valid': margin_percent >= min_margin
            }
        
        # Validation prix minimum/maximum
        if min_price and price < min_price:
            validation['valid'] = False
            validation['errors'].append(f'Prix sous le minimum: {price} < {min_price}')
        
        if max_price and price > max_price:
            validation['valid'] = False
            validation['errors'].append(f'Prix au-dessus du maximum: {price} > {max_price}')
        
        validation['details']['price_bounds'] = {
            'current': price,
            'minimum': min_price,
            'maximum': max_price,
            'within_bounds': (not min_price or price >= min_price) and (not max_price or price <= max_price)
        }
        
        return validation