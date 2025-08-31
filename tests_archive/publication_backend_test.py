#!/usr/bin/env python3
"""
ECOMSIMPLY Phase 2 - Publication Automatique Multi-Plateformes Backend Testing
Tests complets du système de publication automatique sur les 7 plateformes e-commerce
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any

# Configuration de test
BACKEND_URL = "https://ecomsimply.com/api"

class PublicationSystemTester:
    """Testeur complet du système de publication ECOMSIMPLY"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECOMSIMPLY-Publication-Tester/1.0'
        })
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log un résultat de test"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and data:
            print(f"    Data: {data}")
    
    def test_backend_health(self) -> bool:
        """Test santé générale du backend"""
        try:
            response = self.session.get(f"{self.backend_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend opérationnel - Status: {health_data.get('status', 'unknown')}",
                    health_data
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False,
                f"Erreur connexion: {str(e)}"
            )
            return False
    
    def test_publication_status_endpoint(self) -> bool:
        """Test endpoint status publication"""
        try:
            response = self.session.get(f"{self.backend_url}/status/publication")
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Vérifier structure attendue
                expected_fields = ['mode', 'auto_publish', 'available_platforms', 'health_checks']
                missing_fields = [field for field in expected_fields if field not in status_data]
                
                if not missing_fields:
                    # Vérifier les 7 plateformes supportées
                    platforms = status_data.get('available_platforms', [])
                    expected_platforms = ['shopify', 'woocommerce', 'prestashop', 'magento', 'wix', 'squarespace', 'bigcommerce']
                    
                    platforms_found = [p for p in expected_platforms if p in platforms]
                    
                    self.log_test(
                        "Publication Status Endpoint",
                        len(platforms_found) == 7,
                        f"Plateformes trouvées: {len(platforms_found)}/7 - {platforms_found}",
                        status_data
                    )
                    return len(platforms_found) == 7
                else:
                    self.log_test(
                        "Publication Status Endpoint",
                        False,
                        f"Champs manquants: {missing_fields}",
                        status_data
                    )
                    return False
            else:
                self.log_test(
                    "Publication Status Endpoint",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Publication Status Endpoint",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_publication_history_endpoint(self) -> bool:
        """Test endpoint historique publications"""
        try:
            response = self.session.get(f"{self.backend_url}/publications/history")
            
            if response.status_code == 200:
                history_data = response.json()
                
                # Vérifier structure
                if isinstance(history_data, dict) and 'publications' in history_data:
                    publications = history_data['publications']
                    
                    # Vérifier qu'il y a des publications mock
                    if len(publications) > 0:
                        # Vérifier structure d'une publication
                        first_pub = publications[0]
                        expected_pub_fields = ['id', 'platform', 'product_name', 'status', 'created_at']
                        
                        pub_fields_found = [field for field in expected_pub_fields if field in first_pub]
                        
                        self.log_test(
                            "Publication History Endpoint",
                            len(pub_fields_found) == len(expected_pub_fields),
                            f"Publications trouvées: {len(publications)}, Structure: {len(pub_fields_found)}/{len(expected_pub_fields)} champs",
                            {'total_publications': len(publications), 'sample': first_pub}
                        )
                        return len(pub_fields_found) == len(expected_pub_fields)
                    else:
                        self.log_test(
                            "Publication History Endpoint",
                            True,
                            "Endpoint fonctionnel, historique vide (normal en mode test)",
                            history_data
                        )
                        return True
                else:
                    self.log_test(
                        "Publication History Endpoint",
                        False,
                        "Structure de réponse invalide",
                        history_data
                    )
                    return False
            else:
                self.log_test(
                    "Publication History Endpoint",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Publication History Endpoint",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_generate_sheet_with_publication(self) -> bool:
        """Test génération fiche avec publication automatique"""
        try:
            # Données de test pour génération avec publication
            test_data = {
                "product_name": "iPhone 15 Pro Test Publication Multi-Plateformes",
                "product_description": "Smartphone premium Apple avec puce A17 Pro, écran Super Retina XDR 6,1 pouces, appareil photo professionnel 48 Mpx avec zoom optique 3x, design en titane, résistant à l'eau IP68. Disponible en 4 coloris : Titane Naturel, Titane Bleu, Titane Blanc, Titane Noir. Stockage 128GB, 256GB, 512GB, 1TB.",
                "generate_image": False,  # Pas d'images pour test rapide
                "number_of_images": 0,
                "language": "fr",
                "category": "smartphones",
                "use_case": "Test système publication automatique multi-plateformes ECOMSIMPLY"
            }
            
            response = self.session.post(f"{self.backend_url}/generate-sheet", json=test_data)
            
            if response.status_code == 200:
                sheet_data = response.json()
                
                # Vérifier présence des résultats de publication
                if 'publication_results' in sheet_data:
                    pub_results = sheet_data['publication_results']
                    
                    if isinstance(pub_results, list) and len(pub_results) > 0:
                        # Analyser les résultats de publication
                        successful_pubs = [p for p in pub_results if p.get('success', False)]
                        platforms_published = [p.get('platform') for p in pub_results]
                        
                        # Vérifier les 7 plateformes
                        expected_platforms = ['shopify', 'woocommerce', 'prestashop', 'magento', 'wix', 'squarespace', 'bigcommerce']
                        platforms_found = [p for p in expected_platforms if p in platforms_published]
                        
                        self.log_test(
                            "Generate Sheet with Auto-Publication",
                            len(platforms_found) >= 5,  # Au moins 5/7 plateformes
                            f"Publications: {len(successful_pubs)}/{len(pub_results)} réussies sur {len(platforms_found)} plateformes",
                            {
                                'total_publications': len(pub_results),
                                'successful': len(successful_pubs),
                                'platforms': platforms_found,
                                'sample_result': pub_results[0] if pub_results else None
                            }
                        )
                        return len(platforms_found) >= 5
                    else:
                        self.log_test(
                            "Generate Sheet with Auto-Publication",
                            False,
                            "Aucun résultat de publication trouvé",
                            sheet_data
                        )
                        return False
                else:
                    # Vérifier si la génération de base fonctionne au moins
                    basic_fields = ['generated_title', 'marketing_description', 'key_features']
                    fields_found = [field for field in basic_fields if field in sheet_data]
                    
                    self.log_test(
                        "Generate Sheet with Auto-Publication",
                        len(fields_found) == len(basic_fields),
                        f"Génération de base: {len(fields_found)}/{len(basic_fields)} champs, mais pas de publication automatique",
                        {'fields_found': fields_found}
                    )
                    return len(fields_found) == len(basic_fields)
            else:
                self.log_test(
                    "Generate Sheet with Auto-Publication",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Generate Sheet with Auto-Publication",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_publication_system_integration(self) -> bool:
        """Test intégration complète du système de publication"""
        try:
            # Test 1: Vérifier que le système de publication est configuré
            status_response = self.session.get(f"{self.backend_url}/status/publication")
            
            if status_response.status_code != 200:
                self.log_test(
                    "Publication System Integration",
                    False,
                    "Endpoint status publication non accessible"
                )
                return False
            
            status_data = status_response.json()
            
            # Test 2: Vérifier mode publication automatique
            auto_publish_enabled = status_data.get('auto_publish', False)
            
            # Test 3: Vérifier plateformes disponibles
            platforms = status_data.get('available_platforms', [])
            expected_platforms = ['shopify', 'woocommerce', 'prestashop', 'magento', 'wix', 'squarespace', 'bigcommerce']
            platforms_available = len([p for p in expected_platforms if p in platforms])
            
            # Test 4: Vérifier health checks
            health_checks = status_data.get('health_checks', {})
            healthy_platforms = len([p for p, status in health_checks.items() if status.get('status') == 'healthy'])
            
            integration_score = 0
            details = []
            
            if auto_publish_enabled:
                integration_score += 25
                details.append("✅ Publication automatique activée")
            else:
                details.append("⚠️ Publication automatique désactivée")
            
            if platforms_available >= 7:
                integration_score += 35
                details.append(f"✅ Toutes les plateformes disponibles ({platforms_available}/7)")
            elif platforms_available >= 5:
                integration_score += 25
                details.append(f"⚠️ Plateformes partiellement disponibles ({platforms_available}/7)")
            else:
                details.append(f"❌ Plateformes insuffisantes ({platforms_available}/7)")
            
            if healthy_platforms >= 5:
                integration_score += 25
                details.append(f"✅ Health checks OK ({healthy_platforms} plateformes)")
            else:
                details.append(f"⚠️ Health checks partiels ({healthy_platforms} plateformes)")
            
            # Test 5: Vérifier historique accessible
            history_response = self.session.get(f"{self.backend_url}/publications/history")
            if history_response.status_code == 200:
                integration_score += 15
                details.append("✅ Historique publications accessible")
            else:
                details.append("❌ Historique publications inaccessible")
            
            success = integration_score >= 75  # 75% minimum pour considérer comme réussi
            
            self.log_test(
                "Publication System Integration",
                success,
                f"Score intégration: {integration_score}/100 - " + " | ".join(details),
                {
                    'score': integration_score,
                    'auto_publish': auto_publish_enabled,
                    'platforms_available': platforms_available,
                    'healthy_platforms': healthy_platforms,
                    'details': details
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Publication System Integration",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_publication_pipeline_end_to_end(self) -> bool:
        """Test pipeline complet scraping → publication"""
        try:
            # Simuler un pipeline complet avec un produit test
            pipeline_data = {
                "product_name": "Samsung Galaxy S24 Ultra Test Pipeline Publication",
                "product_description": "Smartphone Android premium Samsung avec écran Dynamic AMOLED 2X 6,8 pouces, processeur Snapdragon 8 Gen 3, appareil photo 200 Mpx avec zoom optique 10x, S Pen intégré, batterie 5000 mAh, charge rapide 45W. Disponible en 256GB, 512GB, 1TB. Couleurs : Titane Violet, Titane Noir, Titane Gris, Titane Jaune.",
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": "smartphones",
                "use_case": "Test pipeline end-to-end scraping vers publication automatique"
            }
            
            # Étape 1: Génération avec publication automatique
            start_time = time.time()
            response = self.session.post(f"{self.backend_url}/generate-sheet", json=pipeline_data)
            generation_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_test(
                    "Publication Pipeline End-to-End",
                    False,
                    f"Échec génération: {response.status_code}",
                    response.text
                )
                return False
            
            sheet_data = response.json()
            
            # Étape 2: Vérifier contenu généré
            required_fields = ['generated_title', 'marketing_description', 'key_features', 'seo_tags']
            content_fields = [field for field in required_fields if field in sheet_data and sheet_data[field]]
            
            # Étape 3: Vérifier publications
            publication_results = sheet_data.get('publication_results', [])
            
            if not publication_results:
                self.log_test(
                    "Publication Pipeline End-to-End",
                    False,
                    "Aucun résultat de publication dans la réponse",
                    sheet_data
                )
                return False
            
            # Analyser résultats publication
            successful_publications = [p for p in publication_results if p.get('success', False)]
            failed_publications = [p for p in publication_results if not p.get('success', False)]
            
            platforms_published = [p.get('platform') for p in successful_publications]
            expected_platforms = ['shopify', 'woocommerce', 'prestashop', 'magento', 'wix', 'squarespace', 'bigcommerce']
            
            # Étape 4: Vérifier idempotence (optionnel)
            idempotent_publications = [p for p in publication_results if 'idempotent' in p.get('metadata', {})]
            
            # Calcul score pipeline
            pipeline_score = 0
            pipeline_details = []
            
            # Contenu généré (30 points)
            if len(content_fields) == len(required_fields):
                pipeline_score += 30
                pipeline_details.append(f"✅ Contenu complet ({len(content_fields)}/{len(required_fields)} champs)")
            else:
                pipeline_score += (len(content_fields) / len(required_fields)) * 30
                pipeline_details.append(f"⚠️ Contenu partiel ({len(content_fields)}/{len(required_fields)} champs)")
            
            # Publications réussies (50 points)
            success_rate = len(successful_publications) / len(publication_results) if publication_results else 0
            pipeline_score += success_rate * 50
            pipeline_details.append(f"📤 Publications: {len(successful_publications)}/{len(publication_results)} réussies ({success_rate:.1%})")
            
            # Couverture plateformes (20 points)
            platform_coverage = len(platforms_published) / len(expected_platforms)
            pipeline_score += platform_coverage * 20
            pipeline_details.append(f"🏪 Plateformes: {len(platforms_published)}/{len(expected_platforms)} couvertes")
            
            # Performance (bonus)
            if generation_time < 30:  # Moins de 30 secondes
                pipeline_details.append(f"⚡ Performance: {generation_time:.1f}s")
            else:
                pipeline_details.append(f"⏱️ Performance: {generation_time:.1f}s")
            
            success = pipeline_score >= 70  # 70% minimum
            
            self.log_test(
                "Publication Pipeline End-to-End",
                success,
                f"Score pipeline: {pipeline_score:.1f}/100 - " + " | ".join(pipeline_details),
                {
                    'score': pipeline_score,
                    'generation_time': generation_time,
                    'content_fields': len(content_fields),
                    'successful_publications': len(successful_publications),
                    'total_publications': len(publication_results),
                    'platforms_covered': len(platforms_published),
                    'platforms_published': platforms_published,
                    'sample_publication': successful_publications[0] if successful_publications else None
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Publication Pipeline End-to-End",
                False,
                f"Erreur pipeline: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests et retourne un rapport complet"""
        print("🚀 DÉMARRAGE TESTS SYSTÈME PUBLICATION AUTOMATIQUE ECOMSIMPLY")
        print("=" * 80)
        
        start_time = time.time()
        
        # Tests principaux
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Publication Status API", self.test_publication_status_endpoint),
            ("Publication History API", self.test_publication_history_endpoint),
            ("Generate Sheet with Auto-Publication", self.test_generate_sheet_with_publication),
            ("Publication System Integration", self.test_publication_system_integration),
            ("Publication Pipeline End-to-End", self.test_publication_pipeline_end_to_end)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Test: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
        
        total_time = time.time() - start_time
        success_rate = (passed_tests / total_tests) * 100
        
        # Rapport final
        print("\n" + "=" * 80)
        print("📊 RAPPORT FINAL - SYSTÈME PUBLICATION AUTOMATIQUE ECOMSIMPLY")
        print("=" * 80)
        print(f"✅ Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️ Temps total: {total_time:.1f}s")
        
        # Détail des résultats
        print(f"\n📋 DÉTAIL DES TESTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # Évaluation globale
        if success_rate >= 90:
            overall_status = "🎉 EXCELLENT"
            print(f"\n{overall_status} - Système de publication automatique pleinement opérationnel!")
        elif success_rate >= 75:
            overall_status = "✅ BON"
            print(f"\n{overall_status} - Système de publication automatique fonctionnel avec quelques améliorations possibles.")
        elif success_rate >= 50:
            overall_status = "⚠️ PARTIEL"
            print(f"\n{overall_status} - Système de publication automatique partiellement fonctionnel, corrections nécessaires.")
        else:
            overall_status = "❌ CRITIQUE"
            print(f"\n{overall_status} - Système de publication automatique nécessite des corrections majeures.")
        
        return {
            'overall_status': overall_status,
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'total_time': total_time,
            'test_results': self.test_results,
            'summary': {
                'backend_health': any(r['success'] for r in self.test_results if 'Health' in r['test_name']),
                'publication_apis': any(r['success'] for r in self.test_results if 'API' in r['test_name'] or 'Endpoint' in r['test_name']),
                'auto_publication': any(r['success'] for r in self.test_results if 'Auto-Publication' in r['test_name']),
                'system_integration': any(r['success'] for r in self.test_results if 'Integration' in r['test_name']),
                'end_to_end_pipeline': any(r['success'] for r in self.test_results if 'End-to-End' in r['test_name'])
            }
        }

def main():
    """Fonction principale"""
    tester = PublicationSystemTester()
    results = tester.run_all_tests()
    
    # Sauvegarde des résultats
    with open('/app/publication_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans: /app/publication_test_results.json")
    
    return results['success_rate'] >= 75

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)