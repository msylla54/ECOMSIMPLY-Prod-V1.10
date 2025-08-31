import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AmazonConnectionManager from '../components/AmazonConnectionManager';
import AmazonListingGenerator from '../components/AmazonListingGenerator';
import AmazonSEOPriceManager from '../components/AmazonSEOPriceManager';
import AmazonPricingRulesManager from '../components/AmazonPricingRulesManager';
import AmazonPhase6Manager from '../components/AmazonPhase6Manager';
import AmazonMonitoringDashboard from '../components/AmazonMonitoringDashboard';

const AmazonIntegrationPage = ({ user, token }) => {
  const [activeTab, setActiveTab] = useState('connexions');
  const [amazonConnectionStatus, setAmazonConnectionStatus] = useState(null);
  const navigate = useNavigate();

  // Rediriger si non authentifié
  useEffect(() => {
    if (!user || !token) {
      navigate('/', { replace: true });
      return;
    }
  }, [user, token, navigate]);

  const handleConnectionChange = (connectionData) => {
    setAmazonConnectionStatus(connectionData);
  };

  const tabs = [
    {
      id: 'connexions',
      name: 'Connexions',
      icon: '🔗',
      description: 'Gérer vos connexions Amazon',
      active: true
    },
    {
      id: 'seo',
      name: 'SEO',
      icon: '📈',
      description: 'Optimisation SEO Amazon A9/A10',
      active: false,
      comingSoon: true
    },
    {
      id: 'prix',
      name: 'Prix',
      icon: '💰',
      description: 'Gestion des prix et surveillance',
      active: false,
      comingSoon: true
    },
    {
      id: 'generateur',
      name: 'Générateur de fiche',
      icon: '🤖',
      description: 'Génération automatique de fiches produits',
      active: true
    },
    {
      id: 'seo-prix',
      name: 'SEO & Prix',
      icon: '🚀',
      description: 'Scraping + Optimisation + Auto-publish',
      badge: 'PHASE 3'
    },
    {
      id: 'prix-regles',
      name: 'Prix & Règles',
      icon: '💰',
      description: 'Moteur prix intelligents + Buy Box',
      badge: 'PHASE 4'
    },
    {
      id: 'phase6_optimisations',
      name: 'Optimisations avancées',
      icon: '🚀',
      description: 'A/B Testing, A+ Content, Variations, Compliance',
      badge: 'PHASE 6'
    },
    {
      id: 'monitoring',
      name: 'Monitoring',
      icon: '🔄',
      description: 'Surveillance + Optimisation Auto',
      badge: 'PHASE 5'
    },
    {
      id: 'optimisations',
      name: 'Optimisations',
      icon: '⚡',
      description: 'Améliorations automatiques',
      active: false,
      comingSoon: true
    }
  ];

  if (!user || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
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
                  <span className="text-2xl">🛒</span>
                  Amazon SP-API
                </h1>
                <p className="text-sm text-gray-600">
                  Intégration complète avec Amazon Seller Central
                </p>
              </div>
            </div>

            {/* Indicateur de statut */}
            {amazonConnectionStatus && (
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  amazonConnectionStatus.status === 'connected' 
                    ? 'bg-green-500' 
                    : 'bg-gray-400'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {amazonConnectionStatus.status === 'connected' 
                    ? `${amazonConnectionStatus.connections_count || 0} marketplace(s)` 
                    : 'Non connecté'}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 lg:gap-8">
          {/* Sidebar avec onglets */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900 text-base sm:text-lg">Fonctionnalités</h2>
                <p className="text-xs sm:text-sm text-gray-600 mt-1">
                  Phase 1 - Fondations
                </p>
              </div>
              
              <nav className="space-y-1 p-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => !tab.comingSoon && setActiveTab(tab.id)}
                    disabled={tab.comingSoon}
                    className={`
                      w-full text-left px-3 py-3 rounded-md transition-colors relative touch-manipulation
                      ${activeTab === tab.id 
                        ? 'bg-blue-50 text-blue-700 border border-blue-200' 
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

                    {tab.id === 'generateur' && tab.active && (
                      <div className="absolute top-2 right-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          NOUVEAU
                        </span>
                      </div>
                    )}

                    {tab.badge && (
                      <div className="absolute top-2 right-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          tab.badge === 'PHASE 3' 
                            ? 'bg-purple-100 text-purple-800'
                            : tab.badge === 'PHASE 4'
                            ? 'bg-orange-100 text-orange-800'
                            : tab.badge === 'PHASE 5'
                            ? 'bg-teal-100 text-teal-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {tab.badge}
                        </span>
                      </div>
                    )}
                  </button>
                ))}
              </nav>

              {/* Informations Phase 1 */}
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <div className="text-xs text-gray-600">
                  <div className="font-medium mb-2">🚀 Phase 1 - Fondations</div>
                  <ul className="space-y-1 text-xs">
                    <li>✅ Connexion SP-API OAuth 2.0</li>
                    <li>✅ Multi-tenant sécurisé</li>
                    <li>✅ Chiffrement des tokens</li>
                    <li>🔄 UI dédiée Amazon</li>
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
                    Connexions Amazon
                  </h2>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Configurez vos connexions Amazon Seller Central pour accéder à vos données de vente et gérer vos listings.
                  </p>
                </div>

                <AmazonConnectionManager 
                  user={user}
                  token={token}
                  onConnectionChange={handleConnectionChange}
                />

                <div className="bg-blue-50 rounded-lg border border-blue-200 p-4 sm:p-6">
                  <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2 text-base sm:text-lg">
                    <span>📚</span>
                    Guide de configuration
                  </h3>
                  
                  <div className="space-y-4 text-blue-800">
                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">1. Prérequis</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Compte Amazon Seller Central actif</li>
                        <li>• Statut de vendeur professionnel</li>
                        <li>• Autorisations SP-API activées</li>
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">2. Processus de connexion</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Sélectionnez votre marketplace principal</li>
                        <li>• Cliquez sur "Connecter mon compte Amazon"</li>
                        <li>• Autorisez l'accès dans Amazon Seller Central</li>
                        <li>• Retour automatique avec confirmation</li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2 text-sm sm:text-base">3. Sécurité</h4>
                      <ul className="text-xs sm:text-sm space-y-1 ml-4 leading-relaxed">
                        <li>• Tokens chiffrés avec AES-GCM</li>
                        <li>• Protection CSRF avec state OAuth</li>
                        <li>• Isolation multi-tenant</li>
                        <li>• Révocation possible à tout moment</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'generateur' && (
              <div className="space-y-4 sm:space-y-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
                    <span className="text-2xl sm:text-3xl">🤖</span>
                    <span>Générateur de fiche produit</span>
                  </h2>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    Générez automatiquement des fiches produits Amazon optimisées par IA et publiez-les directement via SP-API.
                  </p>
                </div>

                <AmazonListingGenerator 
                  user={user}
                  token={token}
                />
              </div>
            )}

            {activeTab === 'phase6_optimisations' && (
              <AmazonPhase6Manager user={user} token={token} />
            )}

            {activeTab === 'monitoring' && (
              <AmazonMonitoringDashboard 
                user={user}
                token={token}
              />
            )}

            {/* Placeholders pour les autres onglets */}
            {activeTab !== 'connexions' && activeTab !== 'generateur' && activeTab !== 'seo-prix' && activeTab !== 'prix-regles' && activeTab !== 'monitoring' && (
              <div className="bg-white rounded-lg border border-gray-200 p-6 sm:p-8 text-center">
                <div className="text-4xl sm:text-6xl mb-4">🚀</div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                  Fonctionnalité en développement
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 leading-relaxed">
                  Cette fonctionnalité sera disponible dans les prochaines phases du développement Amazon SP-API.
                </p>
                
                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <div className="flex items-center gap-2 text-yellow-800 mb-2 text-sm sm:text-base">
                    <span>⏳</span>
                    <span className="font-medium">Phase 1 - Fondations</span>
                  </div>
                  <p className="text-xs sm:text-sm text-yellow-700 leading-relaxed">
                    Nous nous concentrons d'abord sur l'établissement d'une connexion sécurisée et fiable avec Amazon SP-API. 
                    Les fonctionnalités avancées seront déployées progressivement.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'seo-prix' && (
              <AmazonSEOPriceManager />
            )}

            {activeTab === 'prix-regles' && (
              <AmazonPricingRulesManager 
                user={user}
                token={token}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmazonIntegrationPage;