"""
Service de conversion de devises avec cache et fallback
ECOMSIMPLY Bloc 4 — Phase 4: Currency Conversion Service

Provider principal: exchangerate.host (BCE, gratuit, sans clé)
Fallback: OpenExchangeRates (si OXR_API_KEY disponible)
Cache: 24h TTL par défaut, configurable
"""

import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from decimal import Decimal, ROUND_HALF_UP
import json
import logging

from models.market_settings import ExchangeRate
from services.logging_service import log_info, log_error, log_operation


class CurrencyConversionService:
    """
    Service de conversion de devises avec providers multiples et cache
    """
    
    def __init__(self, db=None):
        self.db = db
        self.logger = logging.getLogger("ecomsimply.currency")
        
        # Configuration des providers
        self.primary_provider = "exchangerate.host"
        self.fallback_provider = "openexchangerates" if os.environ.get('OXR_API_KEY') else None
        self.oxr_api_key = os.environ.get('OXR_API_KEY')
        
        # Configuration du cache
        self.cache_ttl_hours = int(os.environ.get('CURRENCY_CACHE_TTL_HOURS', '24'))
        self.default_timeout = int(os.environ.get('CURRENCY_API_TIMEOUT_MS', '10000')) / 1000
        
        # Session HTTP réutilisable
        self.session = None
        
        # Devises supportées
        self.supported_currencies = ['EUR', 'GBP', 'USD']
        
        log_info(
            "Service de conversion de devises initialisé",
            service="CurrencyConversionService",
            primary_provider=self.primary_provider,
            fallback_provider=self.fallback_provider,
            cache_ttl_hours=self.cache_ttl_hours,
            supported_currencies=self.supported_currencies
        )
    
    async def _ensure_session(self):
        """Créer la session HTTP si nécessaire"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.default_timeout),
                headers={
                    'User-Agent': 'ECOMSIMPLY-Currency-Service/1.0',
                    'Accept': 'application/json'
                }
            )
    
    async def close(self):
        """Fermer la session HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_exchange_rate(
        self, 
        base_currency: str, 
        target_currency: str,
        force_refresh: bool = False
    ) -> Optional[float]:
        """
        Obtenir le taux de change entre deux devises
        
        Args:
            base_currency: Devise de base (ex: EUR)
            target_currency: Devise cible (ex: USD)
            force_refresh: Forcer le refresh du cache
            
        Returns:
            float: Taux de change ou None si erreur
        """
        base_currency = base_currency.upper()
        target_currency = target_currency.upper()
        
        # Validation des devises
        if base_currency not in self.supported_currencies:
            log_error(
                f"Devise de base non supportée: {base_currency}",
                service="CurrencyConversionService",
                supported_currencies=self.supported_currencies
            )
            return None
            
        if target_currency not in self.supported_currencies:
            log_error(
                f"Devise cible non supportée: {target_currency}",
                service="CurrencyConversionService", 
                supported_currencies=self.supported_currencies
            )
            return None
        
        # Cas trivial: même devise
        if base_currency == target_currency:
            return 1.0
        
        # Vérifier le cache d'abord
        if not force_refresh and self.db is not None:
            cached_rate = await self._get_cached_rate(base_currency, target_currency)
            if cached_rate:
                log_info(
                    "Taux de change trouvé en cache",
                    service="CurrencyConversionService",
                    base_currency=base_currency,
                    target_currency=target_currency,
                    rate=cached_rate,
                    source="cache"
                )
                return cached_rate
        
        # Récupérer depuis les providers
        rate = await self._fetch_rate_from_providers(base_currency, target_currency)
        
        # Mettre en cache si récupération réussie
        if rate and self.db is not None:
            await self._cache_rate(base_currency, target_currency, rate, self.primary_provider)
        
        return rate
    
    async def _get_cached_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        """Récupérer le taux depuis le cache MongoDB"""
        try:
            now = datetime.utcnow()
            cached = await self.db.exchange_rates.find_one({
                "base_currency": base_currency,
                "target_currency": target_currency,
                "expires_at": {"$gt": now}
            })
            
            if cached:
                return cached["rate"]
            return None
            
        except Exception as e:
            log_error(
                "Erreur lecture cache taux de change",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency,
                exception=str(e)
            )
            return None
    
    async def _cache_rate(
        self, 
        base_currency: str, 
        target_currency: str, 
        rate: float, 
        provider: str
    ):
        """Mettre en cache le taux de change"""
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=self.cache_ttl_hours)
            
            exchange_rate = ExchangeRate(
                base_currency=base_currency,
                target_currency=target_currency,
                rate=rate,
                provider=provider,
                fetched_at=now,
                expires_at=expires_at
            )
            
            # Upsert dans MongoDB
            await self.db.exchange_rates.update_one(
                {
                    "base_currency": base_currency,
                    "target_currency": target_currency
                },
                {"$set": exchange_rate.dict()},
                upsert=True
            )
            
            log_info(
                "Taux de change mis en cache",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency,
                rate=rate,
                provider=provider,
                expires_at=expires_at.isoformat()
            )
            
        except Exception as e:
            log_error(
                "Erreur mise en cache taux de change",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency,
                exception=str(e)
            )
    
    async def _fetch_rate_from_providers(
        self, 
        base_currency: str, 
        target_currency: str
    ) -> Optional[float]:
        """Récupérer le taux depuis les providers avec fallback"""
        
        # Essayer le provider principal
        rate = await self._fetch_from_exchangerate_host(base_currency, target_currency)
        if rate:
            return rate
        
        # Fallback sur OXR si disponible
        if self.fallback_provider and self.oxr_api_key:
            log_info(
                "Fallback vers OpenExchangeRates",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency
            )
            rate = await self._fetch_from_oxr(base_currency, target_currency)
            if rate:
                return rate
        
        log_error(
            "Impossible de récupérer le taux de change depuis tous les providers",
            service="CurrencyConversionService",
            base_currency=base_currency,
            target_currency=target_currency,
            primary_provider=self.primary_provider,
            fallback_provider=self.fallback_provider
        )
        return None
    
    async def _fetch_from_exchangerate_host(
        self, 
        base_currency: str, 
        target_currency: str
    ) -> Optional[float]:
        """Récupérer le taux depuis exchangerate.host"""
        try:
            await self._ensure_session()
            
            url = f"https://api.exchangerate.host/convert"
            params = {
                'from': base_currency,
                'to': target_currency,
                'amount': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success') and 'result' in data:
                        rate = float(data['result'])
                        
                        log_operation(
                            "CurrencyConversionService",
                            "fetch_exchangerate_host",
                            "success",
                            base_currency=base_currency,
                            target_currency=target_currency,
                            rate=rate,
                            provider="exchangerate.host"
                        )
                        
                        return rate
                    else:
                        log_error(
                            "Réponse invalide d'exchangerate.host",
                            service="CurrencyConversionService",
                            response_data=data,
                            base_currency=base_currency,
                            target_currency=target_currency
                        )
                else:
                    log_error(
                        "Erreur HTTP exchangerate.host",
                        service="CurrencyConversionService",
                        status_code=response.status,
                        base_currency=base_currency,
                        target_currency=target_currency
                    )
                    
        except Exception as e:
            log_error(
                "Exception lors de l'appel exchangerate.host",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency,
                exception=str(e)
            )
        
        return None
    
    async def _fetch_from_oxr(
        self, 
        base_currency: str, 
        target_currency: str
    ) -> Optional[float]:
        """Récupérer le taux depuis OpenExchangeRates (fallback)"""
        if not self.oxr_api_key:
            return None
            
        try:
            await self._ensure_session()
            
            # OXR utilise USD comme base par défaut
            url = "https://openexchangerates.org/api/latest.json"
            params = {
                'app_id': self.oxr_api_key,
                'base': base_currency
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'rates' in data and target_currency in data['rates']:
                        rate = float(data['rates'][target_currency])
                        
                        log_operation(
                            "CurrencyConversionService",
                            "fetch_oxr",
                            "success",
                            base_currency=base_currency,
                            target_currency=target_currency,
                            rate=rate,
                            provider="openexchangerates"
                        )
                        
                        return rate
                    else:
                        log_error(
                            "Devise non trouvée dans la réponse OXR",
                            service="CurrencyConversionService",
                            target_currency=target_currency,
                            available_currencies=list(data.get('rates', {}).keys())[:10]
                        )
                else:
                    log_error(
                        "Erreur HTTP OpenExchangeRates",
                        service="CurrencyConversionService",
                        status_code=response.status,
                        base_currency=base_currency,
                        target_currency=target_currency
                    )
                    
        except Exception as e:
            log_error(
                "Exception lors de l'appel OpenExchangeRates",
                service="CurrencyConversionService",
                base_currency=base_currency,
                target_currency=target_currency,
                exception=str(e)
            )
        
        return None
    
    async def convert_price(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str,
        precision: int = 2
    ) -> Optional[float]:
        """
        Convertir un montant d'une devise à une autre
        
        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            precision: Nombre de décimales (défaut 2)
            
        Returns:
            float: Montant converti ou None si erreur
        """
        if amount <= 0:
            return None
        
        rate = await self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None
        
        # Conversion avec précision
        converted = Decimal(str(amount)) * Decimal(str(rate))
        rounded = converted.quantize(Decimal('0.' + '0' * precision), rounding=ROUND_HALF_UP)
        
        result = float(rounded)
        
        log_info(
            "Conversion de devise effectuée",
            service="CurrencyConversionService",
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            converted_amount=result
        )
        
        return result
    
    async def get_supported_currencies(self) -> List[str]:
        """Obtenir la liste des devises supportées"""
        return self.supported_currencies.copy()
    
    async def refresh_all_rates(self) -> Dict[str, bool]:
        """
        Rafraîchir tous les taux de change en cache
        Utile pour la maintenance ou les mises à jour forcées
        """
        results = {}
        
        for base in self.supported_currencies:
            for target in self.supported_currencies:
                if base != target:
                    rate = await self.get_exchange_rate(base, target, force_refresh=True)
                    results[f"{base}_{target}"] = rate is not None
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        log_operation(
            "CurrencyConversionService",
            "refresh_all_rates",
            "completed",
            successful_conversions=success_count,
            total_conversions=total_count,
            success_rate=success_count / total_count if total_count > 0 else 0
        )
        
        return results
    
    async def get_cache_statistics(self) -> Dict[str, any]:
        """Obtenir les statistiques du cache de taux de change"""
        if self.db is None:
            return {"error": "Base de données non disponible"}
        
        try:
            now = datetime.utcnow()
            
            # Compter les entrées valides et expirées
            total_entries = await self.db.exchange_rates.count_documents({})
            valid_entries = await self.db.exchange_rates.count_documents({
                "expires_at": {"$gt": now}
            })
            expired_entries = total_entries - valid_entries
            
            # Obtenir les providers utilisés
            providers = await self.db.exchange_rates.distinct("provider")
            
            # Calcul du hit ratio approximatif
            hit_ratio = valid_entries / total_entries if total_entries > 0 else 0
            
            return {
                "total_entries": total_entries,
                "valid_entries": valid_entries,
                "expired_entries": expired_entries,
                "hit_ratio": round(hit_ratio, 3),
                "providers": providers,
                "cache_ttl_hours": self.cache_ttl_hours,
                "supported_currencies": self.supported_currencies
            }
            
        except Exception as e:
            log_error(
                "Erreur lors de la récupération des statistiques de cache",
                service="CurrencyConversionService",
                exception=str(e)
            )
            return {"error": str(e)}


# Instance globale du service
currency_service = None

async def get_currency_service(db=None) -> CurrencyConversionService:
    """Factory pour obtenir l'instance du service de conversion"""
    global currency_service
    if currency_service is None:
        currency_service = CurrencyConversionService(db)
    return currency_service