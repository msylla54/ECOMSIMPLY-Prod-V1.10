import React, { useState, useEffect } from 'react';

const MarketSettingsManager = ({ userConfig, onConfigUpdate }) => {
  const [marketSettings, setMarketSettings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [editingCountry, setEditingCountry] = useState(null);

  // Configuration des pays supportés
  const supportedCountries = {
    'FR': { name: 'France', flag: '🇫🇷', currency: 'EUR' },
    'GB': { name: 'United Kingdom', flag: '🇬🇧', currency: 'GBP' },
    'US': { name: 'United States', flag: '🇺🇸', currency: 'USD' }
  };

  const supportedCurrencies = ['EUR', 'GBP', 'USD'];

  // Charger les paramètres de marché
  useEffect(() => {
    loadMarketSettings();
  }, []);

  const loadMarketSettings = async () => {
    setLoading(true);
    setError(null);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const response = await fetch(`${backendUrl}/api/v1/settings/market`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const settings = await response.json();
      setMarketSettings(settings);

    } catch (err) {
      console.error('Erreur chargement paramètres marché:', err);
      setError(err.message || 'Erreur lors du chargement des paramètres');
    } finally {
      setLoading(false);
    }
  };

  const updateMarketSetting = async (countryCode, settingData) => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const response = await fetch(`${backendUrl}/api/v1/settings/market`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          country_code: countryCode,
          ...settingData
        })
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const updatedSetting = await response.json();

      // Mettre à jour l'état local
      setMarketSettings(prevSettings => 
        prevSettings.map(setting => 
          setting.country_code === countryCode ? updatedSetting : setting
        )
      );

      setSuccess(true);
      setEditingCountry(null);

      // Notification du parent
      if (onConfigUpdate) {
        onConfigUpdate(updatedSetting);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);

    } catch (err) {
      console.error('Erreur mise à jour paramètres marché:', err);
      setError(err.message || 'Erreur lors de la mise à jour');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCountry = async (countryCode, enabled) => {
    const setting = marketSettings.find(s => s.country_code === countryCode);
    if (setting) {
      await updateMarketSetting(countryCode, {
        currency_preference: setting.currency_preference,
        enabled: enabled,
        price_publish_min: setting.price_publish_min,
        price_publish_max: setting.price_publish_max,
        price_variance_threshold: setting.price_variance_threshold
      });
    }
  };

  const getCountryStatus = (setting) => {
    if (!setting.enabled) return 'Inactif';
    
    const hasMinMax = setting.price_publish_min !== null && setting.price_publish_max !== null;
    if (!hasMinMax) return 'Incomplet';
    
    return 'Actif';
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'Actif': return 'bg-green-100 text-green-800';
      case 'Incomplet': return 'bg-yellow-100 text-yellow-800';
      case 'Inactif': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const EditForm = ({ setting, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
      currency_preference: setting.currency_preference || supportedCountries[setting.country_code]?.currency || 'EUR',
      enabled: setting.enabled,
      price_publish_min: setting.price_publish_min || '',
      price_publish_max: setting.price_publish_max || '',
      price_variance_threshold: setting.price_variance_threshold || 0.20
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      
      // Validation
      if (formData.price_publish_min && formData.price_publish_max) {
        if (parseFloat(formData.price_publish_max) <= parseFloat(formData.price_publish_min)) {
          setError('Le prix maximum doit être supérieur au prix minimum');
          return;
        }
      }

      const submitData = {
        ...formData,
        price_publish_min: formData.price_publish_min ? parseFloat(formData.price_publish_min) : null,
        price_publish_max: formData.price_publish_max ? parseFloat(formData.price_publish_max) : null
      };

      onSave(setting.country_code, submitData);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {supportedCountries[setting.country_code]?.flag} Configuration {supportedCountries[setting.country_code]?.name}
              </h3>
              <button
                onClick={onCancel}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Devise préférée */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Devise préférée
                </label>
                <select
                  value={formData.currency_preference}
                  onChange={(e) => setFormData({...formData, currency_preference: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {supportedCurrencies.map(currency => (
                    <option key={currency} value={currency}>{currency}</option>
                  ))}
                </select>
              </div>

              {/* Activation du marché */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <label className="text-sm font-medium text-gray-900">
                    Activer le marché
                  </label>
                  <p className="text-sm text-gray-600">
                    Permet le scraping de prix pour ce pays
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setFormData({...formData, enabled: !formData.enabled})}
                  className={`${
                    formData.enabled ? 'bg-blue-600' : 'bg-gray-200'
                  } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`}
                >
                  <span
                    className={`${
                      formData.enabled ? 'translate-x-5' : 'translate-x-0'
                    } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
                  />
                </button>
              </div>

              {/* Price Guards */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-900">Price Guards (Gardes Prix)</h4>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prix minimum (€)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price_publish_min}
                      onChange={(e) => setFormData({...formData, price_publish_min: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0.01"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prix maximum (€)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price_publish_max}
                      onChange={(e) => setFormData({...formData, price_publish_max: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="10000.00"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Seuil de variance ({(formData.price_variance_threshold * 100).toFixed(0)}%)
                  </label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.50"
                    step="0.05"
                    value={formData.price_variance_threshold}
                    onChange={(e) => setFormData({...formData, price_variance_threshold: parseFloat(e.target.value)})}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>5%</span>
                    <span>25%</span>
                    <span>50%</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sauvegarde...' : 'Sauvegarder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  if (loading && marketSettings.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Chargement des paramètres de marché...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🌍 Paramètres de Marché Multi-Pays
        </h3>
        <p className="text-sm text-gray-600">
          Configurez le scraping de prix et les gardes prix par pays pour optimiser vos publications.
        </p>
      </div>

      {/* Messages d'erreur et succès */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">Paramètres mis à jour avec succès</p>
            </div>
          </div>
        </div>
      )}

      {/* Liste des marchés */}
      <div className="space-y-4">
        {marketSettings.map((setting) => {
          const country = supportedCountries[setting.country_code];
          const status = getCountryStatus(setting);
          
          return (
            <div key={setting.country_code} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{country?.flag}</span>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">
                      {country?.name}
                    </h4>
                    <p className="text-xs text-gray-500">
                      Devise: {setting.currency_preference} • Variance: {(setting.price_variance_threshold * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {/* Badge de statut */}
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(status)}`}>
                    {status}
                  </span>

                  {/* Toggle activation */}
                  <button
                    onClick={() => handleToggleCountry(setting.country_code, !setting.enabled)}
                    disabled={loading}
                    className={`${
                      setting.enabled ? 'bg-blue-600' : 'bg-gray-200'
                    } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <span
                      className={`${
                        setting.enabled ? 'translate-x-5' : 'translate-x-0'
                      } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
                    />
                  </button>

                  {/* Bouton de configuration */}
                  <button
                    onClick={() => setEditingCountry(setting.country_code)}
                    disabled={loading}
                    className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Détails de configuration si activé */}
              {setting.enabled && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Prix min/max:</span>
                      <span className="ml-2 text-gray-900">
                        {setting.price_publish_min ? `${setting.price_publish_min}€` : 'Non défini'} - {setting.price_publish_max ? `${setting.price_publish_max}€` : 'Non défini'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Sources actives:</span>
                      <span className="ml-2 text-gray-900">
                        {setting.country_code === 'FR' ? 'Amazon.fr, Fnac, Darty...' : 
                         setting.country_code === 'GB' ? 'Amazon.co.uk, Argos...' : 
                         'Amazon.com, BestBuy...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Information panel */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-800 mb-1">Fonctionnement des Price Guards</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <p>• <strong>Bornes absolues:</strong> Prix min/max autorisés pour auto-publication</p>
              <p>• <strong>Variance:</strong> Écart maximum entre les sources (défaut 20%)</p>
              <p>• <strong>Hors bornes:</strong> → PENDING_REVIEW (publication manuelle requise)</p>
              <p>• <strong>Dans les bornes:</strong> → APPROVE (auto-publication autorisée)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Modal d'édition */}
      {editingCountry && (
        <EditForm
          setting={marketSettings.find(s => s.country_code === editingCountry)}
          onSave={updateMarketSetting}
          onCancel={() => setEditingCountry(null)}
        />
      )}
    </div>
  );
};

export default MarketSettingsManager;