import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ShopifyConnectionManager from '../components/ShopifyConnectionManager';

const ShopifyIntegrationPage = ({ user, token }) => {
  const [activeTab, setActiveTab] = useState('connexions');
  const [shopifyConnectionStatus, setShopifyConnectionStatus] = useState(null);
  const navigate = useNavigate();

  // Rediriger si non authentifié
  useEffect(() => {
    if (!user || !token) {
      navigate('/', { replace: true });
      return;
    }
  }, [user, token, navigate]);

  const handleConnectionChange = (connectionData) => {
    setShopifyConnectionStatus(connectionData);
  };

  const tabs = [
    {
      id: 'connexions',
      name: 'Connexions',
      icon: '🔗',
      description: 'Gérer vos connexions Shopify',
      active: true
    },
    {
      id: 'generateur',
      name: 'Générateur de fiche',
      icon: '🤖',
      description: 'Génération automatique de fiches produits',
      comingSoon: true
    },
    {
      id: 'seo',
      name: 'SEO',
      icon: '📈',
      description: 'Optimisation SEO Shopify',
      comingSoon: true
    },
    {
      id: 'prix-regles',
      name: 'Prix & Règles',
      icon: '💰',
      description: 'Gestion intelligente des prix',
      comingSoon: true
    },
    {
      id: 'monitoring',
      name: 'Monitoring',
      icon: '🔄',
      description: 'Surveillance automatique',
      comingSoon: true
    },
    {
      id: 'optimisations',
      name: 'Optimisations avancées',
      icon: '⚡',
      description: 'A/B Testing, Analytics avancées',
      comingSoon: true
    }
  ];

  if (!user || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                ← Retour au dashboard
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">🛍️</span>
                  Shopify
                </h1>
                <p className="text-sm text-gray-600">
                  Intégration complète avec vos boutiques Shopify
                </p>
              </div>
            </div>

            {/* Indicateur de statut */}
            {shopifyConnectionStatus && (
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  shopifyConnectionStatus.status === 'connected' 
                    ? 'bg-green-500' 
                    : 'bg-gray-400'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {shopifyConnectionStatus.status === 'connected' 
                    ? `${shopifyConnectionStatus.connections_count || 0} boutique(s)` 
                    : 'Non connecté'}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 lg:gap-8">
          {/* Sidebar avec onglets - Responsive */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900 text-base sm:text-lg">Fonctionnalités</h2>
                <p className="text-xs sm:text-sm text-gray-600 mt-1">
                  Phase 1 - Connexions
                </p>
              </div>
              
              {/* Navigation desktop */}
              <nav className="hidden md:block space-y-1 p-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => !tab.comingSoon && setActiveTab(tab.id)}
                    disabled={tab.comingSoon}
                    className={`
                      w-full text-left px-3 py-3 rounded-md transition-colors relative
                      ${activeTab === tab.id 
                        ? 'bg-green-50 text-green-700 border border-green-200' 
                        : tab.comingSoon
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg sm:text-xl flex-shrink-0">{tab.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm sm:text-base truncate">{tab.name}</div>
                        <div className="text-xs text-gray-500 mt-0.5 leading-tight">
                          {tab.description}
                        </div>
                      </div>
                    </div>
                    
                    {tab.comingSoon && (
                      <div className="absolute top-2 right-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          Bientôt
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </nav>

              {/* Navigation mobile - Dropdown */}
              <div className="md:hidden p-2">
                <select
                  value={activeTab}
                  onChange={(e) => setActiveTab(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {tabs.filter(tab => !tab.comingSoon).map((tab) => (
                    <option key={tab.id} value={tab.id}>
                      {tab.icon} {tab.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Informations Phase 1 */}
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <div className="text-xs text-gray-600">
                  <div className="font-medium mb-2">🚀 Phase 1 - Connexions</div>
                  <ul className="space-y-1 text-xs">
                    <li>✅ OAuth 2.0 sécurisé Shopify</li>
                    <li>✅ Multi-boutiques</li>
                    <li>✅ Chiffrement des tokens</li>
                    <li>🔄 Interface responsive</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Contenu principal */}
          <div className="md:col-span-2 lg:col-span-3">
            {activeTab === 'connexions' && (
              <div className="space-y-4 sm:space-y-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                    Connexions Shopify
                  </h2>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Connectez vos boutiques Shopify pour synchroniser vos produits, gérer votre inventaire et optimiser vos ventes automatiquement.
                  </p>
                </div>

                <ShopifyConnectionManager 
                  user={user}
                  token={token}
                  onConnectionChange={handleConnectionChange}
                />

                <div className="bg-green-50 rounded-lg border border-green-200 p-4 sm:p-6">
                  <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2 text-base sm:text-lg">
                    <span>📚</span>
                    Guide de configuration Shopify
                  </h3>
                  
                  <div className="space-y-4 text-green-800">
                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">1. Prérequis</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Boutique Shopify active avec accès admin</li>
                        <li>• Plan Shopify Basic ou supérieur</li>
                        <li>• Permissions d'installation d'applications</li>
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">2. Processus de connexion</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Entrez le nom de votre boutique (ex: "monshop")</li>
                        <li>• Cliquez sur "Connecter ma boutique Shopify"</li>
                        <li>• Autorisez l'accès dans votre admin Shopify</li>
                        <li>• Retour automatique avec confirmation</li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">3. Permissions accordées</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Lecture et écriture des produits</li>
                        <li>• Gestion de l'inventaire</li>
                        <li>• Accès aux commandes (lecture)</li>
                        <li>• Création et mise à jour des fiches</li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">4. Sécurité</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Tokens chiffrés avec AES-GCM</li>
                        <li>• Protection CSRF avec state OAuth</li>
                        <li>• Isolation multi-boutiques</li>
                        <li>• Révocation possible à tout moment</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Placeholders pour les autres onglets */}
            {activeTab !== 'connexions' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6 sm:p-8 text-center">
                <div className="text-4xl sm:text-6xl mb-4">🚀</div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                  Fonctionnalité en développement
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 leading-relaxed">
                  Cette fonctionnalité sera disponible dans les prochaines phases du développement Shopify.
                </p>
                
                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <div className="flex items-center gap-2 text-yellow-800 mb-2 text-sm sm:text-base">
                    <span>⏳</span>
                    <span className="font-medium">Phase 1 - Connexions</span>
                  </div>
                  <p className="text-xs sm:text-sm text-yellow-700 leading-relaxed">
                    Nous nous concentrons d'abord sur l'établissement d'une connexion sécurisée et fiable avec vos boutiques Shopify. 
                    Les fonctionnalités avancées seront déployées progressivement dans les phases suivantes.
                  </p>
                </div>

                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">🔮 Phase 2 à venir</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• Générateur IA de fiches produits</li>
                      <li>• Publication automatique</li>
                      <li>• Synchronisation inventaire</li>
                    </ul>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <h4 className="font-medium text-purple-900 mb-2">⚡ Phases avancées</h4>
                    <ul className="text-sm text-purple-800 space-y-1">
                      <li>• SEO et optimisation</li>
                      <li>• Gestion des prix dynamiques</li>
                      <li>• Analytics et monitoring</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShopifyIntegrationPage;