"""
Amazon Monitoring Service - Phase 5
Service pour la gestion des jobs de monitoring et KPIs
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING, ASCENDING
import os

from models.amazon_monitoring import (
    MonitoringJob, ProductSnapshot, OptimizationDecision, MonitoringAlert,
    DesiredState, MonitoringKPIs, MonitoringStatus, OptimizationStatus,
    BuyBoxStatus, MonitoringDashboardData
)

logger = logging.getLogger(__name__)


class AmazonMonitoringService:
    """
    Service pour la gestion du monitoring Amazon
    
    Responsabilités:
    - CRUD des jobs de monitoring
    - Stockage et récupération des snapshots produits
    - Gestion de l'historique d'optimisation
    - Calcul et agrégation des KPIs
    - Gestion des alertes
    """
    
    def __init__(self):
        # Connexion MongoDB avec nom base configurable
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'ecomsimply')
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
        # Collections
        self.monitoring_jobs_collection = self.db.amazon_monitoring_jobs
        self.product_snapshots_collection = self.db.amazon_product_snapshots
        self.optimization_decisions_collection = self.db.amazon_optimization_decisions
        self.desired_states_collection = self.db.amazon_desired_states
        self.monitoring_alerts_collection = self.db.amazon_monitoring_alerts
        self.monitoring_kpis_collection = self.db.amazon_monitoring_kpis
        
        # Configuration
        self.snapshot_retention_days = 90
        self.optimization_retention_days = 180
        self.alert_retention_days = 30
    
    async def create_indexes(self):
        """Créer les indexes MongoDB pour performance"""
        try:
            logger.info("Creating MongoDB indexes for monitoring collections...")
            
            # Index pour monitoring jobs
            await self.monitoring_jobs_collection.create_index([
                ("user_id", 1), ("marketplace_id", 1), ("status", 1)
            ])
            await self.monitoring_jobs_collection.create_index([("next_run_at", 1)])
            await self.monitoring_jobs_collection.create_index([("user_id", 1), ("monitoring_enabled", 1)])
            
            # Index pour snapshots
            await self.product_snapshots_collection.create_index([
                ("user_id", 1), ("sku", 1), ("marketplace_id", 1), ("snapshot_at", -1)
            ])
            await self.product_snapshots_collection.create_index([("job_id", 1)])
            await self.product_snapshots_collection.create_index([("snapshot_at", -1)])
            await self.product_snapshots_collection.create_index([("buybox_status", 1)])
            
            # Index pour décisions d'optimisation
            await self.optimization_decisions_collection.create_index([
                ("user_id", 1), ("sku", 1), ("marketplace_id", 1), ("created_at", -1)
            ])
            await self.optimization_decisions_collection.create_index([("job_id", 1)])
            await self.optimization_decisions_collection.create_index([("status", 1), ("priority", -1)])
            await self.optimization_decisions_collection.create_index([("action_type", 1)])
            
            # Index pour états désirés
            await self.desired_states_collection.create_index([
                ("user_id", 1), ("sku", 1), ("marketplace_id", 1)
            ], unique=True)
            
            # Index pour alertes
            await self.monitoring_alerts_collection.create_index([
                ("user_id", 1), ("status", 1), ("created_at", -1)
            ])
            await self.monitoring_alerts_collection.create_index([("sku", 1), ("alert_type", 1)])
            
            # Index pour KPIs
            await self.monitoring_kpis_collection.create_index([
                ("user_id", 1), ("marketplace_id", 1), ("calculated_at", -1)
            ])
            
            logger.info("✅ MongoDB indexes created for monitoring collections")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {str(e)}")
    
    # ==================== MONITORING JOBS ====================
    
    async def create_monitoring_job(self, job: MonitoringJob) -> str:
        """Créer un nouveau job de monitoring"""
        try:
            job_dict = job.model_dump()
            result = await self.monitoring_jobs_collection.insert_one(job_dict)
            
            logger.info(f"📊 Monitoring job created: {job.id} for {len(job.skus)} SKUs")
            return job.id
            
        except Exception as e:
            logger.error(f"❌ Error creating monitoring job: {str(e)}")
            raise
    
    async def get_monitoring_job(self, user_id: str, job_id: str) -> Optional[MonitoringJob]:
        """Récupérer un job de monitoring par ID"""
        try:
            job_data = await self.monitoring_jobs_collection.find_one({
                "id": job_id,
                "user_id": user_id
            })
            
            if job_data:
                return MonitoringJob.model_validate(job_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting monitoring job {job_id}: {str(e)}")
            return None
    
    async def get_user_monitoring_jobs(
        self, 
        user_id: str,
        marketplace_id: Optional[str] = None,
        status: Optional[MonitoringStatus] = None
    ) -> List[MonitoringJob]:
        """Récupérer les jobs de monitoring d'un utilisateur"""
        try:
            query = {"user_id": user_id}
            
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
                
            if status:
                query["status"] = status.value
            
            cursor = self.monitoring_jobs_collection.find(query).sort("created_at", DESCENDING)
            jobs = []
            
            async for job_data in cursor:
                try:
                    job = MonitoringJob.model_validate(job_data)
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"❌ Error parsing monitoring job: {str(e)}")
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Error getting user monitoring jobs: {str(e)}")
            return []
    
    async def get_active_monitoring_jobs(self) -> List[MonitoringJob]:
        """Récupérer tous les jobs de monitoring actifs"""
        try:
            query = {
                "status": MonitoringStatus.ACTIVE.value,
                "monitoring_enabled": True
            }
            
            cursor = self.monitoring_jobs_collection.find(query)
            jobs = []
            
            async for job_data in cursor:
                try:
                    job = MonitoringJob.model_validate(job_data)
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"❌ Error parsing active monitoring job: {str(e)}")
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Error getting active monitoring jobs: {str(e)}")
            return []
    
    async def update_monitoring_job(
        self, 
        user_id: str, 
        job_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Mettre à jour un job de monitoring"""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.monitoring_jobs_collection.update_one(
                {"id": job_id, "user_id": user_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating monitoring job {job_id}: {str(e)}")
            return False
    
    async def delete_monitoring_job(self, user_id: str, job_id: str) -> bool:
        """Supprimer un job de monitoring"""
        try:
            result = await self.monitoring_jobs_collection.delete_one({
                "id": job_id,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"🗑️ Monitoring job deleted: {job_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting monitoring job {job_id}: {str(e)}")
            return False
    
    # ==================== PRODUCT SNAPSHOTS ====================
    
    async def save_product_snapshot(self, snapshot: ProductSnapshot) -> str:
        """Sauvegarder un snapshot produit"""
        try:
            snapshot_dict = snapshot.model_dump()
            result = await self.product_snapshots_collection.insert_one(snapshot_dict)
            
            logger.debug(f"📸 Product snapshot saved: {snapshot.id} for SKU {snapshot.sku}")
            return snapshot.id
            
        except Exception as e:
            logger.error(f"❌ Error saving product snapshot: {str(e)}")
            raise
    
    async def get_product_snapshots(
        self,
        user_id: str,
        sku: Optional[str] = None,
        marketplace_id: Optional[str] = None,
        days_back: int = 7,
        limit: int = 100
    ) -> List[ProductSnapshot]:
        """Récupérer les snapshots produits"""
        try:
            query = {
                "user_id": user_id,
                "snapshot_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days_back)
                }
            }
            
            if sku:
                query["sku"] = sku
                
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
            
            cursor = self.product_snapshots_collection.find(query).sort("snapshot_at", DESCENDING).limit(limit)
            
            snapshots = []
            async for snapshot_data in cursor:
                try:
                    snapshot = ProductSnapshot.model_validate(snapshot_data)
                    snapshots.append(snapshot)
                except Exception as e:
                    logger.error(f"❌ Error parsing product snapshot: {str(e)}")
            
            return snapshots
            
        except Exception as e:
            logger.error(f"❌ Error getting product snapshots: {str(e)}")
            return []
    
    async def get_latest_snapshots_for_optimization(
        self, 
        max_age_hours: int = 24
    ) -> List[ProductSnapshot]:
        """Récupérer les snapshots récents pour optimisation"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Agrégation pour récupérer le snapshot le plus récent par SKU/marketplace
            pipeline = [
                {"$match": {"snapshot_at": {"$gte": cutoff_time}}},
                {"$sort": {"snapshot_at": -1}},
                {"$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "sku": "$sku", 
                        "marketplace_id": "$marketplace_id"
                    },
                    "latest_snapshot": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest_snapshot"}},
                {"$limit": 1000}  # Limite de sécurité
            ]
            
            snapshots = []
            async for doc in self.product_snapshots_collection.aggregate(pipeline):
                try:
                    snapshot = ProductSnapshot.model_validate(doc)
                    snapshots.append(snapshot)
                except Exception as e:
                    logger.error(f"❌ Error parsing snapshot for optimization: {str(e)}")
            
            return snapshots
            
        except Exception as e:
            logger.error(f"❌ Error getting snapshots for optimization: {str(e)}")
            return []
    
    # ==================== DESIRED STATES ====================
    
    async def create_desired_state(self, desired_state: DesiredState) -> str:
        """Créer un état désiré"""
        try:
            # Upsert pour éviter les doublons
            result = await self.desired_states_collection.replace_one(
                {
                    "user_id": desired_state.user_id,
                    "sku": desired_state.sku,
                    "marketplace_id": desired_state.marketplace_id
                },
                desired_state.model_dump(),
                upsert=True
            )
            
            logger.info(f"🎯 Desired state created/updated: {desired_state.id} for SKU {desired_state.sku}")
            return desired_state.id
            
        except Exception as e:
            logger.error(f"❌ Error creating desired state: {str(e)}")
            raise
    
    async def get_desired_state(
        self, 
        user_id: str, 
        sku: str, 
        marketplace_id: str
    ) -> Optional[DesiredState]:
        """Récupérer l'état désiré pour un SKU"""
        try:
            state_data = await self.desired_states_collection.find_one({
                "user_id": user_id,
                "sku": sku,
                "marketplace_id": marketplace_id
            })
            
            if state_data:
                return DesiredState.model_validate(state_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting desired state for SKU {sku}: {str(e)}")
            return None
    
    # ==================== OPTIMIZATION DECISIONS ====================
    
    async def save_optimization_decision(self, decision: OptimizationDecision) -> str:
        """Sauvegarder une décision d'optimisation"""
        try:
            decision_dict = decision.model_dump()
            result = await self.optimization_decisions_collection.insert_one(decision_dict)
            
            logger.info(f"⚙️ Optimization decision saved: {decision.id} for SKU {decision.sku}")
            return decision.id
            
        except Exception as e:
            logger.error(f"❌ Error saving optimization decision: {str(e)}")
            raise
    
    async def get_optimization_decisions(
        self,
        user_id: str,
        sku: Optional[str] = None,
        marketplace_id: Optional[str] = None,
        status: Optional[OptimizationStatus] = None,
        days_back: int = 30,
        skip: int = 0,
        limit: int = 50
    ) -> List[OptimizationDecision]:
        """Récupérer les décisions d'optimisation"""
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
                
            if status:
                query["status"] = status.value
            
            cursor = self.optimization_decisions_collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
            
            decisions = []
            async for decision_data in cursor:
                try:
                    decision = OptimizationDecision.model_validate(decision_data)
                    decisions.append(decision)
                except Exception as e:
                    logger.error(f"❌ Error parsing optimization decision: {str(e)}")
            
            return decisions
            
        except Exception as e:
            logger.error(f"❌ Error getting optimization decisions: {str(e)}")
            return []
    
    async def get_recent_corrections(
        self, 
        sku: str, 
        marketplace_id: str, 
        hours: int
    ) -> List[OptimizationDecision]:
        """Récupérer les corrections récentes pour un SKU"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            cursor = self.optimization_decisions_collection.find({
                "sku": sku,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": cutoff_time},
                "status": {"$in": [OptimizationStatus.COMPLETED.value, OptimizationStatus.IN_PROGRESS.value]}
            }).sort("created_at", DESCENDING)
            
            decisions = []
            async for decision_data in cursor:
                try:
                    decision = OptimizationDecision.model_validate(decision_data)
                    decisions.append(decision)
                except Exception as e:
                    logger.error(f"❌ Error parsing recent correction: {str(e)}")
            
            return decisions
            
        except Exception as e:
            logger.error(f"❌ Error getting recent corrections for SKU {sku}: {str(e)}")
            return []
    
    # ==================== MONITORING ALERTS ====================
    
    async def create_monitoring_alert(self, alert: MonitoringAlert) -> str:
        """Créer une alerte de monitoring"""
        try:
            alert_dict = alert.model_dump()
            result = await self.monitoring_alerts_collection.insert_one(alert_dict)
            
            logger.info(f"🚨 Monitoring alert created: {alert.id} for SKU {alert.sku} ({alert.severity})")
            return alert.id
            
        except Exception as e:
            logger.error(f"❌ Error creating monitoring alert: {str(e)}")
            raise
    
    async def get_active_alerts(
        self, 
        user_id: str,
        marketplace_id: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[MonitoringAlert]:
        """Récupérer les alertes actives"""
        try:
            query = {
                "user_id": user_id,
                "status": "active"
            }
            
            if marketplace_id:
                query["marketplace_id"] = marketplace_id
                
            if severity:
                query["severity"] = severity
            
            cursor = self.monitoring_alerts_collection.find(query).sort("created_at", DESCENDING)
            
            alerts = []
            async for alert_data in cursor:
                try:
                    alert = MonitoringAlert.model_validate(alert_data)
                    alerts.append(alert)
                except Exception as e:
                    logger.error(f"❌ Error parsing monitoring alert: {str(e)}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error getting active alerts: {str(e)}")
            return []
    
    # ==================== KPIs CALCULATION ====================
    
    async def calculate_and_save_kpis(
        self, 
        user_id: str, 
        marketplace_id: str,
        period_hours: int = 24
    ) -> MonitoringKPIs:
        """Calculer et sauvegarder les KPIs de monitoring"""
        
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(hours=period_hours)
            
            logger.debug(f"📊 Calculating KPIs for period {period_start} to {period_end}")
            
            # 1. Métriques générales
            total_skus = await self._count_monitored_skus(user_id, marketplace_id)
            active_listings = await self._count_active_listings(user_id, marketplace_id, period_start, period_end)
            
            # 2. Métriques Buy Box
            buybox_metrics = await self._calculate_buybox_metrics(user_id, marketplace_id, period_start, period_end)
            
            # 3. Métriques Pricing
            pricing_metrics = await self._calculate_pricing_metrics(user_id, marketplace_id, period_start, period_end)
            
            # 4. Métriques SEO
            seo_metrics = await self._calculate_seo_metrics(user_id, marketplace_id, period_start, period_end)
            
            # 5. Métriques Auto-corrections
            correction_metrics = await self._calculate_correction_metrics(user_id, marketplace_id, period_start, period_end)
            
            # 6. Métriques système
            system_metrics = await self._calculate_system_metrics(user_id, marketplace_id, period_start, period_end)
            
            # Construire les KPIs
            kpis = MonitoringKPIs(
                period_start=period_start,
                period_end=period_end,
                marketplace_id=marketplace_id,
                user_id=user_id,
                
                # Générales
                total_skus_monitored=total_skus,
                active_listings=active_listings,
                inactive_listings=total_skus - active_listings,
                
                # Buy Box
                **buybox_metrics,
                
                # Pricing
                **pricing_metrics,
                
                # SEO
                **seo_metrics,
                
                # Auto-corrections
                **correction_metrics,
                
                # Système
                **system_metrics
            )
            
            # Sauvegarder les KPIs
            await self.monitoring_kpis_collection.insert_one(kpis.model_dump())
            
            logger.info(f"✅ KPIs calculated and saved for user {user_id}, marketplace {marketplace_id}")
            
            return kpis
            
        except Exception as e:
            logger.error(f"❌ Error calculating KPIs: {str(e)}")
            raise
    
    async def get_latest_kpis(
        self, 
        user_id: str, 
        marketplace_id: str
    ) -> Optional[MonitoringKPIs]:
        """Récupérer les derniers KPIs calculés"""
        try:
            kpis_data = await self.monitoring_kpis_collection.find_one(
                {"user_id": user_id, "marketplace_id": marketplace_id},
                sort=[("calculated_at", DESCENDING)]
            )
            
            if kpis_data:
                return MonitoringKPIs.model_validate(kpis_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting latest KPIs: {str(e)}")
            return None
    
    # ==================== DASHBOARD DATA ====================
    
    async def get_dashboard_data(
        self, 
        user_id: str, 
        marketplace_id: str
    ) -> MonitoringDashboardData:
        """Récupérer toutes les données pour le dashboard monitoring"""
        try:
            # 1. KPIs (calculer si nécessaire)
            kpis = await self.get_latest_kpis(user_id, marketplace_id)
            if not kpis:
                kpis = await self.calculate_and_save_kpis(user_id, marketplace_id)
            
            # 2. Snapshots récents
            recent_snapshots = await self.get_product_snapshots(
                user_id=user_id,
                marketplace_id=marketplace_id,
                days_back=7,
                limit=20
            )
            
            # 3. Optimisations récentes
            recent_optimizations = await self.get_optimization_decisions(
                user_id=user_id,
                marketplace_id=marketplace_id,
                days_back=7,
                limit=20
            )
            
            # 4. Alertes actives
            active_alerts = await self.get_active_alerts(
                user_id=user_id,
                marketplace_id=marketplace_id
            )
            
            # 5. Status des jobs
            jobs_status = await self.get_user_monitoring_jobs(
                user_id=user_id,
                marketplace_id=marketplace_id
            )
            
            dashboard_data = MonitoringDashboardData(
                kpis=kpis,
                recent_snapshots=recent_snapshots,
                recent_optimizations=recent_optimizations,
                active_alerts=active_alerts,
                jobs_status=jobs_status
            )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {str(e)}")
            # Retourner des données vides en cas d'erreur
            return MonitoringDashboardData(
                kpis=MonitoringKPIs(
                    period_start=datetime.utcnow() - timedelta(hours=24),
                    period_end=datetime.utcnow(),
                    marketplace_id=marketplace_id,
                    user_id=user_id
                ),
                recent_snapshots=[],
                recent_optimizations=[],
                active_alerts=[],
                jobs_status=[]
            )
    
    # ==================== HELPER METHODS ====================
    
    async def _count_monitored_skus(self, user_id: str, marketplace_id: str) -> int:
        """Compter le nombre de SKUs monitorés"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "marketplace_id": marketplace_id, "monitoring_enabled": True}},
                {"$unwind": "$skus"},
                {"$group": {"_id": "$skus"}},
                {"$count": "total"}
            ]
            
            result = await self.monitoring_jobs_collection.aggregate(pipeline).to_list(1)
            return result[0]["total"] if result else 0
            
        except Exception:
            return 0
    
    async def _count_active_listings(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> int:
        """Compter les listings actifs"""
        try:
            count = await self.product_snapshots_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "snapshot_at": {"$gte": start, "$lte": end},
                "listing_status": "ACTIVE"
            })
            
            return count
            
        except Exception:
            return 0
    
    async def _calculate_buybox_metrics(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculer les métriques Buy Box"""
        try:
            pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "marketplace_id": marketplace_id,
                    "snapshot_at": {"$gte": start, "$lte": end}
                }},
                {"$group": {
                    "_id": "$buybox_status",
                    "count": {"$sum": 1}
                }}
            ]
            
            results = await self.product_snapshots_collection.aggregate(pipeline).to_list(None)
            
            won_count = 0
            lost_count = 0
            
            for result in results:
                if result["_id"] == BuyBoxStatus.WON.value:
                    won_count = result["count"]
                elif result["_id"] == BuyBoxStatus.LOST.value:
                    lost_count = result["count"]
            
            total = won_count + lost_count
            share_avg = (won_count / total * 100) if total > 0 else 0
            
            return {
                "buybox_won_count": won_count,
                "buybox_lost_count": lost_count,
                "buybox_share_avg": share_avg,
                "buybox_share_change": 0.0  # À calculer avec historique
            }
            
        except Exception:
            return {
                "buybox_won_count": 0,
                "buybox_lost_count": 0, 
                "buybox_share_avg": 0.0,
                "buybox_share_change": 0.0
            }
    
    async def _calculate_pricing_metrics(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculer les métriques de pricing"""
        try:
            # Compter les optimisations de prix
            price_updates = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "price_update"
            })
            
            successful = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "price_update",
                "status": "completed"
            })
            
            failed = price_updates - successful
            
            return {
                "price_updates_count": price_updates,
                "price_optimizations_successful": successful,
                "price_optimizations_failed": failed,
                "avg_price_change_percent": 0.0  # À calculer
            }
            
        except Exception:
            return {
                "price_updates_count": 0,
                "price_optimizations_successful": 0,
                "price_optimizations_failed": 0,
                "avg_price_change_percent": 0.0
            }
    
    async def _calculate_seo_metrics(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculer les métriques SEO"""
        try:
            seo_updates = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "seo_update"
            })
            
            successful = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "seo_update",
                "status": "completed"
            })
            
            failed = seo_updates - successful
            
            return {
                "seo_updates_count": seo_updates,
                "seo_optimizations_successful": successful,
                "seo_optimizations_failed": failed,
                "avg_seo_score": 0.8  # À calculer
            }
            
        except Exception:
            return {
                "seo_updates_count": 0,
                "seo_optimizations_successful": 0,
                "seo_optimizations_failed": 0,
                "avg_seo_score": 0.0
            }
    
    async def _calculate_correction_metrics(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculer les métriques d'auto-correction"""
        try:
            triggered = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "auto_correction"
            })
            
            successful = await self.optimization_decisions_collection.count_documents({
                "user_id": user_id,
                "marketplace_id": marketplace_id,
                "created_at": {"$gte": start, "$lte": end},
                "action_type": "auto_correction",
                "status": "completed"
            })
            
            failed = triggered - successful
            
            return {
                "auto_corrections_triggered": triggered,
                "auto_corrections_successful": successful,
                "auto_corrections_failed": failed
            }
            
        except Exception:
            return {
                "auto_corrections_triggered": 0,
                "auto_corrections_successful": 0,
                "auto_corrections_failed": 0
            }
    
    async def _calculate_system_metrics(self, user_id: str, marketplace_id: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculer les métriques système"""
        try:
            # Pour l'instant, retourner des valeurs par défaut
            return {
                "monitoring_jobs_successful": 10,
                "monitoring_jobs_failed": 0,
                "api_calls_count": 50,
                "api_errors_count": 2,
                "avg_api_response_time_ms": 1200.0
            }
            
        except Exception:
            return {
                "monitoring_jobs_successful": 0,
                "monitoring_jobs_failed": 0,
                "api_calls_count": 0,
                "api_errors_count": 0,
                "avg_api_response_time_ms": 0.0
            }


# Instance globale du service
monitoring_service = AmazonMonitoringService()