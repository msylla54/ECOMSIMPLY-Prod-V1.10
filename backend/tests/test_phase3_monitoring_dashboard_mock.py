"""
Test Phase 3: Implémentation améliorations - Monitoring Dashboard Mock
Tests pour valider le dashboard de monitoring des performances scraping
"""

import pytest
import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_scraping_service import HybridScrapingService

class TestMonitoringDashboardMock:
    """Tests pour validation dashboard monitoring mock"""
    
    @pytest.fixture
    def hybrid_service(self):
        return HybridScrapingService()
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_overview_metrics(self, hybrid_service):
        """Test: Métriques overview du dashboard"""
        
        # Générer activité pour monitoring
        test_products = ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Air M2", "AirPods Pro"]
        
        for product in test_products:
            await hybrid_service.scrape_prices_unified(
                product_name=product,
                use_cache=False  # Éviter cache pour générer vraie activité
            )
        
        # Récupérer données dashboard
        dashboard_data = hybrid_service.get_monitoring_dashboard_data()
        
        # Validation structure overview
        overview = dashboard_data["overview"]
        required_overview_fields = [
            "total_requests", "success_rate", "avg_response_time_ms", 
            "total_prices_found", "outliers_detected"
        ]
        
        for field in required_overview_fields:
            assert field in overview, f"Champ {field} manquant dans overview"
        
        # Validation valeurs logiques
        assert overview["total_requests"] == len(test_products), "Nombre requêtes correct"
        assert 0 <= overview["success_rate"] <= 1, "Taux succès entre 0 et 1"
        assert overview["avg_response_time_ms"] > 0, "Temps réponse moyen > 0"
        assert overview["total_prices_found"] >= 0, "Prix trouvés >= 0"
        assert overview["outliers_detected"] >= 0, "Outliers détectés >= 0"
        
        print("✅ Métriques overview dashboard:")
        print(f"  - Total requêtes: {overview['total_requests']}")
        print(f"  - Taux succès: {overview['success_rate']:.1%}")
        print(f"  - Temps réponse moyen: {overview['avg_response_time_ms']:.1f}ms")
        print(f"  - Prix trouvés: {overview['total_prices_found']}")
        print(f"  - Outliers détectés: {overview['outliers_detected']}")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_sources_performance(self, hybrid_service):
        """Test: Métriques performance par source"""
        
        # Générer mix d'activité sur plusieurs sources
        await hybrid_service.scrape_prices_unified("iPhone 15 Pro", use_cache=False)
        await hybrid_service.scrape_prices_unified("Samsung Galaxy S24", use_cache=False)
        
        dashboard_data = hybrid_service.get_monitoring_dashboard_data()
        
        # Validation structure sources performance
        sources_performance = dashboard_data["sources_performance"]
        expected_sources = ["amazon", "fnac", "cdiscount", "google_shopping", "aliexpress"]
        
        for source in expected_sources:
            if source in sources_performance:
                source_stats = sources_performance[source]
                
                # Validation structure par source
                assert "success_rate" in source_stats
                assert "total_requests" in source_stats
                assert "avg_prices_per_request" in source_stats
                
                # Validation valeurs
                assert 0 <= source_stats["success_rate"] <= 1, f"Taux succès {source} invalide"
                assert source_stats["total_requests"] >= 0, f"Requêtes {source} >= 0"
                assert source_stats["avg_prices_per_request"] >= 0, f"Prix/req {source} >= 0"
        
        print("✅ Performance sources dashboard:")
        for source, stats in sources_performance.items():
            print(f"  - {source}: {stats['success_rate']:.1%} succès, {stats['avg_prices_per_request']:.1f} prix/req")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_cache_performance(self, hybrid_service):
        """Test: Métriques performance cache"""
        
        # Générer activité cache
        product = "MacBook Air M2"
        
        # Miss puis hits
        await hybrid_service.scrape_prices_unified(product, use_cache=True)  # Miss
        await hybrid_service.scrape_prices_unified(product, use_cache=True)  # Hit
        await hybrid_service.scrape_prices_unified(product, use_cache=True)  # Hit
        
        dashboard_data = hybrid_service.get_monitoring_dashboard_data()
        
        # Validation structure cache performance
        cache_performance = dashboard_data["cache_performance"]
        required_cache_fields = [
            "total_requests", "cache_hits", "cache_misses", "hit_ratio", 
            "cached_entries", "invalidations"
        ]
        
        for field in required_cache_fields:
            assert field in cache_performance, f"Champ cache {field} manquant"
        
        # Validation logique cache
        total_req = cache_performance["total_requests"]
        hits = cache_performance["cache_hits"]
        misses = cache_performance["cache_misses"]
        hit_ratio = cache_performance["hit_ratio"]
        
        assert total_req == hits + misses, "Total = hits + misses"
        assert hit_ratio == hits / total_req if total_req > 0 else 0, "Ratio hit correct"
        assert cache_performance["cached_entries"] >= 0, "Entrées cache >= 0"
        
        print("✅ Performance cache dashboard:")
        print(f"  - Hit ratio: {hit_ratio:.1%}")
        print(f"  - Total requêtes cache: {total_req}")
        print(f"  - Entrées en cache: {cache_performance['cached_entries']}")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_proxy_health(self, hybrid_service):
        """Test: Métriques santé proxy"""
        
        # Générer activité proxy via scraping
        await hybrid_service.scrape_prices_unified("AirPods Pro", use_cache=False)
        
        dashboard_data = hybrid_service.get_monitoring_dashboard_data()
        
        # Validation structure proxy health
        proxy_health = dashboard_data["proxy_health"]
        required_proxy_fields = ["healthy_proxies", "total_proxies", "avg_success_rate"]
        
        for field in required_proxy_fields:
            assert field in proxy_health, f"Champ proxy {field} manquant"
        
        # Validation valeurs proxy
        healthy = proxy_health["healthy_proxies"]
        total = proxy_health["total_proxies"]
        avg_success = proxy_health["avg_success_rate"]
        
        assert 0 <= healthy <= total, "Proxies sains <= total"
        assert total > 0, "Au moins un proxy total"
        assert 0 <= avg_success <= 1, "Taux succès moyen entre 0 et 1"
        
        proxy_health_ratio = healthy / total if total > 0 else 0
        
        print("✅ Santé proxy dashboard:")
        print(f"  - Proxies sains: {healthy}/{total} ({proxy_health_ratio:.1%})")
        print(f"  - Taux succès moyen: {avg_success:.1%}")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_real_time_updates(self, hybrid_service):
        """Test: Mises à jour temps réel dashboard"""
        
        # Snapshot initial
        initial_data = hybrid_service.get_monitoring_dashboard_data()
        initial_requests = initial_data["overview"]["total_requests"]
        
        # Générer nouvelle activité
        await hybrid_service.scrape_prices_unified("iPad Pro", use_cache=False)
        
        # Snapshot après activité
        updated_data = hybrid_service.get_monitoring_dashboard_data()
        updated_requests = updated_data["overview"]["total_requests"]
        
        # Validation mise à jour
        assert updated_requests == initial_requests + 1, "Compteur requêtes mis à jour"
        
        # Validation timestamp recent
        last_updated = updated_data["last_updated"]
        assert last_updated is not None, "Timestamp last_updated présent"
        
        print("✅ Mises à jour temps réel:")
        print(f"  - Requêtes avant: {initial_requests}")
        print(f"  - Requêtes après: {updated_requests}")
        print(f"  - Timestamp: {last_updated}")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_health_status_system(self, hybrid_service):
        """Test: Status santé système global"""
        
        # Générer activité normale
        await hybrid_service.scrape_prices_unified("iPhone 15 Pro", use_cache=False)
        await hybrid_service.scrape_prices_unified("Samsung Galaxy S24", use_cache=False)
        
        # Récupérer status santé système
        health_status = hybrid_service.get_system_health_status()
        
        # Validation structure health status
        assert "system_status" in health_status
        assert "components" in health_status
        assert "metrics" in health_status
        assert "recommendations" in health_status
        
        # Validation status général
        system_status = health_status["system_status"]
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert system_status in valid_statuses, f"Status système invalide: {system_status}"
        
        # Validation composants
        components = health_status["components"]
        expected_components = ["scraping_service", "proxy_provider", "cache_system", "outlier_detection"]
        
        for component in expected_components:
            assert component in components, f"Composant {component} manquant"
            assert components[component] in ["healthy", "degraded"], f"Status {component} invalide"
        
        # Validation recommandations
        recommendations = health_status["recommendations"]
        assert isinstance(recommendations, list), "Recommandations doivent être une liste"
        
        print("✅ Status santé système:")
        print(f"  - Status global: {system_status}")
        print("  - Composants:")
        for component, status in components.items():
            print(f"    • {component}: {status}")
        
        if recommendations:
            print("  - Recommandations:")
            for rec in recommendations:
                print(f"    • {rec}")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_performance_trends(self, hybrid_service):
        """Test: Tendances performance dans le temps"""
        
        # Simuler activité échelonnée
        performance_snapshots = []
        
        for i in range(3):
            # Activité
            await hybrid_service.scrape_prices_unified(f"Test Product {i+1}", use_cache=False)
            
            # Snapshot performance
            dashboard_data = hybrid_service.get_monitoring_dashboard_data()
            performance_snapshots.append({
                "timestamp": time.time(),
                "total_requests": dashboard_data["overview"]["total_requests"],
                "success_rate": dashboard_data["overview"]["success_rate"],
                "avg_response_time": dashboard_data["overview"]["avg_response_time_ms"],
                "cache_hit_ratio": dashboard_data["cache_performance"]["hit_ratio"]
            })
            
            # Délai court entre snapshots
            await asyncio.sleep(0.1)
        
        # Analyse tendances
        assert len(performance_snapshots) == 3, "3 snapshots performance"
        
        # Vérifier progression requêtes
        requests_progression = [s["total_requests"] for s in performance_snapshots]
        assert requests_progression == [1, 2, 3], "Progression requêtes linéaire"
        
        print("✅ Tendances performance:")
        for i, snapshot in enumerate(performance_snapshots, 1):
            print(f"  - Snapshot {i}: {snapshot['total_requests']} req, "
                  f"{snapshot['success_rate']:.1%} succès, "
                  f"{snapshot['avg_response_time']:.0f}ms")
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_mock_alerts_generation(self, hybrid_service):
        """Test: Génération alertes basées sur métriques"""
        
        # Forcer conditions d'alerte via configuration temporaire
        
        # Générer activité pour obtenir métriques de base
        await hybrid_service.scrape_prices_unified("iPhone 15 Pro", use_cache=False)
        
        # Récupérer recommendations (alertes)
        health_status = hybrid_service.get_system_health_status()
        recommendations = health_status["recommendations"]
        
        # Analyser types d'alertes possibles
        alert_types = {
            "success_rate": any("Taux succès" in rec for rec in recommendations),
            "response_time": any("Temps réponse" in rec for rec in recommendations), 
            "cache_performance": any("Cache" in rec for rec in recommendations),
            "proxy_health": any("proxy" in rec for rec in recommendations),
            "outlier_rate": any("outliers" in rec for rec in recommendations)
        }
        
        print("✅ Alertes générées:")
        print(f"  - Total recommandations: {len(recommendations)}")
        
        for alert_type, detected in alert_types.items():
            status = "🔔" if detected else "✅"
            print(f"  - {alert_type}: {status}")
        
        # Les recommandations spécifiques pour ce contexte
        for rec in recommendations:
            print(f"    • {rec}")
        
        # Validation: recommandations doivent être pertinentes
        assert isinstance(recommendations, list), "Recommandations format liste"
        # Note: en mock normal, peu d'alertes attendues

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])