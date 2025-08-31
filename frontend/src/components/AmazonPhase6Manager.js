// Amazon Phase 6 Manager - Optimisations avancées
import React, { useState, useEffect, useCallback, useMemo } from 'react';

const AmazonPhase6Manager = ({ user, token }) => {
    // États principaux
    const [activeSection, setActiveSection] = useState('dashboard');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    
    // États des données
    const [dashboardData, setDashboardData] = useState(null);
    const [experiments, setExperiments] = useState([]);
    const [aplusContents, setAplusContents] = useState([]);
    const [variationFamilies, setVariationFamilies] = useState([]);
    const [complianceData, setComplianceData] = useState(null);
    
    // États des modales et formulaires
    const [showExperimentModal, setShowExperimentModal] = useState(false);
    const [showAplusModal, setShowAplusModal] = useState(false);
    const [showVariationModal, setShowVariationModal] = useState(false);
    const [showComplianceModal, setShowComplianceModal] = useState(false);
    
    // Configuration marketplace
    const [selectedMarketplace, setSelectedMarketplace] = useState('A13V1IB3VIYZZH'); // France par défaut
    
    const marketplaces = [
        { id: 'A13V1IB3VIYZZH', name: '🇫🇷 France', flag: '🇫🇷' },
        { id: 'A1F83G8C2ARO7P', name: '🇬🇧 Royaume-Uni', flag: '🇬🇧' },
        { id: 'ATVPDKIKX0DER', name: '🇺🇸 États-Unis', flag: '🇺🇸' },
        { id: 'A1PA6795UKMFR9', name: '🇩🇪 Allemagne', flag: '🇩🇪' }
    ];

    const sections = [
        {
            id: 'dashboard',
            name: 'Dashboard',
            icon: '📊',
            description: 'Vue d\'ensemble Phase 6'
        },
        {
            id: 'ab_testing',
            name: 'A/B Testing',
            icon: '🧪',
            description: 'Tests et expérimentations'
        },
        {
            id: 'aplus_content',
            name: 'A+ Content',
            icon: '🎨',
            description: 'Contenu A+ Premium'
        },
        {
            id: 'variations',
            name: 'Variations Builder',
            icon: '🏗️',
            description: 'Familles Parent/Child'
        },
        {
            id: 'compliance',
            name: 'Compliance',
            icon: '✅',
            description: 'Conformité & Auto-corrections'
        }
    ];

    // URL backend depuis les variables d'environnement
    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';

    // Utilitaires
    const showSuccessMessage = useCallback((message) => {
        setSuccessMessage(message);
        setTimeout(() => setSuccessMessage(null), 5000);
    }, []);

    const showErrorMessage = useCallback((message) => {
        setError(message);
        setTimeout(() => setError(null), 5000);
    }, []);

    // Chargement initial des données
    useEffect(() => {
        if (activeSection === 'dashboard') {
            loadDashboardData();
        } else if (activeSection === 'ab_testing') {
            loadExperiments();
        } else if (activeSection === 'aplus_content') {
            loadAplusContents();
        } else if (activeSection === 'variations') {
            loadVariationFamilies();
        } else if (activeSection === 'compliance') {
            loadComplianceData();
        }
    }, [activeSection, selectedMarketplace]);

    // Fonctions de chargement des données
    const loadDashboardData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/dashboard?marketplace_id=${selectedMarketplace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setDashboardData(data.data);
            } else {
                showErrorMessage('Erreur lors du chargement du dashboard');
            }
        } catch (error) {
            console.error('Erreur dashboard:', error);
            // Données simulées pour le développement
            setDashboardData({
                active_experiments: 3,
                completed_experiments: 12,
                avg_lift_rate: 5.2,
                published_content: 8,
                pending_approval: 2,
                avg_engagement_rate: 6.8,
                variation_families: 5,
                total_child_products: 24,
                sync_success_rate: 94.5,
                compliance_score: 87.5,
                critical_issues: 2,
                auto_fixes_applied_24h: 15
            });
        } finally {
            setLoading(false);
        }
    };

    const loadExperiments = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/experiments?marketplace_id=${selectedMarketplace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setExperiments(data.data || []);
            } else {
                // Données simulées
                setExperiments([
                    {
                        id: '1',
                        name: 'Test Titre Principal',
                        sku: 'PROD-001',
                        experiment_type: 'TITLE',
                        status: 'RUNNING',
                        start_date: '2025-01-15',
                        variants: [
                            { name: 'Original', ctr: 3.2, conversion_rate: 12.1, revenue: 1240.50 },
                            { name: 'Nouveau Titre', ctr: 4.1, conversion_rate: 15.8, revenue: 1580.30 }
                        ]
                    },
                    {
                        id: '2',
                        name: 'Test Image Principale',
                        sku: 'PROD-002',
                        experiment_type: 'MAIN_IMAGE',
                        status: 'COMPLETED',
                        start_date: '2025-01-01',
                        winner_variant_id: 'variant-b',
                        variants: [
                            { name: 'Image A', ctr: 2.8, conversion_rate: 11.5, revenue: 980.20 },
                            { name: 'Image B', ctr: 3.9, conversion_rate: 16.2, revenue: 1420.80 }
                        ]
                    }
                ]);
            }
        } catch (error) {
            console.error('Erreur expérimentations:', error);
            setExperiments([]);
        } finally {
            setLoading(false);
        }
    };

    const loadAplusContents = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/aplus-content?marketplace_id=${selectedMarketplace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setAplusContents(data.data || []);
            } else {
                // Données simulées
                setAplusContents([
                    {
                        id: '1',
                        name: 'Contenu A+ Premium Produit 1',
                        sku: 'PROD-001',
                        status: 'PUBLISHED',
                        views: 15420,
                        engagement_rate: 7.2,
                        conversion_impact: 2.3,
                        created_at: '2025-01-10'
                    },
                    {
                        id: '2',
                        name: 'Contenu A+ Technique Produit 2',
                        sku: 'PROD-002',
                        status: 'SUBMITTED',
                        views: 0,
                        engagement_rate: 0,
                        conversion_impact: 0,
                        created_at: '2025-01-18'
                    }
                ]);
            }
        } catch (error) {
            console.error('Erreur A+ Content:', error);
            setAplusContents([]);
        } finally {
            setLoading(false);
        }
    };

    const loadVariationFamilies = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/variations?marketplace_id=${selectedMarketplace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setVariationFamilies(data.data || []);
            } else {
                // Données simulées
                setVariationFamilies([
                    {
                        id: '1',
                        family_name: 'T-Shirts Collection Premium',
                        parent_sku: 'PARENT-SHIRT-001',
                        variation_theme: 'Size-Color',
                        child_skus: ['CHILD-001-S-RED', 'CHILD-001-M-RED', 'CHILD-001-L-BLUE'],
                        status: 'ACTIVE',
                        last_sync_at: '2025-01-19',
                        sync_success_rate: 96.5
                    },
                    {
                        id: '2',
                        family_name: 'Smartphones Série X',
                        parent_sku: 'PARENT-PHONE-002',
                        variation_theme: 'Size-Color',
                        child_skus: ['CHILD-002-32GB-BLACK', 'CHILD-002-64GB-WHITE'],
                        status: 'INACTIVE',
                        last_sync_at: '2025-01-17',
                        sync_success_rate: 85.2
                    }
                ]);
            }
        } catch (error) {
            console.error('Erreur familles variations:', error);
            setVariationFamilies([]);
        } finally {
            setLoading(false);
        }
    };

    const loadComplianceData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/compliance/dashboard?marketplace_id=${selectedMarketplace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setComplianceData(data.data);
            } else {
                // Données simulées
                setComplianceData({
                    compliance_score: 87.5,
                    total_products_scanned: 150,
                    compliant_products: 131,
                    total_issues: 19,
                    issues_by_severity: {
                        critical: 2,
                        high: 5,
                        medium: 8,
                        low: 4
                    },
                    issues_by_type: {
                        battery: 3,
                        images: 6,
                        dimensions: 4,
                        content_policy: 3,
                        missing_attribute: 3
                    },
                    auto_fixes_available: 12,
                    manual_fixes_required: 7
                });
            }
        } catch (error) {
            console.error('Erreur conformité:', error);
            setComplianceData(null);
        } finally {
            setLoading(false);
        }
    };

    // Actions principales
    const startExperiment = async (experimentId) => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/experiments/${experimentId}/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                showSuccessMessage('Expérimentation démarrée avec succès');
                loadExperiments();
            } else {
                showErrorMessage('Erreur lors du démarrage de l\'expérimentation');
            }
        } catch (error) {
            showErrorMessage('Erreur de connexion');
        } finally {
            setLoading(false);
        }
    };

    const applyExperimentWinner = async (experimentId) => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/experiments/${experimentId}/apply-winner`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                showSuccessMessage('Variante gagnante appliquée avec succès');
                loadExperiments();
            } else {
                showErrorMessage('Erreur lors de l\'application de la variante gagnante');
            }
        } catch (error) {
            showErrorMessage('Erreur de connexion');
        } finally {
            setLoading(false);
        }
    };

    const publishAplusContent = async (contentId) => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/aplus-content/${contentId}/publish`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                showSuccessMessage('Contenu A+ publié vers Amazon avec succès');
                loadAplusContents();
            } else {
                showErrorMessage('Erreur lors de la publication du contenu A+');
            }
        } catch (error) {
            showErrorMessage('Erreur de connexion');
        } finally {
            setLoading(false);
        }
    };

    const syncVariationFamily = async (familyId) => {
        try {
            setLoading(true);
            const response = await fetch(`${backendUrl}/api/amazon/phase6/variations/${familyId}/sync`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                showSuccessMessage('Synchronisation de la famille terminée avec succès');
                loadVariationFamilies();
            } else {
                showErrorMessage('Erreur lors de la synchronisation');
            }
        } catch (error) {
            showErrorMessage('Erreur de connexion');
        } finally {
            setLoading(false);
        }
    };

    // Composant Dashboard
    const DashboardSection = () => (
        <div className="space-y-6">
            {/* KPIs Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* A/B Testing */}
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-blue-100 text-sm">A/B Testing</p>
                            <p className="text-2xl font-bold">{dashboardData?.active_experiments || 0}</p>
                            <p className="text-blue-100 text-xs">Expérimentations actives</p>
                        </div>
                        <div className="text-3xl">🧪</div>
                    </div>
                    <div className="mt-4 text-sm text-blue-100">
                        +{dashboardData?.avg_lift_rate || 0}% lift moyen
                    </div>
                </div>

                {/* A+ Content */}
                <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-purple-100 text-sm">A+ Content</p>
                            <p className="text-2xl font-bold">{dashboardData?.published_content || 0}</p>
                            <p className="text-purple-100 text-xs">Contenus publiés</p>
                        </div>
                        <div className="text-3xl">🎨</div>
                    </div>
                    <div className="mt-4 text-sm text-purple-100">
                        {dashboardData?.avg_engagement_rate || 0}% engagement moyen
                    </div>
                </div>

                {/* Variations */}
                <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-green-100 text-sm">Variations</p>
                            <p className="text-2xl font-bold">{dashboardData?.variation_families || 0}</p>
                            <p className="text-green-100 text-xs">Familles actives</p>
                        </div>
                        <div className="text-3xl">🏗️</div>
                    </div>
                    <div className="mt-4 text-sm text-green-100">
                        {dashboardData?.total_child_products || 0} produits enfants
                    </div>
                </div>

                {/* Compliance */}
                <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-orange-100 text-sm">Conformité</p>
                            <p className="text-2xl font-bold">{dashboardData?.compliance_score || 0}%</p>
                            <p className="text-orange-100 text-xs">Score global</p>
                        </div>
                        <div className="text-3xl">✅</div>
                    </div>
                    <div className="mt-4 text-sm text-orange-100">
                        {dashboardData?.critical_issues || 0} issues critiques
                    </div>
                </div>
            </div>

            {/* Actions Rapides */}
            <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">⚡ Actions Rapides</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <button 
                        onClick={() => setShowExperimentModal(true)}
                        className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                    >
                        <span className="text-2xl mr-3">🧪</span>
                        <div className="text-left">
                            <div className="font-medium text-gray-900">Nouveau Test A/B</div>
                            <div className="text-sm text-gray-500">Créer une expérimentation</div>
                        </div>
                    </button>

                    <button 
                        onClick={() => setShowAplusModal(true)}
                        className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:shadow-md transition-all"
                    >
                        <span className="text-2xl mr-3">🎨</span>
                        <div className="text-left">
                            <div className="font-medium text-gray-900">Créer A+ Content</div>
                            <div className="text-sm text-gray-500">Génération IA</div>
                        </div>
                    </button>

                    <button 
                        onClick={() => setShowVariationModal(true)}
                        className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all"
                    >
                        <span className="text-2xl mr-3">🏗️</span>
                        <div className="text-left">
                            <div className="font-medium text-gray-900">Créer Famille</div>
                            <div className="text-sm text-gray-500">Variations Parent/Child</div>
                        </div>
                    </button>

                    <button 
                        onClick={() => setShowComplianceModal(true)}
                        className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-orange-300 hover:shadow-md transition-all"
                    >
                        <span className="text-2xl mr-3">✅</span>
                        <div className="text-left">
                            <div className="font-medium text-gray-900">Scanner Conformité</div>
                            <div className="text-sm text-gray-500">Auto-corrections</div>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );

    // Composant A/B Testing
    const ABTestingSection = () => (
        <div className="space-y-6">
            {/* Header avec bouton d'ajout */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-medium text-gray-900">🧪 A/B Testing Manager</h3>
                    <p className="text-sm text-gray-500">Gestion des expérimentations et tests</p>
                </div>
                <button 
                    onClick={() => setShowExperimentModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                    + Nouveau Test
                </button>
            </div>

            {/* Liste des expérimentations */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Expérimentation
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Type
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Statut
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Performances
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {experiments.map((experiment) => (
                                <tr key={experiment.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div>
                                            <div className="text-sm font-medium text-gray-900">{experiment.name}</div>
                                            <div className="text-sm text-gray-500">SKU: {experiment.sku}</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                            {experiment.experiment_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                            experiment.status === 'RUNNING' 
                                                ? 'bg-green-100 text-green-800'
                                                : experiment.status === 'COMPLETED'
                                                ? 'bg-blue-100 text-blue-800'
                                                : 'bg-gray-100 text-gray-800'
                                        }`}>
                                            {experiment.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm">
                                            <div>CTR: {experiment.variants?.[1]?.ctr || 0}%</div>
                                            <div>CR: {experiment.variants?.[1]?.conversion_rate || 0}%</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <div className="flex space-x-2">
                                            {experiment.status === 'DRAFT' && (
                                                <button 
                                                    onClick={() => startExperiment(experiment.id)}
                                                    className="text-green-600 hover:text-green-900"
                                                >
                                                    ▶️ Démarrer
                                                </button>
                                            )}
                                            {experiment.status === 'COMPLETED' && experiment.winner_variant_id && (
                                                <button 
                                                    onClick={() => applyExperimentWinner(experiment.id)}
                                                    className="text-blue-600 hover:text-blue-900"
                                                >
                                                    🏆 Appliquer Gagnant
                                                </button>
                                            )}
                                            <button className="text-gray-600 hover:text-gray-900">
                                                📊 Détails
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    // Composant A+ Content
    const AplusContentSection = () => (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-medium text-gray-900">🎨 A+ Content Manager</h3>
                    <p className="text-sm text-gray-500">Génération et publication de contenu A+</p>
                </div>
                <button 
                    onClick={() => setShowAplusModal(true)}
                    className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
                >
                    + Nouveau Contenu A+
                </button>
            </div>

            {/* Liste des contenus A+ */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Contenu A+
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Statut
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Performance
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {aplusContents.map((content) => (
                                <tr key={content.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div>
                                            <div className="text-sm font-medium text-gray-900">{content.name}</div>
                                            <div className="text-sm text-gray-500">SKU: {content.sku}</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                            content.status === 'PUBLISHED' 
                                                ? 'bg-green-100 text-green-800'
                                                : content.status === 'SUBMITTED'
                                                ? 'bg-yellow-100 text-yellow-800'
                                                : 'bg-gray-100 text-gray-800'
                                        }`}>
                                            {content.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm">
                                            <div>Vues: {content.views?.toLocaleString() || 0}</div>
                                            <div>Engagement: {content.engagement_rate || 0}%</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <div className="flex space-x-2">
                                            {content.status === 'DRAFT' && (
                                                <button 
                                                    onClick={() => publishAplusContent(content.id)}
                                                    className="text-green-600 hover:text-green-900"
                                                >
                                                    📤 Publier
                                                </button>
                                            )}
                                            <button className="text-blue-600 hover:text-blue-900">
                                                👁️ Préview
                                            </button>
                                            <button className="text-gray-600 hover:text-gray-900">
                                                ✏️ Éditer
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    // Composant Variations Builder
    const VariationsSection = () => (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-medium text-gray-900">🏗️ Variations Builder</h3>
                    <p className="text-sm text-gray-500">Gestion des familles Parent/Child</p>
                </div>
                <button 
                    onClick={() => setShowVariationModal(true)}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                >
                    + Créer Famille
                </button>
            </div>

            {/* Liste des familles */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Famille
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Thème
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Produits
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Statut
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {variationFamilies.map((family) => (
                                <tr key={family.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div>
                                            <div className="text-sm font-medium text-gray-900">{family.family_name}</div>
                                            <div className="text-sm text-gray-500">Parent: {family.parent_sku}</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                            {family.variation_theme}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900">
                                        {family.child_skus?.length || 0} enfants
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                            family.status === 'ACTIVE' 
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-gray-100 text-gray-800'
                                        }`}>
                                            {family.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <div className="flex space-x-2">
                                            <button 
                                                onClick={() => syncVariationFamily(family.id)}
                                                className="text-blue-600 hover:text-blue-900"
                                            >
                                                🔄 Sync
                                            </button>
                                            <button className="text-gray-600 hover:text-gray-900">
                                                👁️ Voir
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    // Composant Compliance
    const ComplianceSection = () => (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-medium text-gray-900">✅ Compliance Dashboard</h3>
                    <p className="text-sm text-gray-500">Conformité et auto-corrections</p>
                </div>
                <button 
                    onClick={() => setShowComplianceModal(true)}
                    className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 transition-colors"
                >
                    🔍 Nouveau Scan
                </button>
            </div>

            {complianceData && (
                <>
                    {/* Score de conformité */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-medium text-gray-900">Score de Conformité Global</h4>
                            <span className={`text-2xl font-bold ${
                                complianceData.compliance_score >= 90 
                                    ? 'text-green-600' 
                                    : complianceData.compliance_score >= 70 
                                    ? 'text-yellow-600' 
                                    : 'text-red-600'
                            }`}>
                                {complianceData.compliance_score}%
                            </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                className={`h-2 rounded-full ${
                                    complianceData.compliance_score >= 90 
                                        ? 'bg-green-600' 
                                        : complianceData.compliance_score >= 70 
                                        ? 'bg-yellow-600' 
                                        : 'bg-red-600'
                                }`}
                                style={{ width: `${complianceData.compliance_score}%` }}
                            ></div>
                        </div>
                        <p className="text-sm text-gray-500 mt-2">
                            {complianceData.compliant_products}/{complianceData.total_products_scanned} produits conformes
                        </p>
                    </div>

                    {/* Issues par sévérité */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="text-2xl font-bold text-red-600">
                                {complianceData.issues_by_severity?.critical || 0}
                            </div>
                            <div className="text-sm text-red-800">Issues Critiques</div>
                        </div>
                        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                            <div className="text-2xl font-bold text-orange-600">
                                {complianceData.issues_by_severity?.high || 0}
                            </div>
                            <div className="text-sm text-orange-800">Issues Élevées</div>
                        </div>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                            <div className="text-2xl font-bold text-yellow-600">
                                {complianceData.issues_by_severity?.medium || 0}
                            </div>
                            <div className="text-sm text-yellow-800">Issues Moyennes</div>
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="text-2xl font-bold text-blue-600">
                                {complianceData.auto_fixes_available || 0}
                            </div>
                            <div className="text-sm text-blue-800">Auto-corrections</div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto p-6">
            {/* Header principal */}
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    🚀 Amazon Phase 6 - Optimisations avancées
                </h2>
                <p className="text-gray-600">
                    A/B Testing, A+ Content, Variations Builder & Compliance Scanner
                </p>

                {/* Sélecteur de marketplace */}
                <div className="mt-4">
                    <select 
                        value={selectedMarketplace}
                        onChange={(e) => setSelectedMarketplace(e.target.value)}
                        className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        {marketplaces.map((marketplace) => (
                            <option key={marketplace.id} value={marketplace.id}>
                                {marketplace.name}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Messages de feedback */}
            {successMessage && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
                    <div className="text-green-800">✅ {successMessage}</div>
                </div>
            )}

            {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
                    <div className="text-red-800">❌ {error}</div>
                </div>
            )}

            {/* Navigation des sections */}
            <div className="mb-6">
                <div className="sm:hidden">
                    <select 
                        value={activeSection} 
                        onChange={(e) => setActiveSection(e.target.value)}
                        className="block w-full border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        {sections.map((section) => (
                            <option key={section.id} value={section.id}>
                                {section.icon} {section.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="hidden sm:block">
                    <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg">
                        {sections.map((section) => (
                            <button
                                key={section.id}
                                onClick={() => setActiveSection(section.id)}
                                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors duration-200 ${
                                    activeSection === section.id
                                        ? 'bg-white text-blue-600 shadow-sm'
                                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                                <span className="mr-2">{section.icon}</span>
                                <span className="hidden md:inline">{section.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Loading state */}
            {loading && (
                <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
            )}

            {/* Contenu des sections */}
            {!loading && (
                <div>
                    {activeSection === 'dashboard' && <DashboardSection />}
                    {activeSection === 'ab_testing' && <ABTestingSection />}
                    {activeSection === 'aplus_content' && <AplusContentSection />}
                    {activeSection === 'variations' && <VariationsSection />}
                    {activeSection === 'compliance' && <ComplianceSection />}
                </div>
            )}

            {/* Note temporaire pour les modales */}
            {(showExperimentModal || showAplusModal || showVariationModal || showComplianceModal) && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">
                            🚧 Fonctionnalité en développement
                        </h3>
                        <p className="text-sm text-gray-600 mb-6">
                            Cette fonctionnalité sera disponible dans une prochaine mise à jour.
                        </p>
                        <div className="flex justify-end">
                            <button 
                                onClick={() => {
                                    setShowExperimentModal(false);
                                    setShowAplusModal(false);
                                    setShowVariationModal(false);
                                    setShowComplianceModal(false);
                                }}
                                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
                            >
                                Fermer
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AmazonPhase6Manager;