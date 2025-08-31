"""
Service Price Guards et agrégation des prix
ECOMSIMPLY Bloc 4 — Phase 4: Price Guards & Price Aggregation Service

Fonctionnalités:
- Agrégation des prix (médiane comme référence)
- Validation des bornes absolues (min/max)
- Validation de la variance relative
- Recommandations de publication (APPROVE, PENDING_REVIEW, REJECT)
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import statistics
from decimal import Decimal, ROUND_HALF_UP
import logging

from models.market_settings import PriceSnapshot, PriceAggregation, MarketSettings
from services.logging_service import log_info, log_error, log_operation
from services.currency_conversion_service import get_currency_service


class PriceGuardsService:
    """
    Service de validation et agrégation des prix avec Price Guards
    """
    
    def __init__(self, db=None):
        self.db = db
        self.logger = logging.getLogger("ecomsimply.price_guards")
        
        # Configuration par défaut des guards
        self.default_min_price = float(os.environ.get('DEFAULT_MIN_PRICE', '0.01'))
        self.default_max_price = float(os.environ.get('DEFAULT_MAX_PRICE', '10000.0'))
        self.default_variance_threshold = float(os.environ.get('DEFAULT_VARIANCE_THRESHOLD', '0.20'))
        
        log_info(
            "Service Price Guards initialisé",
            service="PriceGuardsService",
            default_min_price=self.default_min_price,
            default_max_price=self.default_max_price,
            default_variance_threshold=self.default_variance_threshold
        )
    
    async def aggregate_prices(
        self,
        snapshots: List[PriceSnapshot],
        target_currency: str,
        market_settings: Optional[MarketSettings] = None,
        correlation_id: str = None
    ) -> Optional[PriceAggregation]:
        """
        Agréger les prix depuis les snapshots avec conversion de devise
        
        Args:
            snapshots: Liste des snapshots de prix
            target_currency: Devise cible pour l'agrégation
            market_settings: Configuration des price guards
            correlation_id: ID de corrélation pour tracking
            
        Returns:
            PriceAggregation: Résultat d'agrégation avec recommandation
        """
        if not snapshots:
            log_error(
                "Aucun snapshot fourni pour l'agrégation",
                service="PriceGuardsService",
                correlation_id=correlation_id
            )
            return None
        
        # Filtrer les snapshots réussis avec prix valides
        valid_snapshots = [
            snap for snap in snapshots 
            if snap.success and snap.price > 0
        ]
        
        if not valid_snapshots:
            log_error(
                "Aucun snapshot valide pour l'agrégation",
                service="PriceGuardsService",
                total_snapshots=len(snapshots),
                correlation_id=correlation_id
            )
            return None
        
        log_info(
            "Démarrage agrégation des prix",
            service="PriceGuardsService",
            total_snapshots=len(snapshots),
            valid_snapshots=len(valid_snapshots),
            target_currency=target_currency,
            correlation_id=correlation_id
        )
        
        # Convertir tous les prix vers la devise cible
        currency_service = await get_currency_service(self.db)
        converted_prices = []
        conversion_errors = 0
        
        for snapshot in valid_snapshots:
            if snapshot.currency == target_currency:
                # Même devise, pas de conversion nécessaire
                converted_prices.append(snapshot.price)
            else:
                # Conversion nécessaire
                converted_price = await currency_service.convert_price(
                    snapshot.price,
                    snapshot.currency,
                    target_currency
                )
                
                if converted_price is not None:
                    converted_prices.append(converted_price)
                    
                    # Mettre à jour le snapshot avec le prix converti (optionnel)
                    if target_currency == 'EUR':
                        snapshot.price_eur = converted_price
                else:
                    conversion_errors += 1
                    log_error(
                        "Échec conversion devise",
                        service="PriceGuardsService",
                        source_price=snapshot.price,
                        from_currency=snapshot.currency,
                        to_currency=target_currency,
                        source_name=snapshot.source_name
                    )
        
        if not converted_prices:
            log_error(
                "Aucun prix converti disponible",
                service="PriceGuardsService",
                conversion_errors=conversion_errors,
                correlation_id=correlation_id
            )
            return None
        
        # Calculs statistiques
        prices_sorted = sorted(converted_prices)
        
        reference_price = statistics.median(prices_sorted)  # Médiane comme référence
        min_price = min(prices_sorted)
        max_price = max(prices_sorted) 
        avg_price = statistics.mean(prices_sorted)
        
        # Calcul de la variance (écart-type / moyenne)
        if len(prices_sorted) > 1:
            std_dev = statistics.stdev(prices_sorted)
            price_variance = std_dev / avg_price if avg_price > 0 else 0
        else:
            price_variance = 0.0
        
        # Évaluation des Price Guards
        guards_evaluation = await self._evaluate_price_guards(
            reference_price,
            price_variance,
            market_settings
        )
        
        # Calcul du score de qualité
        quality_score = self._calculate_quality_score(
            len(converted_prices),
            len(valid_snapshots),
            conversion_errors,
            price_variance
        )
        
        # Créer l'agrégation
        country_code = valid_snapshots[0].country_code
        product_name = valid_snapshots[0].product_name
        
        aggregation = PriceAggregation(
            correlation_id=correlation_id or f"agg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            product_name=product_name,
            country_code=country_code,
            currency=target_currency,
            reference_price=round(reference_price, 2),
            min_price=round(min_price, 2),
            max_price=round(max_price, 2),
            avg_price=round(avg_price, 2),
            price_variance=round(price_variance, 4),
            sources_count=len(valid_snapshots),
            successful_sources=len(converted_prices),
            collection_success_rate=len(converted_prices) / len(valid_snapshots),
            within_absolute_bounds=guards_evaluation['within_absolute_bounds'],
            within_variance_threshold=guards_evaluation['within_variance_threshold'],
            publish_recommendation=guards_evaluation['recommendation'],
            aggregated_at=datetime.utcnow(),
            snapshots_used=[snap.id for snap in valid_snapshots],
            aggregation_method="median",
            quality_score=quality_score
        )
        
        log_operation(
            "PriceGuardsService", 
            "aggregate_prices",
            "success",
            product_name=product_name,
            country_code=country_code,
            reference_price=reference_price,
            currency=target_currency,
            sources_used=len(converted_prices),
            price_variance=price_variance,
            recommendation=guards_evaluation['recommendation'],
            quality_score=quality_score,
            correlation_id=correlation_id
        )
        
        return aggregation
    
    async def _evaluate_price_guards(
        self,
        reference_price: float,
        price_variance: float,
        market_settings: Optional[MarketSettings]
    ) -> Dict[str, Any]:
        """
        Évaluer les Price Guards pour déterminer la recommandation de publication
        
        Args:
            reference_price: Prix de référence (médiane)
            price_variance: Variance des prix
            market_settings: Configuration des guards
            
        Returns:
            Dict: Résultat de l'évaluation des guards
        """
        # Utiliser les settings fournis ou les valeurs par défaut
        if market_settings:
            min_price = market_settings.price_publish_min or self.default_min_price
            max_price = market_settings.price_publish_max or self.default_max_price
            variance_threshold = market_settings.price_variance_threshold
        else:
            min_price = self.default_min_price
            max_price = self.default_max_price
            variance_threshold = self.default_variance_threshold
        
        # Évaluation des bornes absolues
        within_absolute_bounds = min_price <= reference_price <= max_price
        
        # Évaluation de la variance
        within_variance_threshold = price_variance <= variance_threshold
        
        # Déterminer la recommandation
        if within_absolute_bounds and within_variance_threshold:
            recommendation = "APPROVE"
            reason = "Prix dans les bornes et variance acceptable"
        elif not within_absolute_bounds:
            recommendation = "PENDING_REVIEW"
            if reference_price < min_price:
                reason = f"Prix trop bas ({reference_price:.2f} < {min_price:.2f})"
            else:
                reason = f"Prix trop élevé ({reference_price:.2f} > {max_price:.2f})"
        elif not within_variance_threshold:
            recommendation = "PENDING_REVIEW"
            reason = f"Variance trop élevée ({price_variance:.1%} > {variance_threshold:.1%})"
        else:
            recommendation = "REJECT"
            reason = "Conditions multiples non respectées"
        
        log_info(
            "Évaluation Price Guards",
            service="PriceGuardsService",
            reference_price=reference_price,
            min_price=min_price,
            max_price=max_price,
            price_variance=price_variance,
            variance_threshold=variance_threshold,
            within_absolute_bounds=within_absolute_bounds,
            within_variance_threshold=within_variance_threshold,
            recommendation=recommendation,
            reason=reason
        )
        
        return {
            'within_absolute_bounds': within_absolute_bounds,
            'within_variance_threshold': within_variance_threshold,
            'recommendation': recommendation,
            'reason': reason,
            'guards_config': {
                'min_price': min_price,
                'max_price': max_price,
                'variance_threshold': variance_threshold
            }
        }
    
    def _calculate_quality_score(
        self,
        converted_prices_count: int,
        valid_snapshots_count: int,
        conversion_errors: int,
        price_variance: float
    ) -> float:
        """
        Calculer un score de qualité pour l'agrégation
        
        Args:
            converted_prices_count: Nombre de prix convertis avec succès
            valid_snapshots_count: Nombre de snapshots valides
            conversion_errors: Nombre d'erreurs de conversion
            price_variance: Variance des prix
            
        Returns:
            float: Score de qualité entre 0.0 et 1.0
        """
        # Facteur de complétude des sources
        completeness_factor = converted_prices_count / valid_snapshots_count if valid_snapshots_count > 0 else 0
        
        # Facteur de consistance (inverse de la variance)
        consistency_factor = max(0, 1 - (price_variance * 2))  # Variance > 0.5 = score faible
        
        # Facteur de diversité des sources (plus de sources = meilleur)
        diversity_factor = min(1.0, converted_prices_count / 3)  # 3+ sources = score optimal
        
        # Score composé
        quality_score = (
            completeness_factor * 0.4 +  # 40% complétude
            consistency_factor * 0.4 +   # 40% consistance
            diversity_factor * 0.2        # 20% diversité
        )
        
        return round(quality_score, 3)
    
    async def validate_price_for_publication(
        self,
        product_name: str,
        country_code: str,
        user_id: str,
        correlation_id: str,
        max_sources: int = 5
    ) -> Dict[str, Any]:
        """
        Validation complète d'un prix pour publication
        Pipeline: Scraping → Agrégation → Price Guards → Recommandation
        
        Args:
            product_name: Nom du produit
            country_code: Code pays
            user_id: ID utilisateur 
            correlation_id: ID de corrélation
            max_sources: Nombre max de sources à scraper
            
        Returns:
            Dict: Résultat complet de validation
        """
        start_time = datetime.utcnow()
        
        log_info(
            "Démarrage validation prix complète",
            service="PriceGuardsService",
            product_name=product_name,
            country_code=country_code,
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        try:
            # 1. Récupérer les settings de marché pour l'utilisateur
            market_settings = None
            if self.db is not None:
                settings_data = await self.db.market_settings.find_one({
                    "user_id": user_id,
                    "country_code": country_code.upper(),
                    "enabled": True
                })
                if settings_data:
                    market_settings = MarketSettings(**settings_data)
            
            # 2. Scraper les prix depuis toutes les sources
            from services.multi_country_scraping_service import get_scraping_service
            scraping_service = await get_scraping_service(self.db)
            
            snapshots = await scraping_service.scrape_all_sources_for_country(
                country_code,
                product_name,
                correlation_id,
                max_sources
            )
            
            if not snapshots:
                log_error(
                    "Aucune donnée de prix récupérée",
                    service="PriceGuardsService",
                    correlation_id=correlation_id
                )
                return {
                    'success': False,
                    'error': 'Aucune donnée de prix récupérée - produit possiblement inexistant',
                    'recommendation': 'REJECT',
                    'correlation_id': correlation_id
                }
            
            # 3. Déterminer la devise cible
            target_currency = market_settings.currency_preference if market_settings else 'EUR'
            
            # 4. Agréger les prix
            aggregation = await self.aggregate_prices(
                snapshots,
                target_currency,
                market_settings,
                correlation_id
            )
            
            if not aggregation:
                return {
                    'success': False,
                    'error': 'Échec de l\'agrégation des prix',
                    'recommendation': 'REJECT',
                    'snapshots': len(snapshots),
                    'correlation_id': correlation_id
                }
            
            # 5. Sauvegarder les résultats en base
            if self.db is not None:
                try:
                    # Sauvegarder les snapshots
                    if snapshots:
                        await self.db.price_snapshots.insert_many([
                            snap.dict() for snap in snapshots
                        ])
                    
                    # Sauvegarder l'agrégation
                    await self.db.price_aggregations.insert_one(aggregation.dict())
                    
                except Exception as e:
                    log_error(
                        "Erreur sauvegarde en base",
                        service="PriceGuardsService",
                        correlation_id=correlation_id,
                        exception=str(e)
                    )
            
            # 6. Calculer les métriques de performance
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'correlation_id': correlation_id,
                'product_name': product_name,
                'country_code': country_code,
                'reference_price': aggregation.reference_price,
                'currency': aggregation.currency,
                'price_range': {
                    'min': aggregation.min_price,
                    'max': aggregation.max_price,
                    'avg': aggregation.avg_price
                },
                'variance': aggregation.price_variance,
                'sources': {
                    'total_attempted': len(snapshots),
                    'successful': aggregation.successful_sources,
                    'success_rate': aggregation.collection_success_rate
                },
                'guards_evaluation': {
                    'within_absolute_bounds': aggregation.within_absolute_bounds,
                    'within_variance_threshold': aggregation.within_variance_threshold,
                    'recommendation': aggregation.publish_recommendation
                },
                'quality_score': aggregation.quality_score,
                'processing_time_ms': duration_ms,
                'aggregation_id': aggregation.id
            }
            
            log_operation(
                "PriceGuardsService",
                "validate_price_complete",
                "success",
                product_name=product_name,
                country_code=country_code,
                recommendation=aggregation.publish_recommendation,
                reference_price=aggregation.reference_price,
                quality_score=aggregation.quality_score,
                processing_time_ms=duration_ms,
                correlation_id=correlation_id
            )
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            log_error(
                "Erreur lors de la validation prix complète",
                service="PriceGuardsService",
                product_name=product_name,
                country_code=country_code,
                user_id=user_id,
                correlation_id=correlation_id,
                processing_time_ms=duration_ms,
                exception=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'recommendation': 'REJECT',
                'processing_time_ms': duration_ms,
                'correlation_id': correlation_id
            }
    
    async def get_price_guards_statistics(self, user_id: str) -> Dict[str, Any]:
        """Obtenir les statistiques des Price Guards pour un utilisateur"""
        if self.db is None:
            return {"error": "Base de données non disponible"}
        
        try:
            # Période récente (7 derniers jours)
            from datetime import timedelta
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            
            # Statistiques générales
            total_aggregations = await self.db.price_aggregations.count_documents({
                "aggregated_at": {"$gte": recent_cutoff}
            })
            
            # Répartition des recommandations
            pipeline = [
                {"$match": {"aggregated_at": {"$gte": recent_cutoff}}},
                {"$group": {
                    "_id": "$publish_recommendation",
                    "count": {"$sum": 1},
                    "avg_quality_score": {"$avg": "$quality_score"},
                    "avg_reference_price": {"$avg": "$reference_price"},
                    "avg_variance": {"$avg": "$price_variance"}
                }}
            ]
            
            recommendations_stats = await self.db.price_aggregations.aggregate(pipeline).to_list(length=None)
            
            # Statistiques par pays
            country_pipeline = [
                {"$match": {"aggregated_at": {"$gte": recent_cutoff}}},
                {"$group": {
                    "_id": "$country_code",
                    "total_validations": {"$sum": 1},
                    "approved": {"$sum": {"$cond": [{"$eq": ["$publish_recommendation", "APPROVE"]}, 1, 0]}},
                    "avg_quality_score": {"$avg": "$quality_score"}
                }}
            ]
            
            country_stats = await self.db.price_aggregations.aggregate(country_pipeline).to_list(length=None)
            
            return {
                "period": "last_7_days",
                "total_price_validations": total_aggregations,
                "recommendations_breakdown": recommendations_stats,
                "country_statistics": country_stats,
                "guards_config": {
                    "default_min_price": self.default_min_price,
                    "default_max_price": self.default_max_price,
                    "default_variance_threshold": self.default_variance_threshold
                }
            }
            
        except Exception as e:
            log_error(
                "Erreur récupération statistiques Price Guards",
                service="PriceGuardsService",
                user_id=user_id,
                exception=str(e)
            )
            return {"error": str(e)}


# Instance globale du service  
price_guards_service = None

async def get_price_guards_service(db=None) -> PriceGuardsService:
    """Factory pour obtenir l'instance du service Price Guards"""
    global price_guards_service
    if price_guards_service is None:
        price_guards_service = PriceGuardsService(db)
    return price_guards_service