"""
Service principal PriceTruth - Orchestrateur et calcul de consensus
"""
import asyncio
import os
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import asdict

from models.price_truth import (
    PriceTruth, PriceSource, PriceConsensus, ConsensusPriceStatus,
    PriceTruthResponse, PriceTruthDatabase
)
from services.pricing import (
    AmazonPriceAdapter, GoogleShoppingAdapter, 
    CdiscountAdapter, FnacAdapter, PriceExtractionResult
)


class PriceTruthService:
    """Service principal pour la vérification de prix multi-sources"""
    
    def __init__(self, db: PriceTruthDatabase):
        self.db = db
        
        # Configuration depuis .env
        self.enabled = os.getenv('PRICE_TRUTH_ENABLED', 'true').lower() == 'true'
        self.ttl_hours = int(os.getenv('PRICE_TRUTH_TTL_HOURS', '6'))
        self.consensus_tolerance_pct = float(os.getenv('CONSENSUS_TOLERANCE_PCT', '3.0'))
        self.min_sources_required = 2  # Minimum 2 sources concordantes
        
        # Adapters de sources
        self.adapters = {
            'amazon': AmazonPriceAdapter(),
            'google_shopping': GoogleShoppingAdapter(),
            'cdiscount': CdiscountAdapter(),
            'fnac': FnacAdapter()
        }
        
        # Statistiques globales
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'successful_consensus': 0,
            'failed_consensus': 0,
            'sources_queried': 0
        }
    
    async def get_price_truth(
        self, 
        sku: Optional[str] = None, 
        query: Optional[str] = None,
        force_refresh: bool = False
    ) -> Optional[PriceTruthResponse]:
        """
        Récupère ou calcule la vérité de prix pour un produit
        
        Args:
            sku: SKU du produit (prioritaire)
            query: Requête de recherche (fallback)
            force_refresh: Forcer le rafraîchissement même si cache frais
            
        Returns:
            PriceTruthResponse ou None si pas de données
        """
        if not self.enabled:
            return None
        
        if not sku and not query:
            raise ValueError("SKU ou query requis")
        
        search_key = sku or query
        self.stats['total_queries'] += 1
        
        # Vérifier le cache si pas de force refresh
        if not force_refresh:
            cached = await self.db.get_price_truth(search_key)
            if cached and cached.is_fresh:
                self.stats['cache_hits'] += 1
                return self._build_response(cached)
        
        # Rechercher par query si pas de SKU
        if not sku:
            cached = await self.db.search_by_query(query)
            if cached and cached.is_fresh and not force_refresh:
                self.stats['cache_hits'] += 1
                return self._build_response(cached)
        
        # Lancer la récupération multi-sources
        price_truth = await self._fetch_and_calculate_consensus(search_key, query or search_key)
        
        # Sauvegarder en base
        if price_truth:
            await self.db.upsert_price_truth(price_truth)
            return self._build_response(price_truth)
        
        return None
    
    async def _fetch_and_calculate_consensus(self, sku: str, query: str) -> Optional[PriceTruth]:
        """
        Récupère les prix depuis toutes les sources et calcule le consensus
        
        Args:
            sku: Identifiant produit
            query: Requête de recherche
            
        Returns:
            PriceTruth avec consensus calculé
        """
        print(f"🔍 PriceTruth: Récupération prix pour '{query}'")
        
        # Lancer toutes les sources en parallèle avec limite de concurrence
        semaphore = asyncio.Semaphore(3)  # Max 3 sources simultanées
        tasks = []
        
        for name, adapter in self.adapters.items():
            task = self._fetch_from_source_with_semaphore(semaphore, name, adapter, query)
            tasks.append(task)
        
        # Attendre tous les résultats
        extraction_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les résultats valides
        valid_sources = []
        for i, result in enumerate(extraction_results):
            if isinstance(result, Exception):
                source_name = list(self.adapters.keys())[i]
                print(f"❌ Erreur source {source_name}: {result}")
                continue
            
            if result and result.success and result.price:
                source = PriceSource(
                    name=result.name if hasattr(result, 'name') else list(self.adapters.keys())[i],
                    price=result.price,
                    currency=result.currency,
                    url=result.url,
                    screenshot=result.screenshot_path,
                    selector=result.selector,
                    ts=result.timestamp,
                    success=result.success,
                    error_message=result.error_message
                )
                valid_sources.append(source)
        
        self.stats['sources_queried'] += len(valid_sources)
        
        if len(valid_sources) < 2:
            print(f"⚠️ PriceTruth: Seulement {len(valid_sources)} source(s) valide(s), consensus impossible")
            consensus = PriceConsensus(
                agreeing_sources=len(valid_sources),
                status=ConsensusPriceStatus.INSUFFICIENT_EVIDENCE
            )
            self.stats['failed_consensus'] += 1
        else:
            consensus = self._calculate_consensus(valid_sources)
            if consensus.status == ConsensusPriceStatus.VALID:
                self.stats['successful_consensus'] += 1
            else:
                self.stats['failed_consensus'] += 1
        
        # Créer l'objet PriceTruth
        price_truth = PriceTruth(
            sku=sku,
            query=query,
            currency="EUR",
            value=consensus.median_price if consensus.status == ConsensusPriceStatus.VALID else None,
            sources=valid_sources,
            consensus=consensus,
            updated_at=datetime.now(),
            ttl_hours=self.ttl_hours
        )
        
        print(f"✅ PriceTruth: Consensus calculé - Status: {consensus.status}, Prix: {price_truth.value}€")
        return price_truth
    
    async def _fetch_from_source_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        name: str, 
        adapter: Any, 
        query: str
    ) -> Optional[PriceExtractionResult]:
        """Récupère le prix d'une source avec contrôle de concurrence"""
        async with semaphore:
            try:
                async with adapter:
                    result = await adapter.extract_price(query)
                    # Ajouter le nom de la source au résultat
                    result.name = name
                    return result
            except Exception as e:
                print(f"❌ Erreur adapter {name}: {e}")
                return None
    
    def _calculate_consensus(self, sources: List[PriceSource]) -> PriceConsensus:
        """
        Calcule le consensus des prix selon la méthode trim-mean/median
        
        Args:
            sources: Liste des sources de prix valides
            
        Returns:
            PriceConsensus avec le résultat
        """
        if not sources:
            return PriceConsensus(
                agreeing_sources=0,
                status=ConsensusPriceStatus.INSUFFICIENT_EVIDENCE
            )
        
        prices = [float(source.price) for source in sources]
        
        if len(prices) == 1:
            return PriceConsensus(
                agreeing_sources=1,
                status=ConsensusPriceStatus.INSUFFICIENT_EVIDENCE,
                median_price=Decimal(str(prices[0]))
            )
        
        # Calcul statistiques de base
        median_price = statistics.median(prices)
        stdev = statistics.stdev(prices) if len(prices) > 1 else 0.0
        
        # Détection d'outliers avec IQR method
        outlier_sources = self._detect_outliers_iqr(sources, prices)
        
        # Filtrer les outliers
        filtered_prices = [p for i, p in enumerate(prices) if sources[i].name not in outlier_sources]
        filtered_sources = [s for s in sources if s.name not in outlier_sources]
        
        if not filtered_prices:
            return PriceConsensus(
                agreeing_sources=0,
                status=ConsensusPriceStatus.OUTLIER_DETECTED,
                median_price=Decimal(str(median_price)),
                stdev=stdev,
                outliers=outlier_sources
            )
        
        # Recalculer le médian sans outliers
        final_median = statistics.median(filtered_prices)
        final_stdev = statistics.stdev(filtered_prices) if len(filtered_prices) > 1 else 0.0
        
        # Vérifier le consensus : sources dans la tolérance %
        agreeing_count = 0
        tolerance = final_median * (self.consensus_tolerance_pct / 100)
        
        for price in filtered_prices:
            if abs(price - final_median) <= tolerance:
                agreeing_count += 1
        
        # Décision finale
        if agreeing_count >= self.min_sources_required:
            status = ConsensusPriceStatus.VALID
        else:
            status = ConsensusPriceStatus.INSUFFICIENT_EVIDENCE
        
        return PriceConsensus(
            method="median_trim",
            agreeing_sources=agreeing_count,
            median_price=Decimal(str(final_median)),
            stdev=final_stdev,
            outliers=outlier_sources,
            tolerance_pct=self.consensus_tolerance_pct,
            status=status
        )
    
    def _detect_outliers_iqr(self, sources: List[PriceSource], prices: List[float]) -> List[str]:
        """Détecte les outliers avec la méthode IQR"""
        if len(prices) < 3:
            return []
        
        # Calculer Q1, Q3 et IQR
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        q1 = sorted_prices[n // 4]
        q3 = sorted_prices[3 * n // 4]
        iqr = q3 - q1
        
        # Limites outlier
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, price in enumerate(prices):
            if price < lower_bound or price > upper_bound:
                outliers.append(sources[i].name)
        
        return outliers
    
    def _build_response(self, price_truth: PriceTruth) -> PriceTruthResponse:
        """Construit la réponse API"""
        next_update = None
        if price_truth.updated_at:
            next_update = price_truth.updated_at + timedelta(hours=price_truth.ttl_hours)
        
        return PriceTruthResponse(
            sku=price_truth.sku,
            query=price_truth.query,
            price=float(price_truth.value) if price_truth.value else None,
            currency=price_truth.currency,
            status=price_truth.consensus.status,
            sources_count=len(price_truth.sources),
            agreeing_sources=price_truth.consensus.agreeing_sources,
            updated_at=price_truth.updated_at,
            is_fresh=price_truth.is_fresh,
            next_update_eta=next_update
        )
    
    async def refresh_stale_prices(self) -> Dict[str, Any]:
        """Rafraîchit les prix périmés (pour cron)"""
        if not self.enabled:
            return {'message': 'PriceTruth désactivé'}
        
        stale_records = await self.db.get_stale_records(self.ttl_hours)
        
        if not stale_records:
            return {
                'message': 'Aucun prix périmé à rafraîchir',
                'count': 0
            }
        
        refreshed = 0
        errors = 0
        
        for record in stale_records:
            try:
                await self.get_price_truth(sku=record.sku, force_refresh=True)
                refreshed += 1
            except Exception as e:
                print(f"❌ Erreur refresh {record.sku}: {e}")
                errors += 1
        
        return {
            'message': f'Rafraîchissement terminé',
            'stale_found': len(stale_records),
            'refreshed': refreshed,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        success_rate = 0
        if self.stats['total_queries'] > 0:
            success_rate = (self.stats['successful_consensus'] / self.stats['total_queries']) * 100
        
        cache_rate = 0
        if self.stats['total_queries'] > 0:
            cache_rate = (self.stats['cache_hits'] / self.stats['total_queries']) * 100
        
        return {
            'enabled': self.enabled,
            'ttl_hours': self.ttl_hours,
            'consensus_tolerance_pct': self.consensus_tolerance_pct,
            'min_sources_required': self.min_sources_required,
            'stats': {
                **self.stats,
                'success_rate': f"{success_rate:.1f}%",
                'cache_rate': f"{cache_rate:.1f}%"
            },
            'adapters_available': list(self.adapters.keys())
        }