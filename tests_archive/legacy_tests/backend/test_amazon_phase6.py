"""
Tests Backend Amazon Phase 6 - Optimisations avancées
Tests pour A/B Testing, A+ Content, Variations Builder, Compliance Scanner
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, ANY
from datetime import datetime, timedelta
import json
import uuid

# Imports des modèles et services Phase 6
from models.amazon_phase6 import (
    ABTestExperiment, AplusContent, VariationFamily, ComplianceReport,
    ExperimentStatus, AplusContentStatus, VariationStatus,
    ExperimentType, ComplianceIssueType, ComplianceSeverity
)
from amazon.experiments import ab_testing_engine
from amazon.aplus_content import aplus_content_engine
from amazon.variations_builder import variations_builder_engine
from amazon.compliance_scanner import compliance_scanner_engine
from services.amazon_phase6_service import amazon_phase6_service

# Configuration de test
pytestmark = pytest.mark.asyncio


class TestABTestingEngine:
    """Tests pour le moteur A/B Testing"""
    
    @pytest.fixture
    def experiment_config(self):
        """Configuration d'expérimentation de test"""
        return {
            'name': 'Test Titre Principal',
            'description': 'Test d\'optimisation du titre',
            'experiment_type': 'TITLE',
            'duration_days': 14,
            'primary_metric': 'conversion_rate',
            'confidence_level': 95.0,
            'auto_apply_winner': False,
            'variants': [
                {
                    'name': 'Original',
                    'content': {'title': 'Titre Original'},
                    'traffic_percentage': 50.0
                },
                {
                    'name': 'Nouveau Titre',
                    'content': {'title': 'Nouveau Titre Optimisé'},
                    'traffic_percentage': 50.0
                }
            ]
        }
    
    async def test_create_experiment_success(self, experiment_config):
        """Test de création d'expérimentation réussie"""
        user_id = "test_user_123"
        sku = "TEST-PRODUCT-001"
        marketplace_id = "A13V1IB3VIYZZH"
        
        with patch.object(ab_testing_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse Amazon réussie
            mock_api.return_value = {
                'success': True,
                'data': {'experimentId': 'EXP-123456'}
            }
            
            experiment = await ab_testing_engine.create_experiment(
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                experiment_config=experiment_config
            )
            
            # Vérifications
            assert experiment is not None
            assert experiment.user_id == user_id
            assert experiment.sku == sku
            assert experiment.marketplace_id == marketplace_id
            assert experiment.name == experiment_config['name']
            assert experiment.experiment_type == ExperimentType.TITLE
            assert len(experiment.variants) == 2
            assert experiment.amazon_experiment_id == 'EXP-123456'
    
    async def test_create_experiment_validation_error(self, experiment_config):
        """Test de validation d'expérimentation échouée"""
        user_id = "test_user_123"
        sku = "TEST-PRODUCT-001"
        marketplace_id = "A13V1IB3VIYZZH"
        
        # Configuration invalide - un seule variante
        experiment_config['variants'] = [experiment_config['variants'][0]]
        
        with pytest.raises(ValueError, match="Au moins 2 variantes sont requises"):
            await ab_testing_engine.create_experiment(
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                experiment_config=experiment_config
            )
    
    async def test_start_experiment_success(self):
        """Test de démarrage d'expérimentation réussi"""
        experiment = ABTestExperiment(
            id="test_exp_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test Experiment",
            experiment_type=ExperimentType.TITLE,
            amazon_experiment_id="EXP-123456"
        )
        
        with patch.object(ab_testing_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {'success': True}
            
            success = await ab_testing_engine.start_experiment(experiment)
            
            assert success is True
            assert experiment.status == ExperimentStatus.RUNNING
            assert experiment.start_date is not None
    
    async def test_collect_experiment_metrics_success(self):
        """Test de collecte de métriques réussie"""
        experiment = ABTestExperiment(
            id="test_exp_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test Experiment",
            experiment_type=ExperimentType.TITLE,
            status=ExperimentStatus.RUNNING,
            amazon_experiment_id="EXP-123456",
            start_date=datetime.utcnow() - timedelta(days=5)
        )
        
        with patch.object(ab_testing_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse métriques Amazon
            mock_api.return_value = {
                'success': True,
                'data': {
                    'variants': [
                        {
                            'variantId': 'variant1',
                            'impressions': 10000,
                            'clicks': 320,
                            'conversions': 48,
                            'revenue': 1240.50
                        }
                    ]
                }
            }
            
            # Ajouter une variante avec l'ID correspondant
            from models.amazon_phase6 import ExperimentVariant
            variant = ExperimentVariant(id='variant1', name='Test Variant', content={})
            experiment.variants = [variant]
            
            metrics = await ab_testing_engine.collect_experiment_metrics(experiment)
            
            assert metrics['success'] is True
            assert metrics['total_impressions'] > 0
            assert experiment.variants[0].impressions == 10000
            assert experiment.variants[0].clicks == 320
    
    async def test_analyze_experiment_results_sufficient_data(self):
        """Test d'analyse statistique avec données suffisantes"""
        from models.amazon_phase6 import ExperimentVariant
        
        experiment = ABTestExperiment(
            id="test_exp_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test Experiment",
            experiment_type=ExperimentType.TITLE,
            status=ExperimentStatus.RUNNING
        )
        
        # Créer des variantes avec des données suffisantes
        control_variant = ExperimentVariant(
            id='control',
            name='Control',
            content={},
            impressions=10000,
            clicks=1000,
            conversions=100
        )
        
        treatment_variant = ExperimentVariant(
            id='treatment',
            name='Treatment',
            content={},
            impressions=10000,
            clicks=1200,
            conversions=130
        )
        
        experiment.variants = [control_variant, treatment_variant]
        
        analysis = await ab_testing_engine.analyze_experiment_results(experiment)
        
        assert analysis['status'] == 'analysis_complete'
        assert 'statistical_significance' in analysis
        assert 'lift_percent' in analysis
        assert 'winner' in analysis
        assert analysis['sample_size_adequate'] is True
    
    async def test_apply_winner_success(self):
        """Test d'application de variante gagnante réussie"""
        from models.amazon_phase6 import ExperimentVariant
        
        winner_variant = ExperimentVariant(
            id='winner_variant',
            name='Winner',
            content={'title': 'Titre Gagnant'}
        )
        
        experiment = ABTestExperiment(
            id="test_exp_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test Experiment",
            experiment_type=ExperimentType.TITLE,
            winner_variant_id='winner_variant',
            variants=[winner_variant]
        )
        
        with patch.object(ab_testing_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {'success': True}
            
            success = await ab_testing_engine.apply_winner(experiment)
            
            assert success is True
            assert experiment.status == ExperimentStatus.COMPLETED


class TestAplusContentEngine:
    """Tests pour le moteur A+ Content"""
    
    @pytest.fixture
    def content_config(self):
        """Configuration de contenu A+ de test"""
        return {
            'name': 'Contenu A+ Test',
            'description': 'Description test',
            'language': 'fr-FR',
            'use_ai_generation': True,
            'modules_types': ['STANDARD_SINGLE_IMAGE_TEXT'],
            'style_preferences': {'tone': 'professional'}
        }
    
    async def test_create_aplus_content_success(self, content_config):
        """Test de création de contenu A+ réussie"""
        user_id = "test_user_123"
        sku = "TEST-PRODUCT-001"
        marketplace_id = "A13V1IB3VIYZZH"
        
        with patch.object(aplus_content_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_catalog:
            # Mock réponse Catalog API
            mock_catalog.return_value = {
                'success': True,
                'data': {
                    'asin': 'B0123456789',
                    'attributes': {
                        'item_name': ['Produit Test'],
                        'brand': ['Marque Test'],
                        'product_description': ['Description produit test']
                    }
                }
            }
            
            with patch('services.gpt_content_service.gpt_content_service.generate_aplus_content', new_callable=AsyncMock) as mock_gpt:
                mock_gpt.return_value = {
                    'header': 'En-tête Test',
                    'main_description': 'Description principale test',
                    'features_description': 'Caractéristiques test'
                }
                
                aplus_content = await aplus_content_engine.create_aplus_content(
                    user_id=user_id,
                    sku=sku,
                    marketplace_id=marketplace_id,
                    content_config=content_config
                )
                
                # Vérifications
                assert aplus_content is not None
                assert aplus_content.user_id == user_id
                assert aplus_content.sku == sku
                assert aplus_content.name == content_config['name']
                assert len(aplus_content.modules) > 0
    
    async def test_publish_aplus_content_success(self):
        """Test de publication de contenu A+ réussie"""
        aplus_content = AplusContent(
            id="test_content_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test A+ Content"
        )
        
        with patch.object(aplus_content_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse publication réussie
            mock_api.return_value = {
                'success': True,
                'data': {'contentReferenceId': 'CONTENT-123456'}
            }
            
            success = await aplus_content_engine.publish_aplus_content(aplus_content)
            
            assert success is True
            assert aplus_content.amazon_content_id == 'CONTENT-123456'
            assert aplus_content.status == AplusContentStatus.SUBMITTED
    
    async def test_check_approval_status_approved(self):
        """Test de vérification de statut approuvé"""
        aplus_content = AplusContent(
            id="test_content_123",
            user_id="test_user_123",
            sku="TEST-PRODUCT-001",
            marketplace_id="A13V1IB3VIYZZH",
            name="Test A+ Content",
            amazon_content_id="CONTENT-123456"
        )
        
        with patch.object(aplus_content_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                'success': True,
                'data': {'status': 'APPROVED'}
            }
            
            status = await aplus_content_engine.check_approval_status(aplus_content)
            
            assert status == 'approved'
            assert aplus_content.status == AplusContentStatus.APPROVED


class TestVariationsBuilderEngine:
    """Tests pour le moteur Variations Builder"""
    
    async def test_detect_variation_families_success(self):
        """Test de détection de familles de variations réussie"""
        user_id = "test_user_123"
        marketplace_id = "A13V1IB3VIYZZH"
        sku_list = ["SHIRT-RED-M", "SHIRT-RED-L", "SHIRT-BLUE-M", "SHIRT-BLUE-L"]
        
        with patch.object(variations_builder_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponses Catalog API pour chaque SKU
            def mock_catalog_response(method, endpoint, marketplace_id, **kwargs):
                sku = endpoint.split('/')[-1]
                return {
                    'success': True,
                    'data': {
                        'asin': f'B{sku}',
                        'attributes': {
                            'item_name': [f'T-Shirt {sku}'],
                            'brand': ['TestBrand'],
                            'size': [sku.split('-')[2]],  # M ou L
                            'color': [sku.split('-')[1]]  # RED ou BLUE
                        }
                    }
                }
            
            mock_api.side_effect = mock_catalog_response
            
            families = await variations_builder_engine.detect_variation_families(
                user_id=user_id,
                marketplace_id=marketplace_id,
                sku_list=sku_list
            )
            
            assert len(families) > 0
            family = families[0]
            assert family['has_variations'] is True
            assert 'Color' in family['variation_themes'] or 'Size' in family['variation_themes']
    
    async def test_create_variation_family_success(self):
        """Test de création de famille de variations réussie"""
        user_id = "test_user_123"
        marketplace_id = "A13V1IB3VIYZZH"
        
        family_config = {
            'parent_sku': 'PARENT-SHIRT-001',
            'family_name': 'T-Shirts Collection',
            'variation_theme': 'Size-Color',
            'child_skus': ['CHILD-SHIRT-001-S-RED', 'CHILD-SHIRT-001-M-RED'],
            'children': [
                {
                    'sku': 'CHILD-SHIRT-001-S-RED',
                    'variation_attributes': {'size': 'S', 'color': 'Red'}
                }
            ]
        }
        
        with patch.object(variations_builder_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse feed création réussie
            mock_api.return_value = {
                'success': True,
                'data': {'feedId': 'FEED-123456'}
            }
            
            with patch.object(variations_builder_engine, '_upload_feed_document', new_callable=AsyncMock) as mock_upload:
                mock_upload.return_value = 'DOC-123456'
                
                with patch.object(variations_builder_engine, '_monitor_feed_processing', new_callable=AsyncMock) as mock_monitor:
                    mock_monitor.return_value = True
                    
                    family = await variations_builder_engine.create_variation_family(
                        user_id=user_id,
                        marketplace_id=marketplace_id,
                        family_config=family_config
                    )
                    
                    assert family is not None
                    assert family.user_id == user_id
                    assert family.family_name == family_config['family_name']
                    assert family.status == VariationStatus.ACTIVE
                    assert len(family.relationships) > 0


class TestComplianceScannerEngine:
    """Tests pour le scanner de conformité"""
    
    async def test_scan_user_products_success(self):
        """Test de scan de conformité réussi"""
        user_id = "test_user_123"
        marketplace_id = "A13V1IB3VIYZZH"
        sku_list = ["TEST-PRODUCT-001", "TEST-PRODUCT-002"]
        
        with patch.object(compliance_scanner_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse Catalog API
            def mock_catalog_response(method, endpoint, marketplace_id, **kwargs):
                sku = endpoint.split('/')[-1]
                return {
                    'success': True,
                    'data': {
                        'asin': f'B{sku}',
                        'attributes': {
                            'item_name': [f'Produit {sku}'],
                            'brand': ['TestBrand'],
                            'product_description': ['Description test avec batterie lithium']
                        },
                        'images': [
                            {'link': f'https://example.com/image_{sku}.jpg'}
                        ]
                    }
                }
            
            mock_api.side_effect = mock_catalog_response
            
            report = await compliance_scanner_engine.scan_user_products(
                user_id=user_id,
                marketplace_id=marketplace_id,
                sku_list=sku_list
            )
            
            assert report is not None
            assert report.user_id == user_id
            assert report.total_skus == len(sku_list)
            assert report.compliance_score <= 100.0
    
    async def test_apply_auto_fixes_dry_run(self):
        """Test d'application de corrections en mode dry run"""
        from models.amazon_phase6 import ComplianceIssue
        
        issues = [
            ComplianceIssue(
                id="issue1",
                user_id="test_user_123",
                sku="TEST-PRODUCT-001",
                marketplace_id="A13V1IB3VIYZZH",
                issue_type=ComplianceIssueType.IMAGES,
                severity=ComplianceSeverity.MEDIUM,
                title="Images insuffisantes",
                description="Seulement 1 image, minimum 2 requis",
                auto_fixable=True
            )
        ]
        
        fix_results = await compliance_scanner_engine.apply_auto_fixes(
            issues=issues,
            dry_run=True
        )
        
        assert fix_results['success'] is not False
        assert fix_results['auto_fixable'] == 1
        assert fix_results['total_issues'] == 1


class TestAmazonPhase6Service:
    """Tests pour le service Phase 6"""
    
    async def test_get_phase6_dashboard_data_success(self):
        """Test de récupération des données dashboard Phase 6"""
        user_id = "test_user_123"
        marketplace_id = "A13V1IB3VIYZZH"
        
        dashboard_data = await amazon_phase6_service.get_phase6_dashboard_data(
            user_id=user_id,
            marketplace_id=marketplace_id
        )
        
        assert dashboard_data is not None
        assert hasattr(dashboard_data, 'active_experiments')
        assert hasattr(dashboard_data, 'published_content')
        assert hasattr(dashboard_data, 'variation_families')
        assert hasattr(dashboard_data, 'compliance_score')
    
    async def test_create_ab_experiment_service_success(self):
        """Test de création d'expérimentation via service"""
        user_id = "test_user_123"
        sku = "TEST-PRODUCT-001"
        marketplace_id = "A13V1IB3VIYZZH"
        
        experiment_config = {
            'name': 'Service Test Experiment',
            'experiment_type': 'TITLE',
            'variants': [
                {'name': 'Control', 'content': {'title': 'Original'}, 'traffic_percentage': 50.0},
                {'name': 'Treatment', 'content': {'title': 'New Title'}, 'traffic_percentage': 50.0}
            ]
        }
        
        with patch.object(amazon_phase6_service.ab_testing, 'create_experiment', new_callable=AsyncMock) as mock_create:
            mock_experiment = ABTestExperiment(
                id="test_exp_456",
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                name=experiment_config['name'],
                experiment_type=ExperimentType.TITLE
            )
            mock_create.return_value = mock_experiment
            
            result = await amazon_phase6_service.create_ab_experiment(
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                experiment_config=experiment_config
            )
            
            assert result is not None
            assert result.name == experiment_config['name']
            mock_create.assert_called_once()


class TestPhase6Integration:
    """Tests d'intégration Phase 6"""
    
    async def test_full_ab_testing_workflow(self):
        """Test du workflow complet A/B Testing"""
        # Configuration
        user_id = "test_user_integration"
        sku = "INTEGRATION-PRODUCT-001"
        marketplace_id = "A13V1IB3VIYZZH"
        
        experiment_config = {
            'name': 'Integration Test Experiment',
            'experiment_type': 'TITLE',
            'duration_days': 7,
            'variants': [
                {'name': 'Original', 'content': {'title': 'Titre Original'}, 'traffic_percentage': 50.0},
                {'name': 'Optimisé', 'content': {'title': 'Titre Optimisé SEO'}, 'traffic_percentage': 50.0}
            ]
        }
        
        # Mock toutes les interactions SP-API
        with patch.object(ab_testing_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponses séquentielles
            mock_responses = [
                # Création d'expérimentation
                {'success': True, 'data': {'experimentId': 'INT-EXP-123'}},
                # Récupération ASIN
                {'success': True, 'data': {'asin': 'B0INTEGRATION'}},
                # Démarrage expérimentation
                {'success': True},
                # Collecte métriques
                {
                    'success': True,
                    'data': {
                        'variants': [
                            {'variantId': 'var1', 'impressions': 1000, 'clicks': 50, 'conversions': 8, 'revenue': 240.0},
                            {'variantId': 'var2', 'impressions': 1000, 'clicks': 65, 'conversions': 12, 'revenue': 360.0}
                        ]
                    }
                },
                # Application gagnant
                {'success': True}
            ]
            mock_api.side_effect = mock_responses
            
            # Étape 1: Créer l'expérimentation
            experiment = await amazon_phase6_service.create_ab_experiment(
                user_id=user_id,
                sku=sku,
                marketplace_id=marketplace_id,
                experiment_config=experiment_config
            )
            
            assert experiment.amazon_experiment_id == 'INT-EXP-123'
            
            # Étape 2: Démarrer l'expérimentation
            started = await amazon_phase6_service.start_ab_experiment(
                experiment_id=experiment.id,
                user_id=user_id
            )
            
            assert started is True
            
            # Étape 3: Collecter les métriques (simulé)
            metrics = await amazon_phase6_service.collect_experiment_metrics(
                experiment_id=experiment.id,
                user_id=user_id
            )
            
            assert metrics.get('success') is not False
            
            # Étape 4: Analyser les résultats
            analysis = await amazon_phase6_service.analyze_experiment_results(
                experiment_id=experiment.id,
                user_id=user_id
            )
            
            assert analysis is not None
            
            # Vérifier que le workflow est cohérent
            assert len(mock_api.call_args_list) >= 3  # Au moins 3 appels API
    
    async def test_compliance_to_auto_fix_workflow(self):
        """Test du workflow complet Compliance → Auto-fix"""
        user_id = "test_user_compliance"
        marketplace_id = "A13V1IB3VIYZZH"
        sku_list = ["COMPLIANCE-TEST-001", "COMPLIANCE-TEST-002"]
        
        with patch.object(compliance_scanner_engine.sp_api_client, 'make_request', new_callable=AsyncMock) as mock_api:
            # Mock réponse Catalog avec problèmes de conformité
            def mock_catalog_with_issues(method, endpoint, marketplace_id, **kwargs):
                sku = endpoint.split('/')[-1]
                return {
                    'success': True,
                    'data': {
                        'asin': f'B{sku}',
                        'attributes': {
                            'item_name': [f'Produit {sku} avec batterie lithium meilleur prix garantie'],  # Issues: battery + content policy
                            'brand': ['TestBrand']
                        },
                        'images': []  # Issue: pas d'images
                    }
                }
            
            mock_api.side_effect = mock_catalog_with_issues
            
            # Étape 1: Scanner la conformité
            report = await amazon_phase6_service.scan_compliance(
                user_id=user_id,
                marketplace_id=marketplace_id,
                sku_list=sku_list
            )
            
            assert report is not None
            assert report.issues_found > 0
            
            # Étape 2: Appliquer les auto-corrections en dry run
            fix_results = await amazon_phase6_service.apply_compliance_auto_fixes(
                report_id=report.id,
                user_id=user_id,
                dry_run=True
            )
            
            assert fix_results is not None
            assert fix_results.get('auto_fixable', 0) > 0
            
            # Vérifier que le workflow détecte bien les problèmes
            battery_issues = [i for i in report.issues if i.issue_type == ComplianceIssueType.BATTERY]
            content_issues = [i for i in report.issues if i.issue_type == ComplianceIssueType.CONTENT_POLICY]
            image_issues = [i for i in report.issues if i.issue_type == ComplianceIssueType.IMAGES]
            
            # Au moins un type d'issue devrait être détecté
            assert len(battery_issues) > 0 or len(content_issues) > 0 or len(image_issues) > 0


# Exécution des tests
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Lancer les tests avec pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])
    
    sys.exit(result.returncode)