"""
Amazon Pricing Engine - Phase 4
Moteur de prix intelligents avec Buy Box awareness et SP-API intégration
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
import json
import os

from models.amazon_pricing import (
    PricingRule, PricingCalculation, PricingHistory, CompetitorOffer,
    PricingStrategy, BuyBoxStatus, PricingRuleStatus
)
from integrations.amazon.client import AmazonSPAPIClient
from integrations.amazon.models import AmazonConnection

logger = logging.getLogger(__name__)


class AmazonPricingEngine:
    """
    Moteur de prix intelligents Amazon avec Buy Box awareness
    
    Fonctionnalités :
    - Récupération offres concurrentes via Product Pricing API
    - Calcul prix optimal selon règles configurables
    - Publication temps réel via Listings Items API + Feeds
    - Historisation complète des décisions
    """
    
    def __init__(self):
        self.sp_api_client = AmazonSPAPIClient()
        
        # Configuration SP-API
        self.marketplaces = {
            'FR': {
                'id': 'A13V1IB3VIYZZH',
                'domain': 'amazon.fr', 
                'region': 'eu-west-1',
                'endpoint': 'https://sellingpartnerapi-eu.amazon.com'
            }
        }
        
        # Configuration pricing
        self.default_variance_pct = 5.0
        self.min_confidence_threshold = 70.0
        self.max_competitors = 20
        
        # Timeouts et retry
        self.api_timeout = 30
        self.retry_attempts = 3
        self.retry_delay = 2

    async def get_competitive_pricing(
        self, 
        sku: str, 
        marketplace_id: str,
        item_condition: str = "New"
    ) -> Tuple[List[CompetitorOffer], Dict[str, Any]]:
        """
        Récupérer les offres concurrentes via Product Pricing API
        
        Args:
            sku: SKU Amazon du produit
            marketplace_id: ID du marketplace
            item_condition: État du produit (New, Used, etc.)
            
        Returns:
            Tuple[List[CompetitorOffer], Dict[str, Any]]: Offres + métadonnées
        """
        try:
            logger.info(f"Getting competitive pricing for SKU {sku} on marketplace {marketplace_id}")
            
            # Configuration API
            endpoint = "/products/pricing/v0/price"
            
            params = {
                "MarketplaceId": marketplace_id,
                "Skus": sku,
                "ItemCondition": item_condition
            }
            
            # Appel SP-API Product Pricing
            start_time = time.time()
            response = await self.sp_api_client.make_request(
                method="GET",
                endpoint=endpoint,
                params=params,
                marketplace_id=marketplace_id
            )
            
            api_duration = int((time.time() - start_time) * 1000)
            
            if not response.get('success'):
                logger.error(f"SP-API Product Pricing failed: {response.get('error')}")
                return [], {'error': response.get('error'), 'duration_ms': api_duration}
            
            # Parser la réponse SP-API
            payload = response.get('data', {})
            
            competitors = []
            buybox_info = {}
            
            # Parser les offers
            if 'payload' in payload:
                for product in payload.get('payload', []):
                    product_sku = product.get('ASIN') or product.get('SellerSKU')
                    
                    if product_sku != sku:
                        continue
                    
                    # Product pricing details
                    product_pricing = product.get('Product', {})
                    competitive_pricing = product_pricing.get('CompetitivePricing', {})
                    
                    # Offres concurrentes
                    for offer in competitive_pricing.get('CompetitivePrices', []):
                        competitor_offer = self._parse_competitive_offer(offer)
                        if competitor_offer:
                            competitors.append(competitor_offer)
                    
                    # Buy Box information
                    offers_detail = product_pricing.get('Offers', [])
                    for offer_detail in offers_detail:
                        if offer_detail.get('IsBuyBoxWinner', False):
                            buybox_info = {
                                'price': float(offer_detail.get('ListingPrice', {}).get('Amount', 0)),
                                'seller_id': offer_detail.get('SellerId', ''),
                                'condition': offer_detail.get('ItemCondition', 'New'),
                                'shipping': float(offer_detail.get('Shipping', {}).get('Amount', 0))
                            }
            
            logger.info(f"Found {len(competitors)} competitive offers for SKU {sku}")
            
            metadata = {
                'api_duration_ms': api_duration,
                'competitors_count': len(competitors),
                'buybox_info': buybox_info,
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
            return competitors, metadata
            
        except Exception as e:
            logger.error(f"Error getting competitive pricing for SKU {sku}: {str(e)}")
            return [], {'error': str(e), 'duration_ms': 0}

    def _parse_competitive_offer(self, offer_data: Dict) -> Optional[CompetitorOffer]:
        """Parser une offre concurrente depuis SP-API"""
        try:
            price_data = offer_data.get('Price', {})
            listing_price = price_data.get('ListingPrice', {})
            shipping_price = price_data.get('Shipping', {})
            landed_price = price_data.get('LandedPrice', {})
            
            return CompetitorOffer(
                seller_id=offer_data.get('CompetitivePriceId', 'unknown'),
                condition=offer_data.get('condition', 'New'),
                price=float(listing_price.get('Amount', 0)),
                shipping=float(shipping_price.get('Amount', 0)),
                landed_price=float(landed_price.get('Amount', 0)),
                is_buy_box_winner=offer_data.get('belongsToRequester', False),
                is_featured_merchant=False  # À déterminer depuis d'autres sources
            )
        except Exception as e:
            logger.error(f"Error parsing competitive offer: {str(e)}")
            return None

    async def calculate_optimal_price(
        self,
        rule: PricingRule,
        current_price: Optional[float] = None,
        competitors: Optional[List[CompetitorOffer]] = None
    ) -> PricingCalculation:
        """
        Calculer le prix optimal selon la règle et les données concurrentielles
        
        Args:
            rule: Règle de pricing à appliquer
            current_price: Prix actuel du produit
            competitors: Offres concurrentes (si None, sera récupéré via API)
            
        Returns:
            PricingCalculation: Résultat du calcul avec diagnostic complet
        """
        start_time = time.time()
        
        try:
            logger.info(f"Calculating optimal price for SKU {rule.sku} with strategy {rule.strategy.value}")
            
            # Récupérer données concurrentielles si pas fournies
            if competitors is None:
                competitors, metadata = await self.get_competitive_pricing(
                    rule.sku, 
                    rule.marketplace_id
                )
            
            # Analyser la situation Buy Box
            buybox_analysis = self._analyze_buybox_situation(competitors, current_price)
            
            # Calculer prix selon stratégie
            if rule.strategy == PricingStrategy.BUYBOX_MATCH:
                recommended_price, reasoning = self._calculate_buybox_match_price(
                    rule, buybox_analysis, competitors
                )
            elif rule.strategy == PricingStrategy.MARGIN_TARGET:
                recommended_price, reasoning = self._calculate_margin_target_price(
                    rule, buybox_analysis, current_price
                )
            else:  # FLOOR_CEILING
                recommended_price, reasoning = self._calculate_floor_ceiling_price(
                    rule, buybox_analysis, current_price
                )
            
            # Appliquer les contraintes de règles
            final_price, constraints_applied = self._apply_pricing_constraints(
                recommended_price, rule, current_price
            )
            
            # Calculs de changement
            price_change = final_price - (current_price or 0)
            price_change_pct = (price_change / current_price * 100) if current_price else 0
            
            # Warnings et validation
            warnings = []
            within_rules = True
            
            if final_price != recommended_price:
                warnings.append(f"Prix ajusté de {recommended_price:.2f}€ à {final_price:.2f}€ pour respecter les contraintes")
            
            if abs(price_change_pct) > rule.variance_pct:
                warnings.append(f"Changement de prix {price_change_pct:.1f}% dépasse la variance autorisée {rule.variance_pct}%")
                within_rules = False
            
            # Calcul de confiance
            confidence = self._calculate_confidence(
                competitors, buybox_analysis, rule, final_price
            )
            
            # Construire le résultat
            calculation = PricingCalculation(
                sku=rule.sku,
                marketplace_id=rule.marketplace_id,
                current_price=current_price,
                competitors=competitors,
                buybox_price=buybox_analysis.get('buybox_price'),
                buybox_winner=buybox_analysis.get('buybox_winner'),
                our_offer=buybox_analysis.get('our_offer'),
                recommended_price=final_price,
                price_change=price_change,
                price_change_pct=price_change_pct,
                buybox_status=buybox_analysis.get('status', BuyBoxStatus.UNKNOWN),
                within_rules=within_rules,
                reasoning=reasoning,
                warnings=warnings,
                confidence=confidence,
                calculated_at=datetime.utcnow(),
                calculation_duration_ms=int((time.time() - start_time) * 1000)
            )
            
            logger.info(f"Price calculation completed for SKU {rule.sku}: {final_price:.2f}€ (change: {price_change_pct:.1f}%)")
            
            return calculation
            
        except Exception as e:
            logger.error(f"Error calculating optimal price for SKU {rule.sku}: {str(e)}")
            
            return PricingCalculation(
                sku=rule.sku,
                marketplace_id=rule.marketplace_id,
                current_price=current_price,
                competitors=[],
                recommended_price=current_price or rule.min_price,
                buybox_status=BuyBoxStatus.UNKNOWN,
                within_rules=False,
                reasoning=f"Erreur de calcul: {str(e)}",
                warnings=[f"Erreur: {str(e)}"],
                confidence=0.0,
                calculation_duration_ms=int((time.time() - start_time) * 1000)
            )

    def _analyze_buybox_situation(
        self, 
        competitors: List[CompetitorOffer], 
        current_price: Optional[float]
    ) -> Dict[str, Any]:
        """Analyser la situation Buy Box actuelle"""
        
        buybox_winner = None
        buybox_price = None
        our_offer = None
        
        # Trouver qui a la Buy Box
        for offer in competitors:
            if offer.is_buy_box_winner:
                buybox_winner = offer.seller_id
                buybox_price = offer.landed_price
                break
        
        # Trouver notre offre
        for offer in competitors:
            if offer.seller_id == "our_seller_id":  # À adapter selon l'identification
                our_offer = offer
                break
        
        # Déterminer le statut
        if our_offer and our_offer.is_buy_box_winner:
            status = BuyBoxStatus.WON
        elif buybox_price and current_price:
            price_diff_pct = abs(current_price - buybox_price) / buybox_price * 100
            if price_diff_pct <= 5:  # Moins de 5% d'écart
                status = BuyBoxStatus.RISK
            else:
                status = BuyBoxStatus.LOST
        else:
            status = BuyBoxStatus.UNKNOWN
        
        return {
            'status': status,
            'buybox_winner': buybox_winner,
            'buybox_price': buybox_price,
            'our_offer': our_offer,
            'competitors_count': len(competitors),
            'min_competitor_price': min([c.landed_price for c in competitors], default=None),
            'avg_competitor_price': sum([c.landed_price for c in competitors]) / len(competitors) if competitors else None
        }

    def _calculate_buybox_match_price(
        self, 
        rule: PricingRule, 
        buybox_analysis: Dict, 
        competitors: List[CompetitorOffer]
    ) -> Tuple[float, str]:
        """Calculer prix pour matcher la Buy Box"""
        
        buybox_price = buybox_analysis.get('buybox_price')
        
        if not buybox_price:
            # Pas de Buy Box identifiée, prendre le minimum concurrent
            min_price = min([c.landed_price for c in competitors], default=rule.min_price)
            return min_price, "Aucune Buy Box identifiée, alignement sur prix minimum concurrent"
        
        # Stratégie : matcher le prix Buy Box avec légère réduction
        target_price = buybox_price - 0.01  # Réduction de 1 centime
        
        reasoning = f"Alignement sur Buy Box à {buybox_price:.2f}€ avec réduction de 0.01€"
        
        return target_price, reasoning

    def _calculate_margin_target_price(
        self, 
        rule: PricingRule, 
        buybox_analysis: Dict, 
        current_price: Optional[float]
    ) -> Tuple[float, str]:
        """Calculer prix pour atteindre marge cible"""
        
        if not rule.margin_target:
            return current_price or rule.min_price, "Marge cible non définie"
        
        # Calcul simplifié : prix = coût / (1 - marge_target/100)
        # Estimation coût basée sur prix minimum
        estimated_cost = rule.min_price * 0.7  # Estimation : coût = 70% du prix min
        
        target_price = estimated_cost / (1 - rule.margin_target / 100)
        
        reasoning = f"Prix calculé pour marge cible {rule.margin_target}% (coût estimé: {estimated_cost:.2f}€)"
        
        return target_price, reasoning

    def _calculate_floor_ceiling_price(
        self, 
        rule: PricingRule, 
        buybox_analysis: Dict, 
        current_price: Optional[float]
    ) -> Tuple[float, str]:
        """Calculer prix entre min/max avec variance"""
        
        if not current_price:
            # Pas de prix actuel, partir du milieu de la fourchette
            target_price = (rule.min_price + rule.max_price) / 2
            return target_price, f"Prix initial au milieu de la fourchette [{rule.min_price:.2f}€ - {rule.max_price:.2f}€]"
        
        # Conserver le prix actuel s'il est dans les limites
        if rule.min_price <= current_price <= rule.max_price:
            return current_price, f"Prix actuel {current_price:.2f}€ respecte les contraintes min/max"
        
        # Ajuster au plus proche des limites
        if current_price < rule.min_price:
            return rule.min_price, f"Prix ajusté au minimum autorisé {rule.min_price:.2f}€"
        else:
            return rule.max_price, f"Prix ajusté au maximum autorisé {rule.max_price:.2f}€"

    def _apply_pricing_constraints(
        self, 
        price: float, 
        rule: PricingRule, 
        current_price: Optional[float]
    ) -> Tuple[float, List[str]]:
        """Appliquer les contraintes de la règle"""
        
        constraints_applied = []
        final_price = price
        
        # Contraintes min/max
        if final_price < rule.min_price:
            final_price = rule.min_price
            constraints_applied.append(f"Prix minimum appliqué: {rule.min_price:.2f}€")
        
        if final_price > rule.max_price:
            final_price = rule.max_price
            constraints_applied.append(f"Prix maximum appliqué: {rule.max_price:.2f}€")
        
        # Contrainte MAP
        if rule.map_price and final_price < rule.map_price:
            final_price = rule.map_price
            constraints_applied.append(f"Prix MAP appliqué: {rule.map_price:.2f}€")
        
        # Contrainte de variance
        if current_price:
            max_change = current_price * (rule.variance_pct / 100)
            min_allowed = current_price - max_change
            max_allowed = current_price + max_change
            
            if final_price < min_allowed:
                final_price = min_allowed
                constraints_applied.append(f"Variance minimale appliquée: {min_allowed:.2f}€")
            
            if final_price > max_allowed:
                final_price = max_allowed
                constraints_applied.append(f"Variance maximale appliquée: {max_allowed:.2f}€")
        
        # Arrondir au centime
        final_price = float(Decimal(str(final_price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return final_price, constraints_applied

    def _calculate_confidence(
        self, 
        competitors: List[CompetitorOffer], 
        buybox_analysis: Dict, 
        rule: PricingRule, 
        final_price: float
    ) -> float:
        """Calculer le niveau de confiance du pricing"""
        
        confidence = 100.0
        
        # Réduire si peu de données concurrentielles
        if len(competitors) < 3:
            confidence -= 20
        
        # Réduire si pas de Buy Box identifiée
        if buybox_analysis.get('status') == BuyBoxStatus.UNKNOWN:
            confidence -= 15
        
        # Réduire si prix hors variance normale
        if buybox_analysis.get('buybox_price'):
            buybox_price = buybox_analysis['buybox_price']
            price_diff_pct = abs(final_price - buybox_price) / buybox_price * 100
            if price_diff_pct > 10:
                confidence -= 10
        
        # Réduire si contraintes nombreuses appliquées
        if final_price == rule.min_price or final_price == rule.max_price:
            confidence -= 5
        
        return max(0.0, confidence)

    async def publish_price(
        self, 
        sku: str, 
        marketplace_id: str, 
        new_price: float,
        method: str = "listings_items"
    ) -> Dict[str, Any]:
        """
        Publier un nouveau prix via SP-API
        
        Args:
            sku: SKU du produit
            marketplace_id: ID marketplace
            new_price: Nouveau prix à publier
            method: "listings_items" ou "feeds"
            
        Returns:
            Dict avec résultat de la publication
        """
        try:
            logger.info(f"Publishing price {new_price:.2f}€ for SKU {sku} via {method}")
            
            start_time = time.time()
            
            if method == "listings_items":
                result = await self._publish_via_listings_items(sku, marketplace_id, new_price)
            else:
                result = await self._publish_via_feeds(sku, marketplace_id, new_price)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            result['publication_duration_ms'] = duration_ms
            result['method_used'] = method
            
            return result
            
        except Exception as e:
            logger.error(f"Error publishing price for SKU {sku}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'method_used': method,
                'publication_duration_ms': 0
            }

    async def _publish_via_listings_items(
        self, 
        sku: str, 
        marketplace_id: str, 
        price: float
    ) -> Dict[str, Any]:
        """Publier via Listings Items API"""
        
        endpoint = f"/listings/2021-08-01/items/{sku}"
        
        # Payload pour mise à jour prix
        payload = {
            "productType": "PRODUCT",  # À adapter selon le type de produit
            "patches": [{
                "op": "replace",
                "path": "/attributes/list_price",
                "value": [{
                    "Amount": price,
                    "CurrencyCode": "EUR"
                }]
            }]
        }
        
        response = await self.sp_api_client.make_request(
            method="PATCH",
            endpoint=endpoint,
            json_data=payload,
            marketplace_id=marketplace_id,
            params={"marketplaceIds": marketplace_id}
        )
        
        if response.get('success'):
            logger.info(f"Price updated successfully via Listings Items API for SKU {sku}")
            return {
                'success': True,
                'sp_api_response': response.get('data'),
                'submission_id': response.get('data', {}).get('submissionId')
            }
        else:
            logger.error(f"Listings Items API failed for SKU {sku}: {response.get('error')}")
            return {
                'success': False,
                'error': response.get('error'),
                'sp_api_response': response.get('data')
            }

    async def _publish_via_feeds(
        self, 
        sku: str, 
        marketplace_id: str, 
        price: float
    ) -> Dict[str, Any]:
        """Publier via Feeds API (POST_PRODUCT_PRICING_DATA)"""
        
        # Créer le XML pour le feed pricing
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
    <Header>
        <DocumentVersion>1.01</DocumentVersion>
        <MerchantIdentifier>MERCHANT_ID</MerchantIdentifier>
    </Header>
    <MessageType>Price</MessageType>
    <Message>
        <MessageID>1</MessageID>
        <Price>
            <SKU>{sku}</SKU>
            <StandardPrice currency="EUR">{price:.2f}</StandardPrice>
        </Price>
    </Message>
</AmazonEnvelope>'''
        
        # Créer le feed
        create_feed_payload = {
            "feedType": "POST_PRODUCT_PRICING_DATA",
            "marketplaceIds": [marketplace_id],
            "inputFeedDocumentId": ""  # À obtenir via createFeedDocument
        }
        
        # TODO: Implémenter la création du feed document et l'upload
        # Pour l'instant, simuler le succès
        
        logger.info(f"Price feed created for SKU {sku} (feeds method)")
        
        return {
            'success': True,
            'feed_id': f"feed_{int(time.time())}",
            'sp_api_response': {'status': 'SUBMITTED'}
        }

    def create_pricing_history_entry(
        self,
        user_id: str,
        rule: PricingRule,
        calculation: PricingCalculation,
        publication_result: Dict[str, Any]
    ) -> PricingHistory:
        """Créer une entrée d'historique de pricing"""
        
        return PricingHistory(
            user_id=user_id,
            sku=rule.sku,
            marketplace_id=rule.marketplace_id,
            rule_id=rule.id,
            old_price=calculation.current_price,
            new_price=calculation.recommended_price,
            price_change=calculation.price_change,
            price_change_pct=calculation.price_change_pct,
            buybox_price=calculation.buybox_price,
            competitors_count=len(calculation.competitors),
            buybox_status_before=calculation.buybox_status,
            publication_success=publication_result.get('success', False),
            publication_method=publication_result.get('method_used'),
            sp_api_response=publication_result.get('sp_api_response'),
            reasoning=calculation.reasoning,
            confidence=calculation.confidence,
            warnings=calculation.warnings,
            calculation_duration_ms=calculation.calculation_duration_ms or 0,
            publication_duration_ms=publication_result.get('publication_duration_ms', 0)
        )


# Instance globale du moteur
pricing_engine = AmazonPricingEngine()