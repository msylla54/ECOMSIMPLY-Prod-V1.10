import React, { useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ProductInputForm = ({ onGenerate, loading, user, token }) => {
  const [formData, setFormData] = useState({
    brand: '',
    product_name: '',
    category: 'électronique',
    features: [''],
    target_keywords: [''],
    size: '',
    color: '',
    price: '',
    description: ''
  });

  const [errors, setErrors] = useState({});

  // Catégories supportées
  const categories = [
    { value: 'électronique', label: '📱 Électronique' },
    { value: 'maison', label: '🏠 Maison & Jardin' },
    { value: 'vêtements', label: '👕 Vêtements' },
    { value: 'sport', label: '⚽ Sport & Loisirs' },
    { value: 'cuisine', label: '🍳 Cuisine' },
    { value: 'beauté', label: '💄 Beauté & Santé' },
    { value: 'livres', label: '📚 Livres' },
    { value: 'jouets', label: '🧸 Jouets & Jeux' },
    { value: 'auto', label: '🚗 Auto & Moto' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleArrayInputChange = (field, index, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const addArrayField = (field) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayField = (field, index) => {
    if (formData[field].length > 1) {
      setFormData(prev => ({
        ...prev,
        [field]: prev[field].filter((_, i) => i !== index)
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.brand.trim()) {
      newErrors.brand = 'La marque est requise';
    }

    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Le nom du produit est requis';
    }

    if (!formData.category) {
      newErrors.category = 'La catégorie est requise';
    }

    // Validation des features (au moins une non vide)
    const validFeatures = formData.features.filter(f => f.trim());
    if (validFeatures.length === 0) {
      newErrors.features = 'Au moins une caractéristique est requise';
    }

    // Validation des keywords (au moins un non vide)
    const validKeywords = formData.target_keywords.filter(k => k.trim());
    if (validKeywords.length === 0) {
      newErrors.target_keywords = 'Au moins un mot-clé est requis';
    }

    // Validation du prix si fourni
    if (formData.price && (isNaN(formData.price) || parseFloat(formData.price) <= 0)) {
      newErrors.price = 'Le prix doit être un nombre positif';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Nettoyer les données avant envoi
    const cleanedData = {
      ...formData,
      features: formData.features.filter(f => f.trim()),
      target_keywords: formData.target_keywords.filter(k => k.trim()),
      price: formData.price ? parseFloat(formData.price) : undefined
    };

    // Supprimer les champs vides optionnels
    Object.keys(cleanedData).forEach(key => {
      if (!cleanedData[key] || (Array.isArray(cleanedData[key]) && cleanedData[key].length === 0)) {
        if (!['brand', 'product_name', 'category', 'features', 'target_keywords'].includes(key)) {
          cleanedData[key] = undefined;
        }
      }
    });

    onGenerate(cleanedData);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">🤖</span>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Générateur de fiche produit Amazon
          </h3>
          <p className="text-sm text-gray-600">
            Remplissez les informations pour générer une fiche optimisée par IA
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Informations de base */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Marque *
            </label>
            <input
              type="text"
              value={formData.brand}
              onChange={(e) => handleInputChange('brand', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.brand ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Ex: Apple, Samsung, Nike..."
              disabled={loading}
            />
            {errors.brand && (
              <p className="text-red-500 text-xs mt-1">{errors.brand}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nom du produit *
            </label>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => handleInputChange('product_name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.product_name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Ex: iPhone 15 Pro Max..."
              disabled={loading}
            />
            {errors.product_name && (
              <p className="text-red-500 text-xs mt-1">{errors.product_name}</p>
            )}
          </div>
        </div>

        {/* Catégorie */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Catégorie *
          </label>
          <select
            value={formData.category}
            onChange={(e) => handleInputChange('category', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.category ? 'border-red-300' : 'border-gray-300'
            }`}
            disabled={loading}
          >
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="text-red-500 text-xs mt-1">{errors.category}</p>
          )}
        </div>

        {/* Caractéristiques */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Caractéristiques principales *
          </label>
          <div className="space-y-2">
            {formData.features.map((feature, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={feature}
                  onChange={(e) => handleArrayInputChange('features', index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={`Caractéristique ${index + 1}...`}
                  disabled={loading}
                />
                {formData.features.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeArrayField('features', index)}
                    className="px-3 py-2 text-red-600 hover:text-red-800 disabled:opacity-50"
                    disabled={loading}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => addArrayField('features')}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
            disabled={loading || formData.features.length >= 10}
          >
            + Ajouter une caractéristique
          </button>
          {errors.features && (
            <p className="text-red-500 text-xs mt-1">{errors.features}</p>
          )}
        </div>

        {/* Mots-clés */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mots-clés cibles *
          </label>
          <div className="space-y-2">
            {formData.target_keywords.map((keyword, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => handleArrayInputChange('target_keywords', index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={`Mot-clé ${index + 1}...`}
                  disabled={loading}
                />
                {formData.target_keywords.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeArrayField('target_keywords', index)}
                    className="px-3 py-2 text-red-600 hover:text-red-800 disabled:opacity-50"
                    disabled={loading}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => addArrayField('target_keywords')}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
            disabled={loading || formData.target_keywords.length >= 15}
          >
            + Ajouter un mot-clé
          </button>
          {errors.target_keywords && (
            <p className="text-red-500 text-xs mt-1">{errors.target_keywords}</p>
          )}
        </div>

        {/* Informations optionnelles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Taille (optionnel)
            </label>
            <input
              type="text"
              value={formData.size}
              onChange={(e) => handleInputChange('size', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: 6.7 pouces, XL, 256GB..."
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Couleur (optionnel)
            </label>
            <input
              type="text"
              value={formData.color}
              onChange={(e) => handleInputChange('color', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Noir, Blanc, Rouge..."
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prix (optionnel)
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.price}
                onChange={(e) => handleInputChange('price', e.target.value)}
                className={`w-full px-3 py-2 pr-8 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.price ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="0.00"
                disabled={loading}
              />
              <span className="absolute right-3 top-2 text-gray-500 text-sm">€</span>
            </div>
            {errors.price && (
              <p className="text-red-500 text-xs mt-1">{errors.price}</p>
            )}
          </div>
        </div>

        {/* Description personnalisée */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description personnalisée (optionnel)
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ajoutez des informations supplémentaires sur votre produit..."
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Cette description sera intégrée dans la fiche générée par l'IA
          </p>
        </div>

        {/* Bouton de génération */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-md transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Génération en cours...
              </>
            ) : (
              <>
                <span>🤖</span>
                Générer la fiche Amazon
              </>
            )}
          </button>
        </div>
      </form>

      {/* Instructions */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-medium text-blue-900 mb-2">💡 Conseils pour une génération optimale</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Utilisez des marques et noms de produits précis</li>
          <li>• Listez les caractéristiques les plus importantes en premier</li>
          <li>• Choisissez des mots-clés que vos clients recherchent</li>
          <li>• Les informations optionnelles améliorent la qualité de génération</li>
        </ul>
      </div>
    </div>
  );
};

export default ProductInputForm;