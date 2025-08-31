import React, { useState, useEffect, useCallback } from 'react';
// ✅ Import du client API centralisé  
import apiClient from '../lib/apiClient';
import AmazonPublisher from './AmazonPublisher';

// Amazon Connection Status Component
const ConnectionStatusBadge = ({ status }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'active':
        return {
          color: '#22c55e', // green-500
          bgColor: '#dcfce7', // green-100
          text: 'Connecté',
          icon: '✅'
        };
      case 'pending':
        return {
          color: '#f59e0b', // amber-500
          bgColor: '#fef3c7', // amber-100
          text: 'En attente',
          icon: '⏳'
        };
      case 'expired':
        return {
          color: '#ef4444', // red-500
          bgColor: '#fee2e2', // red-100
          text: 'Expiré',
          icon: '⏰'
        };
      case 'revoked':
        return {
          color: '#6b7280', // gray-500
          bgColor: '#f3f4f6', // gray-100
          text: 'Déconnecté',
          icon: '🔌'
        };
      case 'error':
        return {
          color: '#dc2626', // red-600
          bgColor: '#fecaca', // red-200
          text: 'Erreur',
          icon: '❌'
        };
      default:
        return {
          color: '#6b7280',
          bgColor: '#f3f4f6',
          text: 'Inconnu',
          icon: '❓'
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.25rem 0.75rem',
        borderRadius: '9999px',
        backgroundColor: config.bgColor,
        color: config.color,
        fontSize: '0.875rem',
        fontWeight: '500'
      }}
    >
      <span>{config.icon}</span>
      {config.text}
    </span>
  );
};

// Amazon Connection Card Component
const AmazonConnectionCard = ({ connection, onDisconnect, onRefresh }) => {
  const [disconnecting, setDisconnecting] = useState(false);

  const handleDisconnect = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir déconnecter cette intégration Amazon ?')) {
      return;
    }

    setDisconnecting(true);
    try {
      await onDisconnect(connection.connection_id);
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      alert('Erreur lors de la déconnexion. Veuillez réessayer.');
    } finally {
      setDisconnecting(false);
    }
  };

  const getMarketplaceName = (marketplaceId) => {
    const marketplaces = {
      'A13V1IB3VIYZZH': 'Amazon France',
      'A1PA6795UKMFR9': 'Amazon Allemagne',
      'A1RKKUPIHCS9HS': 'Amazon Espagne',
      'APJ6JRA9NG5V4': 'Amazon Italie',
      'A1F83G8C2ARO7P': 'Amazon Royaume-Uni',
      'ATVPDKIKX0DER': 'Amazon États-Unis',
      'A2EUQ1WTGCTBG2': 'Amazon Canada',
      'A1VC38T7YXB528': 'Amazon Japon'
    };
    return marketplaces[marketplaceId] || marketplaceId;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: '0 0 0.25rem 0', color: '#111827' }}>
            {getMarketplaceName(connection.marketplace_id)}
          </h3>
          <ConnectionStatusBadge status={connection.status} />
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={onRefresh}
            style={{
              padding: '0.5rem',
              borderRadius: '0.375rem',
              border: '1px solid #d1d5db',
              backgroundColor: '#ffffff',
              color: '#6b7280',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
            title="Actualiser"
          >
            🔄
          </button>
          
          {connection.status === 'active' && (
            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid #dc2626',
                backgroundColor: disconnecting ? '#fca5a5' : '#ffffff',
                color: '#dc2626',
                cursor: disconnecting ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem'
              }}
            >
              {disconnecting ? '⏳ Déconnexion...' : '🔌 Déconnecter'}
            </button>
          )}
        </div>
      </div>

      {/* Connection Details */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        {connection.seller_id && (
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase' }}>
              ID Vendeur
            </label>
            <p style={{ margin: '0.25rem 0 0 0', fontFamily: 'monospace', fontSize: '0.875rem' }}>
              {connection.seller_id}
            </p>
          </div>
        )}
        
        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase' }}>
            Région
          </label>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
            {connection.region?.toUpperCase()}
          </p>
        </div>

        {connection.connected_at && (
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase' }}>
              Connecté le
            </label>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
              {formatDate(connection.connected_at)}
            </p>
          </div>
        )}

        {connection.last_used_at && (
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase' }}>
              Dernière utilisation
            </label>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem' }}>
              {formatDate(connection.last_used_at)}
            </p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {connection.error_message && (
        <div
          style={{
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '0.375rem'
          }}
        >
          <p style={{ margin: 0, fontSize: '0.875rem', color: '#dc2626' }}>
            <strong>❌ Erreur:</strong> {connection.error_message}
          </p>
        </div>
      )}
    </div>
  );
};

// Main Amazon Integration Component
const AmazonIntegration = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState('A13V1IB3VIYZZH'); // Default to France
  const [activeView, setActiveView] = useState('connections'); // 'connections' ou 'publisher'

  // Available marketplaces
  const marketplaces = [
    { id: 'A13V1IB3VIYZZH', name: 'Amazon France', region: 'eu', flag: '🇫🇷' },
    { id: 'A1PA6795UKMFR9', name: 'Amazon Allemagne', region: 'eu', flag: '🇩🇪' },
    { id: 'A1RKKUPIHCS9HS', name: 'Amazon Espagne', region: 'eu', flag: '🇪🇸' },
    { id: 'APJ6JRA9NG5V4', name: 'Amazon Italie', region: 'eu', flag: '🇮🇹' },
    { id: 'A1F83G8C2ARO7P', name: 'Amazon Royaume-Uni', region: 'eu', flag: '🇬🇧' },
    { id: 'ATVPDKIKX0DER', name: 'Amazon États-Unis', region: 'na', flag: '🇺🇸' },
    { id: 'A2EUQ1WTGCTBG2', name: 'Amazon Canada', region: 'na', flag: '🇨🇦' },
    { id: 'A1VC38T7YXB528', name: 'Amazon Japon', region: 'fe', flag: '🇯🇵' }
  ];

  // Get API base URL
  const getApiBaseUrl = () => {
    return process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  };

  // Get authentication headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // Load connections
  const loadConnections = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get('/amazon/connections');
      
      setConnections(response.data);
    } catch (err) {
      console.error('Erreur lors du chargement des connexions:', err);
      setError(err.response?.data?.detail || 'Erreur lors du chargement des connexions');
    } finally {
      setLoading(false);
    }
  }, []);

  // Connect to Amazon
  const handleConnect = async () => {
    if (!selectedMarketplace) {
      alert('Veuillez sélectionner un marketplace');
      return;
    }

    setConnecting(true);
    setError(null);

    try {
      const marketplace = marketplaces.find(m => m.id === selectedMarketplace);
      
      const response = await apiClient.post('/amazon/connect', {
        marketplace_id: selectedMarketplace,
        region: marketplace.region
      });

      // Redirect to Amazon OAuth
      window.location.href = response.data.authorization_url;
      
    } catch (err) {
      console.error('Erreur lors de la connexion:', err);
      setError(err.response?.data?.detail || 'Erreur lors de la connexion à Amazon');
      setConnecting(false);
    }
  };

  // Disconnect connection
  const handleDisconnect = async (connectionId) => {
    try {
      await apiClient.delete(`/amazon/connections/${connectionId}`);
      
      // Reload connections
      await loadConnections();
      
    } catch (err) {
      console.error('Erreur lors de la déconnexion:', err);
      throw err;
    }
  };

  // Load connections on mount
  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  // Check for OAuth callback success/error
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const error = urlParams.get('error');

    if (success === 'true') {
      // Clean URL and reload connections
      window.history.replaceState({}, document.title, window.location.pathname);
      loadConnections();
    } else if (error) {
      setError(`Erreur OAuth: ${error}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [loadConnections]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
        <p>Chargement des connexions Amazon...</p>
      </div>
    );
  }

  // Rendu conditionnel selon la vue active
  if (activeView === 'publisher') {
    return (
      <div>
        <div style={{ marginBottom: '2rem' }}>
          <button
            onClick={() => setActiveView('connections')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              cursor: 'pointer'
            }}
          >
            ← Retour aux connexions
          </button>
        </div>
        <AmazonPublisher />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '0.5rem', color: '#111827' }}>
          🛒 Intégration Amazon SP-API
        </h1>
        <p style={{ color: '#6b7280', fontSize: '1rem' }}>
          Connectez votre compte vendeur Amazon pour publier automatiquement vos fiches produits.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '0.5rem',
            marginBottom: '2rem'
          }}
        >
          <p style={{ margin: 0, color: '#dc2626' }}>
            <strong>❌ Erreur:</strong> {error}
          </p>
        </div>
      )}

      {/* New Connection Form */}
      <div
        style={{
          border: '1px solid #e5e7eb',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          backgroundColor: '#f9fafb',
          marginBottom: '2rem'
        }}
      >
        <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#111827' }}>
          ➕ Nouvelle Connexion
        </h2>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
            Sélectionner un marketplace Amazon
          </label>
          <select
            value={selectedMarketplace}
            onChange={(e) => setSelectedMarketplace(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              backgroundColor: '#ffffff',
              fontSize: '0.875rem'
            }}
          >
            {marketplaces.map((marketplace) => (
              <option key={marketplace.id} value={marketplace.id}>
                {marketplace.flag} {marketplace.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleConnect}
          disabled={connecting}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: connecting ? '#9ca3af' : '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: connecting ? 'not-allowed' : 'pointer'
          }}
        >
          {connecting ? '⏳ Connexion en cours...' : '🔗 Se connecter à Amazon'}
        </button>
      </div>

      {/* Existing Connections */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#111827' }}>
            📋 Connexions Existantes
          </h2>
          
          {/* Bouton Publisher */}
          {connections.some(conn => conn.status === 'active') && (
            <button
              onClick={() => setActiveView('publisher')}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              📤 Publier un produit
            </button>
          )}
        </div>
        
        {connections.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '3rem',
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '0.5rem'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
            <p style={{ color: '#6b7280', fontSize: '1rem' }}>
              Aucune connexion Amazon active. Créez votre première connexion ci-dessus.
            </p>
          </div>
        ) : (
          connections.map((connection) => (
            <AmazonConnectionCard
              key={connection.connection_id}
              connection={connection}
              onDisconnect={handleDisconnect}
              onRefresh={loadConnections}
            />
          ))
        )}
      </div>

      {/* Help Section */}
      <div
        style={{
          marginTop: '2rem',
          padding: '1.5rem',
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '0.5rem'
        }}
      >
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#1e40af' }}>
          💡 Aide et Documentation
        </h3>
        <ul style={{ paddingLeft: '1.5rem', margin: 0, color: '#1e40af' }}>
          <li>Vous devez avoir un compte vendeur Amazon actif</li>
          <li>L'autorisation permet à ECOMSIMPLY de publier vos produits</li>
          <li>Vous pouvez révoquer l'accès à tout moment</li>
          <li>Les tokens sont chiffrés et stockés de manière sécurisée</li>
        </ul>
      </div>
    </div>
  );
};

export default AmazonIntegration;