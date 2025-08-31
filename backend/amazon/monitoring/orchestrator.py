"""
Amazon Monitoring Orchestrator - Phase 5
Orchestrateur principal pour le monitoring et l'optimisation automatique
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import json
import uuid

from models.amazon_monitoring import (
    MonitoringJob, ProductSnapshot, OptimizationDecision, MonitoringAlert,
    MonitoringStatus, BuyBoxStatus, OptimizationAction, OptimizationStatus
)
from amazon.pricing_engine import pricing_engine
from integrations.amazon.client import AmazonSPAPIClient

logger = logging.getLogger(__name__)


class AmazonMonitoringOrchestrator:
    """
    Orchestrateur principal du monitoring Amazon
    
    Responsabilités:
    - Scheduler les jobs de monitoring périodiques
    - Collecter les données via SP-API (Catalog, Pricing, Reports)
    - Déclencher les optimisations automatiques
    - Gérer les erreurs et retry logic
    - Maintenir l'état de santé du système
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.sp_api_client = AmazonSPAPIClient()
        self.running_jobs = {}
        self.job_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run': None
        }
        
        # Configuration
        self.max_concurrent_jobs = 3
        self.default_timeout = 300  # 5 minutes
        self.retry_attempts = 3
        self.retry_delay = 60  # 1 minute
        
        # Circuit breaker
        self.circuit_breaker = {
            'failure_count': 0,
            'failure_threshold': 5,
            'recovery_timeout': 900,  # 15 minutes
            'last_failure': None,
            'state': 'closed'  # closed, open, half_open
        }
    
    async def initialize(self):
        """Initialiser l'orchestrateur"""
        try:
            logger.info("🚀 Initializing Amazon Monitoring Orchestrator...")
            
            # Démarrer le scheduler
            self.scheduler.start()
            
            # Programmer les jobs périodiques
            await self._schedule_periodic_jobs()
            
            # Job de maintenance système
            self.scheduler.add_job(
                self._system_maintenance,
                IntervalTrigger(hours=1),
                id='system_maintenance',
                name='System Maintenance',
                replace_existing=True
            )
            
            logger.info("✅ Amazon Monitoring Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing orchestrator: {str(e)}")
            raise
    
    async def _schedule_periodic_jobs(self):
        """Programmer les jobs de monitoring périodiques"""
        
        # Job principal de monitoring (toutes les 6 heures)
        self.scheduler.add_job(
            self._run_monitoring_cycle,
            IntervalTrigger(hours=6),
            id='main_monitoring',
            name='Main Monitoring Cycle',
            replace_existing=True,
            max_instances=1
        )
        
        # Job d'optimisation (toutes les 24 heures)
        self.scheduler.add_job(
            self._run_optimization_cycle,
            IntervalTrigger(hours=24),
            id='optimization_cycle',
            name='Optimization Cycle',
            replace_existing=True,
            max_instances=1
        )
        
        # Job de calcul KPIs (toutes les heures)
        self.scheduler.add_job(
            self._calculate_kpis,
            IntervalTrigger(hours=1),
            id='kpi_calculation',
            name='KPI Calculation',
            replace_existing=True
        )
        
        # Job de nettoyage (tous les jours à 2h)
        self.scheduler.add_job(
            self._cleanup_old_data,
            CronTrigger(hour=2, minute=0),
            id='daily_cleanup',
            name='Daily Cleanup',
            replace_existing=True
        )
        
        logger.info("📅 Periodic jobs scheduled successfully")
    
    async def _run_monitoring_cycle(self):
        """Exécuter un cycle complet de monitoring"""
        job_id = str(uuid.uuid4())
        
        try:
            if not self._check_circuit_breaker():
                logger.warning("🔴 Circuit breaker is OPEN, skipping monitoring cycle")
                return
            
            logger.info(f"🔄 Starting monitoring cycle {job_id}")
            start_time = time.time()
            
            # Récupérer tous les jobs de monitoring actifs
            monitoring_jobs = await self._get_active_monitoring_jobs()
            
            logger.info(f"📊 Found {len(monitoring_jobs)} active monitoring jobs")
            
            processed_jobs = 0
            failed_jobs = 0
            
            # Traiter chaque job
            for job in monitoring_jobs:
                try:
                    await self._process_monitoring_job(job, job_id)
                    processed_jobs += 1
                    
                    # Rate limiting entre jobs
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing monitoring job {job.id}: {str(e)}")
                    failed_jobs += 1
                    await self._record_job_failure(job, str(e))
            
            # Mettre à jour les statistiques
            duration = time.time() - start_time
            await self._update_job_stats(processed_jobs, failed_jobs, duration)
            
            if failed_jobs == 0:
                self._reset_circuit_breaker()
            else:
                self._increment_circuit_breaker(failed_jobs)
            
            logger.info(f"✅ Monitoring cycle {job_id} completed: {processed_jobs} processed, {failed_jobs} failed, {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Critical error in monitoring cycle {job_id}: {str(e)}")
            self._increment_circuit_breaker(1)
            raise
    
    async def _process_monitoring_job(self, job: MonitoringJob, cycle_id: str):
        """Traiter un job de monitoring individuel"""
        
        try:
            logger.info(f"📦 Processing monitoring job {job.id} for {len(job.skus)} SKUs")
            
            snapshots = []
            
            # Collecter les données pour chaque SKU
            for sku in job.skus:
                try:
                    snapshot = await self._collect_product_data(
                        job.user_id, 
                        sku, 
                        job.marketplace_id,
                        job.id
                    )
                    
                    if snapshot:
                        snapshots.append(snapshot)
                        await self._save_product_snapshot(snapshot)
                    
                    # Rate limiting entre SKUs
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Error collecting data for SKU {sku}: {str(e)}")
                    continue
            
            # Mettre à jour le job
            await self._update_job_last_run(job.id)
            
            logger.info(f"✅ Monitoring job {job.id} processed: {len(snapshots)} snapshots collected")
            
        except Exception as e:
            logger.error(f"❌ Error processing monitoring job {job.id}: {str(e)}")
            raise
    
    async def _collect_product_data(
        self, 
        user_id: str, 
        sku: str, 
        marketplace_id: str,
        job_id: str
    ) -> Optional[ProductSnapshot]:
        """Collecter les données complètes d'un produit via SP-API"""
        
        start_time = time.time()
        
        try:
            logger.debug(f"🔍 Collecting data for SKU {sku} on marketplace {marketplace_id}")
            
            # 1. Données Catalog API
            catalog_data = await self._get_catalog_data(sku, marketplace_id)
            
            # 2. Données Pricing API
            pricing_data = await self._get_pricing_data(sku, marketplace_id)
            
            # 3. Données Buy Box (via competitive pricing)
            buybox_data = await self._get_buybox_data(sku, marketplace_id)
            
            # 4. Données Reports (si disponible)
            performance_data = await self._get_performance_data(sku, marketplace_id)
            
            # Construire le snapshot
            api_duration = int((time.time() - start_time) * 1000)
            
            snapshot = ProductSnapshot(
                job_id=job_id,
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                api_call_duration_ms=api_duration,
                
                # Catalog data
                **catalog_data,
                
                # Pricing data
                **pricing_data,
                
                # Buy Box data
                **buybox_data,
                
                # Performance data
                **performance_data,
                
                # Calcul score de complétude
                data_completeness_score=self._calculate_completeness_score(
                    catalog_data, pricing_data, buybox_data, performance_data
                )
            )
            
            logger.debug(f"✅ Data collected for SKU {sku}: {api_duration}ms, completeness: {snapshot.data_completeness_score:.2f}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"❌ Error collecting data for SKU {sku}: {str(e)}")
            return None
    
    async def _get_catalog_data(self, sku: str, marketplace_id: str) -> Dict[str, Any]:
        """Récupérer données Catalog API"""
        try:
            # Appel Catalog Items API
            response = await self.sp_api_client.make_request(
                method="GET",
                endpoint=f"/catalog/2022-04-01/items/{sku}",
                marketplace_id=marketplace_id,
                params={
                    "marketplaceIds": marketplace_id,
                    "includedData": "attributes,identifiers,images,productTypes,salesRanks,summaries"
                }
            )
            
            if not response.get('success'):
                return {}
            
            item_data = response.get('data', {})
            
            # Parser les données catalog
            catalog_data = {}
            
            if 'attributes' in item_data:
                attrs = item_data['attributes']
                catalog_data.update({
                    'title': self._extract_attribute(attrs, 'item_name'),
                    'description': self._extract_attribute(attrs, 'bullet_points'),
                    'bullet_points': self._extract_list_attribute(attrs, 'bullet_points'),
                    'brand': self._extract_attribute(attrs, 'brand'),
                    'category': self._extract_attribute(attrs, 'item_type_name')
                })
            
            if 'images' in item_data:
                images = item_data['images']
                if images:
                    catalog_data['main_image_url'] = images[0].get('link') if images else None
                    catalog_data['images'] = [img.get('link') for img in images if img.get('link')]
            
            return catalog_data
            
        except Exception as e:
            logger.error(f"Error getting catalog data for {sku}: {str(e)}")
            return {}
    
    async def _get_pricing_data(self, sku: str, marketplace_id: str) -> Dict[str, Any]:
        """Récupérer données Pricing API"""
        try:
            # Utiliser le pricing engine existant
            competitors, metadata = await pricing_engine.get_competitive_pricing(
                sku=sku,
                marketplace_id=marketplace_id
            )
            
            pricing_data = {}
            
            # Trouver notre prix
            for competitor in competitors:
                if competitor.seller_id == "our_seller_id":  # À adapter
                    pricing_data.update({
                        'current_price': competitor.price,
                        'currency': 'EUR',  # À déterminer dynamiquement
                        'list_price': competitor.price
                    })
                    break
            
            # Données concurrents
            if competitors:
                pricing_data.update({
                    'competitors_count': len(competitors),
                    'min_competitor_price': min([c.price for c in competitors]),
                    'avg_competitor_price': sum([c.price for c in competitors]) / len(competitors)
                })
            
            return pricing_data
            
        except Exception as e:
            logger.error(f"Error getting pricing data for {sku}: {str(e)}")
            return {}
    
    async def _get_buybox_data(self, sku: str, marketplace_id: str) -> Dict[str, Any]:
        """Récupérer données Buy Box"""
        try:
            # Réutiliser la logique du pricing engine
            competitors, metadata = await pricing_engine.get_competitive_pricing(
                sku=sku,
                marketplace_id=marketplace_id
            )
            
            buybox_data = {
                'buybox_status': BuyBoxStatus.UNKNOWN,
                'buybox_eligibility': False
            }
            
            # Analyser Buy Box
            buybox_info = metadata.get('buybox_info', {})
            if buybox_info:
                buybox_data.update({
                    'buybox_price': buybox_info.get('price'),
                    'buybox_winner': buybox_info.get('seller_id'),
                    'buybox_eligibility': True
                })
                
                # Déterminer notre statut
                our_seller_id = "our_seller_id"  # À adapter
                if buybox_info.get('seller_id') == our_seller_id:
                    buybox_data['buybox_status'] = BuyBoxStatus.WON
                else:
                    buybox_data['buybox_status'] = BuyBoxStatus.LOST
            
            return buybox_data
            
        except Exception as e:
            logger.error(f"Error getting buybox data for {sku}: {str(e)}")
            return {}
    
    async def _get_performance_data(self, sku: str, marketplace_id: str) -> Dict[str, Any]:
        """Récupérer données de performance (Brand Analytics si disponible)"""
        try:
            # Pour l'instant, retourner des données vides
            # TODO: Implémenter Brand Analytics API si l'utilisateur est Brand Owner
            return {
                'impressions': None,
                'clicks': None,
                'ctr_percent': None,
                'conversions': None,
                'conversion_rate_percent': None
            }
            
        except Exception as e:
            logger.error(f"Error getting performance data for {sku}: {str(e)}")
            return {}
    
    def _extract_attribute(self, attributes: Dict, key: str) -> Optional[str]:
        """Extraire un attribut du catalog"""
        if key in attributes and attributes[key]:
            attr = attributes[key]
            if isinstance(attr, list) and attr:
                return str(attr[0])
            elif isinstance(attr, str):
                return attr
        return None
    
    def _extract_list_attribute(self, attributes: Dict, key: str) -> List[str]:
        """Extraire une liste d'attributs du catalog"""
        if key in attributes and attributes[key]:
            attr = attributes[key]
            if isinstance(attr, list):
                return [str(item) for item in attr]
            elif isinstance(attr, str):
                return [attr]
        return []
    
    def _calculate_completeness_score(
        self, 
        catalog_data: Dict, 
        pricing_data: Dict, 
        buybox_data: Dict, 
        performance_data: Dict
    ) -> float:
        """Calculer le score de complétude des données"""
        
        total_fields = 0
        filled_fields = 0
        
        # Catalog data (poids: 40%)
        catalog_fields = ['title', 'description', 'bullet_points', 'brand', 'main_image_url']
        for field in catalog_fields:
            total_fields += 1
            if catalog_data.get(field):
                filled_fields += 1
        
        # Pricing data (poids: 30%)
        pricing_fields = ['current_price', 'competitors_count']
        for field in pricing_fields:
            total_fields += 1
            if pricing_data.get(field) is not None:
                filled_fields += 1
        
        # Buy Box data (poids: 20%)
        buybox_fields = ['buybox_status', 'buybox_price']
        for field in buybox_fields:
            total_fields += 1
            if buybox_data.get(field) is not None:
                filled_fields += 1
        
        # Performance data (poids: 10%)
        performance_fields = ['impressions', 'clicks']
        for field in performance_fields:
            total_fields += 1
            if performance_data.get(field) is not None:
                filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    async def _run_optimization_cycle(self):
        """Exécuter un cycle d'optimisation automatique"""
        try:
            logger.info("🎯 Starting optimization cycle")
            
            # Cette méthode sera implémentée dans le closed_loop_optimizer
            # Importé pour éviter la dépendance circulaire
            from amazon.optimizer.closed_loop import closed_loop_optimizer
            
            await closed_loop_optimizer.run_optimization_cycle()
            
            logger.info("✅ Optimization cycle completed")
            
        except Exception as e:
            logger.error(f"❌ Error in optimization cycle: {str(e)}")
    
    async def _calculate_kpis(self):
        """Calculer et sauvegarder les KPIs"""
        try:
            logger.debug("📊 Calculating KPIs")
            
            # TODO: Implémenter calcul KPIs
            # - Agrégation des snapshots récents
            # - Calcul métriques Buy Box, pricing, SEO
            # - Sauvegarde en DB
            
            pass
            
        except Exception as e:
            logger.error(f"❌ Error calculating KPIs: {str(e)}")
    
    async def _system_maintenance(self):
        """Maintenance système périodique"""
        try:
            logger.debug("🔧 Running system maintenance")
            
            # Nettoyer les jobs expired
            await self._cleanup_expired_jobs()
            
            # Vérifier la santé des connexions SP-API
            await self._check_api_health()
            
            # Optimiser les performances
            await self._optimize_performance()
            
        except Exception as e:
            logger.error(f"❌ Error in system maintenance: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Nettoyer les anciennes données"""
        try:
            logger.info("🧹 Cleaning up old data")
            
            # TODO: Implémenter nettoyage
            # - Snapshots > 90 jours
            # - Optimizations > 180 jours
            # - Alerts résolues > 30 jours
            
            pass
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {str(e)}")
    
    # Circuit Breaker Methods
    
    def _check_circuit_breaker(self) -> bool:
        """Vérifier l'état du circuit breaker"""
        if self.circuit_breaker['state'] == 'open':
            if datetime.utcnow() - self.circuit_breaker['last_failure'] > timedelta(seconds=self.circuit_breaker['recovery_timeout']):
                self.circuit_breaker['state'] = 'half_open'
                logger.info("🔄 Circuit breaker moved to HALF_OPEN state")
                return True
            return False
        return True
    
    def _increment_circuit_breaker(self, failure_count: int):
        """Incrémenter le compteur d'échecs du circuit breaker"""
        self.circuit_breaker['failure_count'] += failure_count
        self.circuit_breaker['last_failure'] = datetime.utcnow()
        
        if self.circuit_breaker['failure_count'] >= self.circuit_breaker['failure_threshold']:
            self.circuit_breaker['state'] = 'open'
            logger.warning(f"🔴 Circuit breaker OPENED after {self.circuit_breaker['failure_count']} failures")
    
    def _reset_circuit_breaker(self):
        """Réinitialiser le circuit breaker"""
        if self.circuit_breaker['state'] != 'closed':
            self.circuit_breaker['state'] = 'closed'
            self.circuit_breaker['failure_count'] = 0
            logger.info("✅ Circuit breaker CLOSED - system healthy")
    
    # Helper methods (à implémenter avec le service DB)
    
    async def _get_active_monitoring_jobs(self) -> List[MonitoringJob]:
        """Récupérer tous les jobs de monitoring actifs"""
        # TODO: Implémenter avec le service MongoDB
        return []
    
    async def _save_product_snapshot(self, snapshot: ProductSnapshot):
        """Sauvegarder un snapshot en DB"""
        # TODO: Implémenter avec le service MongoDB
        pass
    
    async def _update_job_last_run(self, job_id: str):
        """Mettre à jour la dernière exécution d'un job"""
        # TODO: Implémenter avec le service MongoDB
        pass
    
    async def _record_job_failure(self, job: MonitoringJob, error: str):
        """Enregistrer l'échec d'un job"""
        # TODO: Implémenter avec le service MongoDB
        pass
    
    async def _update_job_stats(self, processed: int, failed: int, duration: float):
        """Mettre à jour les statistiques globales"""
        self.job_stats['total_runs'] += 1
        self.job_stats['successful_runs'] += processed
        self.job_stats['failed_runs'] += failed
        self.job_stats['last_run'] = datetime.utcnow()
    
    async def _cleanup_expired_jobs(self):
        """Nettoyer les jobs expirés"""
        pass
    
    async def _check_api_health(self):
        """Vérifier la santé des APIs"""
        pass
    
    async def _optimize_performance(self):
        """Optimiser les performances système"""
        pass
    
    async def shutdown(self):
        """Arrêt propre de l'orchestrateur"""
        try:
            logger.info("🛑 Shutting down Amazon Monitoring Orchestrator...")
            
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            
            logger.info("✅ Amazon Monitoring Orchestrator shut down successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")


# Instance globale de l'orchestrateur
monitoring_orchestrator = AmazonMonitoringOrchestrator()