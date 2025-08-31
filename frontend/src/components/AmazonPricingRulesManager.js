// Amazon Pricing Rules Manager - Phase 4
import React, { useState, useEffect, useCallback } from 'react';

const AmazonPricingRulesManager = ({ user, token }) => {
    // États principaux
    const [activeSection, setActiveSection] = useState('dashboard');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // États des données
    const [rules, setRules] = useState([]);
    const [dashboardData, setDashboardData] = useState(null);
    const [history, setHistory] = useState([]);
    const [selectedRules, setSelectedRules] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [editingRule, setEditingRule] = useState(null);

    // Configuration API
    const backendUrl = process.env.REACT_APP_BACKEND_URL || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8001');

    // Sections de navigation
    const sections = [
        { id: 'dashboard', name: '📊 Dashboard', icon: '📊' },
        { id: 'rules', name: '⚙️ Règles Prix', icon: '⚙️' },
        { id: 'history', name: '📈 Historique', icon: '📈' },
        { id: 'batch', name: '🔄 Traitement Lot', icon: '🔄' }
    ];

    // Stratégies de pricing
    const strategies = [
        { value: 'buybox_match', label: 'Matcher Buy Box', description: 'Aligner sur le prix Buy Box' },
        { value: 'margin_target', label: 'Marge cible', description: 'Maintenir une marge définie' },
        { value: 'floor_ceiling', label: 'Min/Max', description: 'Rester entre min/max avec variance' }
    ];

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
            loadDashboardData();
            loadRules();
        }
    }, [user, token, activeSection]);

    const loadDashboardData = async () => {
        try {
            const data = await apiCall('/api/amazon/pricing/dashboard');
            setDashboardData(data);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    };

    const loadRules = async () => {
        try {
            const data = await apiCall('/api/amazon/pricing/rules');
            setRules(data);
        } catch (error) {
            console.error('Error loading rules:', error);
            setError('Erreur lors du chargement des règles');
        }
    };

    const loadHistory = async () => {
        try {
            const data = await apiCall('/api/amazon/pricing/history');
            setHistory(data.history || []);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    };

    // Gestionnaires d'événements
    const handleCreateRule = async (ruleData) => {
        setLoading(true);
        try {
            await apiCall('/api/amazon/pricing/rules', 'POST', ruleData);
            setSuccessMessage('Règle créée avec succès');
            setShowCreateModal(false);
            loadRules();
        } catch (error) {
            setError(`Erreur lors de la création: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateRule = async (ruleId, updates) => {
        setLoading(true);
        try {
            await apiCall(`/api/amazon/pricing/rules/${ruleId}`, 'PUT', updates);
            setSuccessMessage('Règle mise à jour avec succès');
            setEditingRule(null);
            loadRules();
        } catch (error) {
            setError(`Erreur lors de la mise à jour: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteRule = async (ruleId) => {
        if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette règle ?')) return;
        
        setLoading(true);
        try {
            await apiCall(`/api/amazon/pricing/rules/${ruleId}`, 'DELETE');
            setSuccessMessage('Règle supprimée avec succès');
            loadRules();
        } catch (error) {
            setError(`Erreur lors de la suppression: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handlePublishPrice = async (sku) => {
        setLoading(true);
        try {
            const result = await apiCall('/api/amazon/pricing/publish', 'POST', {
                sku,
                marketplace_id: 'A13V1IB3VIYZZH',
                method: 'listings_items'
            });

            if (result.published) {
                setSuccessMessage(`Prix publié pour ${sku}: ${result.calculation.recommended_price.toFixed(2)}€`);
            } else {
                setError(`Publication échouée pour ${sku}: ${result.message}`);
            }
        } catch (error) {
            setError(`Erreur lors de la publication: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleBatchOptimization = async () => {
        if (selectedRules.length === 0) {
            setError('Veuillez sélectionner au moins un SKU');
            return;
        }

        setLoading(true);
        try {
            const result = await apiCall('/api/amazon/pricing/batch', 'POST', {
                skus: selectedRules,
                marketplace_id: 'A13V1IB3VIYZZH',
                force_update: false
            });

            setSuccessMessage(`Traitement par lot lancé pour ${selectedRules.length} SKUs`);
            setSelectedRules([]);
        } catch (error) {
            setError(`Erreur lors du traitement par lot: ${error.message}`);
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
            {/* Statistiques */}
            {dashboardData?.stats && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">Règles Actives</h3>
                        <p className="text-2xl font-bold text-blue-600">{dashboardData.stats.active_rules}</p>
                        <p className="text-xs text-gray-500">sur {dashboardData.stats.total_rules} total</p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">Buy Box Gagnées</h3>
                        <p className="text-2xl font-bold text-green-600">{dashboardData.stats.skus_with_buybox}</p>
                        <p className="text-xs text-gray-500">SKUs avec Buy Box</p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">À Risque</h3>
                        <p className="text-2xl font-bold text-orange-600">{dashboardData.stats.skus_at_risk}</p>
                        <p className="text-xs text-gray-500">SKUs à risque</p>
                    </div>
                    
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h3 className="text-sm font-medium text-gray-500">Mises à Jour 24h</h3>
                        <p className="text-2xl font-bold text-purple-600">{dashboardData.stats.successful_updates_24h}</p>
                        <p className="text-xs text-gray-500">{dashboardData.stats.failed_updates_24h} échecs</p>
                    </div>
                </div>
            )}

            {/* Alertes Buy Box */}
            {dashboardData?.buybox_alerts && dashboardData.buybox_alerts.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🚨 Alertes Buy Box</h3>
                    <div className="space-y-3">
                        {dashboardData.buybox_alerts.map((alert, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                                <div>
                                    <p className="font-medium text-orange-800">{alert.sku}</p>
                                    <p className="text-sm text-orange-700">{alert.message}</p>
                                </div>
                                <button 
                                    onClick={() => handlePublishPrice(alert.sku)}
                                    className="bg-orange-600 hover:bg-orange-700 text-white text-sm px-3 py-1 rounded-md transition-colors"
                                >
                                    Optimiser
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Historique récent */}
            {dashboardData?.recent_history && (
                <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Activité Récente</h3>
                    <div className="space-y-2">
                        {dashboardData.recent_history.slice(0, 5).map((entry) => (
                            <div key={entry.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                                <div>
                                    <span className="font-medium text-sm">{entry.sku}</span>
                                    <span className="text-sm text-gray-500 ml-2">
                                        {entry.old_price ? `${entry.old_price}€ → ` : ''}{entry.new_price.toFixed(2)}€
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className={`text-xs px-2 py-1 rounded ${
                                        entry.publication_success 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-red-100 text-red-800'
                                    }`}>
                                        {entry.publication_success ? '✅' : '❌'}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {new Date(entry.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    // Composant Règles
    const RulesSection = () => (
        <div className="space-y-4 sm:space-y-6">
            {/* Header avec actions */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Règles de Prix</h2>
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors touch-manipulation"
                    >
                        ➕ Nouvelle Règle
                    </button>
                    {selectedRules.length > 0 && (
                        <button
                            onClick={handleBatchOptimization}
                            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors touch-manipulation"
                        >
                            🔄 Optimiser ({selectedRules.length})
                        </button>
                    )}
                </div>
            </div>

            {/* Tableau des règles - Responsive */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    <input
                                        type="checkbox"
                                        className="rounded"
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setSelectedRules(rules.map(r => r.sku));
                                            } else {
                                                setSelectedRules([]);
                                            }
                                        }}
                                    />
                                </th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prix Min/Max</th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stratégie</th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Buy Box</th>
                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {rules.map((rule) => (
                                <tr key={rule.id} className="hover:bg-gray-50">
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <input
                                            type="checkbox"
                                            className="rounded"
                                            checked={selectedRules.includes(rule.sku)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setSelectedRules([...selectedRules, rule.sku]);
                                                } else {
                                                    setSelectedRules(selectedRules.filter(sku => sku !== rule.sku));
                                                }
                                            }}
                                        />
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{rule.sku}</div>
                                        <div className={`text-xs ${
                                            rule.status === 'active' 
                                                ? 'text-green-600' 
                                                : 'text-gray-500'
                                        }`}>
                                            {rule.status === 'active' ? '✅ Actif' : '⏸️ Inactif'}
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">
                                            {rule.min_price.toFixed(2)}€ - {rule.max_price.toFixed(2)}€
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            ±{rule.variance_pct}% variance
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">
                                            {strategies.find(s => s.value === rule.strategy)?.label || rule.strategy}
                                        </div>
                                        {rule.margin_target && (
                                            <div className="text-xs text-gray-500">
                                                Marge: {rule.margin_target}%
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                        {/* Simuler l'état Buy Box */}
                                        <div className="flex items-center">
                                            <span className="text-green-500 text-lg">✅</span>
                                            <span className="ml-2 text-sm text-gray-700">Gagnée</span>
                                        </div>
                                    </td>
                                    <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <div className="flex flex-col sm:flex-row gap-2">
                                            <button
                                                onClick={() => handlePublishPrice(rule.sku)}
                                                className="bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1 rounded-md transition-colors touch-manipulation"
                                            >
                                                Publier
                                            </button>
                                            <button
                                                onClick={() => setEditingRule(rule)}
                                                className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded-md transition-colors touch-manipulation"
                                            >
                                                Modifier
                                            </button>
                                            <button
                                                onClick={() => handleDeleteRule(rule.id)}
                                                className="bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded-md transition-colors touch-manipulation"
                                            >
                                                Supprimer
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {rules.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">Aucune règle de prix configurée</p>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                        >
                            Créer votre première règle
                        </button>
                    </div>
                )}
            </div>
        </div>
    );

    // Composant Modal de création/édition
    const CreateEditModal = () => {
        const [formData, setFormData] = useState({
            sku: '',
            min_price: '',
            max_price: '',
            variance_pct: 5,
            strategy: 'buybox_match',
            margin_target: '',
            auto_update: true
        });

        useEffect(() => {
            if (editingRule) {
                setFormData({
                    sku: editingRule.sku,
                    min_price: editingRule.min_price,
                    max_price: editingRule.max_price,
                    variance_pct: editingRule.variance_pct,
                    strategy: editingRule.strategy,
                    margin_target: editingRule.margin_target || '',
                    auto_update: editingRule.auto_update
                });
            }
        }, [editingRule]);

        const handleSubmit = (e) => {
            e.preventDefault();
            
            const data = {
                ...formData,
                min_price: parseFloat(formData.min_price),
                max_price: parseFloat(formData.max_price),
                variance_pct: parseFloat(formData.variance_pct),
                margin_target: formData.margin_target ? parseFloat(formData.margin_target) : null
            };

            if (editingRule) {
                handleUpdateRule(editingRule.id, data);
            } else {
                handleCreateRule(data);
            }
        };

        if (!showCreateModal && !editingRule) return null;

        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <div className="bg-white rounded-lg max-w-md w-full max-h-screen overflow-y-auto">
                    <div className="p-6">
                        <h3 className="text-lg font-semibold mb-4">
                            {editingRule ? 'Modifier la règle' : 'Nouvelle règle de prix'}
                        </h3>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    SKU Amazon
                                </label>
                                <input
                                    type="text"
                                    required
                                    disabled={editingRule}
                                    value={formData.sku}
                                    onChange={(e) => setFormData({...formData, sku: e.target.value})}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Ex: B08N5WRWNW"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Prix Min (€)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        required
                                        value={formData.min_price}
                                        onChange={(e) => setFormData({...formData, min_price: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Prix Max (€)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        required
                                        value={formData.max_price}
                                        onChange={(e) => setFormData({...formData, max_price: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Variance (%)
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="100"
                                    value={formData.variance_pct}
                                    onChange={(e) => setFormData({...formData, variance_pct: e.target.value})}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Stratégie
                                </label>
                                <select
                                    value={formData.strategy}
                                    onChange={(e) => setFormData({...formData, strategy: e.target.value})}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    {strategies.map((strategy) => (
                                        <option key={strategy.value} value={strategy.value}>
                                            {strategy.label} - {strategy.description}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {formData.strategy === 'margin_target' && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Marge cible (%)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        max="100"
                                        value={formData.margin_target}
                                        onChange={(e) => setFormData({...formData, margin_target: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            )}

                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="auto_update"
                                    checked={formData.auto_update}
                                    onChange={(e) => setFormData({...formData, auto_update: e.target.checked})}
                                    className="rounded"
                                />
                                <label htmlFor="auto_update" className="ml-2 text-sm text-gray-700">
                                    Mise à jour automatique
                                </label>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                >
                                    {editingRule ? 'Mettre à jour' : 'Créer'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowCreateModal(false);
                                        setEditingRule(null);
                                    }}
                                    className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
                                >
                                    Annuler
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    };

    // Composant Historique
    const HistorySection = () => {
        useEffect(() => {
            if (activeSection === 'history') {
                loadHistory();
            }
        }, [activeSection]);

        return (
            <div className="space-y-4 sm:space-y-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Historique des Prix</h2>

                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prix</th>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Changement</th>
                                    <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {history.map((entry) => (
                                    <tr key={entry.id} className="hover:bg-gray-50">
                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {new Date(entry.created_at).toLocaleDateString()}
                                            <div className="text-xs text-gray-500">
                                                {new Date(entry.created_at).toLocaleTimeString()}
                                            </div>
                                        </td>
                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {entry.sku}
                                        </td>
                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {entry.old_price && `${entry.old_price.toFixed(2)}€ → `}
                                            <span className="font-medium">{entry.new_price.toFixed(2)}€</span>
                                        </td>
                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                            <span className={`text-sm font-medium ${
                                                entry.price_change > 0 
                                                    ? 'text-red-600' 
                                                    : entry.price_change < 0 
                                                    ? 'text-green-600' 
                                                    : 'text-gray-600'
                                            }`}>
                                                {entry.price_change > 0 && '+'}
                                                {entry.price_change.toFixed(2)}€
                                            </span>
                                            <div className="text-xs text-gray-500">
                                                {entry.price_change_pct > 0 && '+'}
                                                {entry.price_change_pct.toFixed(1)}%
                                            </div>
                                        </td>
                                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                entry.publication_success
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {entry.publication_success ? '✅ Publié' : '❌ Échec'}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {history.length === 0 && (
                        <div className="text-center py-8">
                            <p className="text-gray-500">Aucun historique de prix disponible</p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="w-full min-h-screen bg-gray-50 px-3 sm:px-4 lg:px-6 py-4">
            {/* Header */}
            <div className="mb-4 sm:mb-6 lg:mb-8">
                <h1 className="text-lg sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2 leading-tight">
                    💰 Prix & Règles Amazon - Phase 4
                </h1>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Moteur de prix intelligents avec Buy Box awareness et publication temps réel
                </p>
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
            {activeSection === 'rules' && <RulesSection />}
            {activeSection === 'history' && <HistorySection />}
            {activeSection === 'batch' && (
                <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
                    <div className="text-4xl mb-4">🔄</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        Traitement par Lot
                    </h3>
                    <p className="text-gray-600 mb-4">
                        Cette section sera développée pour gérer les traitements en masse.
                    </p>
                </div>
            )}

            {/* Modals */}
            <CreateEditModal />
        </div>
    );
};

export default AmazonPricingRulesManager;