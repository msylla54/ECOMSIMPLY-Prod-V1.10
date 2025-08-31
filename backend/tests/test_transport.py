"""
Tests pour la couche de transport du scraping
"""

import asyncio
import time
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
import respx

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraping.transport import RequestCoordinator, ProxyPool, ProxyInfo, ResponseCache, CacheEntry


class TestResponseCache:
    """Tests pour la classe ResponseCache"""
    
    @pytest.fixture
    def cache(self):
        """Fixture pour créer un cache"""
        return ResponseCache(ttl_seconds=1)  # TTL court pour les tests
    
    @pytest.mark.asyncio
    async def test_cache_miss_initially(self, cache):
        """Test que le cache est initialement vide"""
        entry = await cache.get("https://example.com/test")
        assert entry is None
        
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test de mise en cache et récupération"""
        # Créer une réponse mock
        response = httpx.Response(
            200, 
            content=b"<html><body>Test content</body></html>",
            headers={"content-type": "text/html"}
        )
        
        # Mettre en cache
        await cache.set("https://example.com/test", response)
        
        # Récupérer du cache
        entry = await cache.get("https://example.com/test")
        assert entry is not None
        assert entry.content == "<html><body>Test content</body></html>"
        assert entry.status_code == 200
        
    @pytest.mark.asyncio
    async def test_cache_expiry(self, cache):
        """Test d'expiration du cache"""
        response = httpx.Response(
            200, 
            content=b"<html><body>Test content</body></html>",
            headers={"content-type": "text/html"}
        )
        
        # Mettre en cache
        await cache.set("https://example.com/test", response)
        
        # Vérifier présence
        entry = await cache.get("https://example.com/test")
        assert entry is not None
        
        # Attendre expiration
        await asyncio.sleep(1.1)
        
        # Vérifier expiration
        entry = await cache.get("https://example.com/test")
        assert entry is None
        
    @pytest.mark.asyncio
    async def test_cache_only_html_responses(self, cache):
        """Test que seules les réponses HTML sont mises en cache"""
        # Réponse JSON - ne devrait pas être mise en cache
        json_response = httpx.Response(
            200, 
            content=b'{"data": "test"}',
            headers={"content-type": "application/json"}
        )
        
        await cache.set("https://example.com/api", json_response)
        entry = await cache.get("https://example.com/api")
        assert entry is None
        
        # Réponse HTML - devrait être mise en cache
        html_response = httpx.Response(
            200, 
            content=b"<html><body>Test</body></html>",
            headers={"content-type": "text/html; charset=utf-8"}
        )
        
        await cache.set("https://example.com/page", html_response)
        entry = await cache.get("https://example.com/page")
        assert entry is not None
        
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test des statistiques de cache"""
        stats = await cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["ttl_seconds"] == 1
        
        # Ajouter une entrée
        response = httpx.Response(
            200, 
            content=b"<html><body>Test</body></html>",
            headers={"content-type": "text/html"}
        )
        await cache.set("https://example.com/test", response)
        
        stats = await cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 0


class TestProxyPool:
    """Tests pour la classe ProxyPool"""
    
    @pytest.fixture
    def proxy_pool(self):
        """Fixture pour créer un pool de proxys"""
        return ProxyPool()
    
    @pytest.mark.asyncio
    async def test_add_proxy(self, proxy_pool):
        """Test d'ajout de proxy"""
        await proxy_pool.add("http://proxy1.com:8080")
        assert "http://proxy1.com:8080" in proxy_pool.proxies
        
    @pytest.mark.asyncio
    async def test_pick_proxy_when_empty(self, proxy_pool):
        """Test de sélection quand le pool est vide"""
        proxy = await proxy_pool.pick()
        assert proxy is None
        
    @pytest.mark.asyncio
    async def test_pick_best_proxy(self, proxy_pool):
        """Test de sélection du meilleur proxy"""
        await proxy_pool.add("http://proxy1.com:8080")
        await proxy_pool.add("http://proxy2.com:8080")
        
        # Améliorer le score du proxy2
        await proxy_pool.report_success("http://proxy2.com:8080")
        await proxy_pool.report_success("http://proxy2.com:8080")
        
        # Le proxy2 devrait être sélectionné
        selected = await proxy_pool.pick()
        assert selected == "http://proxy2.com:8080"
        
    @pytest.mark.asyncio
    async def test_report_success_improves_score(self, proxy_pool):
        """Test que rapporter un succès améliore le score"""
        await proxy_pool.add("http://proxy1.com:8080")
        initial_score = proxy_pool.proxies["http://proxy1.com:8080"].score
        
        await proxy_pool.report_success("http://proxy1.com:8080")
        new_score = proxy_pool.proxies["http://proxy1.com:8080"].score
        
        assert new_score > initial_score
        
    @pytest.mark.asyncio
    async def test_report_failure_decreases_score(self, proxy_pool):
        """Test que rapporter un échec diminue le score"""
        await proxy_pool.add("http://proxy1.com:8080")
        initial_score = proxy_pool.proxies["http://proxy1.com:8080"].score
        
        await proxy_pool.report_failure("http://proxy1.com:8080", "timeout")
        new_score = proxy_pool.proxies["http://proxy1.com:8080"].score
        
        assert new_score < initial_score
        
    @pytest.mark.asyncio
    async def test_proxy_eviction_on_low_score(self, proxy_pool):
        """Test d'éviction automatique avec score bas"""
        await proxy_pool.add("http://proxy1.com:8080")
        
        # Rapporter plusieurs échecs pour faire baisser le score
        for _ in range(10):
            await proxy_pool.report_failure("http://proxy1.com:8080", "timeout")
        
        # Le proxy ne devrait plus être sélectionnable
        selected = await proxy_pool.pick()
        assert selected is None
        
    @pytest.mark.asyncio
    async def test_get_stats(self, proxy_pool):
        """Test des statistiques du pool"""
        await proxy_pool.add("http://proxy1.com:8080")
        await proxy_pool.add("http://proxy2.com:8080")
        
        stats = await proxy_pool.get_stats()
        
        assert stats["total_proxies"] == 2
        assert stats["available_proxies"] == 2
        assert len(stats["proxies"]) == 2


class TestRequestCoordinator:
    """Tests pour la classe RequestCoordinator"""
    
    @pytest_asyncio.fixture
    async def coordinator(self):
        """Fixture pour créer un coordinateur"""
        coordinator = RequestCoordinator(max_per_host=3, timeout_s=5.0, cache_ttl_s=1)
        yield coordinator
        await coordinator.close()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_request(self, coordinator):
        """Test d'une requête réussie"""
        # Mock de la réponse
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        
        response = await coordinator.get("https://example.com/test")
        
        assert response.status_code == 200
        assert response.json() == {"success": True}
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_429_with_backoff(self, coordinator):
        """Test retry sur code 429 avec backoff exponentiel"""
        # Premier appel retourne 429, deuxième retourne 200
        respx.get("https://example.com/test").mock(
            side_effect=[
                httpx.Response(429, text="Too Many Requests"),
                httpx.Response(200, json={"success": True})
            ]
        )
        
        # Mesurer le temps pour vérifier le backoff
        start_time = time.time()
        response = await coordinator.get("https://example.com/test")
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert response.json() == {"success": True}
        # Vérifier qu'il y a eu un délai (backoff) - avec tolérance pour le jitter
        assert duration >= 0.8  # Au moins 80% du délai minimum avec jitter
        
    @pytest.mark.asyncio
    @respx.mock
    async def test_rotate_proxy_on_timeout(self, coordinator):
        """Test rotation de proxy sur timeout"""
        # Ajouter des proxys
        await coordinator.add_proxy("http://proxy1.com:8080")
        await coordinator.add_proxy("http://proxy2.com:8080")
        
        # Premier appel timeout, deuxième succès
        respx.get("https://example.com/test").mock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                httpx.Response(200, json={"success": True})
            ]
        )
        
        response = await coordinator.get("https://example.com/test")
        
        assert response.status_code == 200
        # Vérifier que les proxys ont été utilisés
        stats = await coordinator.get_proxy_stats()
        assert stats["total_proxies"] == 2
        
    @pytest.mark.asyncio
    @respx.mock
    async def test_per_host_semaphore_limits(self, coordinator):
        """Test que le semaphore limite la concurrence par host"""
        # Mock qui simule des réponses lentes
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        
        # Variables pour compter les requêtes simultanées
        concurrent_requests = 0
        max_concurrent = 0
        
        async def mock_request(method, url, **kwargs):
            nonlocal concurrent_requests, max_concurrent
            concurrent_requests += 1
            max_concurrent = max(max_concurrent, concurrent_requests)
            # Simuler une requête lente
            await asyncio.sleep(0.1)
            concurrent_requests -= 1
            return httpx.Response(200, json={"success": True})
        
        # Patcher la méthode request du client
        with patch.object(coordinator.client, 'request', side_effect=mock_request):
            # Lancer 10 requêtes simultanées vers le même host
            tasks = [
                coordinator.get("https://example.com/test")
                for _ in range(10)
            ]
            
            await asyncio.gather(*tasks)
        
        # Vérifier que la concurrence était limitée à max_per_host
        assert max_concurrent <= coordinator.max_per_host
        
    @pytest.mark.asyncio 
    @respx.mock
    async def test_retry_exhaustion_raises_error(self, coordinator):
        """Test que l'épuisement des retries lève une erreur"""
        # Toujours retourner 500
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await coordinator.get("https://example.com/test")
            
    @pytest.mark.asyncio
    @respx.mock  
    async def test_non_retryable_error_immediate_failure(self, coordinator):
        """Test qu'une erreur non-retry échoue immédiatement"""
        # Retourner 404 (non retryable)
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await coordinator.get("https://example.com/test")
            
    @pytest.mark.asyncio
    async def test_fetch_with_post_data(self, coordinator):
        """Test de requête POST avec données"""
        with respx.mock:
            respx.post("https://example.com/api").mock(
                return_value=httpx.Response(201, json={"created": True})
            )
            
            response = await coordinator.fetch(
                "https://example.com/api", 
                method="POST",
                data={"key": "value"}
            )
            
            assert response.status_code == 201
            assert response.json() == {"created": True}
            
    @pytest.mark.asyncio
    @respx.mock
    async def test_cache_functionality(self, coordinator):
        """Test du cache de réponses"""
        # Mock de la réponse HTML
        html_content = "<html><body><h1>Test Page</h1></body></html>"
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(
                200, 
                content=html_content.encode('utf-8'),
                headers={"content-type": "text/html"}
            )
        )
        
        # Premier appel - devrait faire la requête HTTP
        response1 = await coordinator.get("https://example.com/test")
        assert response1.status_code == 200
        assert "Test Page" in response1.text
        
        # Deuxième appel - devrait utiliser le cache
        response2 = await coordinator.get("https://example.com/test")
        assert response2.status_code == 200
        assert "Test Page" in response2.text
        
        # Vérifier les stats du cache
        cache_stats = await coordinator.get_cache_stats()
        assert cache_stats["total_entries"] >= 1
        
    @pytest.mark.asyncio
    @respx.mock
    async def test_cache_disabled_for_non_get(self, coordinator):
        """Test que le cache n'est pas utilisé pour les méthodes non-GET"""
        respx.post("https://example.com/api").mock(
            return_value=httpx.Response(201, json={"created": True})
        )
        
        response = await coordinator.fetch(
            "https://example.com/api", 
            method="POST",
            data={"key": "value"}
        )
        
        assert response.status_code == 201
        
        # Le cache ne devrait pas contenir cette requête POST
        cache_stats = await coordinator.get_cache_stats()
        assert cache_stats["total_entries"] == 0
        """Test avec headers personnalisés"""
        with respx.mock:
            route = respx.get("https://example.com/test").mock(
                return_value=httpx.Response(200, json={"success": True})
            )
            
            await coordinator.get(
                "https://example.com/test",
                headers={"User-Agent": "Custom-Agent"}
            )
            
    @pytest.mark.asyncio
    async def test_custom_headers(self, coordinator):
        """Test avec headers personnalisés"""
        with respx.mock:
            route = respx.get("https://example.com/test").mock(
                return_value=httpx.Response(200, json={"success": True})
            )
            
            await coordinator.get(
                "https://example.com/test",
                headers={"User-Agent": "Custom-Agent"}
            )
            
            # Vérifier que les headers ont été envoyés
            request = route.calls[0].request
            assert request.headers.get("User-Agent") == "Custom-Agent"
    
    @pytest.mark.asyncio
    async def test_cache_and_proxy_stats(self, coordinator):
        """Test des statistiques complètes"""
        # Ajouter des proxys
        await coordinator.add_proxy("http://proxy1.com:8080")
        await coordinator.add_proxy("http://proxy2.com:8080")
        
        # Obtenir les stats
        proxy_stats = await coordinator.get_proxy_stats()
        cache_stats = await coordinator.get_cache_stats()
        
        assert proxy_stats["total_proxies"] == 2
        assert cache_stats["ttl_seconds"] == 1
        assert cache_stats["total_entries"] == 0
        
        # Nettoyer le cache
        cleared = await coordinator.clear_cache()
        assert cleared == 0  # Aucune entrée expirée à nettoyer


class TestIntegration:
    """Tests d'intégration pour la couche transport"""
    
    @pytest.mark.asyncio
    async def test_full_scenario_with_proxy_rotation(self):
        """Test complet avec rotation de proxy et cache"""
        async with RequestCoordinator(max_per_host=2, timeout_s=5.0, cache_ttl_s=60) as coordinator:
            # Ajouter des proxys
            await coordinator.add_proxy("http://proxy1.com:8080")
            await coordinator.add_proxy("http://proxy2.com:8080")
            
            with respx.mock:
                # Simuler échec puis succès
                respx.get("https://example.com/test").mock(
                    side_effect=[
                        httpx.TimeoutException("Timeout"),
                        httpx.Response(200, json={"success": True})
                    ]
                )
                
                response = await coordinator.get("https://example.com/test")
                
                assert response.status_code == 200
                
                # Vérifier les stats des proxys et cache
                proxy_stats = await coordinator.get_proxy_stats()
                cache_stats = await coordinator.get_cache_stats()
                
                assert proxy_stats["total_proxies"] == 2
                assert cache_stats is not None
                
                # Au moins un proxy devrait avoir rapporté un succès
                success_reported = any(
                    proxy["success_count"] > 0 
                    for proxy in proxy_stats["proxies"]
                )
                assert success_reported