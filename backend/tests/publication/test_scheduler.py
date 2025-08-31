"""
Tests pour Scheduler - Fenêtres horaires et cooldown multi-stores
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Import modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.publication.scheduler import PublicationScheduler
from scraping.publication.dto import PublicationConfig, PublishTask, StoreType
from scraping.publication.constants import STORES, STORE_RATE_LIMITS
from scraping.semantic.product_dto import ProductDTO, ImageDTO, PriceDTO, Currency
from decimal import Decimal


class TestPublicationScheduler:
    """Tests pour PublicationScheduler"""
    
    @pytest.fixture
    def config(self):
        return PublicationConfig(
            active_hours_start=8,
            active_hours_end=20,
            cooldown_between_publications=300,  # 5 minutes
            max_publications_per_hour=10
        )
    
    @pytest.fixture
    def scheduler(self, config):
        return PublicationScheduler(config)
    
    @pytest.fixture
    def sample_task(self):
        """Tâche exemple pour tests"""
        product = ProductDTO(
            title="Test Scheduler Product",
            description_html="<p>Test scheduler</p>",
            images=[ImageDTO(url="https://test.com/img.webp", alt="Test image")],
            source_url="https://test.com/product",
            payload_signature="scheduler_test_sig",
            extraction_timestamp=1703001234.567
        )
        
        return PublishTask(
            task_id="scheduler_test_task",
            store_id="shopify",
            store_type=StoreType.SHOPIFY,
            product_dto=product
        )
    
    def test_active_hours_detection(self, scheduler):
        """Test détection heures actives"""
        
        # Dans les heures actives (10h)
        active_time = datetime.now().replace(hour=10, minute=0, second=0)
        assert scheduler.is_active_hours(active_time) is True
        
        # Heure de début (8h)
        start_time = datetime.now().replace(hour=8, minute=0, second=0)
        assert scheduler.is_active_hours(start_time) is True
        
        # Heure de fin (20h)
        end_time = datetime.now().replace(hour=20, minute=0, second=0)
        assert scheduler.is_active_hours(end_time) is True
        
        # Hors heures actives (6h)
        inactive_time = datetime.now().replace(hour=6, minute=0, second=0)
        assert scheduler.is_active_hours(inactive_time) is False
        
        # Hors heures actives (22h)
        late_time = datetime.now().replace(hour=22, minute=0, second=0)
        assert scheduler.is_active_hours(late_time) is False
    
    @pytest.mark.parametrize("store_id", STORES[:3])  # Test sur 3 stores
    def test_can_publish_now_all_stores(self, scheduler, store_id):
        """Test can_publish_now pour différents stores"""
        
        # Mock heure active
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=10, minute=0)
            
            # Premier appel → devrait pouvoir publier
            assert scheduler.can_publish_now(store_id) is True
    
    @pytest.mark.parametrize("store_id", STORES[:2])
    def test_cooldown_enforcement(self, scheduler, store_id):
        """Test application cooldown pour différents stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # Heure active
            base_time = datetime.now().replace(hour=10, minute=0, second=0)
            mock_dt.now.return_value = base_time
            
            # Enregistrer publication
            scheduler.record_publication(store_id, base_time)
            
            # Immédiatement après → en cooldown
            mock_dt.now.return_value = base_time + timedelta(seconds=60)  # 1 minute après
            assert scheduler.can_publish_now(store_id) is False
            
            # Après cooldown → peut publier
            mock_dt.now.return_value = base_time + timedelta(seconds=350)  # 5+ minutes après
            assert scheduler.can_publish_now(store_id) is True
    
    @pytest.mark.parametrize("store_id", STORES[:2])
    def test_rate_limiting_per_store(self, scheduler, store_id):
        """Test rate limiting par store"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            base_time = datetime.now().replace(hour=10, minute=0)
            mock_dt.now.return_value = base_time
            
            # Remplir limite publications/heure pour ce store
            max_per_hour = STORE_RATE_LIMITS.get(store_id, scheduler.config.max_publications_per_hour)
            
            for i in range(max_per_hour):
                pub_time = base_time + timedelta(minutes=i)
                scheduler.record_publication(store_id, pub_time)
            
            # Dépasser limite → rate limited
            mock_dt.now.return_value = base_time + timedelta(minutes=max_per_hour)
            assert scheduler.can_publish_now(store_id) is False
    
    def test_different_stores_independent_cooldown(self, scheduler):
        """Test indépendance cooldown entre stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            base_time = datetime.now().replace(hour=12, minute=0)
            mock_dt.now.return_value = base_time
            
            store1, store2 = STORES[0], STORES[1]  # Prendre 2 stores différents
            
            # Publication sur store1 seulement
            scheduler.record_publication(store1, base_time)
            
            # 1 minute après
            mock_dt.now.return_value = base_time + timedelta(minutes=1)
            
            # Store1 en cooldown, store2 disponible
            assert scheduler.can_publish_now(store1) is False
            assert scheduler.can_publish_now(store2) is True
    
    @pytest.mark.parametrize("store_id", STORES[:3])
    def test_schedule_task_all_stores(self, scheduler, store_id):
        """Test planification tâche pour différents stores"""
        
        # Créer tâche pour store spécifique
        product = ProductDTO(
            title=f"Product for {store_id}",
            description_html="<p>Test</p>",
            images=[ImageDTO(url="https://test.com/img.webp", alt="Test")],
            source_url="https://test.com/product",
            payload_signature=f"sig_{store_id}",
            extraction_timestamp=1703001234.567
        )
        
        task = PublishTask(
            task_id=f"task_{store_id}",
            store_id=store_id,
            store_type=StoreType(store_id),
            product_dto=product
        )
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=10, minute=0)
            
            scheduled_time = scheduler.schedule_task(task)
            
            assert isinstance(scheduled_time, datetime)
            assert scheduled_time >= mock_dt.now.return_value
    
    def test_get_next_available_slot_outside_hours(self, scheduler):
        """Test calcul créneau hors heures actives"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # 6h du matin (hors heures)
            early_time = datetime.now().replace(hour=6, minute=0, second=0)
            mock_dt.now.return_value = early_time
            
            next_slot = scheduler.get_next_available_slot("shopify")
            
            # Devrait être reporté à 8h
            assert next_slot.hour == 8
            assert next_slot.minute == 0
            assert next_slot.date() == early_time.date()
    
    def test_get_next_available_slot_late_evening(self, scheduler):
        """Test calcul créneau le soir après heures"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # 22h le soir (après 20h)
            late_time = datetime.now().replace(hour=22, minute=0, second=0)
            mock_dt.now.return_value = late_time
            
            next_slot = scheduler.get_next_available_slot("woocommerce")
            
            # Devrait être reporté au lendemain 8h
            assert next_slot.hour == 8
            assert next_slot.minute == 0
            assert next_slot.date() == (late_time + timedelta(days=1)).date()
    
    def test_store_schedule_status_complete(self, scheduler):
        """Test status complet pour un store"""
        
        store_id = "prestashop"
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=14, minute=30)
            
            status = scheduler.get_store_schedule_status(store_id)
            
            # Vérifier structure complète
            assert status['store_id'] == store_id
            assert isinstance(status['can_publish_now'], bool)
            assert isinstance(status['is_active_hours'], bool)
            assert isinstance(status['is_in_cooldown'], bool)
            assert isinstance(status['is_rate_limited'], bool)
            assert isinstance(status['next_available_slot'], datetime)
            assert isinstance(status['publications_last_hour'], int)
            assert isinstance(status['max_publications_per_hour'], int)
            assert status['total_publications'] >= 0
    
    def test_all_stores_schedule(self, scheduler):
        """Test status pour tous les stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=15, minute=0)
            
            all_status = scheduler.get_all_stores_schedule()
            
            assert len(all_status) == len(STORES)
            
            for store in STORES:
                assert store in all_status
                status = all_status[store]
                assert status['store_id'] == store
                assert 'can_publish_now' in status
                assert 'next_available_slot' in status
    
    @pytest.mark.asyncio
    async def test_wait_for_next_slot(self, scheduler):
        """Test attente asynchrone pour créneau"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # Maintenant
            now = datetime.now().replace(hour=10, minute=0, second=0)
            mock_dt.now.return_value = now
            
            # Prochain slot dans 1 seconde (pour test rapide)
            with patch.object(scheduler, 'get_next_available_slot') as mock_slot:
                mock_slot.return_value = now + timedelta(seconds=1)
                
                start_time = datetime.now()
                result = await scheduler.wait_for_next_slot("bigcommerce")
                end_time = datetime.now()
                
                # Devrait avoir attendu ~1 seconde
                elapsed = (end_time - start_time).total_seconds()
                assert 0.8 <= elapsed <= 1.5  # Tolérance pour timing
                assert isinstance(result, datetime)
    
    def test_scheduler_stats(self, scheduler):
        """Test statistiques scheduler"""
        
        # Ajouter quelques publications
        for store in STORES[:3]:
            scheduler.record_publication(store)
            scheduler.get_next_available_slot(store)  # Incrémente stats slots
        
        stats = scheduler.get_scheduler_stats()
        
        # Vérifier structure stats
        assert 'total_scheduled' in stats
        assert 'slots_calculated' in stats
        assert 'total_publications_recorded' in stats
        assert 'stores_with_history' in stats
        assert 'config' in stats
        
        assert stats['total_publications_recorded'] == 3
        assert stats['stores_with_history'] == 3
        assert stats['slots_calculated'] >= 3
    
    def test_callback_notifications(self, scheduler, sample_task):
        """Test callbacks notifications créneaux"""
        
        callback_calls = []
        
        def test_callback(task, scheduled_time):
            callback_calls.append({'task_id': task.task_id, 'time': scheduled_time})
        
        scheduler.add_slot_callback(test_callback)
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=11, minute=0)
            
            # Planifier tâche
            scheduler.schedule_task(sample_task)
            
            # Callback devrait avoir été appelé
            assert len(callback_calls) == 1
            assert callback_calls[0]['task_id'] == sample_task.task_id
            assert isinstance(callback_calls[0]['time'], datetime)
    
    def test_publication_history_management(self, scheduler):
        """Test gestion historique publications"""
        
        store_id = "magento"
        
        # Ajouter publications
        base_time = datetime.now()
        for i in range(5):
            pub_time = base_time + timedelta(minutes=i*10)
            scheduler.record_publication(store_id, pub_time)
        
        # Vérifier historique
        history = scheduler._publication_history[store_id]
        assert len(history) == 5
        
        # Dernière publication
        last_pub = scheduler._get_last_publication_time(store_id)
        assert last_pub is not None
        expected_last = base_time + timedelta(minutes=40)
        assert abs((last_pub - expected_last).total_seconds()) < 1
    
    def test_rate_limit_configuration_per_store(self, scheduler):
        """Test configuration rate limit par store"""
        
        for store_id in STORES:
            status = scheduler.get_store_schedule_status(store_id)
            max_per_hour = status['max_publications_per_hour']
            
            # Vérifier limite spécifique store ou fallback
            expected = STORE_RATE_LIMITS.get(store_id, scheduler.config.max_publications_per_hour)
            assert max_per_hour == expected
            
            # Vérifier cohérence (limite > 0)
            assert max_per_hour > 0