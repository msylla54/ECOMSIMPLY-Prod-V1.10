import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const GeneratedListingPreview = ({ 
  listingData, 
  onValidate, 
  onPublish, 
  validationData, 
  loading, 
  token 
}) => {
  const [publishLoading, setPublishLoading] = useState(false);
  const [validationLoading, setValidationLoading] = useState(false);
  const [publishResult, setPublishResult] = useState(null);

  if (!listingData) {
    return (
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">📝</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Aucune fiche générée
        </h3>
        <p className="text-gray-600">
          Utilisez le formulaire ci-dessus pour générer une fiche produit Amazon
        </p>
      </div>
    );
  }

  const seoContent = listingData.seo_content || {};
  const productData = listingData.product_data || {};
  const metadata = listingData.generation_metadata || {};

  const handleValidation = async () => {
    setValidationLoading(true);
    try {
      await onValidate(listingData);
    } finally {
      setValidationLoading(false);
    }
  };

  const handlePublish = async (forcePublish = false) => {
    setPublishLoading(true);
    setPublishResult(null);
    
    try {
      const publicationRequest = {
        listing_data: listingData,
        validation_data: validationData,
        force_publish: forcePublish
      };

      const response = await axios.post(
        `${BACKEND_URL}/api/amazon/listings/publish`,
        publicationRequest,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setPublishResult(response.data);
      if (onPublish) {
        onPublish(response.data);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setPublishResult({
        status: 'error',
        message: errorMessage,
        errors: [errorMessage]
      });
    } finally {
      setPublishLoading(false);
    }
  };

  const getValidationStatusColor = (status) => {
    switch (status) {
      case 'APPROVED':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'PENDING_REVIEW':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'REJECTED':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getValidationIcon = (status) => {
    switch (status) {
      case 'APPROVED':
        return '✅';
      case 'PENDING_REVIEW':
        return '⚠️';
      case 'REJECTED':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="space-y-6">
      {/* En-tête avec score d'optimisation */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <span>📋</span>
              Prévisualisation de la fiche générée
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Générée le {new Date(listingData.generated_at).toLocaleString('fr-FR')}
            </p>
          </div>
          
          {/* Score d'optimisation */}
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {metadata.optimization_score || 0}%
            </div>
            <div className="text-xs text-gray-500">Score SEO</div>
          </div>
        </div>

        {/* Statut de validation */}
        {validationData && (
          <div className={`p-3 rounded-md border ${getValidationStatusColor(validationData.overall_status)}`}>
            <div className="flex items-center gap-2">
              <span className="text-lg">{getValidationIcon(validationData.overall_status)}</span>
              <div>
                <div className="font-medium">
                  {validationData.overall_status === 'APPROVED' && 'Fiche approuvée'}
                  {validationData.overall_status === 'PENDING_REVIEW' && 'Révision recommandée'}
                  {validationData.overall_status === 'REJECTED' && 'Fiche rejetée'}
                </div>
                <div className="text-sm">
                  Score de validation: {validationData.validation_score}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Titre */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <span>📝</span>
          Titre Amazon ({seoContent.title?.length || 0}/200 caractères)
        </h4>
        <div className="bg-gray-50 p-4 rounded-md">
          <p className="text-gray-900 font-medium">
            {seoContent.title || 'Titre non généré'}
          </p>
        </div>
        {seoContent.title && seoContent.title.length > 200 && (
          <p className="text-red-500 text-xs mt-2">
            ⚠️ Le titre dépasse la limite de 200 caractères
          </p>
        )}
      </div>

      {/* Bullet Points */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <span>🔸</span>
          Points clés ({seoContent.bullet_points?.length || 0}/5)
        </h4>
        <div className="space-y-2">
          {(seoContent.bullet_points || []).map((bullet, index) => (
            <div key={index} className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-600 mb-1">Point {index + 1}:</div>
              <p className="text-gray-900">{bullet}</p>
              <div className="text-xs text-gray-500 mt-1">
                {bullet.length}/255 caractères
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Description */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <span>📄</span>
          Description produit
        </h4>
        <div className="bg-gray-50 p-4 rounded-md">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: seoContent.description || 'Description non générée' }}
          />
        </div>
        {seoContent.description && (
          <div className="text-xs text-gray-500 mt-2">
            {seoContent.description.replace(/<[^>]*>/g, '').length} caractères (sans HTML)
          </div>
        )}
      </div>

      {/* Mots-clés backend */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <span>🔍</span>
          Mots-clés backend
        </h4>
        <div className="bg-gray-50 p-4 rounded-md">
          <p className="text-gray-900 text-sm">
            {seoContent.backend_keywords || 'Mots-clés non générés'}
          </p>
        </div>
        {seoContent.backend_keywords && (
          <div className="text-xs text-gray-500 mt-2">
            {new Blob([seoContent.backend_keywords]).size} bytes / 250 bytes max
          </div>
        )}
      </div>

      {/* Exigences images */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <span>📸</span>
          Exigences images
        </h4>
        
        {seoContent.image_requirements && (
          <div className="space-y-4">
            {/* Image principale */}
            <div className="bg-blue-50 p-4 rounded-md border border-blue-200">
              <h5 className="font-medium text-blue-900 mb-2">Image principale (obligatoire)</h5>
              <p className="text-blue-800 text-sm">
                {seoContent.image_requirements.main_image?.description || 'Description non disponible'}
              </p>
              <div className="text-xs text-blue-600 mt-2">
                • Résolution minimum: {seoContent.image_requirements.main_image?.min_resolution || '1000x1000px'}
                <br />
                • Fond: {seoContent.image_requirements.main_image?.background || 'Blanc'}
                <br />
                • Format: {seoContent.image_requirements.main_image?.format || 'JPEG/PNG'}
              </div>
            </div>

            {/* Images supplémentaires */}
            {seoContent.image_requirements.additional_images && 
             seoContent.image_requirements.additional_images.length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2">Images supplémentaires suggérées</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {seoContent.image_requirements.additional_images.slice(0, 4).map((img, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-700">
                        {img.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Erreurs et avertissements de validation */}
      {validationData && (validationData.errors?.length > 0 || validationData.warnings?.length > 0) && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
            <span>⚠️</span>
            Résultats de validation
          </h4>
          
          {validationData.errors?.length > 0 && (
            <div className="mb-4">
              <h5 className="font-medium text-red-900 mb-2">Erreurs à corriger:</h5>
              <ul className="list-disc list-inside space-y-1">
                {validationData.errors.map((error, index) => (
                  <li key={index} className="text-red-700 text-sm">{error}</li>
                ))}
              </ul>
            </div>
          )}

          {validationData.warnings?.length > 0 && (
            <div>
              <h5 className="font-medium text-yellow-900 mb-2">Avertissements:</h5>
              <ul className="list-disc list-inside space-y-1">
                {validationData.warnings.map((warning, index) => (
                  <li key={index} className="text-yellow-700 text-sm">{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Résultat de publication */}
      {publishResult && (
        <div className={`bg-white rounded-lg border p-6 ${
          publishResult.status === 'success' 
            ? 'border-green-200' 
            : 'border-red-200'
        }`}>
          <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
            <span>{publishResult.status === 'success' ? '✅' : '❌'}</span>
            Résultat de publication
          </h4>
          
          <p className={`mb-2 ${
            publishResult.status === 'success' 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            {publishResult.message}
          </p>

          {publishResult.status === 'success' && publishResult.data && (
            <div className="bg-green-50 p-4 rounded-md">
              <p className="text-green-800 text-sm">
                <strong>SKU:</strong> {publishResult.data.sku}
              </p>
              {publishResult.data.listing_url && (
                <p className="text-green-800 text-sm mt-1">
                  <strong>URL:</strong> 
                  <a 
                    href={publishResult.data.listing_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline ml-1"
                  >
                    Voir sur Amazon
                  </a>
                </p>
              )}
            </div>
          )}

          {publishResult.errors && publishResult.errors.length > 0 && (
            <div className="bg-red-50 p-4 rounded-md mt-2">
              <h5 className="font-medium text-red-900 mb-2">Erreurs:</h5>
              <ul className="list-disc list-inside space-y-1">
                {publishResult.errors.map((error, index) => (
                  <li key={index} className="text-red-700 text-sm">{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Boutons d'action */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Bouton Valider */}
          <button
            onClick={handleValidation}
            disabled={validationLoading || loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
          >
            {validationLoading ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Validation...
              </>
            ) : (
              <>
                <span>🔍</span>
                Valider la fiche
              </>
            )}
          </button>

          {/* Bouton Publier */}
          <button
            onClick={() => handlePublish(false)}
            disabled={publishLoading || loading || !validationData}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
          >
            {publishLoading ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Publication...
              </>
            ) : (
              <>
                <span>📤</span>
                Publier sur Amazon
              </>
            )}
          </button>

          {/* Bouton Forcer la publication (si rejetée/en attente) */}
          {validationData && validationData.overall_status !== 'APPROVED' && (
            <button
              onClick={() => handlePublish(true)}
              disabled={publishLoading || loading}
              className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
            >
              {publishLoading ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Publication forcée...
                </>
              ) : (
                <>
                  <span>⚡</span>
                  Forcer la publication
                </>
              )}
            </button>
          )}
        </div>

        <div className="mt-4 text-xs text-gray-500">
          <p>
            • La validation vérifie la conformité aux règles Amazon
            <br />
            • La publication envoie réellement la fiche sur Amazon via SP-API
            <br />
            • "Forcer la publication" ignore les avertissements de validation
          </p>
        </div>
      </div>
    </div>
  );
};

export default GeneratedListingPreview;