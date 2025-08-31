// Amazon Monitoring Dashboard - Phase 5
import React, { useState, useEffect, useCallback } from 'react';

const AmazonMonitoringDashboard = ({ user, token }) => {
    // États principaux
    const [activeSection, setActiveSection] = useState('dashboard');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // États des données
    const [dashboardData, setDashboardData] = useState(null);
    const [monitoringJobs, setMonitoringJobs] = useState([]);
    const [snapshots, setSnapshots] = useState([]);
    const [optimizations, setOptimizations] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [desiredStates, setDesiredStates] = useState({});

    // Configuration API
    const backendUrl = process.env.REACT_APP_BACKEND_URL || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8001');

    // Sections de navigation
    const sections = [
        { id: 'dashboard', name: '📊 Dashboard', icon: '📊' },
        { id: 'jobs', name: '🔄 Jobs Monitoring', icon: '🔄' },
        { id: 'snapshots', name: '📸 Snapshots', icon: '📸' },
        { id: 'optimizations', name: '⚙️ Optimisations', icon: '⚙️' },
        { id: 'alerts', name: '🚨 Alertes', icon: '🚨' },
        { id: 'settings', name: '⚙️ Configuration', icon: '⚙️' }
    ];

    // Marketplaces disponibles
    const marketplaces = [
        { id: 'A13V1IB3VIYZZH', name: '🇫🇷 France', domain: 'amazon.fr' },
        { id: 'A1F83G8C2ARO7P', name: '🇬🇧 UK', domain: 'amazon.co.uk' },
        { id: 'ATVPDKIKX0DER', name: '🇺🇸 USA', domain: 'amazon.com' },
        { id: 'A1PA6795UKMFR9', name: '🇩🇪 Allemagne', domain: 'amazon.de' }
    ];

    const [selectedMarketplace, setSelectedMarketplace] = useState('A13V1IB3VIYZZH');

    // Fonction utilitaire pour les appels API
    const apiCall = async (endpoint, method = 'GET', data = null) => {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            };

            if (data && method !== 'GET') {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`${backendUrl}${endpoint}`, options);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    };

    // Charger les données initiales
    useEffect(() => {
        if (user && token) {
            loadInitialData();
        }
    }, [user, token, selectedMarketplace, activeSection]);

    const loadInitialData = async () => {
        try {
            if (activeSection === 'dashboard') {
                await loadDashboardData();
            } else if (activeSection === 'jobs') {
                await loadMonitoringJobs();
            } else if (activeSection === 'snapshots') {
                await loadSnapshots();
            } else if (activeSection === 'optimizations') {
                await loadOptimizations();
            } else if (activeSection === 'alerts') {
                await loadAlerts();
            }
        } catch (error) {
            setError(`Erreur lors du chargement: ${error.message}`);
        }
    };

    const loadDashboardData = async () => {
        try {
            const data = await apiCall(`/api/amazon/monitoring/dashboard?marketplace_id=${selectedMarketplace}`);
            setDashboardData(data);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            setError('Erreur lors du chargement du dashboard');
        }
    };

    const loadMonitoringJobs = async () => {
        try {
            const data = await apiCall(`/api/amazon/monitoring/jobs?marketplace_id=${selectedMarketplace}`);
            setMonitoringJobs(data);
        } catch (error) {
            console.error('Error loading monitoring jobs:', error);
            setError('Erreur lors du chargement des jobs de monitoring');
        }
    };

    const loadSnapshots = async () => {
        try {
            const data = await apiCall(`/api/amazon/monitoring/snapshots?marketplace_id=${selectedMarketplace}&limit=50`);
            setSnapshots(data);
        } catch (error) {
            console.error('Error loading snapshots:', error);
            setError('Erreur lors du chargement des snapshots');
        }
    };

    const loadOptimizations = async () => {
        try {
            const data = await apiCall(`/api/amazon/monitoring/optimizations?marketplace_id=${selectedMarketplace}`);
            setOptimizations(data.decisions || []);
        } catch (error) {
            console.error('Error loading optimizations:', error);
            setError('Erreur lors du chargement des optimisations');
        }
    };

    const loadAlerts = async () => {
        try {
            const data = await apiCall(`/api/amazon/monitoring/alerts?marketplace_id=${selectedMarketplace}`);
            setAlerts(data);
        } catch (error) {
            console.error('Error loading alerts:', error);
            setError('Erreur lors du chargement des alertes');
        }
    };

    // Gestionnaires d'événements
    const handleTriggerOptimization = async (sku = null) => {
        setLoading(true);
        try {
            const payload = {
                marketplace_id: selectedMarketplace
            };
            
            if (sku) {
                payload.sku = sku;
            }

            await apiCall('/api/amazon/monitoring/optimize', 'POST', payload);
            setSuccessMessage(sku ? `Optimisation lancée pour ${sku}` : 'Cycle d\'optimisation global lancé');
            
            // Recharger les données
            setTimeout(() => {
                loadOptimizations();
            }, 2000);
            
        } catch (error) {
            setError(`Erreur lors du déclenchement: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleTriggerMonitoringCycle = async () => {
        setLoading(true);
        try {
            await apiCall('/api/amazon/monitoring/system/trigger-cycle', 'POST');
            setSuccessMessage('Cycle de monitoring lancé manuellement');
            
            // Recharger les données
            setTimeout(() => {
                loadInitialData();
            }, 5000);
            
        } catch (error) {
            setError(`Erreur lors du déclenchement: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Composant Messages
    const MessageAlerts = () => (
        <>
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center">
                        <span className="text-red-500 text-xl mr-3">❌</span>
                        <div>
                            <h3 className="text-red-800 font-medium">Erreur</h3>
                            <p className="text-red-700 text-sm">{error}</p>
                        </div>
                        <button
                            onClick={() => setError(null)}
                            className="ml-auto text-red-500 hover:text-red-700"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {successMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center">
                        <span className="text-green-500 text-xl mr-3">✅</span>
                        <div>
                            <h3 className="text-green-800 font-medium">Succès</h3>
                            <p className="text-green-700 text-sm">{successMessage}</p>
                        </div>
                        <button
                            onClick={() => setSuccessMessage(null)}
                            className="ml-auto text-green-500 hover:text-green-700"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}
        </>
    );

    // Indicateur de chargement
    const LoadingIndicator = () => (
        loading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-center">
                    <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mr-3"></div>
                    <span className="text-blue-700">Traitement en cours...</span>
                </div>
            </div>
        )
    );

    // Composant Dashboard
    const DashboardSection = () => (
        <div className="space-y-4 sm:space-y-6">
            {/* KPIs principaux */}
            {dashboardData?.kpis && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">SKUs Monitorés</h3>
                        <p className="text-2xl font-bold text-blue-600">{dashboardData.kpis.total_skus_monitored}</p>
                        <p className="text-xs text-gray-500">{dashboardData.kpis.active_listings} actifs</p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">Buy Box Share</h3>
                        <p className="text-2xl font-bold text-green-600">{dashboardData.kpis.buybox_share_avg.toFixed(1)}%</p>
                        <p className="text-xs text-gray-500">
                            {dashboardData.kpis.buybox_won_count} gagnées, {dashboardData.kpis.buybox_lost_count} perdues
                        </p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">Auto-corrections</h3>
                        <p className="text-2xl font-bold text-purple-600">{dashboardData.kpis.auto_corrections_successful}</p>
                        <p className="text-xs text-gray-500">
                            {dashboardData.kpis.auto_corrections_triggered} déclenchées
                        </p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">API Calls</h3>
                        <p className="text-2xl font-bold text-orange-600">{dashboardData.kpis.api_calls_count}</p>
                        <p className="text-xs text-gray-500">
                            {dashboardData.kpis.api_errors_count} erreurs ({dashboardData.kpis.avg_api_response_time_ms.toFixed(0)}ms moy.)
                        </p>
                    </div>
                </div>
            )}

            {/* Actions rapides */}
            <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions Rapides</h3>
                <div className="flex flex-col sm:flex-row gap-3">
                    <button
                        onClick={() => handleTriggerOptimization()}
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-4 rounded-md transition-colors touch-manipulation"
                    >
                        🚀 Lancer Optimisation Globale
                    </button>
                    
                    <button
                        onClick={handleTriggerMonitoringCycle}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-4 rounded-md transition-colors touch-manipulation"
                    >
                        🔄 Cycle Monitoring Manuel
                    </button>
                    
                    <button
                        onClick={loadDashboardData}
                        disabled={loading}
                        className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-4 rounded-md transition-colors touch-manipulation"
                    >
                        📊 Recalculer KPIs
                    </button>
                </div>
            </div>

            {/* Alertes actives */}
            {dashboardData?.active_alerts && dashboardData.active_alerts.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🚨 Alertes Actives</h3>
                    <div className="space-y-3">
                        {dashboardData.active_alerts.map((alert) => (
                            <div 
                                key={alert.id} 
                                className={`p-3 rounded-lg border ${
                                    alert.severity === 'critical' 
                                        ? 'bg-red-50 border-red-200' 
                                        : alert.severity === 'warning'
                                        ? 'bg-orange-50 border-orange-200'
                                        : 'bg-blue-50 border-blue-200'
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-medium text-gray-900">{alert.title}</p>
                                        <p className="text-sm text-gray-700">{alert.description}</p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            SKU: {alert.sku} - {new Date(alert.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                    {alert.manual_action_required && (
                                        <button 
                                            onClick={() => handleTriggerOptimization(alert.sku)}
                                            className="bg-orange-600 hover:bg-orange-700 text-white text-sm px-3 py-1 rounded-md transition-colors touch-manipulation"
                                        >
                                            Corriger
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Activité récente */}
            {dashboardData?.recent_optimizations && (
                <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Activité Récente</h3>
                    <div className="space-y-2">
                        {dashboardData.recent_optimizations.slice(0, 10).map((optimization) => (
                            <div key={optimization.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                                <div>
                                    <span className="font-medium text-sm">{optimization.sku}</span>
                                    <span className="text-sm text-gray-500 ml-2">
                                        {optimization.action_type}
                                    </span>
                                    <span className="text-xs text-gray-400 ml-2">
                                        Priorité: {optimization.priority}, Confiance: {(optimization.confidence_score * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className={`text-xs px-2 py-1 rounded ${
                                        optimization.status === 'completed'
                                            ? 'bg-green-100 text-green-800' 
                                            : optimization.status === 'failed'
                                            ? 'bg-red-100 text-red-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {optimization.status === 'completed' ? '✅' : optimization.status === 'failed' ? '❌' : '⏳'}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {new Date(optimization.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    // Composant Jobs de monitoring
    const JobsSection = () => (
        <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Jobs de Monitoring</h2>
                <button
                    onClick={() => {/* TODO: Modal création job */}}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors touch-manipulation"
                >
                    ➕ Nouveau Job
                </button>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Job ID
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    SKUs
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Fréquence
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Dernière Exec.
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {monitoringJobs.map((job) => (
                                <tr key={job.id} className="hover:bg-gray-50">
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900 font-mono">
                                            {job.id.substring(0, 8)}...
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">
                                            {job.skus.length} SKUs
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {job.skus.slice(0, 2).join(', ')}{job.skus.length > 2 && '...'}
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">
                                            {job.monitoring_frequency_hours}h
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            Auto-optim: {job.auto_optimization_enabled ? 'ON' : 'OFF'}
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                            job.status === 'active'
                                                ? 'bg-green-100 text-green-800'
                                                : job.status === 'paused'
                                                ? 'bg-yellow-100 text-yellow-800'
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {job.status === 'active' ? '✅ Actif' : job.status === 'paused' ? '⏸️ Pausé' : '❌ Erreur'}
                                        </span>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {job.last_run_at 
                                            ? new Date(job.last_run_at).toLocaleDateString()
                                            : 'Jamais'
                                        }
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <div className="flex flex-col sm:flex-row gap-2">
                                            <button className="text-blue-600 hover:text-blue-900 text-xs touch-manipulation">
                                                Modifier
                                            </button>
                                            <button className="text-red-600 hover:text-red-900 text-xs touch-manipulation">
                                                Supprimer
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {monitoringJobs.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">Aucun job de monitoring configuré</p>
                        <button className="mt-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors">
                            Créer votre premier job
                        </button>
                    </div>
                )}
            </div>
        </div>
    );

    // Composant Snapshots
    const SnapshotsSection = () => (
        <div className="space-y-4 sm:space-y-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Snapshots Produits</h2>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    SKU
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Prix Actuel
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Buy Box
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Concurrents
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Snapshot
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {snapshots.map((snapshot) => (
                                <tr key={snapshot.id} className="hover:bg-gray-50">
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">
                                            {snapshot.sku}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            ASIN: {snapshot.asin || 'N/A'}
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">
                                            {snapshot.current_price ? `${snapshot.current_price.toFixed(2)}€` : 'N/A'}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {snapshot.currency || 'EUR'}
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <span className={`text-lg mr-2 ${
                                                snapshot.buybox_status === 'won' 
                                                    ? 'text-green-500' 
                                                    : snapshot.buybox_status === 'lost'
                                                    ? 'text-red-500'
                                                    : 'text-yellow-500'
                                            }`}>
                                                {snapshot.buybox_status === 'won' ? '✅' : 
                                                 snapshot.buybox_status === 'lost' ? '❌' : 
                                                 '⚠️'}
                                            </span>
                                            <div>
                                                <div className="text-sm text-gray-900">
                                                    {snapshot.buybox_status === 'won' ? 'Gagnée' : 
                                                     snapshot.buybox_status === 'lost' ? 'Perdue' : 
                                                     'Risque'}
                                                </div>
                                                {snapshot.buybox_price && (
                                                    <div className="text-xs text-gray-500">
                                                        Prix: {snapshot.buybox_price.toFixed(2)}€
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {snapshot.competitors_count} concurrent{snapshot.competitors_count > 1 ? 's' : ''}
                                        {snapshot.min_competitor_price && (
                                            <div className="text-xs">
                                                Min: {snapshot.min_competitor_price.toFixed(2)}€
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(snapshot.snapshot_at).toLocaleString()}
                                        <div className="text-xs">
                                            Score: {(snapshot.data_completeness_score * 100).toFixed(0)}%
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button 
                                            onClick={() => handleTriggerOptimization(snapshot.sku)}
                                            className="text-green-600 hover:text-green-900 text-xs touch-manipulation"
                                        >
                                            Optimiser
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {snapshots.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">Aucun snapshot disponible</p>
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="w-full min-h-screen bg-gray-50 px-3 sm:px-4 lg:px-6 py-4">
            {/* Header */}
            <div className="mb-4 sm:mb-6 lg:mb-8">
                <h1 className="text-lg sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2 leading-tight">
                    🔄 Monitoring & Closed-Loop Optimizer - Phase 5
                </h1>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Surveillance automatique et optimisation continue des listings Amazon en temps réel
                </p>
            </div>

            {/* Sélecteur de marketplace */}
            <div className="bg-white rounded-lg border border-gray-200 mb-4 sm:mb-6 p-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Marketplace:</label>
                    <select
                        value={selectedMarketplace}
                        onChange={(e) => setSelectedMarketplace(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                        {marketplaces.map((marketplace) => (
                            <option key={marketplace.id} value={marketplace.id}>
                                {marketplace.name} ({marketplace.domain})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Navigation des sections - Mobile optimized */}
            <div className="bg-white rounded-lg border border-gray-200 mb-4 sm:mb-6 overflow-hidden">
                <div className="border-b border-gray-200">
                    <nav className="flex overflow-x-auto scrollbar-hide -mb-px">
                        {sections.map((section) => (
                            <button
                                key={section.id}
                                onClick={() => setActiveSection(section.id)}
                                className={`
                                    flex flex-col items-center gap-1 px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium whitespace-nowrap
                                    border-b-2 transition-all min-w-0 flex-shrink-0 touch-manipulation
                                    ${activeSection === section.id
                                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                                    }
                                `}
                                style={{ minWidth: '80px' }}
                            >
                                <span className="text-lg sm:text-xl">{section.icon}</span>
                                <span className="text-xs sm:text-sm font-medium leading-tight text-center">
                                    {section.name.split(' ').slice(1).join(' ')}
                                </span>
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Messages et indicateurs */}
            <MessageAlerts />
            <LoadingIndicator />

            {/* Contenu des sections */}
            {activeSection === 'dashboard' && <DashboardSection />}
            {activeSection === 'jobs' && <JobsSection />}
            {activeSection === 'snapshots' && <SnapshotsSection />}
            
            {/* Sections en développement */}
            {(activeSection === 'optimizations' || activeSection === 'alerts' || activeSection === 'settings') && (
                <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                    <div className="text-4xl mb-4">🚧</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Section en développement
                    </h3>
                    <p className="text-gray-600 mb-4">
                        Cette section du monitoring sera disponible dans une version ultérieure.
                    </p>
                </div>
            )}
        </div>
    );
};

export default AmazonMonitoringDashboard;