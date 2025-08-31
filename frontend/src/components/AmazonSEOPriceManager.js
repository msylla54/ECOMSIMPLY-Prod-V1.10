// Amazon SEO & Price Manager - Phase 3
import React, { useState, useEffect } from 'react';

const AmazonSEOPriceManager = () => {
    // États principaux
    const [activeSection, setActiveSection] = useState('scraping');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // États scraping
    const [scrapingData, setScrapingData] = useState({
        asin: '',
        marketplace: 'FR',
        results: null,
        competitorQuery: '',
        competitorResults: []
    });
    
    // États SEO
    const [seoData, setSeoData] = useState({
        optimizedContent: null,
        variants: [],
        targetKeywords: '',
        originalContent: null
    });
    
    // États prix
    const [priceData, setPriceData] = useState({
        productData: {
            cost_price: '',
            current_price: '',
            min_price: '',
            max_price: '',
            target_margin_percent: 15
        },
        competitorPrices: [],
        optimizedPrice: null,
        pricingStrategy: 'competitive'
    });
    
    // États publication
    const [publicationData, setPublicationData] = useState({
        updates: [],
        updateType: 'full_update',
        validationRequired: true,
        asyncMode: false,
        sessionId: null,
        results: null
    });
    
    // États monitoring
    const [monitoringData, setMonitoringData] = useState({
        recentActions: [],
        sessionStatus: {},
        statistics: {}
    });

    const backendUrl = process.env.REACT_APP_BACKEND_URL || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8001');

    // Sections de navigation
    const sections = [
        { id: 'scraping', name: '🔍 Scraping SEO/Prix', icon: '🔍' },
        { id: 'seo', name: '🚀 Optimisation SEO IA', icon: '🚀' },
        { id: 'price', name: '💰 Optimisation Prix', icon: '💰' },
        { id: 'publish', name: '📤 Auto-Publish', icon: '📤' },
        { id: 'monitoring', name: '📊 Monitoring', icon: '📊' }
    ];

    // Fonction utilitaire pour les appels API
    const apiCall = async (endpoint, method = 'GET', data = null) => {
        try {
            const token = localStorage.getItem('token') || 'demo-token';
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    };

    // Scraping Amazon
    const handleScrapingSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await apiCall(
                `/api/amazon/scraping/${scrapingData.asin}?marketplace=${scrapingData.marketplace}`
            );

            if (response.success) {
                setScrapingData(prev => ({
                    ...prev,
                    results: response.data
                }));
                
                // Copier automatiquement vers SEO
                if (response.data.seo_data) {
                    setSeoData(prev => ({
                        ...prev,
                        originalContent: response.data.seo_data
                    }));
                }
            }
        } catch (error) {
            setError(`Erreur scraping: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Scraping concurrents
    const handleCompetitorScraping = async () => {
        if (!scrapingData.competitorQuery.trim()) return;
        
        setLoading(true);
        setError(null);

        try {
            const response = await apiCall(
                `/api/amazon/scraping/competitors/${encodeURIComponent(scrapingData.competitorQuery)}?marketplace=${scrapingData.marketplace}&max_results=5`
            );

            if (response.success) {
                setScrapingData(prev => ({
                    ...prev,
                    competitorResults: response.data
                }));
                
                // Copier vers optimisation prix
                setPriceData(prev => ({
                    ...prev,
                    competitorPrices: response.data
                }));
            }
        } catch (error) {
            setError(`Erreur scraping concurrents: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Optimisation SEO
    const handleSEOOptimization = async () => {
        if (!seoData.originalContent) {
            setError('Veuillez d\'abord scraper un produit pour obtenir le contenu original');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const keywords = seoData.targetKeywords.split(',').map(k => k.trim()).filter(k => k);
            
            const response = await apiCall('/api/amazon/seo/optimize', 'POST', {
                scraped_data: {
                    seo_data: seoData.originalContent
                },
                target_keywords: keywords,
                optimization_goals: {
                    primary: 'conversion',
                    secondary: 'visibility'
                }
            });

            if (response.success) {
                setSeoData(prev => ({
                    ...prev,
                    optimizedContent: response.optimization_result
                }));
            }
        } catch (error) {
            setError(`Erreur optimisation SEO: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Génération variantes SEO
    const handleSEOVariants = async () => {
        if (!seoData.optimizedContent?.optimized_seo) {
            setError('Veuillez d\'abord optimiser le SEO pour générer des variantes');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await apiCall('/api/amazon/seo/variants', 'POST', {
                base_seo: seoData.optimizedContent.optimized_seo,
                variant_count: 3
            });

            if (response.success) {
                setSeoData(prev => ({
                    ...prev,
                    variants: response.variants
                }));
            }
        } catch (error) {
            setError(`Erreur génération variantes: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Optimisation prix
    const handlePriceOptimization = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiCall('/api/amazon/price/optimize', 'POST', {
                product_data: {
                    ...priceData.productData,
                    cost_price: parseFloat(priceData.productData.cost_price) || 0,
                    current_price: parseFloat(priceData.productData.current_price) || 0,
                    min_price: parseFloat(priceData.productData.min_price) || 0,
                    max_price: parseFloat(priceData.productData.max_price) || 0,
                    pricing_strategy: priceData.pricingStrategy
                },
                competitor_prices: priceData.competitorPrices,
                target_marketplace: scrapingData.marketplace
            });

            if (response.success) {
                setPriceData(prev => ({
                    ...prev,
                    optimizedPrice: response.price_optimization
                }));
            }
        } catch (error) {
            setError(`Erreur optimisation prix: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Publication
    const handlePublication = async () => {
        if (!seoData.optimizedContent && !priceData.optimizedPrice) {
            setError('Veuillez optimiser le SEO et/ou le prix avant publication');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Construire les mises à jour
            const updates = [];
            
            if (seoData.optimizedContent?.optimized_seo) {
                const seo = seoData.optimizedContent.optimized_seo;
                updates.push({
                    sku: scrapingData.asin, // Utiliser ASIN comme SKU pour demo
                    title: seo.title,
                    bullet_points: seo.bullet_points,
                    description: seo.description,
                    search_terms: seo.backend_keywords
                });
            }

            if (priceData.optimizedPrice?.optimized_price) {
                updates.push({
                    sku: scrapingData.asin,
                    standard_price: priceData.optimizedPrice.optimized_price.amount,
                    currency: priceData.optimizedPrice.currency
                });
            }

            const response = await apiCall('/api/amazon/publish', 'POST', {
                marketplace_id: scrapingData.marketplace,
                updates: updates,
                update_type: publicationData.updateType,
                validation_required: publicationData.validationRequired,
                async_mode: publicationData.asyncMode
            });

            if (response.success) {
                setPublicationData(prev => ({
                    ...prev,
                    results: response,
                    sessionId: response.session_id
                }));
                
                // Passer au monitoring si async
                if (publicationData.asyncMode) {
                    setActiveSection('monitoring');
                }
            }
        } catch (error) {
            setError(`Erreur publication: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Monitoring
    const loadMonitoringData = async () => {
        try {
            const response = await apiCall('/api/amazon/monitoring?limit=10');
            if (response.success) {
                setMonitoringData(prev => ({
                    ...prev,
                    recentActions: response.monitoring_data.entries,
                    statistics: response.monitoring_data.summary
                }));
            }
        } catch (error) {
            console.error('Erreur monitoring:', error);
        }
    };

    // Charger monitoring au démarrage
    useEffect(() => {
        if (activeSection === 'monitoring') {
            loadMonitoringData();
        }
    }, [activeSection]);

    return (
        <div className="w-full min-h-screen bg-gray-50 px-3 sm:px-4 lg:px-6 py-4">
            {/* Header */}
            <div className="mb-4 sm:mb-6 lg:mb-8">
                <h1 className="text-lg sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2 leading-tight">
                    🚀 Amazon SEO & Prix - Phase 3
                </h1>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Scraping automatique, optimisation IA et publication en temps réel via SP-API
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
                                    {section.name.split(' ').slice(0, 2).join(' ')}
                                </span>
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Affichage erreur globale */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center">
                        <span className="text-red-500 text-xl mr-3">❌</span>
                        <div>
                            <h3 className="text-red-800 font-medium">Erreur</h3>
                            <p className="text-red-700 text-sm">{error}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Indicateur de chargement global */}
            {loading && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center">
                        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mr-3"></div>
                        <span className="text-blue-700">Traitement en cours...</span>
                    </div>
                </div>
            )}

            {/* Section Scraping */}
            {activeSection === 'scraping' && (
                <div className="space-y-4 sm:space-y-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            🔍 Scraping SEO + Prix Amazon
                        </h2>
                        
                        <form onSubmit={handleScrapingSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div className="sm:col-span-2 lg:col-span-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        ASIN Amazon
                                    </label>
                                    <input
                                        type="text"
                                        value={scrapingData.asin}
                                        onChange={(e) => setScrapingData(prev => ({...prev, asin: e.target.value}))}
                                        className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                        placeholder="Ex: B08N5WRWNW"
                                        required
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Marketplace
                                    </label>
                                    <select
                                        value={scrapingData.marketplace}
                                        onChange={(e) => setScrapingData(prev => ({...prev, marketplace: e.target.value}))}
                                        className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                    >
                                        <option value="FR">🇫🇷 France (amazon.fr)</option>
                                        <option value="DE">🇩🇪 Allemagne (amazon.de)</option>
                                        <option value="UK">🇬🇧 Royaume-Uni (amazon.co.uk)</option>
                                        <option value="US">🇺🇸 États-Unis (amazon.com)</option>
                                        <option value="IT">🇮🇹 Italie (amazon.it)</option>
                                        <option value="ES">🇪🇸 Espagne (amazon.es)</option>
                                    </select>
                                </div>
                                
                                <div className="sm:col-span-2 lg:col-span-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-2 opacity-0 select-none">
                                        Action
                                    </label>
                                    <button
                                        type="submit"
                                        disabled={loading || !scrapingData.asin}
                                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-4 rounded-md transition-colors touch-manipulation"
                                    >
                                        Récupérer données Amazon
                                    </button>
                                </div>
                            </div>
                        </form>

                        {/* Scraping concurrents */}
                        <div className="mt-6 pt-6 border-t border-gray-200">
                            <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-4">
                                Prix des concurrents
                            </h3>
                            
                            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                                <input
                                    type="text"
                                    value={scrapingData.competitorQuery}
                                    onChange={(e) => setScrapingData(prev => ({...prev, competitorQuery: e.target.value}))}
                                    className="flex-1 px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                    placeholder="Ex: iPhone 15 Pro Max"
                                />
                                <button
                                    onClick={handleCompetitorScraping}
                                    disabled={loading || !scrapingData.competitorQuery}
                                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-6 rounded-md transition-colors touch-manipulation whitespace-nowrap"
                                >
                                    Scraper concurrents
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Résultats scraping */}
                    {scrapingData.results && (
                        <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">
                                ✅ Données récupérées
                            </h3>
                            
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
                                {/* SEO Data */}
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-3 text-sm sm:text-base">📄 Données SEO</h4>
                                    <div className="space-y-3">
                                        <div>
                                            <span className="text-xs sm:text-sm font-medium text-gray-700">Titre:</span>
                                            <p className="text-xs sm:text-sm text-gray-900 bg-gray-50 p-2 sm:p-3 rounded mt-1 leading-relaxed">
                                                {scrapingData.results.seo_data?.title || 'N/A'}
                                            </p>
                                        </div>
                                        
                                        <div>
                                            <span className="text-xs sm:text-sm font-medium text-gray-700">
                                                Bullet Points ({scrapingData.results.seo_data?.bullet_points?.length || 0}):
                                            </span>
                                            <div className="mt-1 space-y-1">
                                                {scrapingData.results.seo_data?.bullet_points?.slice(0, 3).map((bullet, i) => (
                                                    <p key={i} className="text-xs sm:text-sm text-gray-900 bg-gray-50 p-2 sm:p-3 rounded leading-relaxed">
                                                        • {bullet.substring(0, 100)}...
                                                    </p>
                                                )) || <p className="text-xs sm:text-sm text-gray-500">Aucun bullet point trouvé</p>}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Price Data */}
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-3 text-sm sm:text-base">💰 Données Prix</h4>
                                    <div className="space-y-3">
                                        {scrapingData.results.price_data?.current_price ? (
                                            <>
                                                <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                                                    <span className="text-xs sm:text-sm font-medium text-green-800">Prix actuel:</span>
                                                    <span className="text-base sm:text-lg font-bold text-green-900">
                                                        {scrapingData.results.price_data.current_price} {scrapingData.results.price_data.currency}
                                                    </span>
                                                </div>
                                                
                                                {scrapingData.results.price_data.compare_prices?.length > 0 && (
                                                    <div>
                                                        <span className="text-xs sm:text-sm font-medium text-gray-700">Prix de comparaison:</span>
                                                        <div className="mt-1 space-y-1">
                                                            {scrapingData.results.price_data.compare_prices.map((price, i) => (
                                                                <div key={i} className="flex justify-between text-xs sm:text-sm bg-gray-50 p-2 rounded">
                                                                    <span>{price.type}</span>
                                                                    <span className="font-medium">{price.formatted}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <p className="text-xs sm:text-sm text-gray-500 p-3 bg-gray-50 rounded">
                                                Prix non trouvé
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Résultats concurrents */}
                    {scrapingData.competitorResults.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">
                                🏪 Prix des concurrents ({scrapingData.competitorResults.length})
                            </h3>
                            
                            <div className="overflow-x-auto -mx-4 sm:-mx-6">
                                <div className="inline-block min-w-full px-4 sm:px-6 align-middle">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Produit
                                                </th>
                                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Prix
                                                </th>
                                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Note
                                                </th>
                                                <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    ASIN
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {scrapingData.competitorResults.map((competitor, i) => (
                                                <tr key={i}>
                                                    <td className="px-3 sm:px-6 py-4 text-xs sm:text-sm text-gray-900">
                                                        <div className="max-w-xs truncate">
                                                            {competitor.title?.substring(0, 60)}...
                                                        </div>
                                                    </td>
                                                    <td className="px-3 sm:px-6 py-4 text-xs sm:text-sm font-medium text-green-600 whitespace-nowrap">
                                                        {competitor.price} {competitor.currency}
                                                    </td>
                                                    <td className="px-3 sm:px-6 py-4 text-xs sm:text-sm text-gray-500">
                                                        {competitor.rating ? `${competitor.rating}/5` : 'N/A'}
                                                    </td>
                                                    <td className="px-3 sm:px-6 py-4 text-xs sm:text-sm text-gray-500 font-mono">
                                                        {competitor.asin}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Section SEO */}
            {activeSection === 'seo' && (
                <div className="space-y-4 sm:space-y-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            🚀 Optimisation SEO avec IA
                        </h2>
                        
                        {!seoData.originalContent ? (
                            <div className="text-center py-8">
                                <p className="text-gray-500 mb-4 text-sm sm:text-base">
                                    Veuillez d'abord scraper un produit dans la section "Scraping"
                                </p>
                                <button
                                    onClick={() => setActiveSection('scraping')}
                                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 sm:py-2 px-4 rounded-md transition-colors touch-manipulation"
                                >
                                    Aller au scraping
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Mots-clés cibles (séparés par des virgules)
                                    </label>
                                    <input
                                        type="text"
                                        value={seoData.targetKeywords}
                                        onChange={(e) => setSeoData(prev => ({...prev, targetKeywords: e.target.value}))}
                                        className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                        placeholder="Ex: smartphone, premium, apple, iphone, pro"
                                    />
                                </div>
                                
                                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                                    <button
                                        onClick={handleSEOOptimization}
                                        disabled={loading}
                                        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-6 rounded-md transition-colors touch-manipulation"
                                    >
                                        Optimiser SEO avec IA
                                    </button>
                                    
                                    {seoData.optimizedContent && (
                                        <button
                                            onClick={handleSEOVariants}
                                            disabled={loading}
                                            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 text-white font-medium py-3 sm:py-2 px-6 rounded-md transition-colors touch-manipulation"
                                        >
                                            Générer variantes A/B
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Résultats optimisation SEO */}
                    {seoData.optimizedContent && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-between">
                                <span>✨ SEO Optimisé</span>
                                <div className="flex items-center gap-4">
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                                        Score: {seoData.optimizedContent.optimization_score}%
                                    </span>
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                        seoData.optimizedContent.validation?.overall_status === 'APPROVED'
                                            ? 'bg-blue-100 text-blue-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                        {seoData.optimizedContent.validation?.overall_status === 'APPROVED' ? '✅ Conforme A9/A10' : '⚠️ À vérifier'}
                                    </span>
                                </div>
                            </h3>
                            
                            <div className="space-y-6">
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Titre optimisé</h4>
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <p className="text-gray-900">{seoData.optimizedContent.optimized_seo?.title}</p>
                                        <p className="text-sm text-gray-500 mt-2">
                                            {seoData.optimizedContent.optimized_seo?.title?.length || 0}/200 caractères
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Bullet Points optimisés</h4>
                                    <div className="space-y-2">
                                        {seoData.optimizedContent.optimized_seo?.bullet_points?.map((bullet, i) => (
                                            <div key={i} className="p-3 bg-gray-50 rounded-lg">
                                                <p className="text-gray-900">{bullet}</p>
                                                <p className="text-sm text-gray-500 mt-1">
                                                    {bullet.length}/255 caractères
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Description optimisée</h4>
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <p className="text-gray-900 whitespace-pre-line">
                                            {seoData.optimizedContent.optimized_seo?.description?.substring(0, 500)}...
                                        </p>
                                        <p className="text-sm text-gray-500 mt-2">
                                            {seoData.optimizedContent.optimized_seo?.description?.length || 0}/2000 caractères
                                        </p>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Mots-clés backend</h4>
                                    <div className="p-3 bg-gray-50 rounded-lg">
                                        <p className="text-gray-900">{seoData.optimizedContent.optimized_seo?.backend_keywords}</p>
                                        <p className="text-sm text-gray-500 mt-1">
                                            {new Blob([seoData.optimizedContent.optimized_seo?.backend_keywords || '']).size}/250 bytes
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Variantes SEO */}
                    {seoData.variants.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                🔄 Variantes A/B Testing ({seoData.variants.length})
                            </h3>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                                {seoData.variants.map((variant, i) => (
                                    <div key={i} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="font-medium text-gray-900">
                                                Variante {variant.variant_id}
                                            </h4>
                                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                                                variant.validation?.overall_status === 'APPROVED'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {variant.validation?.overall_status || 'N/A'}
                                            </span>
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <div>
                                                <span className="text-xs font-medium text-gray-600">Titre:</span>
                                                <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded mt-1">
                                                    {variant.title?.substring(0, 80)}...
                                                </p>
                                            </div>
                                            
                                            <div>
                                                <span className="text-xs font-medium text-gray-600">
                                                    Bullets ({variant.bullet_points?.length || 0}):
                                                </span>
                                                <div className="mt-1 space-y-1">
                                                    {variant.bullet_points?.slice(0, 2).map((bullet, j) => (
                                                        <p key={j} className="text-xs text-gray-900 bg-gray-50 p-1 rounded">
                                                            • {bullet.substring(0, 60)}...
                                                        </p>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Section Prix */}
            {activeSection === 'price' && (
                <div className="space-y-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            💰 Optimisation Prix
                        </h2>
                        
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                            {/* Configuration produit */}
                            <div>
                                <h3 className="font-medium text-gray-900 mb-4 text-sm sm:text-base">📊 Données Produit</h3>
                                <div className="space-y-4">
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Coût produit (€)
                                            </label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={priceData.productData.cost_price}
                                                onChange={(e) => setPriceData(prev => ({
                                                    ...prev,
                                                    productData: {...prev.productData, cost_price: e.target.value}
                                                }))}
                                                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                                placeholder="50.00"
                                            />
                                        </div>
                                        
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Prix actuel (€)
                                            </label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={priceData.productData.current_price}
                                                onChange={(e) => setPriceData(prev => ({
                                                    ...prev,
                                                    productData: {...prev.productData, current_price: e.target.value}
                                                }))}
                                                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                                placeholder="79.99"
                                            />
                                        </div>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Prix minimum (€)
                                            </label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={priceData.productData.min_price}
                                                onChange={(e) => setPriceData(prev => ({
                                                    ...prev,
                                                    productData: {...prev.productData, min_price: e.target.value}
                                                }))}
                                                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                                placeholder="55.00"
                                            />
                                        </div>
                                        
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Prix maximum (€)
                                            </label>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={priceData.productData.max_price}
                                                onChange={(e) => setPriceData(prev => ({
                                                    ...prev,
                                                    productData: {...prev.productData, max_price: e.target.value}
                                                }))}
                                                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                                placeholder="150.00"
                                            />
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Marge cible (%)
                                        </label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={priceData.productData.target_margin_percent}
                                            onChange={(e) => setPriceData(prev => ({
                                                ...prev,
                                                productData: {...prev.productData, target_margin_percent: parseInt(e.target.value)}
                                            }))}
                                            className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Stratégie de pricing
                                        </label>
                                        <select
                                            value={priceData.pricingStrategy}
                                            onChange={(e) => setPriceData(prev => ({...prev, pricingStrategy: e.target.value}))}
                                            className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base sm:text-sm"
                                        >
                                            <option value="competitive">Compétitif</option>
                                            <option value="premium">Premium</option>
                                            <option value="aggressive">Agressif</option>
                                            <option value="value">Rapport qualité/prix</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Données concurrents */}
                            <div>
                                <h3 className="font-medium text-gray-900 mb-4">
                                    🏪 Prix Concurrents ({priceData.competitorPrices.length})
                                </h3>
                                
                                {priceData.competitorPrices.length === 0 ? (
                                    <div className="text-center py-8 bg-gray-50 rounded-lg">
                                        <p className="text-gray-500 mb-4">
                                            Aucun prix concurrent disponible
                                        </p>
                                        <button
                                            onClick={() => setActiveSection('scraping')}
                                            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                        >
                                            Scraper les concurrents
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-2 max-h-64 overflow-y-auto">
                                        {priceData.competitorPrices.map((competitor, i) => (
                                            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-gray-900 truncate">
                                                        {competitor.title?.substring(0, 40)}...
                                                    </p>
                                                    <p className="text-xs text-gray-500">
                                                        {competitor.rating ? `${competitor.rating}/5` : 'N/A'} • {competitor.asin}
                                                    </p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-sm font-bold text-green-600">
                                                        {competitor.price} {competitor.currency}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        <div className="mt-6">
                            <button
                                onClick={handlePriceOptimization}
                                disabled={loading}
                                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-medium py-2 px-6 rounded-md transition-colors"
                            >
                                Calculer prix optimal
                            </button>
                        </div>
                    </div>

                    {/* Résultats optimisation prix */}
                    {priceData.optimizedPrice && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-between">
                                <span>💎 Prix Optimisé</span>
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                    priceData.optimizedPrice.optimization_metadata?.confidence_score >= 80
                                        ? 'bg-green-100 text-green-800'
                                        : priceData.optimizedPrice.optimization_metadata?.confidence_score >= 60
                                        ? 'bg-yellow-100 text-yellow-800'
                                        : 'bg-red-100 text-red-800'
                                }`}>
                                    Confiance: {priceData.optimizedPrice.optimization_metadata?.confidence_score || 0}%
                                </span>
                            </h3>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Prix recommandé */}
                                <div>
                                    <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-blue-200">
                                        <h4 className="text-2xl font-bold text-gray-900 mb-2">
                                            {priceData.optimizedPrice.optimized_price?.amount} {priceData.optimizedPrice.currency}
                                        </h4>
                                        <p className="text-sm text-gray-600">
                                            Prix recommandé
                                        </p>
                                        
                                        {priceData.optimizedPrice.optimized_price?.constrained && (
                                            <div className="mt-3 p-2 bg-yellow-100 rounded text-xs text-yellow-800">
                                                ⚠️ Prix ajusté selon contraintes: {priceData.optimizedPrice.optimized_price.constraints_applied?.join(', ')}
                                            </div>
                                        )}
                                    </div>
                                    
                                    {/* Stratégie */}
                                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                                        <h5 className="font-medium text-gray-900 mb-2">Stratégie de pricing</h5>
                                        <p className="text-sm text-gray-700 mb-2">
                                            <strong>{priceData.optimizedPrice.pricing_strategy?.strategy}</strong>
                                        </p>
                                        <p className="text-xs text-gray-600">
                                            {priceData.optimizedPrice.pricing_strategy?.rationale}
                                        </p>
                                        <div className="flex items-center mt-2">
                                            <span className="text-xs text-gray-500">Confiance:</span>
                                            <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                                                priceData.optimizedPrice.pricing_strategy?.confidence === 'high'
                                                    ? 'bg-green-100 text-green-800'
                                                    : priceData.optimizedPrice.pricing_strategy?.confidence === 'medium'
                                                    ? 'bg-yellow-100 text-yellow-800'
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {priceData.optimizedPrice.pricing_strategy?.confidence}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Métriques */}
                                <div>
                                    <h4 className="font-medium text-gray-900 mb-4">📊 Métriques</h4>
                                    <div className="space-y-4">
                                        {/* Marge */}
                                        {priceData.optimizedPrice.metrics?.margin && (
                                            <div className="p-3 bg-gray-50 rounded-lg">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm font-medium text-gray-700">Marge</span>
                                                    <span className={`text-sm font-bold ${
                                                        priceData.optimizedPrice.metrics.margin.target_met 
                                                            ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                        {priceData.optimizedPrice.metrics.margin.percentage}%
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    Montant: {priceData.optimizedPrice.metrics.margin.amount} {priceData.optimizedPrice.currency}
                                                </p>
                                            </div>
                                        )}

                                        {/* Position concurrentielle */}
                                        {priceData.optimizedPrice.metrics?.competitive_position && (
                                            <div className="p-3 bg-gray-50 rounded-lg">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm font-medium text-gray-700">Position marché</span>
                                                    <span className="text-sm font-bold text-blue-600">
                                                        {priceData.optimizedPrice.metrics.competitive_position.percentile}e percentile
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {priceData.optimizedPrice.metrics.competitive_position.positioning} • 
                                                    Rang {priceData.optimizedPrice.metrics.competitive_position.rank}/{priceData.optimizedPrice.metrics.competitive_position.total_competitors + 1}
                                                </p>
                                                <div className="text-xs text-gray-500 mt-2">
                                                    vs Moyenne: {priceData.optimizedPrice.metrics.competitive_position.vs_average > 0 ? '+' : ''}{priceData.optimizedPrice.metrics.competitive_position.vs_average}% •
                                                    vs Médiane: {priceData.optimizedPrice.metrics.competitive_position.vs_median > 0 ? '+' : ''}{priceData.optimizedPrice.metrics.competitive_position.vs_median}%
                                                </div>
                                            </div>
                                        )}

                                        {/* Changement de prix */}
                                        {priceData.optimizedPrice.metrics?.price_change && (
                                            <div className="p-3 bg-gray-50 rounded-lg">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm font-medium text-gray-700">Changement</span>
                                                    <span className={`text-sm font-bold ${
                                                        priceData.optimizedPrice.metrics.price_change.direction === 'increase' 
                                                            ? 'text-red-600' 
                                                            : priceData.optimizedPrice.metrics.price_change.direction === 'decrease'
                                                            ? 'text-green-600'
                                                            : 'text-gray-600'
                                                    }`}>
                                                        {priceData.optimizedPrice.metrics.price_change.direction === 'increase' ? '+' : ''}
                                                        {priceData.optimizedPrice.metrics.price_change.percentage}%
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {priceData.optimizedPrice.metrics.price_change.direction === 'increase' ? '+' : ''}
                                                    {priceData.optimizedPrice.metrics.price_change.amount} {priceData.optimizedPrice.currency}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Section Publication */}
            {activeSection === 'publish' && (
                <div className="space-y-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            📤 Auto-Publication Amazon SP-API
                        </h2>
                        
                        {(!seoData.optimizedContent && !priceData.optimizedPrice) ? (
                            <div className="text-center py-8">
                                <p className="text-gray-500 mb-4">
                                    Veuillez d'abord optimiser le SEO et/ou le prix pour pouvoir publier
                                </p>
                                <div className="flex gap-4 justify-center">
                                    <button
                                        onClick={() => setActiveSection('seo')}
                                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                    >
                                        Optimiser SEO
                                    </button>
                                    <button
                                        onClick={() => setActiveSection('price')}
                                        className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                    >
                                        Optimiser Prix
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* Configuration publication */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <div>
                                        <h3 className="font-medium text-gray-900 mb-4">⚙️ Configuration</h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    Type de mise à jour
                                                </label>
                                                <select
                                                    value={publicationData.updateType}
                                                    onChange={(e) => setPublicationData(prev => ({...prev, updateType: e.target.value}))}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                >
                                                    <option value="full_update">SEO + Prix</option>
                                                    <option value="seo_only">SEO seulement</option>
                                                    <option value="price_only">Prix seulement</option>
                                                </select>
                                            </div>
                                            
                                            <div className="flex items-center space-x-2">
                                                <input
                                                    type="checkbox"
                                                    id="validationRequired"
                                                    checked={publicationData.validationRequired}
                                                    onChange={(e) => setPublicationData(prev => ({...prev, validationRequired: e.target.checked}))}
                                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                                <label htmlFor="validationRequired" className="text-sm font-medium text-gray-700">
                                                    Validation obligatoire avant publication
                                                </label>
                                            </div>
                                            
                                            <div className="flex items-center space-x-2">
                                                <input
                                                    type="checkbox"
                                                    id="asyncMode"
                                                    checked={publicationData.asyncMode}
                                                    onChange={(e) => setPublicationData(prev => ({...prev, asyncMode: e.target.checked}))}
                                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                                <label htmlFor="asyncMode" className="text-sm font-medium text-gray-700">
                                                    Mode asynchrone (traitement en arrière-plan)
                                                </label>
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="font-medium text-gray-900 mb-4">📋 Aperçu des mises à jour</h3>
                                        <div className="space-y-3">
                                            {seoData.optimizedContent && (publicationData.updateType === 'full_update' || publicationData.updateType === 'seo_only') && (
                                                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                                    <h4 className="text-sm font-medium text-blue-900 mb-2">✨ Mise à jour SEO</h4>
                                                    <ul className="text-xs text-blue-800 space-y-1">
                                                        <li>• Titre optimisé ({seoData.optimizedContent.optimized_seo?.title?.length || 0} chars)</li>
                                                        <li>• {seoData.optimizedContent.optimized_seo?.bullet_points?.length || 0} bullet points</li>
                                                        <li>• Description ({seoData.optimizedContent.optimized_seo?.description?.length || 0} chars)</li>
                                                        <li>• Mots-clés backend ({new Blob([seoData.optimizedContent.optimized_seo?.backend_keywords || '']).size} bytes)</li>
                                                    </ul>
                                                </div>
                                            )}
                                            
                                            {priceData.optimizedPrice && (publicationData.updateType === 'full_update' || publicationData.updateType === 'price_only') && (
                                                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                                                    <h4 className="text-sm font-medium text-green-900 mb-2">💰 Mise à jour Prix</h4>
                                                    <ul className="text-xs text-green-800 space-y-1">
                                                        <li>• Prix: {priceData.optimizedPrice.optimized_price?.amount} {priceData.optimizedPrice.currency}</li>
                                                        <li>• Stratégie: {priceData.optimizedPrice.pricing_strategy?.strategy}</li>
                                                        <li>• Confiance: {priceData.optimizedPrice.optimization_metadata?.confidence_score}%</li>
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="flex justify-center">
                                    <button
                                        onClick={handlePublication}
                                        disabled={loading}
                                        className="bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white font-bold py-3 px-8 rounded-lg transition-colors flex items-center gap-2"
                                    >
                                        <span>🚀</span>
                                        Publier sur Amazon SP-API
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Résultats publication */}
                    {publicationData.results && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                {publicationData.results.success ? '✅' : '❌'} Résultats de publication
                            </h3>
                            
                            {publicationData.results.async_mode ? (
                                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                                    <h4 className="font-medium text-blue-900 mb-2">📋 Publication en cours</h4>
                                    <p className="text-blue-800 text-sm mb-3">
                                        Session ID: <code className="bg-blue-100 px-2 py-1 rounded font-mono">{publicationData.results.session_id}</code>
                                    </p>
                                    <p className="text-blue-700 text-sm">
                                        La publication s'effectue en arrière-plan. Consultez la section Monitoring pour suivre l'avancement.
                                    </p>
                                    <button
                                        onClick={() => setActiveSection('monitoring')}
                                        className="mt-3 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                                    >
                                        Voir le monitoring
                                    </button>
                                </div>
                            ) : (
                                <div>
                                    {publicationData.results.success ? (
                                        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                                            <h4 className="font-medium text-green-900 mb-3">🎉 Publication réussie</h4>
                                            
                                            {publicationData.results.publication_result?.summary && (
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                                    <div className="text-center">
                                                        <div className="text-2xl font-bold text-green-600">
                                                            {publicationData.results.publication_result.summary.success_count}
                                                        </div>
                                                        <div className="text-sm text-green-700">Succès</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-2xl font-bold text-red-600">
                                                            {publicationData.results.publication_result.summary.error_count}
                                                        </div>
                                                        <div className="text-sm text-red-700">Erreurs</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-2xl font-bold text-blue-600">
                                                            {publicationData.results.publication_result.summary.success_rate}%
                                                        </div>
                                                        <div className="text-sm text-blue-700">Taux de succès</div>
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {publicationData.results.publication_result?.feed_tracking?.feed_ids_created?.length > 0 && (
                                                <div className="mt-4">
                                                    <h5 className="font-medium text-green-900 mb-2">Feed Amazon créés:</h5>
                                                    <div className="space-y-1">
                                                        {publicationData.results.publication_result.feed_tracking.feed_ids_created.map((feedId, i) => (
                                                            <code key={i} className="block bg-green-100 px-2 py-1 rounded font-mono text-sm">
                                                                {feedId}
                                                            </code>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                                            <h4 className="font-medium text-red-900 mb-2">❌ Erreur de publication</h4>
                                            <p className="text-red-800 text-sm">
                                                {publicationData.results.error || 'Erreur inconnue'}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Section Monitoring */}
            {activeSection === 'monitoring' && (
                <div className="space-y-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center justify-between">
                            <span className="flex items-center gap-2">
                                📊 Monitoring & Logs
                            </span>
                            <button
                                onClick={loadMonitoringData}
                                disabled={loading}
                                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors"
                            >
                                Actualiser
                            </button>
                        </h2>
                        
                        {/* Statistiques */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                    {monitoringData.statistics?.scraping_operations || 0}
                                </div>
                                <div className="text-sm text-blue-700">Scraping</div>
                            </div>
                            <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-center">
                                <div className="text-2xl font-bold text-green-600">
                                    {monitoringData.statistics?.seo_optimizations || 0}
                                </div>
                                <div className="text-sm text-green-700">SEO IA</div>
                            </div>
                            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200 text-center">
                                <div className="text-2xl font-bold text-yellow-600">
                                    {monitoringData.statistics?.price_optimizations || 0}
                                </div>
                                <div className="text-sm text-yellow-700">Prix</div>
                            </div>
                            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200 text-center">
                                <div className="text-2xl font-bold text-purple-600">
                                    {monitoringData.statistics?.publications || 0}
                                </div>
                                <div className="text-sm text-purple-700">Publications</div>
                            </div>
                        </div>
                        
                        {/* Actions récentes */}
                        <div>
                            <h3 className="font-medium text-gray-900 mb-4">🕒 Actions récentes</h3>
                            
                            {monitoringData.recentActions?.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    Aucune action récente trouvée
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {/* Placeholder pour les actions - sera rempli par l'API réelle */}
                                    <div className="p-3 bg-gray-50 rounded-lg border">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-900">
                                                🔍 Scraping ASIN: {scrapingData.asin || 'N/A'}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                Il y a 2 minutes
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-600 mt-1">
                                            Marketplace: {scrapingData.marketplace} • Statut: Succès
                                        </p>
                                    </div>
                                    
                                    {seoData.optimizedContent && (
                                        <div className="p-3 bg-gray-50 rounded-lg border">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-900">
                                                    🚀 Optimisation SEO IA
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    Il y a 5 minutes
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-600 mt-1">
                                                Score: {seoData.optimizedContent.optimization_score}% • 
                                                Status: {seoData.optimizedContent.validation?.overall_status}
                                            </p>
                                        </div>
                                    )}
                                    
                                    {priceData.optimizedPrice && (
                                        <div className="p-3 bg-gray-50 rounded-lg border">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-900">
                                                    💰 Optimisation Prix
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    Il y a 8 minutes
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-600 mt-1">
                                                Prix: {priceData.optimizedPrice.optimized_price?.amount} {priceData.optimizedPrice.currency} • 
                                                Confiance: {priceData.optimizedPrice.optimization_metadata?.confidence_score}%
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Session de publication active */}
                    {publicationData.sessionId && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                📋 Session de publication active
                            </h3>
                            
                            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="font-medium text-blue-900">
                                        Session: <code className="bg-blue-100 px-2 py-1 rounded font-mono text-sm">{publicationData.sessionId}</code>
                                    </span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={async () => {
                                                // Recharger le statut de session
                                                try {
                                                    const response = await apiCall(`/api/amazon/monitoring/session/${publicationData.sessionId}`);
                                                    if (response.success) {
                                                        setMonitoringData(prev => ({
                                                            ...prev,
                                                            sessionStatus: response.session_status
                                                        }));
                                                    }
                                                } catch (error) {
                                                    setError(`Erreur statut session: ${error.message}`);
                                                }
                                            }}
                                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                        >
                                            Actualiser
                                        </button>
                                        <button
                                            onClick={async () => {
                                                try {
                                                    const response = await apiCall(`/api/amazon/monitoring/session/${publicationData.sessionId}/cancel`, 'POST');
                                                    if (response.success) {
                                                        setPublicationData(prev => ({...prev, sessionId: null}));
                                                    }
                                                } catch (error) {
                                                    setError(`Erreur annulation: ${error.message}`);
                                                }
                                            }}
                                            className="text-red-600 hover:text-red-700 text-sm font-medium"
                                        >
                                            Annuler
                                        </button>
                                    </div>
                                </div>
                                <p className="text-blue-800 text-sm">
                                    Statut: <strong>{monitoringData.sessionStatus?.status || 'En cours...'}</strong>
                                </p>
                                {monitoringData.sessionStatus?.message && (
                                    <p className="text-blue-700 text-xs mt-2">
                                        {monitoringData.sessionStatus.message}
                                    </p>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AmazonSEOPriceManager;