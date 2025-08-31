/**
 * Composants PriceTruth - Affichage des prix vérifiés multi-sources
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Badge prix vérifié
export const PriceVerifiedBadge = ({ status, price, currency = "EUR" }) => {
  const getBadgeColor = () => {
    switch (status) {
      case 'valid':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'insufficient_evidence':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'outlier_detected':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'stale_data':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getBadgeIcon = () => {
    switch (status) {
      case 'valid':
        return '✅';
      case 'insufficient_evidence':
        return '⚠️';
      case 'outlier_detected':
        return '📊';
      case 'stale_data':
        return '🕒';
      default:
        return '💰';
    }
  };

  const getBadgeText = () => {
    if (status === 'valid' && price) {
      return `Prix vérifié: ${price}€`;
    }
    switch (status) {
      case 'valid':
        return 'Prix vérifié';
      case 'insufficient_evidence':
        return 'Données insuffisantes';
      case 'outlier_detected':
        return 'Prix variable';
      case 'stale_data':
        return 'Données anciennes';
      default:
        return 'Prix en cours';
    }
  };

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getBadgeColor()}`}>
      <span className="mr-1">{getBadgeIcon()}</span>
      {getBadgeText()}
    </div>
  );
};

// Chips des sources
export const SourceChips = ({ sources = [] }) => {
  const getSourceIcon = (sourceName) => {
    switch (sourceName.toLowerCase()) {
      case 'amazon':
        return '🛒';
      case 'google_shopping':
        return '🛍️';
      case 'cdiscount':
        return '🔵';
      case 'fnac':
        return '📚';
      default:
        return '🏪';
    }
  };

  const getSourceName = (sourceName) => {
    switch (sourceName.toLowerCase()) {
      case 'amazon':
        return 'Amazon';
      case 'google_shopping':
        return 'Google Shopping';
      case 'cdiscount':
        return 'Cdiscount';
      case 'fnac':
        return 'Fnac';
      default:
        return sourceName;
    }
  };

  const getSourceColor = (success) => {
    return success 
      ? 'bg-blue-100 text-blue-800 border-blue-200'
      : 'bg-gray-100 text-gray-600 border-gray-200';
  };

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {sources.map((source, index) => (
        <div 
          key={index}
          className={`inline-flex items-center px-2 py-1 rounded-md text-xs border ${getSourceColor(source.success)}`}
          title={source.success ? `Prix: ${source.price}€` : `Erreur: ${source.error_message}`}
        >
          <span className="mr-1">{getSourceIcon(source.name)}</span>
          {getSourceName(source.name)}
          {source.success && source.price && (
            <span className="ml-1 font-medium">{parseFloat(source.price).toFixed(2)}€</span>
          )}
        </div>
      ))}
    </div>
  );
};

// Composant principal PriceTruth
export const PriceTruthDisplay = ({ productName, className = "" }) => {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchPriceData = async (force = false) => {
    if (!productName) return;

    setLoading(true);
    setError(null);

    try {
      const params = {
        q: productName,
        include_details: 'true'
      };
      
      if (force) {
        params.force = 'true';
      }

      const response = await axios.get(`${API}/price-truth`, { params });
      
      setPriceData(response.data);
      setLastUpdated(new Date(response.data.updated_at));
      setError(null);
    } catch (err) {
      console.error('Erreur récupération prix PriceTruth:', err);
      
      if (err.response?.status === 404) {
        setError('Prix indisponible (sources non concordantes)');
      } else if (err.response?.status === 503) {
        setError('Service de vérification prix temporairement indisponible');
      } else {
        setError('Erreur lors de la récupération du prix');
      }
      setPriceData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productName) {
      fetchPriceData();
    }
  }, [productName]);

  const formatTimestamp = (date) => {
    if (!date) return '';
    
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return 'À l\'instant';
    if (minutes < 60) return `Il y a ${minutes} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!productName) {
    return null;
  }

  return (
    <div className={`price-truth-display ${className}`}>
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 mb-2 flex items-center">
              💰 Prix Vérifié Multi-Sources
              {loading && (
                <svg className="animate-spin ml-2 h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
            </h4>
            
            {/* Badge prix vérifié */}
            {priceData && (
              <PriceVerifiedBadge 
                status={priceData.status} 
                price={priceData.price}
                currency={priceData.currency}
              />
            )}
            
            {/* Message d'erreur */}
            {error && (
              <div className="bg-red-100 border border-red-200 text-red-800 px-3 py-2 rounded-md text-sm">
                {error}
              </div>
            )}
          </div>
          
          {/* Bouton actualiser */}
          <button
            onClick={() => fetchPriceData(true)}
            disabled={loading}
            className="ml-3 bg-white hover:bg-gray-50 disabled:bg-gray-100 border border-gray-300 text-gray-700 px-3 py-1 rounded-md text-xs font-medium flex items-center transition duration-200"
            title="Actualiser maintenant"
          >
            <svg 
              className={`w-3 h-3 mr-1 ${loading ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {loading ? 'MAJ...' : 'Actualiser'}
          </button>
        </div>
        
        {/* Sources chips */}
        {priceData?.sources && (
          <div className="mb-3">
            <div className="text-xs text-gray-600 mb-1">
              Sources consultées ({priceData.sources_count}) - Concordantes ({priceData.agreeing_sources}) :
            </div>
            <SourceChips sources={priceData.sources} />
          </div>
        )}
        
        {/* Timestamp dernière MAJ */}
        {lastUpdated && (
          <div className="flex items-center text-xs text-gray-500 mt-2">
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Dernière mise à jour: {formatTimestamp(lastUpdated)}
            {priceData?.is_fresh && (
              <span className="ml-2 bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs">Frais</span>
            )}
          </div>
        )}
        
        {/* Prix principal si disponible */}
        {priceData?.status === 'valid' && priceData?.price && (
          <div className="mt-3 pt-3 border-t border-blue-200">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {priceData.price.toFixed(2)} {priceData.currency}
              </div>
              <div className="text-xs text-gray-600">
                Prix consensus basé sur {priceData.agreeing_sources} source{priceData.agreeing_sources > 1 ? 's' : ''} concordante{priceData.agreeing_sources > 1 ? 's' : ''}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Composant simplifié pour usage dans la liste des produits
export const PriceTruthBadge = ({ productName, className = "" }) => {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!productName) return;

    const fetchPrice = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API}/price-truth`, {
          params: { q: productName }
        });
        setPriceData(response.data);
      } catch (err) {
        console.error('Erreur prix simple:', err);
        setPriceData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPrice();
  }, [productName]);

  if (loading) {
    return (
      <div className={`inline-flex items-center px-2 py-1 bg-gray-100 rounded text-xs ${className}`}>
        <svg className="animate-spin w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Prix...
      </div>
    );
  }

  if (!priceData || priceData.status !== 'valid' || !priceData.price) {
    return (
      <div className={`inline-flex items-center px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs ${className}`}>
        ⚠️ Prix indisponible
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded text-xs ${className}`}>
      ✅ {priceData.price.toFixed(2)}€
    </div>
  );
};

export default PriceTruthDisplay;