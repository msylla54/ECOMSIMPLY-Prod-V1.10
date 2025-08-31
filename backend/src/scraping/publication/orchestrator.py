"""
Orchestrateur Principal - Publication Automatique Multi-Stores ECOMSIMPLY
Coordonne queue, scheduler, guardrails, et publishers pour toutes les plateformes
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import logging

from ..semantic import ProductDTO
from .dto import PublishTask, PublishBatch, PublicationConfig, PublicationStatus, StoreType
from .queue import PublishQueue, PublishWorker
from .scheduler import PublicationScheduler
from .guardrails import GuardRailEngine
from .idempotency import IdempotencyManager
from .publishers import get_all_publishers, IdempotencyStore
from .constants import STORES, DEFAULT_PUBLICATION_CONFIG

logger = logging.getLogger(__name__)


class PublicationOrchestrator:
    """Orchestrateur principal pour publication multi-stores"""
    
    def __init__(self, config: Optional[PublicationConfig] = None):
        """
        Args:
            config: Configuration publication (défaut depuis constants)
        """
        # Configuration
        if config is None:
            config = PublicationConfig(**DEFAULT_PUBLICATION_CONFIG)
        self.config = config
        
        # Composants principaux
        self.scheduler = PublicationScheduler(config)
        self.guardrails = GuardRailEngine(
            price_variance_threshold=config.price_variance_threshold,
            min_confidence=config.min_confidence_score
        )
        self.idempotency_manager = IdempotencyManager()
        
        # Publishers pour tous les stores
        self.idem_store = IdempotencyStore()
        self.publishers = get_all_publishers(self.idem_store)
        
        # Queue et workers
        self.queue = PublishQueue(config)
        self.workers: Dict[str, PublishWorker] = {}
        self.is_running = False
        
        # État des publications
        self.active_publications: Set[str] = set()  # task_ids en cours
        self.completed_tasks: List[PublishTask] = []
        self.failed_tasks: List[PublishTask] = []
        self.duplicate_tasks: List[PublishTask] = []
        
        # Statistiques globales
        self.stats = {
            'orchestrator_start_time': time.time(),
            'total_enqueued': 0,
            'total_processed': 0,
            'total_successful': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'total_skipped_guardrails': 0,
            'total_skipped_duplicate': 0,
            'processing_time_total': 0.0,
            'by_store': defaultdict(lambda: {
                'enqueued': 0, 'successful': 0, 'failed': 0, 'skipped': 0
            })
        }
    
    async def enqueue(self, product: ProductDTO, store_id: str, 
                     priority: int = 5, publish_options: Optional[Dict] = None) -> str:
        """
        Met en queue une publication pour un store spécifique
        
        Args:
            product: ProductDTO à publier
            store_id: ID du store cible (doit être dans STORES)
            priority: Priorité 1-10 (1=urgent)
            publish_options: Options spécifiques publication
            
        Returns:
            task_id généré
            
        Raises:
            ValueError: Si store_id non supporté
        """
        
        if store_id not in STORES:
            raise ValueError(f"Store '{store_id}' non supporté. Stores disponibles: {STORES}")
        
        # Génération task_id unique
        task_id = f"{store_id}_{uuid.uuid4().hex[:8]}"
        
        # Conversion store_id en StoreType
        store_type = StoreType(store_id)
        
        # Créer la tâche
        task = PublishTask(
            task_id=task_id,
            store_id=store_id,
            store_type=store_type,
            product_dto=product,
            priority=priority,
            publish_options=publish_options or {}
        )
        
        # Vérification idempotence AVANT mise en queue
        idempotency_key = self.idempotency_manager.generate_idempotency_key(store_id, product)
        if await self.idempotency_manager.exists(idempotency_key):
            # Marquer comme doublon mais garder dans une liste pour récupération
            task.status = PublicationStatus.SKIPPED_DUPLICATE
            task.error_message = f"Doublon détecté: {idempotency_key[:8]}"
            self.duplicate_tasks.append(task)
            
            logger.info(f"🔄 Doublon détecté {task_id}: {product.title[:30]}...")
            
            # Statistiques
            self.stats['total_enqueued'] += 1
            self.stats['total_skipped'] += 1
            self.stats['total_skipped_duplicate'] += 1  # Ajouté
            self.stats['by_store'][store_id]['enqueued'] += 1
            self.stats['by_store'][store_id]['skipped'] += 1
            
            return task_id
        
        # Si pas de doublon, ajouter à la queue normale
        await self.queue.add_task(task)
        
        # Statistiques
        self.stats['total_enqueued'] += 1
        self.stats['by_store'][store_id]['enqueued'] += 1
        
        logger.info(f"📥 Tâche {task_id} mise en queue pour {store_id} "
                   f"(priorité: {priority}, produit: {product.title[:30]}...)")
        
        return task_id
    
    async def enqueue_batch(self, products: List[ProductDTO], store_id: str,
                           batch_priority: int = 5) -> PublishBatch:
        """
        Met en queue un batch de produits pour un store
        
        Args:
            products: Liste ProductDTO à publier
            store_id: Store cible
            batch_priority: Priorité du batch
            
        Returns:
            PublishBatch créé
        """
        
        if not products:
            raise ValueError("Liste produits vide")
        
        batch_id = f"batch_{store_id}_{uuid.uuid4().hex[:8]}"
        tasks = []
        
        for i, product in enumerate(products):
            # Créer la tâche directement
            task_id = f"{store_id}_{uuid.uuid4().hex[:8]}"
            store_type = StoreType(store_id)
            
            task = PublishTask(
                task_id=task_id,
                store_id=store_id,
                store_type=store_type,
                product_dto=product,
                priority=batch_priority,
                publish_options={'batch_id': batch_id, 'batch_position': i}
            )
            
            # Ajouter à la queue
            await self.queue.add_task(task)
            
            # Ajouter à la liste des tâches du batch
            tasks.append(task)
            
            # Statistiques
            self.stats['total_enqueued'] += 1
            self.stats['by_store'][store_id]['enqueued'] += 1
        
        batch = PublishBatch(
            batch_id=batch_id,
            tasks=tasks
        )
        batch.update_stats()
        
        logger.info(f"📦 Batch {batch_id} créé avec {len(tasks)} tâches pour {store_id}")
        
        return batch
    
    async def work_once(self) -> Optional[PublishTask]:
        """
        Traite une tâche de publication complète
        
        Returns:
            Tâche traitée ou None si aucune disponible
        """
        
        # 1. Vérifier d'abord les tâches doublons (retour immédiat)
        if self.duplicate_tasks:
            task = self.duplicate_tasks.pop(0)
            logger.info(f"🔄 Retour tâche doublon: {task.task_id}")
            return task
        
        # 2. Récupérer prochaine tâche selon rate limits
        task = await self.queue.get_next_task()
        if not task:
            return None
        
        start_time = time.time()
        self.active_publications.add(task.task_id)
        
        try:
            logger.info(f"⚙️  Traitement tâche {task.task_id} pour {task.store_id}")
            
            # 2. Vérification guardrails
            can_publish, blocking_reason, guardrail_analysis = self.guardrails.validate_publication(task)
            
            if not can_publish:
                task.mark_skipped(f"Guardrails: {blocking_reason}")
                self.failed_tasks.append(task)
                self.stats['total_skipped_guardrails'] += 1
                self.stats['by_store'][task.store_id]['skipped'] += 1
                
                logger.warning(f"🚫 Tâche {task.task_id} bloquée par guardrails: {blocking_reason}")
                return task
            
            # 3. Génération clé idempotence
            idempotency_key = self.idempotency_manager.generate_idempotency_key(
                task.store_id, task.product_dto
            )
            
            # 4. Vérification doublons
            if await self.idempotency_manager.exists(idempotency_key):
                task.mark_skipped(f"Duplicate: {idempotency_key}")
                self.failed_tasks.append(task)
                self.stats['total_skipped_duplicate'] += 1
                self.stats['by_store'][task.store_id]['skipped'] += 1
                
                logger.warning(f"♻️  Tâche {task.task_id} ignorée (doublon)")
                return task
            
            # 5. Vérification scheduling (fenêtre horaire, cooldown)
            if not self.scheduler.can_publish_now(task.store_id):
                next_slot = self.scheduler.get_next_available_slot(task.store_id)
                logger.info(f"⏰ Tâche {task.task_id} reportée à {next_slot.strftime('%H:%M:%S')}")
                
                # Marquer la tâche comme en attente et la retourner
                task.status = PublicationStatus.PENDING
                task.error_message = f"Cooldown/fenêtre horaire - reporté à {next_slot.strftime('%H:%M:%S')}"
                
                # Remettre en queue pour plus tard (optionnel en production)
                await self.queue.requeue_task(task)
                return task
            
            # 6. Publication via publisher approprié
            publisher = self.publishers.get(task.store_id)
            if not publisher:
                raise ValueError(f"Publisher non trouvé pour {task.store_id}")
            
            publish_result = await publisher.publish(
                task.product_dto,
                idempotency_key=idempotency_key
            )
            
            # 7. Traitement résultat
            if publish_result.success:
                # Succès
                task.mark_success({
                    'external_id': publish_result.external_id,
                    'store_response': publish_result.metadata,
                    'guardrail_analysis': guardrail_analysis,
                    'duration_ms': publish_result.duration_ms
                })
                
                self.completed_tasks.append(task)
                self.stats['total_successful'] += 1
                self.stats['by_store'][task.store_id]['successful'] += 1
                
                # Sauvegarder idempotence
                await self.idempotency_manager.store(
                    idempotency_key, task.store_id, task.product_dto,
                    {'external_id': publish_result.external_id, 'task_id': task.task_id}
                )
                
                # Enregistrer publication dans scheduler
                self.scheduler.record_publication(task.store_id)
                
                logger.info(f"✅ Publication réussie {task.task_id}: {publish_result.external_id}")
                
            else:
                # Échec
                task.mark_failed(f"Publisher error: {publish_result.message}")
                self.failed_tasks.append(task)
                self.stats['total_failed'] += 1
                self.stats['by_store'][task.store_id]['failed'] += 1
                
                logger.error(f"❌ Publication échouée {task.task_id}: {publish_result.message}")
            
            return task
            
        except Exception as e:
            # Erreur inattendue
            task.mark_failed(f"Unexpected error: {str(e)}")
            self.failed_tasks.append(task)
            self.stats['total_failed'] += 1
            self.stats['by_store'][task.store_id]['failed'] += 1
            
            logger.error(f"💥 Erreur inattendue tâche {task.task_id}: {e}")
            return task
            
        finally:
            # Nettoyage
            processing_time = time.time() - start_time
            self.stats['total_processed'] += 1
            self.stats['processing_time_total'] += processing_time
            self.active_publications.discard(task.task_id)
    
    async def start_workers(self) -> None:
        """Démarre les workers pour traitement automatique"""
        
        if self.is_running:
            logger.warning("Workers déjà démarrés")
            return
        
        self.is_running = True
        logger.info(f"🚀 Démarrage {self.config.max_concurrent_workers} workers")
        
        # Créer workers
        for i in range(self.config.max_concurrent_workers):
            worker_id = f"worker_{i+1}"
            
            async def worker_loop(worker_id=worker_id):
                """Boucle principale worker"""
                logger.info(f"🔄 Worker {worker_id} démarré")
                
                while self.is_running:
                    try:
                        task = await self.work_once()
                        if not task:
                            await asyncio.sleep(5)  # Pas de tâche → attendre
                    except Exception as e:
                        logger.error(f"Erreur worker {worker_id}: {e}")
                        await asyncio.sleep(10)  # Pause sur erreur
                
                logger.info(f"⏹️  Worker {worker_id} arrêté")
            
            # Démarrer worker async
            asyncio.create_task(worker_loop())
    
    async def stop_workers(self) -> None:
        """Arrête tous les workers"""
        
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("⏹️  Arrêt workers en cours...")
        
        # Attendre fin des publications en cours
        max_wait = 30  # 30s max
        waited = 0
        
        while self.active_publications and waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
        
        if self.active_publications:
            logger.warning(f"Publications encore actives après {max_wait}s: {self.active_publications}")
        
        logger.info("✅ Workers arrêtés")
    
    async def _find_task_by_id(self, task_id: str) -> Optional[PublishTask]:
        """Trouve une tâche par son ID (helper)"""
        
        # Rechercher dans les tâches créées
        for task in self.completed_tasks + self.failed_tasks:
            if task.task_id == task_id:
                return task
        
        # Si pas trouvée, créer une tâche simulée pour les besoins du batch
        # En production, ceci devrait être géré différemment
        return None
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Statistiques complètes orchestrateur"""
        
        uptime = time.time() - self.stats['orchestrator_start_time']
        
        # Statistiques composants
        async def get_queue_stats_safe():
            try:
                return await self.queue.get_queue_stats()
            except:
                return {}
        
        async def get_idempotency_stats_safe():
            try:
                return await self.idempotency_manager.get_stats()
            except:
                return {}
        
        # Exécuter les fonctions async de manière sécurisée
        try:
            queue_stats = await get_queue_stats_safe()
            idempotency_stats = await get_idempotency_stats_safe()
        except:
            queue_stats = {}
            idempotency_stats = {}
            
        scheduler_stats = self.scheduler.get_scheduler_stats()
        guardrails_stats = self.guardrails.get_validation_stats()
        
        # Statistiques publishers
        publisher_stats = {}
        for store_id, publisher in self.publishers.items():
            publisher_stats[store_id] = publisher.get_stats()
        
        return {
            'orchestrator': {
                **self.stats,
                'uptime_seconds': uptime,
                'is_running': self.is_running,
                'active_publications': len(self.active_publications),
                'completed_tasks': len(self.completed_tasks),
                'failed_tasks': len(self.failed_tasks),
                'avg_processing_time': (
                    self.stats['processing_time_total'] / self.stats['total_processed']
                    if self.stats['total_processed'] > 0 else 0.0
                )
            },
            'components': {
                'queue': queue_stats,
                'scheduler': scheduler_stats,
                'guardrails': guardrails_stats,
                'idempotency': idempotency_stats
            },
            'publishers': publisher_stats,
            'supported_stores': STORES
        }
    
    def get_store_summary(self, store_id: str) -> Dict[str, Any]:
        """Résumé complet pour un store spécifique"""
        
        if store_id not in STORES:
            raise ValueError(f"Store '{store_id}' non supporté")
        
        # Stats scheduler pour ce store
        schedule_status = self.scheduler.get_store_schedule_status(store_id)
        
        # Stats publisher pour ce store
        publisher = self.publishers.get(store_id)
        publisher_stats = publisher.get_stats() if publisher else {}
        
        # Stats orchestrateur pour ce store
        orchestrator_stats = self.stats['by_store'][store_id]
        
        return {
            'store_id': store_id,
            'orchestrator_stats': orchestrator_stats,
            'schedule_status': schedule_status,
            'publisher_stats': publisher_stats,
            'can_publish_now': schedule_status['can_publish_now'],
            'next_available_slot': schedule_status['next_available_slot']
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check santé complet de l'orchestrateur"""
        
        health_status = {
            'orchestrator': {
                'status': 'healthy' if self.is_running else 'stopped',
                'uptime': time.time() - self.stats['orchestrator_start_time'],
                'active_publications': len(self.active_publications)
            },
            'stores': {}
        }
        
        # Check santé de chaque publisher
        for store_id, publisher in self.publishers.items():
            try:
                store_health = await publisher.health_check()
                health_status['stores'][store_id] = store_health
            except Exception as e:
                health_status['stores'][store_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status