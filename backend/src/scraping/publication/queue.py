"""
Queue et Rate Limiting - Gestion des files de publication et limitation débit par boutique - ECOMSIMPLY
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging

from .dto import PublishTask, PublishBatch, PublicationConfig, PublicationStatus

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket pour rate limiting par store"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Nombre max de tokens
            refill_rate: Tokens ajoutés par seconde
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Consomme des tokens si disponibles
        
        Returns:
            True si tokens consommés, False sinon
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Recharge tokens selon le taux"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def time_until_available(self, tokens: int = 1) -> float:
        """Temps d'attente pour avoir les tokens (secondes)"""
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        needed = tokens - self.tokens
        return needed / self.refill_rate
    
    def get_stats(self) -> Dict[str, float]:
        """Statistiques du bucket"""
        self._refill()
        return {
            'available_tokens': self.tokens,
            'capacity': self.capacity,
            'fill_percentage': (self.tokens / self.capacity) * 100,
            'refill_rate_per_sec': self.refill_rate
        }


class PublishQueue:
    """Queue de publication avec priorité et rate limiting"""
    
    def __init__(self, config: PublicationConfig):
        self.config = config
        
        # Queue principale avec priorité
        self._queue: List[PublishTask] = []
        self._queue_lock = asyncio.Lock()
        
        # Rate limiters par store (Token Bucket)
        self._rate_limiters: Dict[str, TokenBucket] = {}
        
        # Historique pour cooldown par store
        self._last_publication: Dict[str, datetime] = {}
        
        # Statistiques
        self.stats = {
            'tasks_added': 0,
            'tasks_processed': 0,
            'rate_limited_count': 0,
            'queue_depth_max': 0
        }
    
    async def add_task(self, task: PublishTask) -> None:
        """Ajouter tâche à la queue"""
        
        async with self._queue_lock:
            self._queue.append(task)
            # Trier par priorité (1 = urgent, 10 = bas)
            self._queue.sort(key=lambda t: (t.priority, t.created_at))
            
            current_depth = len(self._queue)
            self.stats['queue_depth_max'] = max(self.stats['queue_depth_max'], current_depth)
            self.stats['tasks_added'] += 1
            
            logger.debug(f"Tâche ajoutée à la queue: {task.task_id} (priorité {task.priority}), "
                        f"depth: {current_depth}")
    
    async def add_batch(self, batch: PublishBatch) -> None:
        """Ajouter un batch de tâches"""
        
        for task in batch.tasks:
            await self.add_task(task)
        
        logger.info(f"Batch ajouté: {batch.batch_id} avec {len(batch.tasks)} tâches")
    
    async def get_next_task(self) -> Optional[PublishTask]:
        """
        Récupérer prochaine tâche disponible selon rate limiting
        
        Returns:
            Tâche prête ou None si rate limited
        """
        
        async with self._queue_lock:
            if not self._queue:
                return None
            
            # Chercher première tâche disponible selon rate limits
            for i, task in enumerate(self._queue):
                if await self._can_process_task(task):
                    # Retirer tâche de la queue
                    task = self._queue.pop(i)
                    self.stats['tasks_processed'] += 1
                    
                    # Marquer comme démarrée
                    task.mark_started()
                    
                    # Enregistrer dernière publication pour cooldown
                    self._last_publication[task.store_id] = datetime.now()
                    
                    logger.debug(f"Tâche récupérée: {task.task_id} pour store {task.store_id}")
                    return task
            
            # Aucune tâche disponible → rate limited
            self.stats['rate_limited_count'] += 1
            return None
    
    async def _can_process_task(self, task: PublishTask) -> bool:
        """Vérifier si tâche peut être traitée selon rate limits"""
        
        store_id = task.store_id
        
        # 1. Vérifier fenêtre horaire
        if not self.config.is_active_hours():
            return False
        
        # 2. Vérifier cooldown entre publications
        last_pub = self._last_publication.get(store_id)
        if last_pub:
            time_since_last = datetime.now() - last_pub
            if time_since_last.total_seconds() < self.config.cooldown_between_publications:
                return False
        
        # 3. Vérifier token bucket
        rate_limiter = self._get_rate_limiter(store_id)
        return rate_limiter.consume(1)
    
    def _get_rate_limiter(self, store_id: str) -> TokenBucket:
        """Obtenir rate limiter pour un store (lazy creation)"""
        
        if store_id not in self._rate_limiters:
            # Créer token bucket: capacity = publications/heure, rate = tokens/seconde
            capacity = self.config.max_publications_per_hour
            refill_rate = capacity / 3600.0  # tokens par seconde
            
            self._rate_limiters[store_id] = TokenBucket(capacity, refill_rate)
            logger.debug(f"Rate limiter créé pour store {store_id}: "
                        f"{capacity} tokens, {refill_rate:.4f}/sec")
        
        return self._rate_limiters[store_id]
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Statistiques de la queue"""
        
        async with self._queue_lock:
            queue_depth = len(self._queue)
            
            # Répartition par status
            status_counts = defaultdict(int)
            priority_counts = defaultdict(int)
            store_counts = defaultdict(int)
            
            for task in self._queue:
                status_counts[task.status.value] += 1
                priority_counts[task.priority] += 1
                store_counts[task.store_id] += 1
            
            return {
                **self.stats,
                'current_queue_depth': queue_depth,
                'status_distribution': dict(status_counts),
                'priority_distribution': dict(priority_counts),
                'store_distribution': dict(store_counts),
                'active_rate_limiters': len(self._rate_limiters)
            }
    
    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Statistiques rate limiting par store"""
        
        rate_stats = {}
        for store_id, limiter in self._rate_limiters.items():
            rate_stats[store_id] = {
                **limiter.get_stats(),
                'last_publication': self._last_publication.get(store_id),
                'next_available_in_sec': limiter.time_until_available()
            }
        
        return rate_stats
    
    async def get_next_available_slot(self, store_id: str) -> datetime:
        """Calculer prochain créneau disponible pour un store"""
        
        now = datetime.now()
        
        # Vérifier fenêtre horaire
        if not self.config.is_active_hours():
            next_slot = self.config.calculate_next_slot()
            return next_slot
        
        # Vérifier cooldown
        last_pub = self._last_publication.get(store_id)
        if last_pub:
            cooldown_end = last_pub + timedelta(seconds=self.config.cooldown_between_publications)
            if cooldown_end > now:
                return cooldown_end
        
        # Vérifier rate limiter
        rate_limiter = self._get_rate_limiter(store_id)
        wait_seconds = rate_limiter.time_until_available()
        
        return now + timedelta(seconds=wait_seconds)
    
    async def requeue_task(self, task: PublishTask) -> None:
        """Remettre tâche en queue (échec temporaire)"""
        
        # Reset status
        task.status = PublicationStatus.PENDING
        task.started_at = None
        
        # Baisser priorité pour éviter boucle
        task.priority = min(10, task.priority + 1)
        
        await self.add_task(task)
        logger.warning(f"Tâche remise en queue: {task.task_id} (nouvelle priorité: {task.priority})")


class PublishWorker:
    """Worker pour traiter les tâches de publication"""
    
    def __init__(self, worker_id: str, queue: PublishQueue, 
                 publisher_factory: Callable[[str], Any]):
        """
        Args:
            worker_id: ID unique du worker
            queue: Queue de tâches
            publisher_factory: Factory pour créer publishers par store_type
        """
        self.worker_id = worker_id
        self.queue = queue
        self.publisher_factory = publisher_factory
        
        self.is_running = False
        self.current_task: Optional[PublishTask] = None
        
        # Statistiques worker
        self.stats = {
            'tasks_processed': 0,
            'tasks_successful': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'start_time': None
        }
    
    async def start(self):
        """Démarrer worker"""
        
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        logger.info(f"🔄 Worker {self.worker_id} démarré")
        
        while self.is_running:
            try:
                # Récupérer prochaine tâche
                task = await self.queue.get_next_task()
                
                if task:
                    await self._process_task(task)
                else:
                    # Pas de tâche disponible → attendre
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Erreur worker {self.worker_id}: {e}")
                await asyncio.sleep(10)  # Pause avant retry
    
    async def stop(self):
        """Arrêter worker"""
        self.is_running = False
        logger.info(f"⏹️  Worker {self.worker_id} arrêté")
    
    async def _process_task(self, task: PublishTask):
        """Traiter une tâche de publication"""
        
        self.current_task = task
        start_time = time.time()
        
        try:
            logger.info(f"📤 Worker {self.worker_id} traite: {task.task_id}")
            
            # Obtenir publisher pour le type de store
            publisher = self.publisher_factory(task.store_type.value)
            if not publisher:
                raise ValueError(f"Publisher non trouvé pour type: {task.store_type}")
            
            # Publication via transport robuste
            result = await publisher.publish_product(task)
            
            # Marquer succès
            task.mark_success(result)
            self.stats['tasks_successful'] += 1
            
            duration = time.time() - start_time
            logger.info(f"✅ Tâche {task.task_id} réussie en {duration:.2f}s")
            
        except Exception as e:
            # Marquer échec
            task.mark_failed(str(e))
            self.stats['tasks_failed'] += 1
            
            duration = time.time() - start_time
            logger.error(f"❌ Tâche {task.task_id} échouée après {duration:.2f}s: {e}")
            
            # Réessayer si éligible
            if task.is_retryable():
                await asyncio.sleep(60)  # Attendre avant requeue
                await self.queue.requeue_task(task)
        
        finally:
            processing_time = time.time() - start_time
            self.stats['tasks_processed'] += 1
            self.stats['total_processing_time'] += processing_time
            self.current_task = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du worker"""
        
        uptime = 0.0
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
        
        avg_processing_time = 0.0
        if self.stats['tasks_processed'] > 0:
            avg_processing_time = self.stats['total_processing_time'] / self.stats['tasks_processed']
        
        return {
            **self.stats,
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'avg_processing_time': avg_processing_time,
            'current_task_id': self.current_task.task_id if self.current_task else None
        }