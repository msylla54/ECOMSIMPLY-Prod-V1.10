import React, { useState, useEffect, useCallback } from 'react';

const AmazonSEOOptimizer = ({ userConfig, onConfigUpdate }) => {
  const [activeMode, setActiveMode] = useState('generate'); // generate, validate, optimize
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // État pour génération
  const [productData, setProductData] = useState({
    product_name: '',
    brand: '',
    model: '',
    category: 'électronique',
    features: [''],
    benefits: [''],
    use_cases: [''],
    size: '',
    color: '',
    images: [''],
    additional_keywords: ['']
  });
  
  // État pour validation/optimisation
  const [listingData, setListingData] = useState({
    title: '',
    bullets: ['', '', '', '', ''],
    description: '',
    backend_keywords: '',
    images: [''],
    brand: '',
    model: '',
    category: 'électronique'
  });
  
  // Résultats
  const [generatedListing, setGeneratedListing] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  
  // Règles Amazon A9/A10
  const amazonRules = {
    title: { maxLength: 200, required: true },
    bullets: { count: 5, maxLength: 255, required: true },
    description: { minLength: 100, maxLength: 2000, required: true },
    backend_keywords: { maxBytes: 250, required: false }
  };

  const categories = [
    { value: 'électronique', label: 'Électronique & High-Tech' },
    { value: 'mode', label: 'Mode & Accessoires' },
    { value: 'maison', label: 'Maison & Décoration' },
    { value: 'sport', label: 'Sports & Loisirs' },
    { value: 'auto', label: 'Auto & Moto' },
    { value: 'santé', label: 'Santé & Beauté' }
  ];

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccess(false);
  }, []);

  const handleArrayFieldChange = (array, setArray, index, value) => {
    const newArray = [...array];
    newArray[index] = value;
    setArray(newArray);
  };

  const addArrayField = (array, setArray) => {
    if (array.length < 10) {
      setArray([...array, '']);
    }
  };

  const removeArrayField = (array, setArray, index) => {
    if (array.length > 1) {
      const newArray = array.filter((_, i) => i !== index);
      setArray(newArray);
    }
  };

  const generateOptimizedListing = async () => {
    setLoading(true);
    clearMessages();

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      // Nettoyer les données (supprimer les champs vides)
      const cleanProductData = {
        ...productData,
        features: productData.features.filter(f => f.trim()),
        benefits: productData.benefits.filter(b => b.trim()),
        use_cases: productData.use_cases.filter(u => u.trim()),
        images: productData.images.filter(i => i.trim()),
        additional_keywords: productData.additional_keywords.filter(k => k.trim())
      };

      const response = await fetch(`${backendUrl}/api/amazon/seo/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(cleanProductData)
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setGeneratedListing(result.data);
      setSuccess(true);

      // Auto-remplir les champs de validation avec le listing généré
      const listing = result.data.listing;
      setListingData({
        title: listing.title,
        bullets: listing.bullets.concat(['', '', '', '', '']).slice(0, 5),
        description: listing.description,
        backend_keywords: listing.backend_keywords,
        images: listing.images.concat(['', '', '', '']).slice(0, 4),
        brand: listing.metadata?.brand || '',
        model: listing.metadata?.model || '',
        category: listing.metadata?.category || 'électronique'
      });

    } catch (err) {
      console.error('Erreur génération SEO:', err);
      setError(err.message || 'Erreur lors de la génération du listing optimisé');
    } finally {
      setLoading(false);
    }
  };

  const validateListing = async () => {
    setLoading(true);
    clearMessages();

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      // Nettoyer les données
      const cleanListingData = {
        ...listingData,
        bullets: listingData.bullets.filter(b => b.trim()),
        images: listingData.images.filter(i => i.trim())
      };

      const response = await fetch(`${backendUrl}/api/amazon/seo/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(cleanListingData)
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setValidationResult(result.data);
      setSuccess(true);

    } catch (err) {
      console.error('Erreur validation SEO:', err);
      setError(err.message || 'Erreur lors de la validation du listing');
    } finally {
      setLoading(false);
    }
  };

  const optimizeListing = async () => {
    setLoading(true);
    clearMessages();

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const cleanListingData = {
        ...listingData,
        bullets: listingData.bullets.filter(b => b.trim()),
        images: listingData.images.filter(i => i.trim())
      };

      const response = await fetch(`${backendUrl}/api/amazon/seo/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_listing: cleanListingData,
          optimization_options: {}
        })
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setOptimizationResult(result.data);
      
      // Proposer d'appliquer les optimisations
      if (result.data.recommendations.should_update) {
        const optimizedListing = result.data.optimized.listing;
        setListingData({
          title: optimizedListing.title,
          bullets: optimizedListing.bullets.concat(['', '', '', '', '']).slice(0, 5),
          description: optimizedListing.description,
          backend_keywords: optimizedListing.backend_keywords,
          images: optimizedListing.images.concat(['', '', '', '']).slice(0, 4),
          brand: optimizedListing.metadata?.brand || listingData.brand,
          model: optimizedListing.metadata?.model || listingData.model,
          category: optimizedListing.metadata?.category || listingData.category
        });
      }
      
      setSuccess(true);

    } catch (err) {
      console.error('Erreur optimisation SEO:', err);
      setError(err.message || 'Erreur lors de l\'optimisation du listing');
    } finally {
      setLoading(false);
    }
  };

  const getValidationStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-50 border-green-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'rejected': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getValidationStatusIcon = (status) => {
    switch (status) {
      case 'approved': return '✅';
      case 'warning': return '⚠️';
      case 'rejected': return '❌';
      default: return '⭕';
    }
  };

  const CharacterCounter = ({ text, maxLength, maxBytes = null }) => {
    const currentLength = text.length;
    const currentBytes = maxBytes ? new TextEncoder().encode(text).length : null;
    const isOverLimit = maxBytes ? currentBytes > maxBytes : currentLength > maxLength;
    
    return (
      <div className={`text-xs mt-1 ${isOverLimit ? 'text-red-500' : 'text-gray-500'}`}>
        {maxBytes ? (
          `${currentBytes}/${maxBytes} bytes`
        ) : (
          `${currentLength}/${maxLength} caractères`
        )}
        {isOverLimit && (
          <span className="ml-2 font-medium">⚠️ Limite dépassée</span>
        )}
      </div>
    );
  };

  const ValidationFeedback = ({ validation }) => {
    if (!validation) return null;

    return (
      <div className="mt-4 p-4 border rounded-lg bg-white">
        <div className="flex items-center mb-3">
          <span className="text-2xl mr-2">
            {getValidationStatusIcon(validation.status)}
          </span>
          <div>
            <h4 className="font-semibold text-lg">
              Validation Amazon A9/A10
            </h4>
            <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium border ${getValidationStatusColor(validation.status)}`}>
              {validation.status.toUpperCase()} - Score: {validation.score}/100
            </div>
          </div>
        </div>

        {validation.reasons.length > 0 && (
          <div className="mb-3">
            <h5 className="font-medium text-red-600 mb-2">Issues critiques:</h5>
            <ul className="list-disc pl-5 space-y-1">
              {validation.reasons.map((reason, index) => (
                <li key={index} className="text-sm text-red-600">{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {validation.warnings.length > 0 && (
          <div className="mb-3">
            <h5 className="font-medium text-yellow-600 mb-2">Avertissements:</h5>
            <ul className="list-disc pl-5 space-y-1">
              {validation.warnings.map((warning, index) => (
                <li key={index} className="text-sm text-yellow-600">{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {validation.suggestions.length > 0 && (
          <div>
            <h5 className="font-medium text-blue-600 mb-2">Suggestions d'amélioration:</h5>
            <ul className="list-disc pl-5 space-y-1">
              {validation.suggestions.map((suggestion, index) => (
                <li key={index} className="text-sm text-blue-600">{suggestion}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          🚀 Amazon SEO A9/A10 Optimizer
        </h3>
        <p className="text-sm text-gray-600">
          Optimisez vos listings Amazon selon les algorithmes A9 (recherche) et A10 (recommandations).
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
              <p className="text-sm text-green-800">
                {activeMode === 'generate' && 'Listing optimisé généré avec succès!'}
                {activeMode === 'validate' && 'Validation du listing terminée!'}
                {activeMode === 'optimize' && 'Optimisation du listing terminée!'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Onglets de mode */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'generate', label: '🎯 Générer', desc: 'Créer un listing optimisé' },
          { id: 'validate', label: '✅ Valider', desc: 'Vérifier un listing existant' },
          { id: 'optimize', label: '⚡ Optimiser', desc: 'Améliorer un listing' }
        ].map((mode) => (
          <button
            key={mode.id}
            onClick={() => setActiveMode(mode.id)}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeMode === mode.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            title={mode.desc}
          >
            {mode.label}
          </button>
        ))}
      </div>

      {/* Mode Génération */}
      {activeMode === 'generate' && (
        <div className="space-y-6">
          <h4 className="font-medium text-gray-900">📝 Informations produit</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nom du produit *
              </label>
              <input
                type="text"
                value={productData.product_name}
                onChange={(e) => setProductData({...productData, product_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="iPhone 15 Pro Max"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Catégorie *
              </label>
              <select
                value={productData.category}
                onChange={(e) => setProductData({...productData, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Marque
              </label>
              <input
                type="text"
                value={productData.brand}
                onChange={(e) => setProductData({...productData, brand: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Apple"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Modèle
              </label>
              <input
                type="text"
                value={productData.model}
                onChange={(e) => setProductData({...productData, model: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="iPhone 15 Pro Max"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Taille
              </label>
              <input
                type="text"
                value={productData.size}
                onChange={(e) => setProductData({...productData, size: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="6.7 pouces"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Couleur
              </label>
              <input
                type="text"
                value={productData.color}
                onChange={(e) => setProductData({...productData, color: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Titanium Naturel"
              />
            </div>
          </div>

          {/* Caractéristiques */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Caractéristiques principales
              </label>
              <button
                type="button"
                onClick={() => addArrayField(productData.features, (features) => setProductData({...productData, features}))}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + Ajouter
              </button>
            </div>
            {productData.features.map((feature, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={feature}
                  onChange={(e) => handleArrayFieldChange(
                    productData.features,
                    (features) => setProductData({...productData, features}),
                    index,
                    e.target.value
                  )}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Puce A17 Pro"
                />
                {productData.features.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeArrayField(
                      productData.features,
                      (features) => setProductData({...productData, features}),
                      index
                    )}
                    className="px-2 py-2 text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Bénéfices */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Bénéfices clients
              </label>
              <button
                type="button"
                onClick={() => addArrayField(productData.benefits, (benefits) => setProductData({...productData, benefits}))}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + Ajouter
              </button>
            </div>
            {productData.benefits.map((benefit, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={benefit}
                  onChange={(e) => handleArrayFieldChange(
                    productData.benefits,
                    (benefits) => setProductData({...productData, benefits}),
                    index,
                    e.target.value
                  )}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Photos de qualité professionnelle"
                />
                {productData.benefits.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeArrayField(
                      productData.benefits,
                      (benefits) => setProductData({...productData, benefits}),
                      index
                    )}
                    className="px-2 py-2 text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={generateOptimizedListing}
            disabled={loading || !productData.product_name}
            className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Génération en cours...' : '🎯 Générer le listing SEO optimisé'}
          </button>
        </div>
      )}

      {/* Mode Validation */}
      {activeMode === 'validate' && (
        <div className="space-y-6">
          <h4 className="font-medium text-gray-900">✅ Valider un listing existant</h4>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Titre Amazon *
            </label>
            <input
              type="text"
              value={listingData.title}
              onChange={(e) => setListingData({...listingData, title: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Samsung Galaxy S24 Ultra Smartphone 5G 256GB Titanium Gray"
            />
            <CharacterCounter text={listingData.title} maxLength={amazonRules.title.maxLength} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bullet Points * (5 requis)
            </label>
            {listingData.bullets.map((bullet, index) => (
              <div key={index} className="mb-2">
                <input
                  type="text"
                  value={bullet}
                  onChange={(e) => handleArrayFieldChange(
                    listingData.bullets,
                    (bullets) => setListingData({...listingData, bullets}),
                    index,
                    e.target.value
                  )}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`✓ ${['PERFORMANCE', 'QUALITÉ', 'DESIGN', 'UTILISATION', 'GARANTIE'][index]}: Décrivez le bénéfice...`}
                />
                <CharacterCounter text={bullet} maxLength={amazonRules.bullets.maxLength} />
              </div>
            ))}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description produit *
            </label>
            <textarea
              value={listingData.description}
              onChange={(e) => setListingData({...listingData, description: e.target.value})}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Découvrez le [produit], une solution innovante qui..."
            />
            <CharacterCounter 
              text={listingData.description} 
              maxLength={amazonRules.description.maxLength}
            />
            {listingData.description.length < amazonRules.description.minLength && (
              <div className="text-xs text-red-500 mt-1">
                Minimum {amazonRules.description.minLength} caractères requis
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mots-clés backend (search terms)
            </label>
            <textarea
              value={listingData.backend_keywords}
              onChange={(e) => setListingData({...listingData, backend_keywords: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="smartphone 5g android camera photo écran amoled..."
            />
            <CharacterCounter 
              text={listingData.backend_keywords} 
              maxLength={999}
              maxBytes={amazonRules.backend_keywords.maxBytes}
            />
          </div>

          <button
            onClick={validateListing}
            disabled={loading || !listingData.title || !listingData.description}
            className="w-full px-4 py-3 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Validation en cours...' : '✅ Valider selon les règles A9/A10'}
          </button>
        </div>
      )}

      {/* Mode Optimisation */}
      {activeMode === 'optimize' && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800">⚡ Mode Optimisation</h4>
                <div className="text-sm text-blue-700 mt-1">
                  Remplissez les champs avec votre listing actuel. Le système analysera et proposera des optimisations selon les règles Amazon A9/A10.
                </div>
              </div>
            </div>
          </div>

          {/* Utiliser le même formulaire que la validation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Titre Amazon actuel *
            </label>
            <input
              type="text"
              value={listingData.title}
              onChange={(e) => setListingData({...listingData, title: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Titre actuel à optimiser..."
            />
            <CharacterCounter text={listingData.title} maxLength={amazonRules.title.maxLength} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bullet Points actuels
            </label>
            {listingData.bullets.map((bullet, index) => (
              <div key={index} className="mb-2">
                <input
                  type="text"
                  value={bullet}
                  onChange={(e) => handleArrayFieldChange(
                    listingData.bullets,
                    (bullets) => setListingData({...listingData, bullets}),
                    index,
                    e.target.value
                  )}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`Bullet point ${index + 1}...`}
                />
                <CharacterCounter text={bullet} maxLength={amazonRules.bullets.maxLength} />
              </div>
            ))}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description actuelle *
            </label>
            <textarea
              value={listingData.description}
              onChange={(e) => setListingData({...listingData, description: e.target.value})}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Description actuelle à optimiser..."
            />
            <CharacterCounter 
              text={listingData.description} 
              maxLength={amazonRules.description.maxLength}
            />
          </div>

          <button
            onClick={optimizeListing}
            disabled={loading || !listingData.title || !listingData.description}
            className="w-full px-4 py-3 bg-purple-600 text-white font-medium rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Optimisation en cours...' : '⚡ Optimiser le listing'}
          </button>
        </div>
      )}

      {/* Résultats de génération */}
      {generatedListing && (
        <div className="mt-6 p-4 border border-green-200 rounded-lg bg-green-50">
          <h4 className="font-medium text-green-800 mb-3">🎯 Listing optimisé généré</h4>
          
          <div className="space-y-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Titre:</span>
              <div className="mt-1 p-2 bg-white rounded border">{generatedListing.listing.title}</div>
            </div>
            
            <div>
              <span className="font-medium text-gray-700">Bullet Points:</span>
              <div className="mt-1 space-y-1">
                {generatedListing.listing.bullets.map((bullet, index) => (
                  <div key={index} className="p-2 bg-white rounded border text-sm">
                    {bullet}
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <span className="font-medium text-gray-700">Mots-clés backend:</span>
              <div className="mt-1 p-2 bg-white rounded border text-sm">{generatedListing.listing.backend_keywords}</div>
            </div>
          </div>

          {generatedListing.validation && (
            <ValidationFeedback validation={generatedListing.validation} />
          )}
        </div>
      )}

      {/* Résultats de validation */}
      {validationResult && (
        <ValidationFeedback validation={validationResult.validation} />
      )}

      {/* Résultats d'optimisation */}
      {optimizationResult && (
        <div className="mt-6 p-4 border border-purple-200 rounded-lg bg-purple-50">
          <h4 className="font-medium text-purple-800 mb-3">⚡ Résultats d'optimisation</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="bg-white p-3 rounded border">
              <h5 className="font-medium text-gray-700 mb-2">📊 Scores</h5>
              <div className="text-sm space-y-1">
                <div>Score original: {optimizationResult.original.validation.score}/100</div>
                <div className="text-green-600 font-medium">
                  Score optimisé: {optimizationResult.optimized.validation.score}/100
                  {optimizationResult.recommendations.score_improvement > 0 && (
                    <span className="ml-2 text-xs bg-green-100 px-2 py-1 rounded">
                      +{optimizationResult.recommendations.score_improvement.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="bg-white p-3 rounded border">
              <h5 className="font-medium text-gray-700 mb-2">💡 Recommandation</h5>
              <div className="text-sm">
                {optimizationResult.recommendations.should_update ? (
                  <div className="text-green-600 font-medium">✅ Mise à jour recommandée</div>
                ) : (
                  <div className="text-gray-600">ℹ️ Listing déjà optimal</div>
                )}
              </div>
            </div>
          </div>

          {optimizationResult.optimized.validation && (
            <ValidationFeedback validation={optimizationResult.optimized.validation} />
          )}
        </div>
      )}

      {/* Informations règles A9/A10 */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-800 mb-1">Règles Amazon A9/A10</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <p>• <strong>Titre:</strong> Max 200 caractères, format {`{Marque} {Modèle} {Caractéristique} {Taille} {Couleur}`}</p>
              <p>• <strong>Bullets:</strong> 5 bullets max 255 caractères chacun, focalisés sur les bénéfices</p>
              <p>• <strong>Description:</strong> 100-2000 caractères, texte riche et structuré</p>
              <p>• <strong>Search Terms:</strong> Max 250 bytes, mots-clés FR/EN sans marques concurrentes</p>
              <p>• <strong>Images:</strong> Min 1000x1000px, fond blanc pour l'image principale</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmazonSEOOptimizer;