// Amazon Publisher Component - Interface de publication Amazon
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AmazonPublisher = () => {
  const [product, setProduct] = useState({
    product_name: '',
    brand: '',
    description: '',
    key_features: [''],
    benefits: [''],
    category: 'electronique',
    price: '',
    currency: 'EUR',
    images: []
  });
  
  const [selectedMarketplace, setSelectedMarketplace] = useState('A13V1IB3VIYZZH');
  const [seoPreview, setSeoPreview] = useState(null);
  const [publishing, setPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Marketplaces disponibles
  const marketplaces = [
    { id: 'A13V1IB3VIYZZH', name: 'Amazon France', flag: '🇫🇷' },
    { id: 'A1PA6795UKMFR9', name: 'Amazon Allemagne', flag: '🇩🇪' },
    { id: 'ATVPDKIKX0DER', name: 'Amazon États-Unis', flag: '🇺🇸' },
    { id: 'A1F83G8C2ARO7P', name: 'Amazon Royaume-Uni', flag: '🇬🇧' }
  ];

  // Catégories produits
  const categories = [
    { value: 'electronique', label: '📱 Électronique' },
    { value: 'mode', label: '👕 Mode & Vêtements' },
    { value: 'maison', label: '🏠 Maison & Jardin' },
    { value: 'sport', label: '⚽ Sports & Loisirs' },
    { value: 'auto', label: '🚗 Auto & Moto' }
  ];

  // API helpers
  const getApiBaseUrl = () => process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // Optimisation SEO en temps réel
  const optimizeSEO = async () => {
    if (!product.product_name || !product.description) {
      alert('Veuillez renseigner au minimum le nom et la description du produit');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${getApiBaseUrl()}/api/amazon/publisher/optimize-seo`,
        {
          product_data: product,
          marketplace_id: selectedMarketplace
        },
        { headers: getAuthHeaders() }
      );

      setSeoPreview(response.data);
    } catch (error) {
      console.error('Erreur optimisation SEO:', error);
      alert('Erreur lors de l\'optimisation SEO: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Publication vers Amazon
  const publishToAmazon = async () => {
    if (!seoPreview) {
      alert('Veuillez d\'abord optimiser le SEO');
      return;
    }

    setPublishing(true);
    try {
      const publishData = {
        product_data: {
          ...product,
          optimized_title: seoPreview.optimized_title,
          optimized_bullets: seoPreview.bullet_points,
          optimized_description: seoPreview.description,
          backend_keywords: seoPreview.backend_keywords
        },
        marketplace_id: selectedMarketplace,
        options: {
          include_images: true
        }
      };

      const response = await axios.post(
        `${getApiBaseUrl()}/api/amazon/publisher/publish`,
        publishData,
        { headers: getAuthHeaders() }
      );

      setPublishResult(response.data);
      
      if (response.data.success) {
        alert('✅ Produit publié avec succès sur Amazon !');
      } else {
        alert('❌ Échec de publication: ' + response.data.errors.join(', '));
      }
    } catch (error) {
      console.error('Erreur publication:', error);
      alert('Erreur lors de la publication: ' + (error.response?.data?.detail || error.message));
    } finally {
      setPublishing(false);
    }
  };

  // Gestion des champs dynamiques
  const addFeature = () => {
    setProduct(prev => ({
      ...prev,
      key_features: [...prev.key_features, '']
    }));
  };

  const updateFeature = (index, value) => {
    setProduct(prev => ({
      ...prev,
      key_features: prev.key_features.map((feat, i) => i === index ? value : feat)
    }));
  };

  const removeFeature = (index) => {
    setProduct(prev => ({
      ...prev,
      key_features: prev.key_features.filter((_, i) => i !== index)
    }));
  };

  const addBenefit = () => {
    setProduct(prev => ({
      ...prev,
      benefits: [...prev.benefits, '']
    }));
  };

  const updateBenefit = (index, value) => {
    setProduct(prev => ({
      ...prev,
      benefits: prev.benefits.map((benefit, i) => i === index ? value : benefit)
    }));
  };

  const removeBenefit = (index) => {
    setProduct(prev => ({
      ...prev,
      benefits: prev.benefits.filter((_, i) => i !== index)
    }));
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          📤 Publication Amazon SP-API
        </h1>
        <p style={{ color: '#6b7280' }}>
          Optimisez et publiez vos produits sur Amazon avec le SEO A9/A10
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Formulaire produit */}
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            📋 Informations Produit
          </h2>

          {/* Informations de base */}
          <div style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb', marginBottom: '1rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                Nom du produit *
              </label>
              <input
                type="text"
                value={product.product_name}
                onChange={(e) => setProduct(prev => ({ ...prev, product_name: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem'
                }}
                placeholder="Ex: Casque Audio Bluetooth Premium"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                  Marque *
                </label>
                <input
                  type="text"
                  value={product.brand}
                  onChange={(e) => setProduct(prev => ({ ...prev, brand: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                  placeholder="Ex: AudioTech"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                  Catégorie
                </label>
                <select
                  value={product.category}
                  onChange={(e) => setProduct(prev => ({ ...prev, category: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                Description *
              </label>
              <textarea
                value={product.description}
                onChange={(e) => setProduct(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem'
                }}
                placeholder="Description détaillée du produit..."
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                  Prix (€)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={product.price}
                  onChange={(e) => setProduct(prev => ({ ...prev, price: parseFloat(e.target.value) || '' }))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                  placeholder="79.99"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                  Marketplace
                </label>
                <select
                  value={selectedMarketplace}
                  onChange={(e) => setSelectedMarketplace(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                >
                  {marketplaces.map(market => (
                    <option key={market.id} value={market.id}>
                      {market.flag} {market.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Caractéristiques */}
          <div style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>Caractéristiques</h3>
              <button
                onClick={addFeature}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem'
                }}
              >
                + Ajouter
              </button>
            </div>

            {product.key_features.map((feature, index) => (
              <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  value={feature}
                  onChange={(e) => updateFeature(index, e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                  placeholder="Ex: Bluetooth 5.0"
                />
                {product.key_features.length > 1 && (
                  <button
                    onClick={() => removeFeature(index)}
                    style={{
                      padding: '0.5rem',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.375rem'
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Avantages */}
          <div style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>Avantages</h3>
              <button
                onClick={addBenefit}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem'
                }}
              >
                + Ajouter
              </button>
            </div>

            {product.benefits.map((benefit, index) => (
              <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  value={benefit}
                  onChange={(e) => updateBenefit(index, e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem'
                  }}
                  placeholder="Ex: Qualité audio premium"
                />
                {product.benefits.length > 1 && (
                  <button
                    onClick={() => removeBenefit(index)}
                    style={{
                      padding: '0.5rem',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.375rem'
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Bouton optimisation */}
          <button
            onClick={optimizeSEO}
            disabled={loading || !product.product_name || !product.description}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: loading ? '#9ca3af' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '⏳ Optimisation...' : '🎯 Optimiser pour Amazon'}
          </button>
        </div>

        {/* Aperçu SEO */}
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            🎯 Aperçu SEO Amazon
          </h2>

          {seoPreview ? (
            <div style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb' }}>
              {/* Score SEO */}
              <div style={{ 
                marginBottom: '1.5rem', 
                padding: '1rem', 
                backgroundColor: seoPreview.seo_score >= 0.7 ? '#dcfce7' : '#fef2f2',
                borderRadius: '0.5rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '600' }}>Score SEO</span>
                  <span style={{ 
                    fontSize: '1.5rem', 
                    fontWeight: '700',
                    color: seoPreview.seo_score >= 0.7 ? '#16a34a' : '#dc2626'
                  }}>
                    {Math.round(seoPreview.seo_score * 100)}%
                  </span>
                </div>
                {seoPreview.seo_score < 0.7 && (
                  <p style={{ fontSize: '0.875rem', color: '#dc2626', marginTop: '0.5rem' }}>
                    Score minimum recommandé: 70%
                  </p>
                )}
              </div>

              {/* Titre optimisé */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                  Titre optimisé ({seoPreview.optimized_title.length}/200 caractères)
                </label>
                <div style={{ 
                  padding: '0.75rem', 
                  backgroundColor: '#f9fafb', 
                  borderRadius: '0.375rem',
                  marginTop: '0.5rem',
                  fontSize: '0.875rem'
                }}>
                  {seoPreview.optimized_title}
                </div>
              </div>

              {/* Bullet points */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                  Points clés (5 requis)
                </label>
                <div style={{ marginTop: '0.5rem' }}>
                  {seoPreview.bullet_points.map((bullet, index) => (
                    <div key={index} style={{ 
                      padding: '0.5rem', 
                      backgroundColor: '#f9fafb', 
                      borderRadius: '0.375rem',
                      marginBottom: '0.5rem',
                      fontSize: '0.875rem'
                    }}>
                      {bullet}
                    </div>
                  ))}
                </div>
              </div>

              {/* Mots-clés backend */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                  Mots-clés backend ({seoPreview.backend_keywords.length} caractères/250)
                </label>
                <div style={{ 
                  padding: '0.75rem', 
                  backgroundColor: '#f9fafb', 
                  borderRadius: '0.375rem',
                  marginTop: '0.5rem',
                  fontSize: '0.875rem'
                }}>
                  {seoPreview.backend_keywords}
                </div>
              </div>

              {/* Recommandations */}
              {seoPreview.recommendations.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                    Recommandations
                  </label>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1rem' }}>
                    {seoPreview.recommendations.map((rec, index) => (
                      <li key={index} style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Bouton publication */}
              <button
                onClick={publishToAmazon}
                disabled={publishing || seoPreview.seo_score < 0.7}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: publishing ? '#9ca3af' : (seoPreview.seo_score >= 0.7 ? '#f59e0b' : '#6b7280'),
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: (publishing || seoPreview.seo_score < 0.7) ? 'not-allowed' : 'pointer'
                }}
              >
                {publishing ? '⏳ Publication...' : '📤 Publier sur Amazon'}
              </button>

              {seoPreview.seo_score < 0.7 && (
                <p style={{ fontSize: '0.875rem', color: '#6b7280', textAlign: 'center', marginTop: '0.5rem' }}>
                  Améliorez le score SEO avant publication
                </p>
              )}
            </div>
          ) : (
            <div style={{ 
              backgroundColor: '#f9fafb', 
              padding: '2rem', 
              borderRadius: '0.5rem', 
              textAlign: 'center',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
              <p style={{ color: '#6b7280' }}>
                Remplissez les informations produit et cliquez sur "Optimiser pour Amazon" pour voir l'aperçu SEO
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Résultat de publication */}
      {publishResult && (
        <div style={{ 
          marginTop: '2rem', 
          padding: '1.5rem', 
          backgroundColor: publishResult.success ? '#dcfce7' : '#fef2f2',
          borderRadius: '0.5rem',
          border: `1px solid ${publishResult.success ? '#16a34a' : '#dc2626'}`
        }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            color: publishResult.success ? '#16a34a' : '#dc2626',
            marginBottom: '1rem'
          }}>
            {publishResult.success ? '✅ Publication réussie' : '❌ Échec de publication'}
          </h3>

          {publishResult.success && publishResult.listing_id && (
            <p style={{ marginBottom: '0.5rem' }}>
              <strong>ID Listing:</strong> {publishResult.listing_id}
            </p>
          )}

          {publishResult.errors && publishResult.errors.length > 0 && (
            <div>
              <strong>Erreurs:</strong>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1rem' }}>
                {publishResult.errors.map((error, index) => (
                  <li key={index} style={{ color: '#dc2626' }}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {publishResult.seo_score && (
            <p style={{ marginTop: '0.5rem' }}>
              <strong>Score SEO final:</strong> {Math.round(publishResult.seo_score * 100)}%
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default AmazonPublisher;