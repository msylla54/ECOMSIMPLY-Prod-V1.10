# 📋 EXTRACTION SEO AUTOMATIQUE - PARTIE 3: COMPOSANTS FRONTEND

## 🎯 INTERFACE UTILISATEUR POUR LA GÉNÉRATION AUTOMATIQUE

### 1. Composant Principal de Génération (`/app/frontend/src/App.js` - Extraits)

```javascript
// ================================================================================
// COMPOSANT GÉNÉRATION DE FICHE PRODUIT AVEC SEO AUTOMATIQUE
// ================================================================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const ProductSheetGenerator = ({ user, onSheetGenerated }) => {
  const [formData, setFormData] = useState({
    product_name: '',
    product_description: '',
    generate_image: true,
    number_of_images: 1,
    language: 'fr',
    category: '',
    use_case: '',
    image_style: 'studio'
  });
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    setProgress(0);

    try {
      console.log('🚀 Démarrage génération fiche produit avec SEO automatique...');
      
      // Simulation du progrès
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 15;
        });
      }, 500);
      
      const response = await axios.post(`${API}/api/generate-sheet`, formData, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      clearInterval(progressInterval);
      setProgress(100);

      console.log('✅ Fiche générée avec succès:', response.data);
      
      // Validation des métadonnées SEO
      const metadata = {
        model_used: response.data.model_used,
        generation_method: response.data.generation_method,
        seo_tags_count: response.data.seo_tags_count,
        seo_diversity_score: response.data.seo_diversity_score,
        seo_target_reached: response.data.seo_target_reached,
        generation_time: response.data.generation_time
      };
      
      console.log('📊 Métadonnées SEO automatique:', metadata);
      
      setResult(response.data);
      if (onSheetGenerated) onSheetGenerated(response.data);
      
    } catch (error) {
      console.error('❌ Erreur génération:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la génération');
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🚀 Générateur de Fiches Produit avec SEO Automatique
        </h2>
        <p className="text-gray-600">
          Intelligence artificielle avancée pour créer des fiches optimisées avec 20 tags SEO uniques
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Nom du produit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nom du produit *
            <span className="text-xs text-gray-500 ml-2">(5-200 caractères)</span>
          </label>
          <input
            type="text"
            value={formData.product_name}
            onChange={(e) => setFormData({...formData, product_name: e.target.value})}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            placeholder="iPhone 15 Pro, MacBook Air M3, Nike Air Max..."
            required
            minLength={5}
            maxLength={200}
          />
        </div>

        {/* Description du produit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description du produit *
            <span className="text-xs text-gray-500 ml-2">(10-2000 caractères)</span>
          </label>
          <textarea
            value={formData.product_description}
            onChange={(e) => setFormData({...formData, product_description: e.target.value})}
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            placeholder="Décrivez les caractéristiques principales, spécifications techniques, avantages..."
            required
            minLength={10}
            maxLength={2000}
          />
          <div className="text-xs text-gray-500 mt-1">
            {formData.product_description.length}/2000 caractères
          </div>
        </div>

        {/* Options avancées SEO */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">🎯 Options SEO Avancées</h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            {/* Catégorie pour SEO */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Catégorie (optimise les tendances SEO)
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Sélectionner une catégorie</option>
                <option value="électronique">📱 Électronique</option>
                <option value="smartphone">📱 Smartphone</option>
                <option value="ordinateur">💻 Ordinateur</option>
                <option value="mode">👕 Mode</option>
                <option value="beauté">💄 Beauté</option>
                <option value="maison">🏠 Maison</option>
                <option value="sport">⚽ Sport</option>
                <option value="auto">🚗 Automobile</option>
              </select>
            </div>

            {/* Cas d'usage */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cas d'usage spécifique
              </label>
              <input
                type="text"
                value={formData.use_case}
                onChange={(e) => setFormData({...formData, use_case: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="photographie pro, gaming, travail..."
                maxLength={300}
              />
            </div>
          </div>

          {/* Langue */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Langue de génération
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({...formData, language: e.target.value})}
              className="w-40 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="fr">🇫🇷 Français</option>
              <option value="en">🇬🇧 English</option>
              <option value="de">🇩🇪 Deutsch</option>
              <option value="es">🇪🇸 Español</option>
              <option value="pt">🇵🇹 Português</option>
            </select>
          </div>
        </div>

        {/* Options images */}
        <div className="bg-green-50 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-3">📸 Génération d'Images IA</h3>
          
          <div className="flex items-center mb-4">
            <input
              type="checkbox"
              id="generate_image"
              checked={formData.generate_image}
              onChange={(e) => setFormData({...formData, generate_image: e.target.checked})}
              className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <label htmlFor="generate_image" className="ml-2 text-sm font-medium text-gray-700">
              Générer des images avec IA (FAL.ai Flux Pro) - Haute qualité
            </label>
          </div>

          {formData.generate_image && (
            <div className="grid md:grid-cols-2 gap-4">
              {/* Nombre d'images */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre d'images
                </label>
                <select
                  value={formData.number_of_images}
                  onChange={(e) => setFormData({...formData, number_of_images: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value={1}>1 image</option>
                  <option value={2}>2 images</option>
                  <option value={3}>3 images</option>
                  <option value={4}>4 images</option>
                  <option value={5}>5 images</option>
                </select>
              </div>

              {/* Style d'image */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Style d'image
                </label>
                <select
                  value={formData.image_style}
                  onChange={(e) => setFormData({...formData, image_style: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="studio">📷 Studio (fond blanc professionnel)</option>
                  <option value="lifestyle">🏠 Lifestyle (contexte réel)</option>
                  <option value="detailed">🔍 Détaillé (macro haute définition)</option>
                  <option value="technical">⚙️ Technique (spécifications)</option>
                  <option value="emotional">❤️ Émotionnel (aspirationnel)</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Informations plan utilisateur */}
        {user && (
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-purple-900">
                  🎯 Plan {user.subscription_plan?.toUpperCase() || 'GRATUIT'}
                </h3>
                <p className="text-sm text-purple-700">
                  {user.subscription_plan === 'premium' ? 'Modèle GPT-4o + 20 tags SEO' :
                   user.subscription_plan === 'pro' ? 'Modèle GPT-4 Turbo + 20 tags SEO' :
                   'Modèle GPT-4 Turbo + 20 tags SEO'}
                </p>
              </div>
              <div className="text-2xl">
                {user.subscription_plan === 'premium' ? '🏆' :
                 user.subscription_plan === 'pro' ? '⚡' : '📦'}
              </div>
            </div>
          </div>
        )}

        {/* Barre de progression */}
        {loading && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Génération en cours...</span>
              <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-2">
              {progress < 30 ? '🔄 Scraping des données SEO...' :
               progress < 60 ? '🤖 Génération du contenu IA...' :
               progress < 90 ? '📸 Création des images...' :
               '✅ Finalisation...'}
            </div>
          </div>
        )}

        {/* Bouton de génération */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-4 px-6 rounded-lg text-white font-medium text-lg transition-all duration-200 ${
            loading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transform hover:scale-105 shadow-lg hover:shadow-xl'
          }`}
        >
          {loading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
              Génération en cours...
            </div>
          ) : (
            '🚀 Générer la Fiche Produit avec SEO Automatique'
          )}
        </button>
      </form>

      {/* Affichage des erreurs */}
      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="text-red-600 text-xl mr-3">❌</div>
            <div>
              <h4 className="text-red-800 font-semibold">Erreur de génération</h4>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Affichage des résultats */}
      {result && (
        <ProductSheetDisplay result={result} />
      )}
    </div>
  );
};

// ================================================================================
// COMPOSANT D'AFFICHAGE DES RÉSULTATS AVEC MÉTADONNÉES SEO
// ================================================================================

const ProductSheetDisplay = ({ result }) => {
  const [activeTab, setActiveTab] = useState('content');
  const [exportFormat, setExportFormat] = useState('json');

  const downloadSheet = (format) => {
    let content, filename, mimeType;
    
    switch (format) {
      case 'json':
        content = JSON.stringify(result, null, 2);
        filename = `fiche-${result.generation_id?.substring(0, 8)}.json`;
        mimeType = 'application/json';
        break;
      case 'csv':
        content = convertToCSV(result);
        filename = `fiche-${result.generation_id?.substring(0, 8)}.csv`;
        mimeType = 'text/csv';
        break;
      case 'txt':
        content = convertToText(result);
        filename = `fiche-${result.generation_id?.substring(0, 8)}.txt`;
        mimeType = 'text/plain';
        break;
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mt-8 bg-white border border-gray-200 rounded-xl shadow-lg">
      {/* Header avec actions */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold">
              ✅ Fiche Produit Générée avec SEO Automatique
            </h3>
            <p className="text-purple-100 mt-1">
              {result.seo_tags_count}/20 tags SEO • Score diversité: {result.seo_diversity_score} • 
              Temps: {result.generation_time?.toFixed(2)}s
            </p>
          </div>
          <div className="flex space-x-2">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              className="px-3 py-1 rounded text-gray-800 text-sm"
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="txt">TXT</option>
            </select>
            <button
              onClick={() => downloadSheet(exportFormat)}
              className="bg-white text-purple-600 px-4 py-1 rounded text-sm font-medium hover:bg-gray-100"
            >
              📥 Télécharger
            </button>
          </div>
        </div>
      </div>

      {/* Onglets de navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { id: 'content', label: '📝 Contenu', icon: '📝' },
            { id: 'seo', label: '🏷️ SEO Tags', icon: '🏷️' },
            { id: 'images', label: '📸 Images', icon: '📸' },
            { id: 'metadata', label: '📊 Métadonnées', icon: '📊' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Contenu des onglets */}
      <div className="p-6">
        {activeTab === 'content' && (
          <ContentTab result={result} />
        )}
        {activeTab === 'seo' && (
          <SEOTab result={result} />
        )}
        {activeTab === 'images' && (
          <ImagesTab result={result} />
        )}
        {activeTab === 'metadata' && (
          <MetadataTab result={result} />
        )}
      </div>
    </div>
  );
};

// ================================================================================
// ONGLETS DE CONTENU SPÉCIALISÉS
// ================================================================================

const ContentTab = ({ result }) => (
  <div className="space-y-6">
    {/* Titre SEO optimisé */}
    <div>
      <h5 className="font-semibold text-gray-900 mb-3 text-lg">📝 Titre SEO Optimisé</h5>
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <p className="text-lg font-medium text-purple-800">{result.generated_title}</p>
        <div className="text-sm text-purple-600 mt-2">
          {result.generated_title.length} caractères (optimal: 50-70)
        </div>
      </div>
    </div>

    {/* Description marketing */}
    <div>
      <h5 className="font-semibold text-gray-900 mb-3 text-lg">📄 Description Marketing</h5>
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
          {result.marketing_description}
        </p>
        <div className="text-sm text-gray-500 mt-3">
          {result.marketing_description.split(' ').length} mots
        </div>
      </div>
    </div>

    {/* Caractéristiques clés */}
    <div>
      <h5 className="font-semibold text-gray-900 mb-3 text-lg">⭐ Caractéristiques Clés</h5>
      <div className="grid md:grid-cols-2 gap-3">
        {result.key_features.map((feature, index) => (
          <div key={index} className="flex items-start bg-green-50 border border-green-200 rounded-lg p-3">
            <span className="text-green-600 mr-3 mt-0.5">✅</span>
            <span className="text-gray-800 font-medium">{feature}</span>
          </div>
        ))}
      </div>
    </div>

    {/* Autres sections */}
    <div className="grid md:grid-cols-2 gap-6">
      {/* Audience cible */}
      <div>
        <h5 className="font-semibold text-gray-900 mb-3">🎯 Audience Cible</h5>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-gray-700">{result.target_audience}</p>
        </div>
      </div>

      {/* Call-to-action */}
      <div>
        <h5 className="font-semibold text-gray-900 mb-3">📢 Call-to-Action</h5>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-orange-800 font-medium">{result.call_to_action}</p>
        </div>
      </div>
    </div>

    {/* Suggestions prix */}
    <div>
      <h5 className="font-semibold text-gray-900 mb-3 text-lg">💰 Analyse Prix Concurrentielle</h5>
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <p className="text-gray-700">{result.price_suggestions}</p>
      </div>
    </div>
  </div>
);

const SEOTab = ({ result }) => (
  <div className="space-y-6">
    {/* Résumé SEO */}
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-semibold text-blue-900 mb-3">📊 Résumé Performance SEO</h4>
      <div className="grid md:grid-cols-4 gap-4 text-sm">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{result.seo_tags_count}</div>
          <div className="text-blue-700">Tags générés</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {result.seo_diversity_score ? (result.seo_diversity_score * 100).toFixed(0) + '%' : 'N/A'}
          </div>
          <div className="text-green-700">Diversité</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {result.seo_target_reached ? '✅' : '❌'}
          </div>
          <div className="text-purple-700">Objectif 20 tags</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {result.seo_tags_source || 'Mixed'}
          </div>
          <div className="text-orange-700">Source</div>
        </div>
      </div>
    </div>

    {/* Tags SEO avec couleurs par source */}
    <div>
      <h5 className="font-semibold text-gray-900 mb-3 text-lg">
        🏷️ Tags SEO Automatiques ({result.seo_tags?.length}/20)
      </h5>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {result.seo_tags?.map((tag, index) => (
          <span 
            key={index} 
            className={`px-3 py-2 rounded-full text-sm font-medium text-center ${
              index < (result.seo_source_breakdown?.trending || 0) 
                ? 'bg-red-100 text-red-800' // Tendances
                : index < (result.seo_source_breakdown?.trending || 0) + (result.seo_source_breakdown?.ai || 0)
                ? 'bg-blue-100 text-blue-800' // IA
                : 'bg-gray-100 text-gray-800' // Statique
            }`}
            title={
              index < (result.seo_source_breakdown?.trending || 0) 
                ? 'Tag tendance' 
                : index < (result.seo_source_breakdown?.trending || 0) + (result.seo_source_breakdown?.ai || 0)
                ? 'Tag généré par IA'
                : 'Tag statique'
            }
          >
            {tag}
          </span>
        ))}
      </div>
      
      {/* Légende */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-100 rounded-full mr-2"></div>
          <span>Tendances ({result.seo_source_breakdown?.trending || 0})</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-100 rounded-full mr-2"></div>
          <span>IA ({result.seo_source_breakdown?.ai || 0})</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-gray-100 rounded-full mr-2"></div>
          <span>Statique ({result.seo_source_breakdown?.static || 0})</span>
        </div>
      </div>
    </div>

    {/* Analyse de diversité */}
    {result.seo_diversity_score && (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h5 className="font-semibold text-green-900 mb-2">🎯 Analyse de Diversité Jaccard</h5>
        <div className="text-sm text-green-700">
          <p>Score de diversité: <strong>{(result.seo_diversity_score * 100).toFixed(1)}%</strong></p>
          <p className="mt-1">
            {result.seo_diversity_score > 0.7 ? 
              '✅ Excellente diversité - Les tags sont bien différenciés' :
              result.seo_diversity_score > 0.5 ?
              '⚠️ Diversité correcte - Quelques tags similaires' :
              '❌ Diversité faible - Beaucoup de tags similaires'
            }
          </p>
        </div>
      </div>
    )}
  </div>
);

const ImagesTab = ({ result }) => (
  <div className="space-y-6">
    {result.generated_images && result.generated_images.length > 0 ? (
      <>
        <div className="flex items-center justify-between">
          <h5 className="font-semibold text-gray-900 text-lg">
            📸 Images Générées ({result.generated_images.length})
          </h5>
          <div className="text-sm text-gray-500">
            Générées avec FAL.ai Flux Pro
          </div>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {result.generated_images.map((image, index) => (
            <div key={index} className="relative group">
              <div className="aspect-w-4 aspect-h-3 rounded-lg overflow-hidden shadow-md">
                <img
                  src={`data:image/png;base64,${image}`}
                  alt={`${result.generated_title} - Image ${index + 1}`}
                  className="w-full h-64 object-cover transition-transform duration-200 group-hover:scale-105"
                />
              </div>
              <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs font-medium">
                #{index + 1}
              </div>
              <div className="absolute bottom-2 left-2 right-2 bg-gradient-to-t from-black to-transparent text-white p-2 rounded-b opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="text-xs truncate">{result.generated_title}</p>
              </div>
              
              {/* Actions sur l'image */}
              <div className="mt-3 flex justify-center space-x-2">
                <button
                  onClick={() => downloadImage(image, `${result.generated_title}-${index + 1}`)}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
                >
                  📥 Télécharger
                </button>
                <button
                  onClick={() => copyImageToClipboard(image)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                >
                  📋 Copier
                </button>
              </div>
            </div>
          ))}
        </div>
        
        {/* Informations techniques */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h6 className="font-medium text-gray-900 mb-2">ℹ️ Informations Techniques</h6>
          <div className="text-sm text-gray-600 space-y-1">
            <p>• Format: PNG Base64</p>
            <p>• Générateur: FAL.ai Flux Pro</p>
            <p>• Qualité: Haute résolution e-commerce</p>
            <p>• Optimisé pour: Boutiques en ligne</p>
          </div>
        </div>
      </>
    ) : (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📷</div>
        <h5 className="text-lg font-medium text-gray-900 mb-2">Aucune image générée</h5>
        <p className="text-gray-500">
          Les images n'ont pas été demandées ou ont échoué lors de la génération.
        </p>
      </div>
    )}
  </div>
);

const MetadataTab = ({ result }) => (
  <div className="space-y-6">
    {/* Métadonnées IA */}
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <h5 className="font-semibold text-purple-900 mb-3">🤖 Routing Intelligence Artificielle</h5>
      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-medium text-gray-700">Modèle utilisé:</span>
          <span className="ml-2 text-purple-600 font-mono">{result.model_used || 'N/A'}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Méthode:</span>
          <span className="ml-2 text-purple-600">{result.generation_method || 'N/A'}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Niveau fallback:</span>
          <span className="ml-2 text-purple-600">{result.fallback_level || 'N/A'}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Cost Guard:</span>
          <span className={`ml-2 ${result.cost_guard_triggered ? 'text-red-600' : 'text-green-600'}`}>
            {result.cost_guard_triggered ? '🚨 Activé' : '✅ Inactif'}
          </span>
        </div>
        <div className="md:col-span-2">
          <span className="font-medium text-gray-700">Route complète:</span>
          <span className="ml-2 text-purple-600 font-mono text-xs">{result.model_route || 'N/A'}</span>
        </div>
      </div>
    </div>

    {/* Métadonnées SEO détaillées */}
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h5 className="font-semibold text-blue-900 mb-3">🏷️ Métadonnées SEO Avancées</h5>
      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-medium text-gray-700">Tags générés:</span>
          <span className="ml-2 text-blue-600">{result.seo_tags_count || 0}/20</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Validation:</span>
          <span className={`ml-2 ${result.seo_validation_passed ? 'text-green-600' : 'text-red-600'}`}>
            {result.seo_validation_passed ? '✅ Passée' : '❌ Échouée'}
          </span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Cible atteinte:</span>
          <span className={`ml-2 ${result.seo_target_reached ? 'text-green-600' : 'text-orange-600'}`}>
            {result.seo_target_reached ? '✅ Oui' : '⚠️ Non'}
          </span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Score Jaccard:</span>
          <span className="ml-2 text-blue-600">
            {result.seo_diversity_score ? (result.seo_diversity_score * 100).toFixed(1) + '%' : 'N/A'}
          </span>
        </div>
      </div>
    </div>

    {/* Métadonnées système */}
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <h5 className="font-semibold text-gray-900 mb-3">⚙️ Informations Système</h5>
      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-medium text-gray-700">Temps génération:</span>
          <span className="ml-2 text-gray-600">{result.generation_time?.toFixed(2)}s</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">ID génération:</span>
          <span className="ml-2 text-gray-600 font-mono text-xs">
            {result.generation_id?.substring(0, 8) || 'N/A'}...
          </span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Catégorie:</span>
          <span className="ml-2 text-gray-600">{result.category || 'Non spécifiée'}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Images générées:</span>
          <span className="ml-2 text-gray-600">{result.generated_images?.length || 0}</span>
        </div>
      </div>
    </div>

    {/* Breakdown des sources SEO */}
    {result.seo_source_breakdown && (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h5 className="font-semibold text-yellow-900 mb-3">📈 Répartition des Sources SEO</h5>
        <div className="space-y-2">
          {Object.entries(result.seo_source_breakdown).map(([source, count]) => (
            <div key={source} className="flex items-center justify-between">
              <span className="font-medium text-gray-700 capitalize">
                {source === 'trending' ? '📈 Tendances' :
                 source === 'ai' ? '🤖 Intelligence Artificielle' :
                 '📚 Statique'}:
              </span>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                  <div 
                    className={`h-2 rounded-full ${
                      source === 'trending' ? 'bg-red-500' :
                      source === 'ai' ? 'bg-blue-500' : 'bg-gray-500'
                    }`}
                    style={{ width: `${(count / result.seo_tags_count) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 w-8">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// ================================================================================
// FONCTIONS UTILITAIRES
// ================================================================================

const downloadImage = (base64Data, filename) => {
  const link = document.createElement('a');
  link.href = `data:image/png;base64,${base64Data}`;
  link.download = `${filename}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const copyImageToClipboard = async (base64Data) => {
  try {
    const response = await fetch(`data:image/png;base64,${base64Data}`);
    const blob = await response.blob();
    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': blob })
    ]);
    alert('Image copiée dans le presse-papiers !');
  } catch (err) {
    console.error('Erreur copie image:', err);
    alert('Erreur lors de la copie de l\'image');
  }
};

const convertToCSV = (result) => {
  const headers = ['Champ', 'Valeur'];
  const rows = [
    ['Titre', result.generated_title],
    ['Description', result.marketing_description],
    ['Caractéristiques', result.key_features.join('; ')],
    ['Tags SEO', result.seo_tags.join('; ')],
    ['Prix', result.price_suggestions],
    ['Audience', result.target_audience],
    ['Call-to-Action', result.call_to_action],
    ['Temps génération', `${result.generation_time}s`],
    ['Modèle IA', result.model_used],
    ['Score SEO', result.seo_diversity_score]
  ];
  
  return [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n');
};

const convertToText = (result) => {
  return `
FICHE PRODUIT GÉNÉRÉE - ${result.generated_title}
===============================================

TITRE SEO: ${result.generated_title}

DESCRIPTION:
${result.marketing_description}

CARACTÉRISTIQUES:
${result.key_features.map(f => `• ${f}`).join('\n')}

TAGS SEO (${result.seo_tags_count}/20):
${result.seo_tags.join(', ')}

AUDIENCE CIBLE:
${result.target_audience}

CALL-TO-ACTION:
${result.call_to_action}

PRIX:
${result.price_suggestions}

MÉTADONNÉES:
• Modèle IA: ${result.model_used}
• Temps génération: ${result.generation_time}s
• Score diversité SEO: ${result.seo_diversity_score}
• ID: ${result.generation_id}
`;
};

export default ProductSheetGenerator;
```

---

## 🎯 AVANTAGES DE CETTE INTERFACE

### 1. **Expérience Utilisateur Optimisée**
- Interface intuitive avec onglets
- Progression en temps réel
- Validation côté client
- Messages d'erreur clairs

### 2. **Visualisation des Métadonnées SEO**
- Score de diversité Jaccard
- Répartition des sources de tags
- Performance du routing IA
- Métriques détaillées

### 3. **Fonctionnalités Avancées**
- Export multi-format (JSON, CSV, TXT)
- Téléchargement d'images
- Copie dans le presse-papiers
- Prévisualisation en temps réel

### 4. **Responsive Design**
- Adapté mobile/tablet/desktop
- Grille flexible pour les tags
- Images responsive
- Navigation tactile

### 5. **Intégration Complète**
- Authentification utilisateur
- Gestion des plans d'abonnement
- Logging des actions
- Cache des résultats

Cette interface offre une expérience complète pour la génération automatique de fiches produit avec SEO optimisé, permettant aux utilisateurs de visualiser et comprendre tous les aspects du processus de génération.