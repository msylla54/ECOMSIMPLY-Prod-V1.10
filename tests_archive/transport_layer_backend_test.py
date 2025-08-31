#!/usr/bin/env python3
"""
Test complet du transport layer robuste ECOMSIMPLY
Validation des fonctionnalités principales et intégration backend
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any

# Ajouter le chemin du backend
sys.path.append('/app/backend')
sys.path.append('/app/backend/src')

# Import des modules à tester
from scraping.transport import RequestCoordinator, ProxyPool, ResponseCache
from services.enhanced_seo_scraping_service import EnhancedSEOScrapingService

class TransportLayerTester:
    """Testeur complet pour la couche de transport"""
    
    def __init__(self):
        self.results = {
            "test_name": "Transport Layer Robuste ECOMSIMPLY",
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Enregistrer le résultat d'un test"""
        self.results["tests"][test_name] = {
            "success": success,
            "details": details,
            "data": data,
            "timestamp": time.time()
        }
        
        self.results["summary"]["total_tests"] += 1
        if success:
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {details}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {details}")
    
    async def test_request_coordinator_initialization(self):
        """Test 1: Initialisation du RequestCoordinator"""
        try:
            coordinator = RequestCoordinator(max_per_host=3, timeout_s=10.0, cache_ttl_s=180)
            
            # Vérifier les paramètres de configuration
            assert coordinator.max_per_host == 3, "max_per_host incorrect"
            assert coordinator.timeout_s == 10.0, "timeout_s incorrect"
            assert coordinator.cache.ttl_seconds == 180, "cache_ttl_s incorrect"
            
            # Vérifier les codes de retry
            expected_retry_codes = {408, 429, 500, 502, 503, 504}
            assert coordinator.retry_codes == expected_retry_codes, "retry_codes incorrects"
            
            # Vérifier la configuration backoff
            assert coordinator.max_retries == 3, "max_retries incorrect"
            assert coordinator.base_delay == 1.0, "base_delay incorrect"
            assert coordinator.backoff_factor == 2.0, "backoff_factor incorrect"
            
            await coordinator.close()
            
            self.log_test(
                "RequestCoordinator Initialization",
                True,
                "Configuration correcte: max_per_host=3, timeout=10s, cache_ttl=180s, retry_codes={408,429,5xx}"
            )
            
        except Exception as e:
            self.log_test(
                "RequestCoordinator Initialization",
                False,
                f"Erreur d'initialisation: {str(e)}"
            )
    
    async def test_proxy_pool_functionality(self):
        """Test 2: Fonctionnalité du ProxyPool"""
        try:
            proxy_pool = ProxyPool(eviction_threshold=-0.5)
            
            # Test ajout de proxys
            test_proxies = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:8080",
                "http://proxy3.example.com:8080"
            ]
            
            for proxy in test_proxies:
                await proxy_pool.add(proxy)
            
            # Vérifier l'ajout
            assert len(proxy_pool.proxies) == 3, "Nombre de proxys incorrect"
            
            # Test sélection de proxy
            selected_proxy = await proxy_pool.pick()
            assert selected_proxy in test_proxies, "Proxy sélectionné invalide"
            
            # Test rapport de succès
            await proxy_pool.report_success(selected_proxy)
            proxy_info = proxy_pool.proxies[selected_proxy]
            assert proxy_info.success_count == 1, "Compteur de succès incorrect"
            assert proxy_info.score > 0, "Score non amélioré après succès"
            
            # Test rapport d'échec
            await proxy_pool.report_failure(selected_proxy, "timeout")
            assert proxy_info.failure_count == 1, "Compteur d'échecs incorrect"
            
            # Test statistiques
            stats = await proxy_pool.get_stats()
            assert stats["total_proxies"] == 3, "Stats total_proxies incorrect"
            assert stats["available_proxies"] == 3, "Stats available_proxies incorrect"
            
            self.log_test(
                "ProxyPool Functionality",
                True,
                f"Pool fonctionnel: {len(test_proxies)} proxys, sélection et scoring OK",
                {"stats": stats}
            )
            
        except Exception as e:
            self.log_test(
                "ProxyPool Functionality",
                False,
                f"Erreur ProxyPool: {str(e)}"
            )
    
    async def test_response_cache_functionality(self):
        """Test 3: Fonctionnalité du cache de réponses"""
        try:
            cache = ResponseCache(ttl_seconds=5)  # TTL court pour test
            
            # Test cache miss initial
            entry = await cache.get("https://example.com/test")
            assert entry is None, "Cache devrait être vide initialement"
            
            # Simuler une réponse HTML
            import httpx
            mock_response = httpx.Response(
                200,
                content=b"<html><body>Test content</body></html>",
                headers={"content-type": "text/html"}
            )
            
            # Test mise en cache
            await cache.set("https://example.com/test", mock_response)
            
            # Test récupération du cache
            cached_entry = await cache.get("https://example.com/test")
            assert cached_entry is not None, "Entrée devrait être en cache"
            assert cached_entry.status_code == 200, "Status code incorrect"
            assert "Test content" in cached_entry.content, "Contenu incorrect"
            
            # Test statistiques
            stats = await cache.get_stats()
            assert stats["total_entries"] >= 1, "Stats total_entries incorrect"
            assert stats["ttl_seconds"] == 5, "TTL incorrect dans stats"
            
            self.log_test(
                "ResponseCache Functionality",
                True,
                f"Cache fonctionnel: TTL={stats['ttl_seconds']}s, entrées={stats['total_entries']}",
                {"stats": stats}
            )
            
        except Exception as e:
            self.log_test(
                "ResponseCache Functionality",
                False,
                f"Erreur Cache: {str(e)}"
            )
    
    async def test_concurrency_limits(self):
        """Test 4: Limites de concurrence par domaine"""
        try:
            coordinator = RequestCoordinator(max_per_host=2, timeout_s=5.0)
            
            # Vérifier que les semaphores sont créés correctement
            host = "example.com"
            semaphore = coordinator.host_semaphores[host]
            assert semaphore._value == 2, "Semaphore mal configuré"
            
            # Test extraction d'host
            test_urls = [
                ("https://example.com/page1", "example.com"),
                ("http://test.fr/api", "test.fr"),
                ("https://subdomain.example.com/path", "subdomain.example.com")
            ]
            
            for url, expected_host in test_urls:
                actual_host = coordinator._get_host(url)
                assert actual_host == expected_host, f"Host extraction incorrect pour {url}"
            
            await coordinator.close()
            
            self.log_test(
                "Concurrency Limits",
                True,
                f"Semaphores configurés correctement: max_per_host=2, extraction d'host OK"
            )
            
        except Exception as e:
            self.log_test(
                "Concurrency Limits",
                False,
                f"Erreur concurrence: {str(e)}"
            )
    
    async def test_backoff_calculation(self):
        """Test 5: Calcul du backoff exponentiel avec jitter"""
        try:
            coordinator = RequestCoordinator()
            
            # Test backoff sans jitter
            delays_no_jitter = []
            for attempt in range(4):
                delay = coordinator._calculate_backoff_delay(attempt, jitter=False)
                delays_no_jitter.append(delay)
            
            # Vérifier progression exponentielle
            expected_delays = [1.0, 2.0, 4.0, 8.0]  # base_delay * (backoff_factor ** attempt)
            for i, (actual, expected) in enumerate(zip(delays_no_jitter, expected_delays)):
                assert abs(actual - expected) < 0.01, f"Backoff incorrect à l'attempt {i}"
            
            # Test backoff avec jitter
            delays_with_jitter = []
            for attempt in range(4):
                delay = coordinator._calculate_backoff_delay(attempt, jitter=True)
                delays_with_jitter.append(delay)
            
            # Vérifier que le jitter modifie les délais
            jitter_applied = any(
                abs(with_jitter - without_jitter) > 0.01
                for with_jitter, without_jitter in zip(delays_with_jitter, delays_no_jitter)
            )
            assert jitter_applied, "Jitter non appliqué"
            
            await coordinator.close()
            
            self.log_test(
                "Backoff Calculation",
                True,
                f"Backoff exponentiel OK: {delays_no_jitter}, jitter appliqué",
                {"delays_no_jitter": delays_no_jitter, "delays_with_jitter": delays_with_jitter}
            )
            
        except Exception as e:
            self.log_test(
                "Backoff Calculation",
                False,
                f"Erreur backoff: {str(e)}"
            )
    
    async def test_retry_logic(self):
        """Test 6: Logique de retry"""
        try:
            coordinator = RequestCoordinator()
            
            # Test codes de retry
            import httpx
            
            # Codes qui doivent déclencher un retry
            retry_responses = [
                httpx.Response(408, text="Request Timeout"),
                httpx.Response(429, text="Too Many Requests"),
                httpx.Response(500, text="Internal Server Error"),
                httpx.Response(502, text="Bad Gateway"),
                httpx.Response(503, text="Service Unavailable"),
                httpx.Response(504, text="Gateway Timeout")
            ]
            
            for response in retry_responses:
                should_retry = coordinator._should_retry(response, None)
                assert should_retry, f"Code {response.status_code} devrait déclencher un retry"
            
            # Codes qui ne doivent PAS déclencher un retry
            no_retry_responses = [
                httpx.Response(200, text="OK"),
                httpx.Response(404, text="Not Found"),
                httpx.Response(401, text="Unauthorized"),
                httpx.Response(403, text="Forbidden")
            ]
            
            for response in no_retry_responses:
                should_retry = coordinator._should_retry(response, None)
                assert not should_retry, f"Code {response.status_code} ne devrait PAS déclencher un retry"
            
            # Test exceptions qui déclenchent un retry
            retry_exceptions = [
                httpx.TimeoutException("Timeout"),
                httpx.ConnectError("Connection failed"),
                httpx.ReadError("Read failed")
            ]
            
            for exception in retry_exceptions:
                should_retry = coordinator._should_retry(None, exception)
                assert should_retry, f"Exception {type(exception).__name__} devrait déclencher un retry"
            
            await coordinator.close()
            
            self.log_test(
                "Retry Logic",
                True,
                "Logique de retry correcte: codes 408/429/5xx et exceptions réseau"
            )
            
        except Exception as e:
            self.log_test(
                "Retry Logic",
                False,
                f"Erreur retry logic: {str(e)}"
            )
    
    async def test_enhanced_seo_scraping_service_integration(self):
        """Test 7: Intégration EnhancedSEOScrapingService"""
        try:
            # Test initialisation du service
            service = EnhancedSEOScrapingService(max_per_host=3, timeout_s=10.0, cache_ttl_s=180)
            
            # Vérifier que le coordinator est bien configuré
            assert service.coordinator.max_per_host == 3, "max_per_host incorrect dans service"
            assert service.coordinator.timeout_s == 10.0, "timeout_s incorrect dans service"
            assert service.coordinator.cache.ttl_seconds == 180, "cache_ttl_s incorrect dans service"
            
            # Vérifier les sources de prix configurées
            assert len(service.price_sources) >= 3, "Pas assez de sources de prix"
            
            source_names = [source['name'] for source in service.price_sources]
            expected_sources = ['Amazon', 'Cdiscount', 'Fnac']
            for expected in expected_sources:
                assert expected in source_names, f"Source {expected} manquante"
            
            # Vérifier la configuration des headers
            headers = service._get_headers()
            assert 'User-Agent' in headers, "User-Agent manquant"
            assert 'Accept' in headers, "Accept header manquant"
            assert 'Accept-Language' in headers, "Accept-Language manquant"
            
            # Test ajout de proxy
            await service.add_proxy("http://test-proxy.com:8080")
            proxy_stats = await service.get_transport_stats()
            assert proxy_stats["total_proxies"] >= 1, "Proxy non ajouté"
            
            await service.coordinator.close()
            
            self.log_test(
                "EnhancedSEOScrapingService Integration",
                True,
                f"Service intégré: {len(service.price_sources)} sources, transport configuré",
                {"sources": source_names, "proxy_stats": proxy_stats}
            )
            
        except Exception as e:
            self.log_test(
                "EnhancedSEOScrapingService Integration",
                False,
                f"Erreur intégration service: {str(e)}"
            )
    
    async def test_import_validation(self):
        """Test 8: Validation des imports"""
        try:
            # Test imports principaux
            from scraping.transport import RequestCoordinator, ProxyPool, ResponseCache, CacheEntry, ProxyInfo
            from services.enhanced_seo_scraping_service import EnhancedSEOScrapingService
            
            # Vérifier que les classes sont bien importées
            assert RequestCoordinator is not None, "RequestCoordinator non importé"
            assert ProxyPool is not None, "ProxyPool non importé"
            assert ResponseCache is not None, "ResponseCache non importé"
            assert EnhancedSEOScrapingService is not None, "EnhancedSEOScrapingService non importé"
            
            # Test instanciation rapide
            coordinator = RequestCoordinator()
            proxy_pool = ProxyPool()
            cache = ResponseCache()
            
            assert coordinator is not None, "RequestCoordinator non instanciable"
            assert proxy_pool is not None, "ProxyPool non instanciable"
            assert cache is not None, "ResponseCache non instanciable"
            
            await coordinator.close()
            
            self.log_test(
                "Import Validation",
                True,
                "Tous les imports fonctionnent correctement"
            )
            
        except Exception as e:
            self.log_test(
                "Import Validation",
                False,
                f"Erreur d'import: {str(e)}"
            )
    
    async def test_configuration_constraints(self):
        """Test 9: Validation des contraintes de configuration"""
        try:
            # Test contraintes par défaut
            coordinator = RequestCoordinator()
            
            # Vérifier les valeurs par défaut
            assert coordinator.max_per_host == 3, "max_per_host par défaut incorrect"
            assert coordinator.timeout_s == 10.0, "timeout_s par défaut incorrect"
            assert coordinator.cache.ttl_seconds == 180, "cache_ttl_s par défaut incorrect"
            
            await coordinator.close()
            
            # Test contraintes personnalisées
            custom_coordinator = RequestCoordinator(max_per_host=5, timeout_s=15.0, cache_ttl_s=300)
            
            assert custom_coordinator.max_per_host == 5, "max_per_host personnalisé incorrect"
            assert custom_coordinator.timeout_s == 15.0, "timeout_s personnalisé incorrect"
            assert custom_coordinator.cache.ttl_seconds == 300, "cache_ttl_s personnalisé incorrect"
            
            await custom_coordinator.close()
            
            # Test service avec contraintes
            service = EnhancedSEOScrapingService(max_per_host=2, timeout_s=8.0, cache_ttl_s=120)
            
            assert service.coordinator.max_per_host == 2, "Service max_per_host incorrect"
            assert service.coordinator.timeout_s == 8.0, "Service timeout_s incorrect"
            assert service.coordinator.cache.ttl_seconds == 120, "Service cache_ttl_s incorrect"
            
            await service.coordinator.close()
            
            self.log_test(
                "Configuration Constraints",
                True,
                "Toutes les contraintes respectées: concurrence=3, timeout=10s, cache=180s"
            )
            
        except Exception as e:
            self.log_test(
                "Configuration Constraints",
                False,
                f"Erreur contraintes: {str(e)}"
            )
    
    async def test_observability_and_logging(self):
        """Test 10: Observabilité et logging"""
        try:
            coordinator = RequestCoordinator()
            
            # Test statistiques du cache
            cache_stats = await coordinator.get_cache_stats()
            required_cache_fields = ["total_entries", "active_entries", "expired_entries", "ttl_seconds"]
            for field in required_cache_fields:
                assert field in cache_stats, f"Champ {field} manquant dans cache_stats"
            
            # Test statistiques des proxys
            proxy_stats = await coordinator.get_proxy_stats()
            required_proxy_fields = ["total_proxies", "available_proxies", "evicted_proxies", "average_score", "proxies"]
            for field in required_proxy_fields:
                assert field in proxy_stats, f"Champ {field} manquant dans proxy_stats"
            
            # Test ajout de proxy et stats
            await coordinator.add_proxy("http://test-proxy.com:8080")
            updated_proxy_stats = await coordinator.get_proxy_stats()
            assert updated_proxy_stats["total_proxies"] == 1, "Proxy non ajouté dans stats"
            
            # Test nettoyage du cache
            cleared_entries = await coordinator.clear_cache()
            assert isinstance(cleared_entries, int), "clear_cache ne retourne pas un int"
            
            await coordinator.close()
            
            self.log_test(
                "Observability and Logging",
                True,
                "Observabilité complète: stats cache/proxy, nettoyage fonctionnel",
                {"cache_stats": cache_stats, "proxy_stats": updated_proxy_stats}
            )
            
        except Exception as e:
            self.log_test(
                "Observability and Logging",
                False,
                f"Erreur observabilité: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 Début des tests du Transport Layer Robuste ECOMSIMPLY")
        print("=" * 70)
        
        test_methods = [
            self.test_request_coordinator_initialization,
            self.test_proxy_pool_functionality,
            self.test_response_cache_functionality,
            self.test_concurrency_limits,
            self.test_backoff_calculation,
            self.test_retry_logic,
            self.test_enhanced_seo_scraping_service_integration,
            self.test_import_validation,
            self.test_configuration_constraints,
            self.test_observability_and_logging
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
                self.log_test(test_name, False, f"Exception non gérée: {str(e)}")
        
        # Calculer le taux de succès
        if self.results["summary"]["total_tests"] > 0:
            self.results["summary"]["success_rate"] = (
                self.results["summary"]["passed"] / self.results["summary"]["total_tests"]
            ) * 100
        
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 70)
        print(f"Total des tests: {self.results['summary']['total_tests']}")
        print(f"Tests réussis: {self.results['summary']['passed']}")
        print(f"Tests échoués: {self.results['summary']['failed']}")
        print(f"Taux de succès: {self.results['summary']['success_rate']:.1f}%")
        
        if self.results["summary"]["success_rate"] >= 90:
            print("🎉 TRANSPORT LAYER VALIDATION: EXCELLENT!")
        elif self.results["summary"]["success_rate"] >= 80:
            print("✅ TRANSPORT LAYER VALIDATION: BON")
        elif self.results["summary"]["success_rate"] >= 70:
            print("⚠️ TRANSPORT LAYER VALIDATION: ACCEPTABLE")
        else:
            print("❌ TRANSPORT LAYER VALIDATION: PROBLÈMES DÉTECTÉS")
        
        return self.results

async def main():
    """Fonction principale"""
    tester = TransportLayerTester()
    results = await tester.run_all_tests()
    
    # Sauvegarder les résultats
    with open('/app/transport_layer_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Résultats sauvegardés dans: /app/transport_layer_test_results.json")
    
    return results["summary"]["success_rate"] >= 80

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)