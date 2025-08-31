"""
Tests End-to-End pour Orchestrateur Principal - Multi-stores ECOMSIMPLY
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from decimal import Decimal

# Import modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scraping.publication.orchestrator import PublicationOrchestrator
from scraping.publication.dto import PublicationConfig, PublishTask, PublicationStatus, StoreType
from scraping.publication.constants import STORES
from scraping.semantic.product_dto import ProductDTO, ImageDTO, PriceDTO, Currency

def get_current_year() -> int:
    """Retourne l'année courante pour usage dans les tests"""
    return datetime.now().year


class TestPublicationOrchestrator:
    """Tests End-to-End pour PublicationOrchestrator"""
    
    @pytest.fixture
    def config(self):
        """Configuration test avec timings courts"""
        return PublicationConfig(
            active_hours_start=8,
            active_hours_end=20,
            cooldown_between_publications=60,  # 1 minute pour tests rapides
            max_publications_per_hour=20,     # Limite généreuse
            max_concurrent_workers=1,         # 1 worker pour tests déterministes
            price_variance_threshold=0.3,     # Seuil tolérant pour tests
            min_confidence_score=0.4          # Score bas pour tests
        )
    
    @pytest.fixture
    def orchestrator(self, config):
        """Orchestrateur configuré pour tests"""
        return PublicationOrchestrator(config)
    
    @pytest.fixture
    def sample_product_high_quality(self):
        """Produit haute qualité qui passe les guardrails"""
        return ProductDTO(
            title="iPhone 15 Pro 256GB Premium Edition Ultra Test",
            description_html="<p><strong>Smartphone premium</strong> avec puce A17 Pro révolutionnaire. " +
                            "Écran Super Retina XDR 6,1 pouces, appareil photo professionnel 48 Mpx.</p>" +
                            "<ul><li>Puce A17 Pro</li><li>256GB stockage</li><li>Appareil photo Pro</li></ul>",
            price=PriceDTO(amount=Decimal('1299.99'), currency=Currency.EUR, original_text="1 299,99 €"),
            images=[
                ImageDTO(url="https://cdn.apple.com/iphone15pro-main.webp", alt="iPhone 15 Pro vue principale"),
                ImageDTO(url="https://cdn.apple.com/iphone15pro-back.webp", alt="iPhone 15 Pro vue arrière"),
                ImageDTO(url="https://cdn.apple.com/iphone15pro-side.webp", alt="iPhone 15 Pro profil")
            ],
            source_url="https://apple.com/fr/iphone-15-pro",
            attributes={
                'brand': 'Apple',
                'model': 'iPhone 15 Pro',
                'storage': '256GB',
                'category': 'Smartphones',
                'sku': 'IPHONE15PRO256'
            },
            payload_signature="high_quality_product_sig",
            extraction_timestamp=1703001234.567,
            # Champs SEO (nouveaux) avec année dynamique
            seo_title=f"iPhone 15 Pro {get_current_year()} - Prix, Test et Guide Achat",
            seo_description=f"Découvrez l'iPhone 15 Pro en {get_current_year()} : prix actualisé, test complet et guide d'achat.",
            seo_keywords=[f"iphone 15 pro {get_current_year()}", f"prix iphone {get_current_year()}", "test iphone 15"],
            structured_data={"@type": "Product", "name": "iPhone 15 Pro"}
        )
    
    @pytest.fixture
    def sample_product_low_quality(self):
        """Produit basse qualité pour tester guardrails"""
        return ProductDTO(
            title="Bad",  # Titre trop court
            description_html="<p>Test</p>",  # Description trop courte
            # Pas de prix → échouera guardrails
            images=[ImageDTO(url="https://test.com/bad.webp", alt="Bad")],
            source_url="https://test.com/bad-product",
            payload_signature="low_quality_sig",
            extraction_timestamp=1703001234.567
        )
    
    # Tests de base orchestrateur
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test initialisation orchestrateur"""
        
        assert orchestrator.config is not None
        assert orchestrator.scheduler is not None
        assert orchestrator.guardrails is not None
        assert orchestrator.idempotency_manager is not None
        assert orchestrator.queue is not None
        
        # Vérifier publishers pour tous les stores
        assert len(orchestrator.publishers) == len(STORES)
        for store in STORES:
            assert store in orchestrator.publishers
            assert orchestrator.publishers[store].name == store
    
    @pytest.mark.parametrize("store_id", STORES)
    @pytest.mark.asyncio
    async def test_enqueue_all_stores(self, orchestrator, sample_product_high_quality, store_id):
        """Test mise en queue pour chaque store"""
        
        task_id = await orchestrator.enqueue(
            product=sample_product_high_quality,
            store_id=store_id,
            priority=3
        )
        
        assert isinstance(task_id, str)
        assert store_id in task_id
        assert orchestrator.stats['total_enqueued'] >= 1
        assert orchestrator.stats['by_store'][store_id]['enqueued'] >= 1
    
    @pytest.mark.asyncio
    async def test_enqueue_invalid_store(self, orchestrator, sample_product_high_quality):
        """Test échec store invalide"""
        
        with pytest.raises(ValueError, match="Store 'invalid_store' non supporté"):
            await orchestrator.enqueue(sample_product_high_quality, "invalid_store")
    
    @pytest.mark.parametrize("store_id", STORES[:3])  # Test sur 3 stores
    @pytest.mark.asyncio
    async def test_enqueue_batch_multiple_stores(self, orchestrator, sample_product_high_quality, store_id):
        """Test batch pour différents stores"""
        
        products = [sample_product_high_quality] * 3  # 3 produits identiques
        
        batch = await orchestrator.enqueue_batch(
            products=products,
            store_id=store_id,
            batch_priority=2
        )
        
        assert batch.batch_id is not None
        assert store_id in batch.batch_id
        assert len(batch.tasks) == 3
        assert batch.total_tasks == 3
        assert all(task.store_id == store_id for task in batch.tasks)
    
    # Tests publication dans heures actives
    
    @pytest.mark.parametrize("store_id", STORES[:2])  # Test 2 stores
    @pytest.mark.asyncio
    async def test_work_once_success_active_hours(self, orchestrator, sample_product_high_quality, store_id):
        """Test publication réussie dans heures actives"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # Simuler heure active (14h)
            mock_dt.now.return_value = datetime.now().replace(hour=14, minute=0, second=0)
            
            # Enqueue tâche
            await orchestrator.enqueue(sample_product_high_quality, store_id)
            
            # Traiter tâche
            task = await orchestrator.work_once()
            
            assert task is not None
            assert task.status == PublicationStatus.SUCCESS
            assert task.store_id == store_id
            assert task.result_data is not None
            assert 'external_id' in task.result_data
            
            # Vérifier stats
            assert orchestrator.stats['total_successful'] >= 1
            assert orchestrator.stats['by_store'][store_id]['successful'] >= 1
    
    @pytest.mark.asyncio
    async def test_work_once_outside_active_hours(self, orchestrator, sample_product_high_quality):
        """Test rejet hors heures actives"""
        
        store_id = "shopify"
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            # Simuler heure inactive (6h du matin)
            mock_dt.now.return_value = datetime.now().replace(hour=6, minute=0, second=0)
            
            # Enqueue tâche
            await orchestrator.enqueue(sample_product_high_quality, store_id)
            
            # Traiter tâche → devrait être reportée
            task = await orchestrator.work_once()
            
            assert task is not None
            assert task.status == PublicationStatus.PENDING  # Remise en queue
    
    @pytest.mark.parametrize("store_id", STORES[:2])
    @pytest.mark.asyncio
    async def test_work_once_guardrails_blocked(self, orchestrator, sample_product_low_quality, store_id):
        """Test blocage par guardrails pour différents stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=12, minute=0)
            
            # Enqueue produit de mauvaise qualité
            await orchestrator.enqueue(sample_product_low_quality, store_id)
            
            # Traiter → devrait être bloqué
            task = await orchestrator.work_once()
            
            assert task is not None
            assert task.status == PublicationStatus.SKIPPED_GUARDRAIL
            assert "Guardrails" in task.error_message
            
            # Stats guardrails
            assert orchestrator.stats['total_skipped_guardrails'] >= 1
            assert orchestrator.stats['by_store'][store_id]['skipped'] >= 1
    
    @pytest.mark.parametrize("store_id", STORES[:2])
    @pytest.mark.asyncio
    async def test_work_once_duplicate_detection(self, orchestrator, sample_product_high_quality, store_id):
        """Test détection doublons pour différents stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=15, minute=0)
            
            # Première publication
            await orchestrator.enqueue(sample_product_high_quality, store_id)
            task1 = await orchestrator.work_once()
            assert task1.status == PublicationStatus.SUCCESS
            
            # Deuxième publication même produit → doublon
            await orchestrator.enqueue(sample_product_high_quality, store_id)
            task2 = await orchestrator.work_once()
            
            assert task2.status == PublicationStatus.SKIPPED_DUPLICATE
            assert "Doublon" in task2.error_message
            assert orchestrator.stats['total_skipped_duplicate'] >= 1
    
    # Tests cooldown et rate limiting
    
    @pytest.mark.asyncio
    async def test_cooldown_enforcement_between_stores(self, orchestrator, sample_product_high_quality):
        """Test cooldown indépendant entre stores"""
        
        store1, store2 = STORES[0], STORES[1]
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            base_time = datetime.now().replace(hour=13, minute=0, second=0)
            mock_dt.now.return_value = base_time
            
            # Publication sur store1
            await orchestrator.enqueue(sample_product_high_quality, store1)
            task1 = await orchestrator.work_once()
            assert task1.status == PublicationStatus.SUCCESS
            
            # 30 secondes plus tard (< 60s cooldown)
            mock_dt.now.return_value = base_time + timedelta(seconds=30)
            
            # Store1 → en cooldown
            # Modifier le produit pour éviter la détection de doublon
            modified_product = sample_product_high_quality.model_copy()
            modified_product.payload_signature = "cooldown_test_product_different"
            
            await orchestrator.enqueue(modified_product, store1)
            task1_cooldown = await orchestrator.work_once()
            assert task1_cooldown.status == PublicationStatus.PENDING  # Remis en queue
            
            # Store2 → pas de cooldown (indépendant)
            # Modifier légèrement le produit pour éviter duplication
            different_product = sample_product_high_quality.model_copy()
            different_product.payload_signature = "different_sig_store2"
            
            await orchestrator.enqueue(different_product, store2)
            task2 = await orchestrator.work_once()
            assert task2.status == PublicationStatus.SUCCESS
    
    # Tests retry et backoff
    
    @pytest.mark.asyncio
    async def test_publisher_temporary_failure(self, orchestrator, sample_product_high_quality):
        """Test gestion échec temporaire publisher"""
        
        store_id = "woocommerce"
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=16, minute=0)
            
            # Mock publisher pour échouer temporairement
            original_publish = orchestrator.publishers[store_id].publish
            
            async def failing_publish(product, *, idempotency_key):
                # Simuler échec temporaire
                from scraping.publication.publishers.base import PublishResult
                return PublishResult(
                    success=False,
                    status_code=503,
                    message="Service temporarily unavailable",
                    store=store_id
                )
            
            orchestrator.publishers[store_id].publish = failing_publish
            
            try:
                # Enqueue et traiter
                await orchestrator.enqueue(sample_product_high_quality, store_id)
                task = await orchestrator.work_once()
                
                assert task.status == PublicationStatus.FAILED
                assert "Service temporarily unavailable" in task.error_message
                assert orchestrator.stats['total_failed'] >= 1
                
            finally:
                # Restaurer méthode originale
                orchestrator.publishers[store_id].publish = original_publish
    
    # Tests statistiques et monitoring
    
    @pytest.mark.asyncio
    async def test_orchestrator_complete_stats(self, orchestrator, sample_product_high_quality):
        """Test statistiques complètes orchestrateur"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=11, minute=0)
            
            # Publier sur plusieurs stores
            for store in STORES[:3]:
                # Modifier produit pour éviter doublons
                product = sample_product_high_quality.model_copy()
                product.payload_signature = f"stats_test_{store}"
                
                await orchestrator.enqueue(product, store)
                await orchestrator.work_once()
            
            stats = await orchestrator.get_orchestrator_stats()
            
            # Vérifier structure complète
            assert 'orchestrator' in stats
            assert 'components' in stats
            assert 'publishers' in stats
            assert 'supported_stores' in stats
            
            # Stats orchestrateur
            orch_stats = stats['orchestrator']
            assert orch_stats['total_enqueued'] >= 3
            assert orch_stats['total_processed'] >= 3
            assert orch_stats['total_successful'] >= 3
            assert orch_stats['is_running'] is False  # Pas de workers démarrés
            
            # Stats par store
            for store in STORES[:3]:
                assert store in orch_stats['by_store']
                store_stats = orch_stats['by_store'][store]
                assert store_stats['enqueued'] >= 1
                assert store_stats['successful'] >= 1
            
            # Stats publishers
            assert len(stats['publishers']) == len(STORES)
            for store in STORES:
                assert store in stats['publishers']
                pub_stats = stats['publishers'][store]
                assert 'total_publishes' in pub_stats
                assert 'store_name' in pub_stats
    
    @pytest.mark.parametrize("store_id", STORES[:3])
    def test_store_summary_all_stores(self, orchestrator, store_id):
        """Test résumé par store pour tous les stores"""
        
        summary = orchestrator.get_store_summary(store_id)
        
        assert summary['store_id'] == store_id
        assert 'orchestrator_stats' in summary
        assert 'schedule_status' in summary
        assert 'publisher_stats' in summary
        assert isinstance(summary['can_publish_now'], bool)
        assert 'next_available_slot' in summary
    
    def test_store_summary_invalid_store(self, orchestrator):
        """Test échec résumé store invalide"""
        
        with pytest.raises(ValueError, match="Store 'invalid' non supporté"):
            orchestrator.get_store_summary('invalid')
    
    @pytest.mark.asyncio
    async def test_health_check_all_stores(self, orchestrator):
        """Test health check complet"""
        
        health = await orchestrator.health_check()
        
        assert 'orchestrator' in health
        assert 'stores' in health
        
        # Health orchestrateur
        orch_health = health['orchestrator']
        assert 'status' in orch_health
        assert 'uptime' in orch_health
        
        # Health tous les stores
        assert len(health['stores']) == len(STORES)
        for store in STORES:
            assert store in health['stores']
            store_health = health['stores'][store]
            assert 'status' in store_health
    
    # Tests intégration workflow complet
    
    @pytest.mark.asyncio
    async def test_complete_workflow_multiple_stores(self, orchestrator, sample_product_high_quality):
        """Test workflow complet sur plusieurs stores"""
        
        with patch('scraping.publication.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = datetime.now().replace(hour=10, minute=0)
            
            results = {}
            
            # Traiter 3 stores différents
            for i, store in enumerate(STORES[:3]):
                # Produits légèrement différents pour éviter doublons
                product = sample_product_high_quality.model_copy()
                product.title = f"{sample_product_high_quality.title} - Store {store}"
                product.payload_signature = f"workflow_test_{store}_{i}"
                
                # 1. Enqueue
                task_id = await orchestrator.enqueue(product, store, priority=1)
                
                # 2. Process
                task = await orchestrator.work_once()
                
                assert task is not None
                assert task.status == PublicationStatus.SUCCESS
                assert task.store_id == store
                
                results[store] = {
                    'task_id': task_id,
                    'external_id': task.result_data['external_id'],
                    'task': task
                }
            
            # Vérifier résultats
            assert len(results) == 3
            
            # External IDs différents
            external_ids = [r['external_id'] for r in results.values()]
            assert len(set(external_ids)) == 3  # Tous différents
            
            # Stats finales
            stats = await orchestrator.get_orchestrator_stats()
            assert stats['orchestrator']['total_successful'] >= 3
            
            # Chaque store a au moins 1 publication réussie
            for store in STORES[:3]:
                assert stats['orchestrator']['by_store'][store]['successful'] >= 1
    
    @pytest.mark.asyncio
    async def test_no_task_available(self, orchestrator):
        """Test comportement sans tâche disponible"""
        
        # Queue vide
        task = await orchestrator.work_once()
        assert task is None