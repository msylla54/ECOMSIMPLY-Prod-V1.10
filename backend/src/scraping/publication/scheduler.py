"""
Scheduler - Gestion fenêtres horaires, cooldown et planification - ECOMSIMPLY
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import logging

from .dto import PublishTask, PublicationConfig, PublicationStatus
from .constants import STORES, STORE_RATE_LIMITS

logger = logging.getLogger(__name__)


class PublicationScheduler:
    """Planificateur de publications avec fenêtres horaires et cooldown"""
    
    def __init__(self, config: PublicationConfig):
        """
        Args:
            config: Configuration publication
        """
        self.config = config
        
        # Historique des publications par store
        self._publication_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Prochains créneaux disponibles par store
        self._next_available_slots: Dict[str, datetime] = {}
        
        # Callbacks pour notifications
        self._slot_callbacks: List[Callable] = []
        
        # Statistiques
        self.stats = {
            'total_scheduled': 0,
            'scheduled_by_store': defaultdict(int),
            'slots_calculated': 0,
            'cooldown_enforced': 0,
            'outside_hours_delayed': 0
        }
    
    def is_active_hours(self, check_time: Optional[datetime] = None) -> bool:
        """
        Vérifie si on est dans les heures actives
        
        Args:
            check_time: Heure à vérifier (défaut: maintenant)
            
        Returns:
            True si dans les heures actives
        """
        
        if check_time is None:
            check_time = datetime.now()
        
        current_hour = check_time.hour
        return self.config.active_hours_start <= current_hour <= self.config.active_hours_end
    
    def can_publish_now(self, store_id: str) -> bool:
        """
        Vérifie si publication immédiate possible pour un store
        
        Args:
            store_id: ID du store
            
        Returns:
            True si publication possible maintenant
        """
        
        now = datetime.now()
        
        # 1. Vérifier fenêtre horaire
        if not self.is_active_hours(now):
            return False
        
        # 2. Vérifier cooldown store
        if self._is_in_cooldown(store_id, now):
            return False
        
        # 3. Vérifier rate limiting horaire
        if self._is_rate_limited(store_id, now):
            return False
        
        return True
    
    def get_next_available_slot(self, store_id: str) -> datetime:
        """
        Calcule prochain créneau disponible pour un store
        
        Args:
            store_id: ID du store
            
        Returns:
            Datetime du prochain créneau disponible
        """
        
        self.stats['slots_calculated'] += 1
        
        now = datetime.now()
        candidate_slot = now
        
        # 1. Appliquer cooldown si nécessaire
        if self._is_in_cooldown(store_id, candidate_slot):
            last_pub = self._get_last_publication_time(store_id)
            if last_pub:
                candidate_slot = last_pub + timedelta(seconds=self.config.cooldown_between_publications)
                self.stats['cooldown_enforced'] += 1
        
        # 2. Vérifier fenêtre horaire
        if not self.is_active_hours(candidate_slot):
            candidate_slot = self._get_next_active_hours_start(candidate_slot)
            self.stats['outside_hours_delayed'] += 1
        
        # 3. Vérifier rate limiting
        if self._is_rate_limited(store_id, candidate_slot):
            # Ajouter délai pour respecter rate limit
            publications_last_hour = self._count_publications_last_hour(store_id, candidate_slot)
            max_per_hour = STORE_RATE_LIMITS.get(store_id, self.config.max_publications_per_hour)
            
            if publications_last_hour >= max_per_hour:
                # Attendre jusqu'à ce qu'une publication sorte de la fenêtre d'1h
                oldest_in_hour = self._get_oldest_publication_in_hour(store_id, candidate_slot)
                if oldest_in_hour:
                    candidate_slot = oldest_in_hour + timedelta(hours=1, seconds=1)
        
        # 4. Re-vérifier fenêtre horaire après ajustement rate limit
        if not self.is_active_hours(candidate_slot):
            candidate_slot = self._get_next_active_hours_start(candidate_slot)
        
        # 5. Mettre en cache
        self._next_available_slots[store_id] = candidate_slot
        
        logger.debug(f"⏰ Prochain créneau {store_id}: {candidate_slot.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return candidate_slot
    
    def schedule_task(self, task: PublishTask) -> datetime:
        """
        Planifie une tâche de publication
        
        Args:
            task: Tâche à planifier
            
        Returns:
            Datetime de publication planifiée
        """
        
        self.stats['total_scheduled'] += 1
        self.stats['scheduled_by_store'][task.store_id] += 1
        
        scheduled_time = self.get_next_available_slot(task.store_id)
        
        logger.info(f"📅 Tâche planifiée {task.task_id} pour {task.store_id} "
                   f"à {scheduled_time.strftime('%H:%M:%S')}")
        
        # Notifier callbacks
        for callback in self._slot_callbacks:
            try:
                callback(task, scheduled_time)
            except Exception as e:
                logger.warning(f"Erreur callback scheduler: {e}")
        
        return scheduled_time
    
    def record_publication(self, store_id: str, publication_time: Optional[datetime] = None):
        """
        Enregistre une publication effectuée
        
        Args:
            store_id: ID du store
            publication_time: Heure de publication (défaut: maintenant)
        """
        
        if publication_time is None:
            publication_time = datetime.now()
        
        self._publication_history[store_id].append(publication_time)
        
        # Nettoyer cache créneau suivant
        self._next_available_slots.pop(store_id, None)
        
        logger.debug(f"📝 Publication enregistrée {store_id} à {publication_time.strftime('%H:%M:%S')}")
    
    def get_store_schedule_status(self, store_id: str) -> Dict[str, Any]:
        """
        Status de planification pour un store
        
        Args:
            store_id: ID du store
            
        Returns:
            Dict avec status détaillé
        """
        
        now = datetime.now()
        
        return {
            'store_id': store_id,
            'can_publish_now': self.can_publish_now(store_id),
            'is_active_hours': self.is_active_hours(now),
            'is_in_cooldown': self._is_in_cooldown(store_id, now),
            'is_rate_limited': self._is_rate_limited(store_id, now),
            'next_available_slot': self.get_next_available_slot(store_id),
            'publications_last_hour': self._count_publications_last_hour(store_id, now),
            'max_publications_per_hour': STORE_RATE_LIMITS.get(store_id, self.config.max_publications_per_hour),
            'last_publication': self._get_last_publication_time(store_id),
            'total_publications': len(self._publication_history[store_id])
        }
    
    def get_all_stores_schedule(self) -> Dict[str, Dict[str, Any]]:
        """Status de planification pour tous les stores"""
        
        return {store: self.get_store_schedule_status(store) for store in STORES}
    
    def add_slot_callback(self, callback: Callable):
        """Ajoute callback pour notifications de créneaux"""
        self._slot_callbacks.append(callback)
    
    def _is_in_cooldown(self, store_id: str, check_time: datetime) -> bool:
        """Vérifie si store est en cooldown"""
        
        last_pub = self._get_last_publication_time(store_id)
        if not last_pub:
            return False
        
        elapsed = check_time - last_pub
        return elapsed.total_seconds() < self.config.cooldown_between_publications
    
    def _is_rate_limited(self, store_id: str, check_time: datetime) -> bool:
        """Vérifie si store atteint sa limite de publications/heure"""
        
        publications_count = self._count_publications_last_hour(store_id, check_time)
        max_per_hour = STORE_RATE_LIMITS.get(store_id, self.config.max_publications_per_hour)
        
        return publications_count >= max_per_hour
    
    def _get_last_publication_time(self, store_id: str) -> Optional[datetime]:
        """Dernière publication pour un store"""
        
        history = self._publication_history[store_id]
        return history[-1] if history else None
    
    def _count_publications_last_hour(self, store_id: str, from_time: datetime) -> int:
        """Compte publications dans la dernière heure"""
        
        one_hour_ago = from_time - timedelta(hours=1)
        history = self._publication_history[store_id]
        
        return sum(1 for pub_time in history if pub_time >= one_hour_ago)
    
    def _get_oldest_publication_in_hour(self, store_id: str, from_time: datetime) -> Optional[datetime]:
        """Publication la plus ancienne dans l'heure écoulée"""
        
        one_hour_ago = from_time - timedelta(hours=1)
        history = self._publication_history[store_id]
        
        publications_in_hour = [pub_time for pub_time in history if pub_time >= one_hour_ago]
        
        return min(publications_in_hour) if publications_in_hour else None
    
    def _get_next_active_hours_start(self, from_time: datetime) -> datetime:
        """Calcule prochaine heure de début de fenêtre active"""
        
        # Si on est le même jour mais après les heures actives
        if from_time.hour > self.config.active_hours_end:
            # Lendemain à l'heure de début
            next_day = from_time + timedelta(days=1)
            return next_day.replace(
                hour=self.config.active_hours_start,
                minute=0,
                second=0,
                microsecond=0
            )
        
        # Si on est avant les heures actives le même jour
        if from_time.hour < self.config.active_hours_start:
            return from_time.replace(
                hour=self.config.active_hours_start,
                minute=0,
                second=0,
                microsecond=0
            )
        
        # Sinon on est déjà dans les heures actives
        return from_time
    
    async def wait_for_next_slot(self, store_id: str) -> datetime:
        """Attend le prochain créneau disponible (async)"""
        
        next_slot = self.get_next_available_slot(store_id)
        now = datetime.now()
        
        if next_slot > now:
            wait_seconds = (next_slot - now).total_seconds()
            logger.info(f"⏳ Attente {wait_seconds:.0f}s pour créneau {store_id}")
            await asyncio.sleep(wait_seconds)
        
        return next_slot
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Statistiques complètes du scheduler"""
        
        total_publications = sum(len(history) for history in self._publication_history.values())
        
        return {
            **self.stats,
            'total_publications_recorded': total_publications,
            'stores_with_history': len(self._publication_history),
            'cached_next_slots': len(self._next_available_slots),
            'active_callbacks': len(self._slot_callbacks),
            'config': {
                'active_hours': f"{self.config.active_hours_start}h-{self.config.active_hours_end}h",
                'cooldown_seconds': self.config.cooldown_between_publications,
                'default_max_per_hour': self.config.max_publications_per_hour
            }
        }