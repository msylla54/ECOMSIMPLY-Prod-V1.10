import React, { useState, useEffect } from 'react';

const ImageManagementSettings = ({ userConfig, onConfigUpdate }) => {
  const [settings, setSettings] = useState({
    generate_images: true,
    include_images_manual: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Initialize settings from userConfig prop
  useEffect(() => {
    if (userConfig) {
      setSettings({
        generate_images: userConfig.generate_images ?? true,
        include_images_manual: userConfig.include_images_manual ?? true
      });
    }
  }, [userConfig]);

  const updatePreferences = async (newSettings) => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const response = await fetch(`${backendUrl}/api/images/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newSettings)
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Update local state with the response
      setSettings({
        generate_images: result.generate_images,
        include_images_manual: result.include_images_manual
      });

      setSuccess(true);
      
      // Call parent component callback if provided
      if (onConfigUpdate) {
        onConfigUpdate(result);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);

    } catch (err) {
      console.error('Erreur mise à jour préférences images:', err);
      setError(err.message || 'Erreur lors de la mise à jour des préférences');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateImagesChange = async (newValue) => {
    const newSettings = {
      generate_images: newValue,
      // Auto-correct: if we disable image generation, also disable manual inclusion
      include_images_manual: newValue ? settings.include_images_manual : false
    };

    await updatePreferences(newSettings);
  };

  const handleIncludeImagesManualChange = async (newValue) => {
    // Only allow manual inclusion if image generation is enabled
    if (!settings.generate_images && newValue) {
      setError("Impossible d'inclure des images en publication manuelle si la génération d'images est désactivée");
      return;
    }

    const newSettings = {
      ...settings,
      include_images_manual: newValue
    };

    await updatePreferences(newSettings);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Gestion des Images
        </h3>
        <p className="text-sm text-gray-600">
          Configurez comment les images sont générées et incluses dans vos publications.
        </p>
      </div>

      {/* Error Alert */}
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

      {/* Success Alert */}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">Préférences mises à jour avec succès</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Generate Images Toggle */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex-1 pr-4">
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Génération d'images
            </label>
            <p className="text-sm text-gray-600">
              Active la génération automatique d'images IA pour vos fiches produit
            </p>
          </div>
          <div className="flex-shrink-0">
            <button
              type="button"
              disabled={loading}
              onClick={() => handleGenerateImagesChange(!settings.generate_images)}
              className={`${
                settings.generate_images ? 'bg-blue-600' : 'bg-gray-200'
              } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed`}
              role="switch"
              aria-checked={settings.generate_images}
            >
              <span
                aria-hidden="true"
                className={`${
                  settings.generate_images ? 'translate-x-5' : 'translate-x-0'
                } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
              />
            </button>
          </div>
        </div>

        {/* Include Images Manual Toggle */}
        <div className={`flex items-center justify-between p-4 rounded-lg ${
          settings.generate_images ? 'bg-gray-50' : 'bg-gray-100 opacity-60'
        }`}>
          <div className="flex-1 pr-4">
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Inclure images en publication manuelle
            </label>
            <p className="text-sm text-gray-600">
              {settings.generate_images 
                ? "Contrôle si les images sont incluses lors des publications manuelles"
                : "Disponible uniquement si la génération d'images est activée"
              }
            </p>
          </div>
          <div className="flex-shrink-0">
            <button
              type="button"
              disabled={loading || !settings.generate_images}
              onClick={() => handleIncludeImagesManualChange(!settings.include_images_manual)}
              className={`${
                settings.include_images_manual && settings.generate_images ? 'bg-blue-600' : 'bg-gray-200'
              } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed`}
              role="switch"
              aria-checked={settings.include_images_manual && settings.generate_images}
            >
              <span
                aria-hidden="true"
                className={`${
                  settings.include_images_manual && settings.generate_images ? 'translate-x-5' : 'translate-x-0'
                } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
              />
            </button>
          </div>
        </div>

        {/* Information Panel */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800 mb-1">Règles de publication</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>• <strong>Publication automatique:</strong> Les images sont toujours exclues</p>
                <p>• <strong>Publication manuelle:</strong> Respecte vos paramètres ci-dessus</p>
                {!settings.generate_images && (
                  <p>• <strong>Génération désactivée:</strong> Aucune image ne sera générée</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600">Mise à jour en cours...</span>
        </div>
      )}
    </div>
  );
};

export default ImageManagementSettings;