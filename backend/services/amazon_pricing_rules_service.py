"""
Amazon Pricing Rules Service - Phase 4
Service pour la gestion des règles de pricing et l'historique
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
import os

from models.amazon_pricing import (
    PricingRule, PricingHistory, PricingBatch, PricingStats, 
    PricingDashboardData, PricingRuleStatus, BuyBoxStatus
)

logger = logging.getLogger(__name__)


class AmazonPricingRulesService:
    """
    Service pour la gestion des règles de pricing et historique
    
    Responsabilités:
    - CRUD des règles de pricing par SKU/marketplace
    - Stockage et récupération de l'historique
    - Statistiques et dashboard data
    - Gestion des traitements par lot
    """
    
    def __init__(self):
        # Connexion MongoDB avec nom base configurable
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'ecomsimply')
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
        # Collections
        self.pricing_rules_collection = self.db.amazon_pricing_rules
        self.pricing_history_collection = self.db.amazon_pricing_history
        self.pricing_batches_collection = self.db.amazon_pricing_batches
        
        # Configuration
        self.history_retention_days = 90  # Conserver 90 jours d'historique
    
    async def create_indexes(self):
        """Créer les indexes MongoDB pour performance"""
        try:
            # Index pour les règles
            await self.pricing_rules_collection.create_index([
                ("user_id", 1), ("sku", 1), ("marketplace_id", 1)
            ], unique=True)
            
            await self.pricing_rules_collection.create_index([("user_id", 1), ("status", 1)])
            await self.pricing_rules_collection.create_index([("marketplace_id", 1)])
            
            # Index pour l'historique
            await self.pricing_history_collection.create_index([("user_id", 1), ("created_at", -1)])
            await self.pricing_history_collection.create_index([("sku", 1), ("marketplace_id", 1)])
            await self.pricing_history_collection.create_index([("rule_id", 1)])
            await self.pricing_history_collection.create_index([("created_at", -1)])
            
            # Index pour les batches
            await self.pricing_batches_collection.create_index([("user_id", 1), ("created_at", -1)])
            
            logger.info("MongoDB indexes created for pricing collections")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")

    # ==================== RÈGLES DE PRICING ====================

    async def create_pricing_rule(self, rule: PricingRule) -> str:
        """Créer une nouvelle règle de pricing"""
        try:
            # Vérifier l'unicité (user_id, sku, marketplace_id)
            existing = await self.pricing_rules_collection.find_one({
                "user_id": rule.user_id,
                "sku": rule.sku,
                "marketplace_id": rule.marketplace_id
            })
            
            if existing:
                raise ValueError(f"Règle déjà existante pour SKU {rule.sku} sur marketplace {rule.marketplace_id}")
            
            # Insérer la règle
            rule_dict = rule.model_dump()
            result = await self.pricing_rules_collection.insert_one(rule_dict)
            
            logger.info(f"Pricing rule created: {rule.id} for SKU {rule.sku}")
            
            return rule.id
            
        except Exception as e:
            logger.error(f"Error creating pricing rule: {str(e)}")
            raise

    async def get_pricing_rule(self, user_id: str, rule_id: str) -> Optional[PricingRule]:
        """Récupérer une règle par ID"""
        try:
            rule_data = await self.pricing_rules_collection.find_one({
                "id": rule_id,
                "user_id": user_id
            })
            
            if rule_data:
                return PricingRule.model_validate(rule_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pricing rule {rule_id}: {str(e)}")
            return None

    async def get_user_pricing_rules(
        self, 
        user_id: str,
        marketplace_id: Optional[str] = None,
        status: Optional[PricingRuleStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[PricingRule]:
        """Récupérer les règles d'un utilisateur"""
        try:
            query = {"user_id": user_id}
            
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
                
            if status:
                query["status"] = status.value
            
            cursor = self.pricing_rules_collection.find(query).skip(skip).limit(limit)
            rules = []
            
            async for rule_data in cursor:
                try:
                    rule = PricingRule.model_validate(rule_data)
                    rules.append(rule)
                except Exception as e:
                    logger.error(f"Error parsing pricing rule: {str(e)}")
            
            return rules
            
        except Exception as e:
            logger.error(f"Error getting user pricing rules: {str(e)}")
            return []

    async def get_pricing_rule_by_sku(
        self, 
        user_id: str, 
        sku: str, 
        marketplace_id: str
    ) -> Optional[PricingRule]:
        """Récupérer la règle pour un SKU spécifique"""
        try:
            rule_data = await self.pricing_rules_collection.find_one({
                "user_id": user_id,
                "sku": sku,
                "marketplace_id": marketplace_id
            })
            
            if rule_data:
                return PricingRule.model_validate(rule_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pricing rule for SKU {sku}: {str(e)}")
            return None

    async def update_pricing_rule(self, user_id: str, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Mettre à jour une règle de pricing"""
        try:
            # Ajouter timestamp de mise à jour
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.pricing_rules_collection.update_one(
                {"id": rule_id, "user_id": user_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Pricing rule updated: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating pricing rule {rule_id}: {str(e)}")
            return False

    async def delete_pricing_rule(self, user_id: str, rule_id: str) -> bool:
        """Supprimer une règle de pricing"""
        try:
            result = await self.pricing_rules_collection.delete_one({
                "id": rule_id,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Pricing rule deleted: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting pricing rule {rule_id}: {str(e)}")
            return False

    async def update_rule_last_applied(self, rule_id: str) -> bool:
        """Mettre à jour le timestamp de dernière application"""
        try:
            result = await self.pricing_rules_collection.update_one(
                {"id": rule_id},
                {"$set": {"last_applied_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating last_applied_at for rule {rule_id}: {str(e)}")
            return False

    # ==================== HISTORIQUE ====================

    async def save_pricing_history(self, history: PricingHistory) -> str:
        """Sauvegarder une entrée d'historique"""
        try:
            history_dict = history.model_dump()
            result = await self.pricing_history_collection.insert_one(history_dict)
            
            logger.info(f"Pricing history saved: {history.id} for SKU {history.sku}")
            
            return history.id
            
        except Exception as e:
            logger.error(f"Error saving pricing history: {str(e)}")
            raise

    async def get_pricing_history(
        self,
        user_id: str,
        sku: Optional[str] = None,
        marketplace_id: Optional[str] = None,
        days_back: int = 30,
        skip: int = 0,
        limit: int = 100
    ) -> List[PricingHistory]:
        """Récupérer l'historique de pricing"""
        try:
            query = {
                "user_id": user_id,
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days_back)
                }
            }
            
            if sku:
                query["sku"] = sku
                
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
            
            cursor = self.pricing_history_collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
            
            history = []
            async for entry_data in cursor:
                try:
                    entry = PricingHistory.model_validate(entry_data)
                    history.append(entry)
                except Exception as e:
                    logger.error(f"Error parsing pricing history: {str(e)}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting pricing history: {str(e)}")
            return []

    async def get_sku_pricing_history(
        self,
        user_id: str,
        sku: str,
        marketplace_id: str,
        limit: int = 50
    ) -> List[PricingHistory]:
        """Récupérer l'historique pour un SKU spécifique"""
        try:
            cursor = self.pricing_history_collection.find({
                "user_id": user_id,
                "sku": sku,
                "marketplace_id": marketplace_id
            }).sort("created_at", DESCENDING).limit(limit)
            
            history = []
            async for entry_data in cursor:
                try:
                    entry = PricingHistory.model_validate(entry_data)
                    history.append(entry)
                except Exception as e:
                    logger.error(f"Error parsing SKU pricing history: {str(e)}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting SKU pricing history for {sku}: {str(e)}")
            return []

    # ==================== BATCHES ====================

    async def create_pricing_batch(self, batch: PricingBatch) -> str:
        """Créer un traitement par lot"""
        try:
            batch_dict = batch.model_dump()
            result = await self.pricing_batches_collection.insert_one(batch_dict)
            
            logger.info(f"Pricing batch created: {batch.id} for {len(batch.skus)} SKUs")
            
            return batch.id
            
        except Exception as e:
            logger.error(f"Error creating pricing batch: {str(e)}")
            raise

    async def get_pricing_batch(self, user_id: str, batch_id: str) -> Optional[PricingBatch]:
        """Récupérer un batch par ID"""
        try:
            batch_data = await self.pricing_batches_collection.find_one({
                "id": batch_id,
                "user_id": user_id
            })
            
            if batch_data:
                return PricingBatch.model_validate(batch_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pricing batch {batch_id}: {str(e)}")
            return None

    async def update_batch_progress(
        self,
        batch_id: str,
        processed_skus: int,
        successful_updates: int,
        failed_updates: int,
        results: List[Dict[str, Any]]
    ) -> bool:
        """Mettre à jour le progrès d'un batch"""
        try:
            # Calculer le pourcentage
            batch_data = await self.pricing_batches_collection.find_one({"id": batch_id})
            if not batch_data:
                return False
            
            total_skus = batch_data.get('total_skus', len(batch_data.get('skus', [])))
            progress_pct = (processed_skus / total_skus * 100) if total_skus > 0 else 0
            
            updates = {
                "processed_skus": processed_skus,
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "progress_pct": progress_pct,
                "results": results
            }
            
            # Marquer comme complété si tous les SKUs sont traités
            if processed_skus >= total_skus:
                updates.update({
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                })
                
                if batch_data.get('started_at'):
                    started_at = batch_data['started_at']
                    duration = (datetime.utcnow() - started_at).total_seconds()
                    updates["duration_seconds"] = duration
            
            result = await self.pricing_batches_collection.update_one(
                {"id": batch_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating batch progress {batch_id}: {str(e)}")
            return False

    # ==================== STATISTIQUES ====================

    async def get_pricing_stats(self, user_id: str, marketplace_id: str) -> PricingStats:
        """Récupérer les statistiques de pricing"""
        try:
            # Statistiques des règles
            total_rules = await self.pricing_rules_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id
            })
            
            active_rules = await self.pricing_rules_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "status": PricingRuleStatus.ACTIVE.value
            })
            
            # Statistiques des dernières 24h
            yesterday = datetime.utcnow() - timedelta(hours=24)
            
            recent_history = self.pricing_history_collection.find({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": yesterday}
            })
            
            successful_updates_24h = 0
            failed_updates_24h = 0
            price_changes = []
            
            async for entry in recent_history:
                if entry.get('publication_success'):
                    successful_updates_24h += 1
                else:
                    failed_updates_24h += 1
                
                price_change_pct = entry.get('price_change_pct', 0)
                price_changes.append(abs(price_change_pct))
            
            # Moyenne des changements de prix
            avg_price_change_pct = sum(price_changes) / len(price_changes) if price_changes else 0
            
            # Dernière mise à jour
            last_history = await self.pricing_history_collection.find_one(
                {"user_id": user_id, "marketplace_id": marketplace_id},
                sort=[("created_at", DESCENDING)]
            )
            
            last_update = last_history.get('created_at') if last_history else None
            
            # TODO: Implémenter comptage Buy Box et risques (nécessite données temps réel)
            skus_with_buybox = 0
            skus_at_risk = 0
            
            return PricingStats(
                total_rules=total_rules,
                active_rules=active_rules,
                skus_with_buybox=skus_with_buybox,
                skus_at_risk=skus_at_risk,
                avg_price_change_pct=avg_price_change_pct,
                successful_updates_24h=successful_updates_24h,
                failed_updates_24h=failed_updates_24h,
                last_update=last_update
            )
            
        except Exception as e:
            logger.error(f"Error getting pricing stats: {str(e)}")
            return PricingStats()

    async def get_dashboard_data(self, user_id: str, marketplace_id: str) -> PricingDashboardData:
        """Récupérer les données pour le dashboard pricing"""
        try:
            # Statistiques
            stats = await self.get_pricing_stats(user_id, marketplace_id)
            
            # Historique récent
            recent_history = await self.get_pricing_history(
                user_id=user_id,
                marketplace_id=marketplace_id,
                days_back=7,
                limit=20
            )
            
            # Résumé des règles
            rules = await self.get_user_pricing_rules(
                user_id=user_id,
                marketplace_id=marketplace_id,
                limit=100
            )
            
            rules_summary = []
            for rule in rules:
                rules_summary.append({
                    "id": rule.id,
                    "sku": rule.sku,
                    "strategy": rule.strategy.value,
                    "status": rule.status.value,
                    "min_price": rule.min_price,
                    "max_price": rule.max_price,
                    "last_applied_at": rule.last_applied_at
                })
            
            # Alertes Buy Box (simulées pour l'instant)
            buybox_alerts = [
                {
                    "sku": "EXAMPLE-SKU-1",
                    "message": "Risque de perte Buy Box - concurrent à 0.50€ de moins",
                    "severity": "warning",
                    "created_at": datetime.utcnow()
                }
            ]
            
            return PricingDashboardData(
                stats=stats,
                recent_history=recent_history,
                rules_summary=rules_summary,
                buybox_alerts=buybox_alerts
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return PricingDashboardData(
                stats=PricingStats(),
                recent_history=[],
                rules_summary=[],
                buybox_alerts=[]
            )

    # ==================== MAINTENANCE ====================

    async def cleanup_old_history(self) -> int:
        """Nettoyer l'ancien historique"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.history_retention_days)
            
            result = await self.pricing_history_collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old pricing history entries")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old history: {str(e)}")
            return 0


# Instance globale du service
pricing_rules_service = AmazonPricingRulesService()