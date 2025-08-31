import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProductInputForm from './ProductInputForm';
import GeneratedListingPreview from './GeneratedListingPreview';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AmazonListingGenerator = ({ user, token }) => {
  const [currentStep, setCurrentStep] = useState('input'); // 'input', 'preview', 'validation', 'published'
  const [generatedListing, setGeneratedListing] = useState(null);
  const [validationData, setValidationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Vérifier la connexion Amazon au montage
  useEffect(() => {
    checkAmazonConnection();
  }, []);

  const checkAmazonConnection = async () => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/amazon/status`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.status !== 'connected') {
        setError('Connexion Amazon requise. Veuillez vous connecter dans l\'onglet Connexions.');
      }
    } catch (err) {
      console.error('Erreur vérification connexion Amazon:', err);
      setError('Impossible de vérifier la connexion Amazon');
    }
  };

  const handleGenerate = async (productData) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/amazon/listings/generate`,
        productData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.status === 'success') {
        setGeneratedListing(response.data.data);
        setCurrentStep('preview');
        setValidationData(null); // Reset validation when new listing generated
      } else {
        setError(response.data.message || 'Erreur lors de la génération');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      setError(errorMessage);
      console.error('Erreur génération:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async (listingData) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/amazon/listings/validate`,
        listingData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.status === 'success') {
        setValidationData(response.data.data);
        setCurrentStep('validation');
      } else {
        setError(response.data.message || 'Erreur lors de la validation');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      setError(errorMessage);
      console.error('Erreur validation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = (publishResult) => {
    if (publishResult.status === 'success') {
      setCurrentStep('published');
    }
    // Le résultat de publication est géré directement par GeneratedListingPreview
  };

  const handleReset = () => {
    setCurrentStep('input');
    setGeneratedListing(null);
    setValidationData(null);
    setError('');
  };

  const getStepIcon = (step) => {
    const icons = {
      input: '📝',
      preview: '👁️',
      validation: '🔍',
      published: '✅'
    };
    return icons[step] || '📝';
  };

  const getStepTitle = (step) => {
    const titles = {
      input: 'Saisie des informations',
      preview: 'Prévisualisation',
      validation: 'Validation',
      published: 'Publié sur Amazon'
    };
    return titles[step] || 'Génération';
  };

  return (
    <div className="space-y-6">
      {/* En-tête avec progression */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <span className="text-3xl">🤖</span>
              Générateur de fiche produit Amazon
            </h2>
            <p className="text-gray-600 mt-1">
              Génération automatique par IA + Publication réelle via SP-API
            </p>
          </div>
          
          {generatedListing && (
            <button
              onClick={handleReset}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
            >
              🔄 Nouvelle fiche
            </button>
          )}
        </div>

        {/* Indicateur de progression */}
        <div className="flex items-center justify-between">
          {['input', 'preview', 'validation', 'published'].map((step, index) => (
            <div key={step} className="flex items-center">
              <div className={`
                flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                ${currentStep === step || (index <= ['input', 'preview', 'validation', 'published'].indexOf(currentStep))
                  ? 'bg-blue-500 border-blue-500 text-white' 
                  : 'bg-white border-gray-300 text-gray-400'
                }
              `}>
                <span className="text-lg">{getStepIcon(step)}</span>
              </div>
              
              {index < 3 && (
                <div className={`
                  h-1 w-16 mx-2 transition-colors
                  ${index < ['input', 'preview', 'validation', 'published'].indexOf(currentStep)
                    ? 'bg-blue-500' 
                    : 'bg-gray-300'
                  }
                `}></div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 text-center">
          <h3 className="font-medium text-gray-900">
            {getStepTitle(currentStep)}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {currentStep === 'input' && 'Remplissez les informations de votre produit'}
            {currentStep === 'preview' && 'Vérifiez le contenu généré par l\'IA'}
            {currentStep === 'validation' && 'Validation selon les règles Amazon'}
            {currentStep === 'published' && 'Votre fiche est maintenant sur Amazon'}
          </p>
        </div>
      </div>

      {/* Message d'erreur global */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <span className="text-red-500 text-xl">⚠️</span>
            <div>
              <h4 className="font-medium text-red-900">Erreur</h4>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
          
          {error.includes('Connexion Amazon') && (
            <div className="mt-3">
              <button
                onClick={() => window.location.reload()}
                className="text-red-600 hover:text-red-800 text-sm underline"
              >
                Rafraîchir la page après connexion
              </button>
            </div>
          )}
        </div>
      )}

      {/* Contenu principal selon l'étape */}
      {currentStep === 'input' && (
        <ProductInputForm
          onGenerate={handleGenerate}
          loading={loading}
          user={user}
          token={token}
        />
      )}

      {(currentStep === 'preview' || currentStep === 'validation' || currentStep === 'published') && (
        <GeneratedListingPreview
          listingData={generatedListing}
          onValidate={handleValidate}
          onPublish={handlePublish}
          validationData={validationData}
          loading={loading}
          token={token}
        />
      )}

      {/* Instructions et informations */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
        <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
          <span>💡</span>
          Comment ça fonctionne
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl mb-2">📝</div>
            <h4 className="font-medium text-blue-900 mb-1">1. Saisie</h4>
            <p className="text-blue-700 text-sm">
              Renseignez les informations de votre produit
            </p>
          </div>
          
          <div className="text-center">
            <div className="text-3xl mb-2">🤖</div>
            <h4 className="font-medium text-blue-900 mb-1">2. Génération IA</h4>
            <p className="text-blue-700 text-sm">
              L'IA génère titre, bullets, description optimisés
            </p>
          </div>
          
          <div className="text-center">
            <div className="text-3xl mb-2">🔍</div>
            <h4 className="font-medium text-blue-900 mb-1">3. Validation</h4>
            <p className="text-blue-700 text-sm">
              Vérification des règles Amazon A9/A10
            </p>
          </div>
          
          <div className="text-center">
            <div className="text-3xl mb-2">📤</div>
            <h4 className="font-medium text-blue-900 mb-1">4. Publication</h4>
            <p className="text-blue-700 text-sm">
              Publication réelle sur Amazon via SP-API
            </p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-100 rounded-md">
          <h4 className="font-medium text-blue-900 mb-2">🔒 Sécurité & Conformité</h4>
          <ul className="text-blue-800 text-sm space-y-1">
            <li>• Publication via l'API officielle Amazon SP-API</li>
            <li>• Respect des règles Amazon A9/A10 pour le référencement</li>
            <li>• Validation automatique avant publication</li>
            <li>• Connexion sécurisée avec votre compte Amazon Seller</li>
          </ul>
        </div>
      </div>

      {/* Statistiques utilisateur (si disponible) */}
      {currentStep === 'published' && (
        <div className="bg-green-50 rounded-lg border border-green-200 p-6">
          <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2">
            <span>🎉</span>
            Félicitations !
          </h3>
          <p className="text-green-800">
            Votre fiche produit a été publiée avec succès sur Amazon. 
            Elle sera visible dans votre Seller Central sous 24-48h après validation par Amazon.
          </p>
          
          <div className="mt-4 flex gap-3">
            <button
              onClick={handleReset}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              Générer une nouvelle fiche
            </button>
            <button
              onClick={() => window.open('https://sellercentral.amazon.fr', '_blank')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              Ouvrir Seller Central
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AmazonListingGenerator;