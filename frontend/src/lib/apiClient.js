/**
 * 🚀 ECOMSIMPLY - Client API Centralisé
 * Gestion centralisée de tous les appels API avec respect strict des ENV Vercel
 */

import axios from 'axios';

// ✅ Configuration ENV avec fallback sécurisé
const getBackendURL = () => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (!backendUrl) {
    console.error('❌ REACT_APP_BACKEND_URL non défini dans les variables d\'environnement');
    console.warn('🔧 Utilisation du fallback de développement local');
    return 'http://localhost:8001';
  }
  
  console.log('✅ Backend URL configuré:', backendUrl);
  return backendUrl;
};

// Construction sécurisée des URLs API
const BACKEND_URL = getBackendURL();
const API_BASE_URL = `${BACKEND_URL}/api`;

// ✅ Instance Axios centralisée avec configuration optimisée
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 secondes
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ✅ Intercepteur de requête pour JWT automatique
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log pour debugging (uniquement en dev)
    if (process.env.NODE_ENV === 'development') {
      console.log(`🌐 API Call: ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Erreur dans la configuration de la requête:', error);
    return Promise.reject(error);
  }
);

// ✅ Intercepteur de réponse pour gestion globale des erreurs
apiClient.interceptors.response.use(
  (response) => {
    // Log pour debugging (uniquement en dev)
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    console.error('❌ Erreur API:', error);
    
    // Gestion automatique des erreurs 401 (non authentifié)
    if (error.response?.status === 401) {
      console.warn('🔐 Token invalide ou expiré - redirection vers login');
      localStorage.removeItem('token');
      localStorage.removeItem('currentUser');
      
      // Déclencher un événement pour que l'AuthContext puisse réagir
      window.dispatchEvent(new CustomEvent('auth:logout'));
      
      // Redirection vers login si nous ne sommes pas déjà sur la page d'accueil
      if (window.location.pathname !== '/' && window.location.pathname !== '/login') {
        window.location.href = '/';
      }
    }
    
    return Promise.reject(error);
  }
);

// ✅ Helper pour construire des URLs complètes avec validation
export const buildApiUrl = (endpoint) => {
  if (!endpoint) {
    throw new Error('Endpoint requis pour construire l\'URL API');
  }
  
  // Nettoyer l'endpoint (supprimer les slashes multiples)
  const cleanEndpoint = endpoint.replace(/^\/+/, '');
  const fullUrl = new URL(cleanEndpoint, API_BASE_URL).toString();
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔗 URL construite: ${fullUrl}`);
  }
  
  return fullUrl;
};

// ✅ Méthodes API simplifiées avec gestion d'état intégrée
export const apiMethods = {
  // GET request avec gestion d'état optionnelle
  async get(endpoint, options = {}) {
    const { onLoading, onSuccess, onError } = options;
    
    if (onLoading) onLoading(true);
    
    try {
      const response = await apiClient.get(endpoint);
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } catch (error) {
      if (onError) onError(error);
      throw error;
    } finally {
      if (onLoading) onLoading(false);
    }
  },

  // POST request avec gestion d'état optionnelle
  async post(endpoint, data = {}, options = {}) {
    const { onLoading, onSuccess, onError } = options;
    
    if (onLoading) onLoading(true);
    
    try {
      const response = await apiClient.post(endpoint, data);
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } catch (error) {
      if (onError) onError(error);
      throw error;
    } finally {
      if (onLoading) onLoading(false);
    }
  },

  // PUT request avec gestion d'état optionnelle
  async put(endpoint, data = {}, options = {}) {
    const { onLoading, onSuccess, onError } = options;
    
    if (onLoading) onLoading(true);
    
    try {
      const response = await apiClient.put(endpoint, data);
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } catch (error) {
      if (onError) onError(error);
      throw error;
    } finally {
      if (onLoading) onLoading(false);
    }
  },

  // DELETE request avec gestion d'état optionnelle
  async delete(endpoint, options = {}) {
    const { onLoading, onSuccess, onError } = options;
    
    if (onLoading) onLoading(true);
    
    try {
      const response = await apiClient.delete(endpoint);
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } catch (error) {
      if (onError) onError(error);
      throw error;
    } finally {
      if (onLoading) onLoading(false);
    }
  }
};

// ✅ Hooks utilitaires pour la gestion d'état UI
export const createApiState = () => {
  return {
    loading: false,
    data: null,
    error: null,
    success: false
  };
};

// ✅ Helper pour reset l'état API
export const resetApiState = (setState) => {
  setState({
    loading: false,
    data: null,
    error: null,
    success: false
  });
};

// ✅ Configuration pour désactiver les fonctionnalités si ENV manquante
export const featureFlags = {
  amazonIntegration: !!BACKEND_URL,
  shopifyIntegration: !!BACKEND_URL,
  paymentSystem: !!BACKEND_URL,
  aiFeatures: !!BACKEND_URL,
};

// ✅ Fonction utilitaire pour vérifier la disponibilité des features
export const isFeatureEnabled = (featureName) => {
  const enabled = featureFlags[featureName];
  if (!enabled && process.env.NODE_ENV === 'development') {
    console.warn(`⚠️ Feature "${featureName}" désactivée - REACT_APP_BACKEND_URL manquante`);
  }
  return enabled;
};

// Export de l'instance principale pour compatibilité
export default apiClient;

// Export des constantes utiles
export { BACKEND_URL, API_BASE_URL };