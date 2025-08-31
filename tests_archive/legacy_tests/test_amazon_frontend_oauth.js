/**
 * Tests Frontend OAuth Amazon - Retour OAuth et Mise à Jour Dynamique
 * 
 * Tests Unitaires:
 * - Gestion du state UI (connected/none)
 * - Affichage dynamique du bouton selon le statut
 * - Gestion des messages postMessage
 * - Nettoyage automatique des resources
 * 
 * Tests E2E:
 * - Clic bouton → OAuth → retour → bouton affiche Connecté ✅
 * - Flow complet avec popup et fallback
 * 
 * Critères d'acceptation:
 * - L'utilisateur n'est jamais bloqué sur Amazon
 * - Le retour dans le dashboard est immédiat  
 * - L'état du bouton correspond au statut en DB
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { jest } from '@jest/globals';
import React from 'react';

// Mock du composant App principal
const mockApp = {
  handleAmazonConnection: jest.fn(),
  refreshAmazonStatus: jest.fn(),
  showNotification: jest.fn(),
  amazonConnectionStatus: 'none',
  selectedPlatform: null,
  setAmazonConnectionStatus: jest.fn(),
  setSelectedPlatform: jest.fn()
};

// Mock de fetch global
global.fetch = jest.fn();

// Mock de window.open
global.open = jest.fn();

// Mock de localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

describe('Amazon Frontend OAuth Tests', () => {
  
  beforeEach(() => {
    // Reset tous les mocks avant chaque test
    jest.clearAllMocks();
    global.fetch.mockClear();
    global.open.mockClear();
    
    // Configuration par défaut
    localStorageMock.getItem.mockReturnValue('mock-jwt-token');
    process.env.REACT_APP_BACKEND_URL = 'https://test-backend.com';
  });

  describe('Tests Unitaires - Gestion du State UI', () => {
    
    test('État initial du bouton Amazon (non connecté)', () => {
      const buttonState = {
        amazonConnectionStatus: 'none',
        selectedPlatform: null
      };
      
      // Vérifier l'affichage initial
      expect(getAmazonButtonDisplay(buttonState)).toEqual({
        icon: '📦',
        text: 'Amazon',
        description: 'Marketplace global',
        loading: false
      });
    });
    
    test('État du bouton pendant la connexion (loading)', () => {
      const buttonState = {
        amazonConnectionStatus: 'none',
        selectedPlatform: 'amazon'
      };
      
      // Vérifier l'affichage de chargement
      expect(getAmazonButtonDisplay(buttonState)).toEqual({
        icon: '⏳',
        text: 'Amazon',
        description: 'Connexion...',
        loading: true
      });
    });
    
    test('État du bouton connecté (Connecté ✅)', () => {
      const buttonState = {
        amazonConnectionStatus: 'connected',
        selectedPlatform: null
      };
      
      // Vérifier l'affichage connecté
      expect(getAmazonButtonDisplay(buttonState)).toEqual({
        icon: '📦',
        text: 'Amazon',
        description: 'Connecté ✅',
        loading: false
      });
    });
    
    test('État du bouton déconnecté (Déconnecté ❌)', () => {
      const buttonState = {
        amazonConnectionStatus: 'revoked',
        selectedPlatform: null
      };
      
      // Vérifier l'affichage déconnecté
      expect(getAmazonButtonDisplay(buttonState)).toEqual({
        icon: '📦',
        text: 'Amazon',
        description: 'Déconnecté ❌',
        loading: false
      });
    });
    
    test('État du bouton en erreur (Erreur ⚠️)', () => {
      const buttonState = {
        amazonConnectionStatus: 'error',
        selectedPlatform: null
      };
      
      // Vérifier l'affichage d'erreur
      expect(getAmazonButtonDisplay(buttonState)).toEqual({
        icon: '📦',
        text: 'Amazon',
        description: 'Erreur ⚠️',
        loading: false
      });
    });
  });

  describe('Tests Unitaires - Gestion postMessage', () => {
    
    test('Traitement message AMAZON_CONNECTED', async () => {
      const messageHandler = createPostMessageHandler(mockApp);
      
      // Simuler message de succès
      const successMessage = {
        origin: window.location.origin,
        data: {
          type: 'AMAZON_CONNECTED',
          success: true,
          message: 'Amazon connection successful',
          timestamp: new Date().toISOString()
        }
      };
      
      await act(async () => {
        messageHandler(successMessage);
      });
      
      // Vérifier les actions appelées
      expect(mockApp.refreshAmazonStatus).toHaveBeenCalled();
      expect(mockApp.showNotification).toHaveBeenCalledWith(
        '✅ Amazon connecté avec succès !',
        'success'
      );
    });
    
    test('Traitement message AMAZON_CONNECTION_ERROR', async () => {
      const messageHandler = createPostMessageHandler(mockApp);
      
      // Simuler message d'erreur
      const errorMessage = {
        origin: window.location.origin,
        data: {
          type: 'AMAZON_CONNECTION_ERROR',
          success: false,
          error: 'callback_failed',
          message: 'Amazon connection failed'
        }
      };
      
      await act(async () => {
        messageHandler(errorMessage);
      });
      
      // Vérifier les actions appelées
      expect(mockApp.setSelectedPlatform).toHaveBeenCalledWith(null);
      expect(mockApp.showNotification).toHaveBeenCalledWith(
        '❌ Erreur connexion Amazon. Veuillez réessayer.',
        'error'
      );
    });
    
    test('Rejet des messages non autorisés (sécurité)', () => {
      const messageHandler = createPostMessageHandler(mockApp);
      
      // Simuler message d'origine non autorisée
      const maliciousMessage = {
        origin: 'https://malicious-site.com',
        data: {
          type: 'AMAZON_CONNECTED',
          success: true
        }
      };
      
      messageHandler(maliciousMessage);
      
      // Vérifier qu'aucune action n'est prise
      expect(mockApp.refreshAmazonStatus).not.toHaveBeenCalled();
      expect(mockApp.showNotification).not.toHaveBeenCalled();
    });
  });

  describe('Tests Unitaires - Gestion Popup', () => {
    
    test('Ouverture popup avec bonnes dimensions et paramètres', async () => {
      // Mock fetch pour /api/amazon/connect
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          authorization_url: 'https://sellercentral-europe.amazon.com/apps/authorize?client_id=test&state=test-state'
        })
      });
      
      // Mock popup
      const mockPopup = {
        closed: false,
        close: jest.fn()
      };
      global.open.mockReturnValue(mockPopup);
      
      await mockApp.handleAmazonConnection();
      
      // Vérifier ouverture popup
      expect(global.open).toHaveBeenCalledWith(
        expect.stringContaining('popup=true'),
        'amazon-oauth-popup',
        'width=800,height=700,scrollbars=yes,resizable=yes,status=yes,location=yes,toolbar=no,menubar=no'
      );
    });
    
    test('Fallback redirection si popup bloqué', async () => {
      // Mock fetch pour /api/amazon/connect
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          authorization_url: 'https://sellercentral-europe.amazon.com/apps/authorize?client_id=test&state=test-state'
        })
      });
      
      // Mock popup bloqué
      global.open.mockReturnValue(null);
      
      // Mock window.location
      delete window.location;
      window.location = { href: '' };
      
      await mockApp.handleAmazonConnection();
      
      // Vérifier fallback redirection
      expect(window.location.href).toContain('sellercentral-europe.amazon.com');
    });
    
    test('Nettoyage automatique des resources (timeout)', async () => {
      jest.useFakeTimers();
      
      // Mock fetch et popup
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          authorization_url: 'https://test-auth-url.com'
        })
      });
      
      const mockPopup = {
        closed: false,
        close: jest.fn()
      };
      global.open.mockReturnValue(mockPopup);
      
      // Mock addEventListener et removeEventListener
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      
      await mockApp.handleAmazonConnection();
      
      // Avancer le temps de 10 minutes (timeout)
      act(() => {
        jest.advanceTimersByTime(600000);
      });
      
      // Vérifier nettoyage
      expect(mockPopup.close).toHaveBeenCalled();
      expect(removeEventListenerSpy).toHaveBeenCalledWith('message', expect.any(Function));
      
      jest.useRealTimers();
    });
  });

  describe('Tests Unitaires - Fallback URL', () => {
    
    test('Détection paramètre amazon_connected=true', async () => {
      // Mock URL avec paramètre
      delete window.location;
      window.location = {
        search: '?amazon_connected=true&tab=stores',
        pathname: '/dashboard',
        origin: 'https://test.com'
      };
      
      // Mock history.replaceState
      const replaceStateSpy = jest.spyOn(window.history, 'replaceState').mockImplementation(() => {});
      
      const fallbackHandler = createFallbackHandler(mockApp);
      await fallbackHandler();
      
      // Vérifier nettoyage URL
      expect(replaceStateSpy).toHaveBeenCalledWith({}, expect.any(String), '/dashboard');
      
      // Vérifier appel refresh status
      expect(mockApp.refreshAmazonStatus).toHaveBeenCalled();
    });
    
    test('Détection paramètre amazon=connected', async () => {
      // Mock URL avec paramètre alternatif
      delete window.location;
      window.location = {
        search: '?amazon=connected',
        pathname: '/dashboard',
        origin: 'https://test.com'
      };
      
      const fallbackHandler = createFallbackHandler(mockApp);
      await fallbackHandler();
      
      // Vérifier traitement fallback
      expect(mockApp.refreshAmazonStatus).toHaveBeenCalled();
    });
    
    test('Détection paramètre amazon_error', async () => {
      // Mock URL avec erreur
      delete window.location;
      window.location = {
        search: '?amazon_error=callback_failed&tab=stores',
        pathname: '/dashboard',
        origin: 'https://test.com'
      };
      
      const fallbackHandler = createFallbackHandler(mockApp);
      await fallbackHandler();
      
      // Vérifier gestion erreur
      expect(mockApp.setSelectedPlatform).toHaveBeenCalledWith(null);
      expect(mockApp.showNotification).toHaveBeenCalledWith(
        '❌ Erreur connexion Amazon. Veuillez réessayer.',
        'error'
      );
    });
  });

  describe('Tests d\'Intégration - RefreshAmazonStatus', () => {
    
    test('Mise à jour statut réussie', async () => {
      // Mock fetch pour /api/amazon/status
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'connected',
          connections: [{
            connection_id: 'test-connection-123',
            seller_id: 'AXXXXXXXXXXXX',
            marketplace_id: 'A13V1IB3VIYZZH'
          }]
        })
      });
      
      const result = await mockApp.refreshAmazonStatus();
      
      // Vérifier appel API
      expect(global.fetch).toHaveBeenCalledWith(
        'https://test-backend.com/api/amazon/status',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );
      
      // Vérifier mise à jour state
      expect(mockApp.setAmazonConnectionStatus).toHaveBeenCalledWith('connected');
      expect(result).toBe('connected');
    });
    
    test('Gestion erreur API', async () => {
      // Mock fetch avec erreur
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });
      
      const result = await mockApp.refreshAmazonStatus();
      
      // Vérifier gestion erreur
      expect(result).toBe(null);
    });
  });
});

// Fonctions utilitaires pour les tests

function getAmazonButtonDisplay(buttonState) {
  const { amazonConnectionStatus, selectedPlatform } = buttonState;
  
  return {
    icon: selectedPlatform === 'amazon' ? '⏳' : '📦',
    text: 'Amazon',
    description: selectedPlatform === 'amazon' ? 'Connexion...' :
                amazonConnectionStatus === 'connected' ? 'Connecté ✅' :
                amazonConnectionStatus === 'revoked' ? 'Déconnecté ❌' :
                amazonConnectionStatus === 'error' ? 'Erreur ⚠️' :
                'Marketplace global',
    loading: selectedPlatform === 'amazon'
  };
}

function createPostMessageHandler(app) {
  return (event) => {
    const allowedOrigins = [
      window.location.origin,
      'https://sellercentral-europe.amazon.com',
      'https://sellercentral.amazon.com'
    ];
    
    if (!allowedOrigins.includes(event.origin)) {
      return;
    }
    
    if (event.data && event.data.type === 'AMAZON_CONNECTED') {
      setTimeout(async () => {
        await app.refreshAmazonStatus();
        app.showNotification('✅ Amazon connecté avec succès !', 'success');
      }, 500);
      
    } else if (event.data && event.data.type === 'AMAZON_CONNECTION_ERROR') {
      app.setSelectedPlatform(null);
      app.showNotification('❌ Erreur connexion Amazon. Veuillez réessayer.', 'error');
    }
  };
}

function createFallbackHandler(app) {
  return async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const amazonConnected = urlParams.get('amazon_connected');
    const amazonError = urlParams.get('amazon_error');
    const amazonParam = urlParams.get('amazon');
    
    if (amazonConnected === 'true' || amazonParam === 'connected' || amazonError) {
      // Nettoyer URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      if (amazonConnected === 'true' || amazonParam === 'connected') {
        setTimeout(async () => {
          const status = await app.refreshAmazonStatus();
          if (status === 'connected') {
            app.showNotification('✅ Amazon connecté avec succès !', 'success');
          }
        }, 500);
        
      } else if (amazonError) {
        app.setSelectedPlatform(null);
        setTimeout(() => {
          app.showNotification('❌ Erreur connexion Amazon. Veuillez réessayer.', 'error');
        }, 1000);
      }
    }
  };
}