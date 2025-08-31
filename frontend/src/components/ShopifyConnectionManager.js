import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ShopifyConnectionManager = ({ user, token, onConnectionChange }) => {
  const [connectionStatus, setConnectionStatus] = useState('none');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [connections, setConnections] = useState([]);
  const [shopDomain, setShopDomain] = useState('');

  // Charger le statut de connexion au montage
  useEffect(() => {
    loadConnectionStatus();
  }, []);

  // Vérifier les paramètres URL pour les redirections OAuth
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const shopifyStatus = urlParams.get('shopify');
    const shopifyError = urlParams.get('shopify_error');

    if (shopifyStatus === 'connected') {
      setConnectionStatus('connected');
      setError('');
      loadConnectionStatus();
      // Nettoyer l'URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (shopifyError) {
      setError(`Erreur de connexion: ${urlParams.get('message') || shopifyError}`);
      // Nettoyer l'URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const loadConnectionStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${BACKEND_URL}/api/shopify/status`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setConnectionStatus(response.data.status);
      setConnections(response.data.active_shops || []);
      
      // Notifier le parent du changement
      if (onConnectionChange) {
        onConnectionChange(response.data);
      }
      
    } catch (err) {
      console.error('Erreur lors du chargement du statut:', err);
      setError('Impossible de charger le statut de connexion');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    if (!shopDomain.trim()) {
      setError('Veuillez entrer le nom de votre boutique Shopify');
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Valider et nettoyer le domaine
      let cleanDomain = shopDomain.trim().toLowerCase();
      
      // Supprimer https:// si présent
      cleanDomain = cleanDomain.replace(/^https?:\/\//, '');
      
      // Ajouter .myshopify.com si pas présent
      if (!cleanDomain.includes('.')) {
        cleanDomain = `${cleanDomain}.myshopify.com`;
      }

      // Lancer l'installation OAuth
      const response = await axios.post(
        `${BACKEND_URL}/api/shopify/install`,
        {
          shop_domain: cleanDomain
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Rediriger vers Shopify pour OAuth
      window.location.href = response.data.install_url;

    } catch (err) {
      console.error('Erreur de connexion:', err);
      setError(
        err.response?.data?.detail || 
        'Erreur lors de la connexion à Shopify'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir déconnecter vos boutiques Shopify ?')) {
      return;
    }

    try {
      setLoading(true);
      setError('');

      await axios.post(
        `${BACKEND_URL}/api/shopify/disconnect`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setConnectionStatus('revoked');
      setConnections([]);
      
      // Notifier le parent
      if (onConnectionChange) {
        onConnectionChange({ status: 'revoked', connections: [] });
      }

    } catch (err) {
      console.error('Erreur de déconnexion:', err);
      setError(
        err.response?.data?.detail || 
        'Erreur lors de la déconnexion'
      );
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          icon: '✅',
          text: 'Connecté',
          description: `${connections.length} boutique(s) connectée(s)`
        };
      case 'pending':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          icon: '⏳',
          text: 'En cours',
          description: 'Installation en cours de traitement'
        };
      case 'error':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          icon: '❌',
          text: 'Erreur',
          description: 'Problème de connexion détecté'
        };
      case 'revoked':
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          icon: '🔌',
          text: 'Déconnecté',
          description: 'Boutiques déconnectées'
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          icon: '➖',
          text: 'Non connecté',
          description: 'Aucune connexion Shopify'
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🛍️</span>
            Connexion Shopify
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Connectez vos boutiques Shopify pour la gestion automatisée
          </p>
        </div>
        
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${statusDisplay.bgColor} ${statusDisplay.color} flex items-center gap-2`}>
          <span>{statusDisplay.icon}</span>
          {statusDisplay.text}
        </div>
      </div>

      {/* Message d'erreur */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Statut détaillé */}
      <div className="mb-6">
        <div className={`p-4 rounded-lg ${statusDisplay.bgColor} border border-gray-200`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{statusDisplay.icon}</span>
            <div>
              <p className={`font-medium ${statusDisplay.color}`}>
                {statusDisplay.text}
              </p>
              <p className="text-sm text-gray-600">
                {statusDisplay.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Boutiques connectées */}
      {connections.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-900 mb-3">Boutiques connectées</h4>
          <div className="space-y-2">
            {connections.map((connection, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🏪</span>
                  <div>
                    <p className="font-medium text-gray-900">
                      {connection.shop_name || connection.shop_domain}
                    </p>
                    <p className="text-sm text-gray-600">
                      {connection.shop_domain}
                    </p>
                    {connection.shop_plan && (
                      <p className="text-xs text-gray-500 capitalize">
                        Plan: {connection.shop_plan}
                      </p>
                    )}
                  </div>
                </div>
                <span className="text-green-600 text-sm">✅ Actif</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interface de connexion */}
      {connectionStatus !== 'connected' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nom de votre boutique Shopify
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={shopDomain}
                  onChange={(e) => setShopDomain(e.target.value)}
                  placeholder="monshop"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 pr-32"
                  disabled={loading}
                />
                <span className="absolute right-3 top-2 text-sm text-gray-500">
                  .myshopify.com
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Entrez le nom de votre boutique (ex: "monshop" pour monshop.myshopify.com)
            </p>
          </div>

          <button
            onClick={handleConnect}
            disabled={loading || !shopDomain.trim()}
            className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Connexion en cours...
              </>
            ) : (
              <>
                <span>🔗</span>
                Connecter ma boutique Shopify
              </>
            )}
          </button>
        </div>
      )}

      {/* Bouton de déconnexion */}
      {connectionStatus === 'connected' && (
        <button
          onClick={handleDisconnect}
          disabled={loading}
          className="w-full bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
              Déconnexion...
            </>
          ) : (
            <>
              <span>🔌</span>
              Déconnecter Shopify
            </>
          )}
        </button>
      )}

      {/* Informations sur les permissions */}
      <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
        <h4 className="font-medium text-green-900 mb-2">🔐 Sécurité & Permissions</h4>
        <ul className="text-sm text-green-800 space-y-1">
          <li>• Connexion sécurisée via OAuth 2.0</li>
          <li>• Tokens chiffrés et stockés de manière sécurisée</li>
          <li>• Accès en lecture/écriture à vos produits</li>
          <li>• Gestion sécurisée de l'inventaire</li>
        </ul>
      </div>

      {/* Guide d'installation */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-medium text-blue-900 mb-2">📖 Guide rapide</h4>
        <div className="text-sm text-blue-800 space-y-2">
          <div>
            <p className="font-medium">1. Préparez votre boutique</p>
            <p className="text-xs">Assurez-vous d'avoir accès admin à votre boutique Shopify</p>
          </div>
          <div>
            <p className="font-medium">2. Entrez le nom de boutique</p>
            <p className="text-xs">Juste le nom, sans .myshopify.com (ex: "monshop")</p>
          </div>
          <div>
            <p className="font-medium">3. Autorisez l'accès</p>
            <p className="text-xs">Vous serez redirigé vers Shopify pour confirmer les permissions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShopifyConnectionManager;