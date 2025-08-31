// Tests automatiques pour AmazonConnectionManager
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import AmazonConnectionManager from '../../src/components/AmazonConnectionManager';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock environment variables
process.env.REACT_APP_BACKEND_URL = 'https://api.test.com';

describe('AmazonConnectionManager', () => {
  const mockProps = {
    user: { id: 'user123', email: 'test@example.com' },
    token: 'mock_jwt_token',
    onConnectionChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders connection manager with initial state', () => {
    render(<AmazonConnectionManager {...mockProps} />);
    
    expect(screen.getByText('Connexion Amazon')).toBeInTheDocument();
    expect(screen.getByText('Connectez votre compte Amazon Seller Central')).toBeInTheDocument();
    expect(screen.getByText('Connecter mon compte Amazon')).toBeInTheDocument();
  });

  test('displays marketplaces dropdown', () => {
    render(<AmazonConnectionManager {...mockProps} />);
    
    const marketplaceSelect = screen.getByDisplayValue('🇫🇷 France (Amazon.fr)');
    expect(marketplaceSelect).toBeInTheDocument();
    
    // Vérifier que toutes les options sont présentes
    fireEvent.click(marketplaceSelect);
    expect(screen.getByText('🇩🇪 Allemagne (Amazon.de)')).toBeInTheDocument();
    expect(screen.getByText('🇺🇸 États-Unis (Amazon.com)')).toBeInTheDocument();
  });

  test('loads connection status on mount', async () => {
    const mockStatusResponse = {
      data: {
        status: 'connected',
        active_marketplaces: [
          {
            connection_id: 'conn123',
            marketplace_id: 'A13V1IB3VIYZZH',
            seller_id: 'seller123',
            region: 'eu'
          }
        ]
      }
    };

    mockedAxios.get.mockResolvedValueOnce(mockStatusResponse);

    render(<AmazonConnectionManager {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        'https://api.test.com/api/amazon/status',
        { headers: { Authorization: 'Bearer mock_jwt_token' } }
      );
    });
  });

  test('handles connection process', async () => {
    const mockConnectResponse = {
      data: {
        connection_id: 'conn123',
        authorization_url: 'https://amazon.com/oauth/authorize?...',
        state: 'secure_state_123',
        marketplace_id: 'A13V1IB3VIYZZH'
      }
    };

    mockedAxios.post.mockResolvedValueOnce(mockConnectResponse);
    
    // Mock window.location.href
    delete window.location;
    window.location = { href: '' };

    render(<AmazonConnectionManager {...mockProps} />);

    const connectButton = screen.getByText('Connecter mon compte Amazon');
    fireEvent.click(connectButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'https://api.test.com/api/amazon/connect',
        {
          marketplace_id: 'A13V1IB3VIYZZH',
          region: 'eu'
        },
        { headers: { Authorization: 'Bearer mock_jwt_token' } }
      );
    });

    expect(window.location.href).toBe('https://amazon.com/oauth/authorize?...');
  });

  test('displays connected state correctly', async () => {
    const mockStatusResponse = {
      data: {
        status: 'connected',
        connections_count: 2,
        active_marketplaces: [
          {
            connection_id: 'conn1',
            marketplace_id: 'A13V1IB3VIYZZH',
            seller_id: 'seller123',
            region: 'eu'
          },
          {
            connection_id: 'conn2', 
            marketplace_id: 'A1PA6795UKMFR9',
            seller_id: 'seller456',
            region: 'eu'
          }
        ]
      }
    };

    mockedAxios.get.mockResolvedValueOnce(mockStatusResponse);

    render(<AmazonConnectionManager {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Connecté')).toBeInTheDocument();
      expect(screen.getByText('2 marketplace(s) connecté(s)')).toBeInTheDocument();
    });

    // Vérifier l'affichage des marketplaces connectés
    expect(screen.getByText('Marketplaces connectés')).toBeInTheDocument();
    expect(screen.getByText('🇫🇷')).toBeInTheDocument();
    expect(screen.getByText('🇩🇪')).toBeInTheDocument();
  });

  test('handles disconnection process', async () => {
    const mockStatusResponse = {
      data: {
        status: 'connected',
        active_marketplaces: [
          {
            connection_id: 'conn123',
            marketplace_id: 'A13V1IB3VIYZZH',
            seller_id: 'seller123'
          }
        ]
      }
    };

    const mockDisconnectResponse = {
      data: {
        status: 'revoked',
        message: '1 connexion(s) Amazon déconnectée(s)',
        disconnected_count: 1
      }
    };

    mockedAxios.get.mockResolvedValueOnce(mockStatusResponse);
    mockedAxios.post.mockResolvedValueOnce(mockDisconnectResponse);

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    render(<AmazonConnectionManager {...mockProps} />);

    // Attendre que le statut connecté soit chargé
    await waitFor(() => {
      expect(screen.getByText('Connecté')).toBeInTheDocument();
    });

    const disconnectButton = screen.getByText('Déconnecter Amazon');
    fireEvent.click(disconnectButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'https://api.test.com/api/amazon/disconnect',
        {},
        { headers: { Authorization: 'Bearer mock_jwt_token' } }
      );
    });

    expect(mockProps.onConnectionChange).toHaveBeenCalledWith({
      status: 'revoked',
      connections: []
    });
  });

  test('handles URL parameters for OAuth callback', () => {
    // Mock URL parameters
    delete window.location;
    window.location = {
      search: '?amazon=connected',
      pathname: '/dashboard'
    };

    const mockReplaceState = jest.fn();
    window.history = {
      replaceState: mockReplaceState
    };

    render(<AmazonConnectionManager {...mockProps} />);

    expect(mockReplaceState).toHaveBeenCalledWith(
      {},
      document.title,
      '/dashboard'
    );
  });

  test('handles OAuth error parameters', () => {
    delete window.location;
    window.location = {
      search: '?amazon_error=invalid_state&message=État OAuth invalide',
      pathname: '/dashboard'
    };

    window.history = {
      replaceState: jest.fn()
    };

    render(<AmazonConnectionManager {...mockProps} />);

    expect(screen.getByText('Erreur de connexion: État OAuth invalide')).toBeInTheDocument();
  });

  test('displays loading states correctly', async () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AmazonConnectionManager {...mockProps} />);

    // Le composant devrait afficher un état de chargement initial
    const connectButton = screen.getByText('Connecter mon compte Amazon');
    
    // Cliquer sur le bouton de connexion
    mockedAxios.post.mockImplementation(() => new Promise(() => {}));
    fireEvent.click(connectButton);

    await waitFor(() => {
      expect(screen.getByText('Connexion en cours...')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    const mockError = {
      response: {
        data: {
          detail: 'Une connexion existe déjà pour ce marketplace'
        }
      }
    };

    mockedAxios.post.mockRejectedValueOnce(mockError);

    render(<AmazonConnectionManager {...mockProps} />);

    const connectButton = screen.getByText('Connecter mon compte Amazon');
    fireEvent.click(connectButton);

    await waitFor(() => {
      expect(screen.getByText('Une connexion existe déjà pour ce marketplace')).toBeInTheDocument();
    });
  });

  test('displays security information', () => {
    render(<AmazonConnectionManager {...mockProps} />);

    expect(screen.getByText('🔐 Sécurité & Permissions')).toBeInTheDocument();
    expect(screen.getByText('• Connexion sécurisée via OAuth 2.0')).toBeInTheDocument();
    expect(screen.getByText('• Tokens chiffrés et stockés de manière sécurisée')).toBeInTheDocument();
    expect(screen.getByText('• Accès en lecture seule à vos listings')).toBeInTheDocument();
  });

  test('allows marketplace selection', () => {
    render(<AmazonConnectionManager {...mockProps} />);

    const marketplaceSelect = screen.getByLabelText('Marketplace à connecter');
    
    // Changer de marketplace
    fireEvent.change(marketplaceSelect, { target: { value: 'ATVPDKIKX0DER' } });
    
    expect(marketplaceSelect.value).toBe('ATVPDKIKX0DER');
  });

  test('calls onConnectionChange when status updates', async () => {
    const mockStatusResponse = {
      data: {
        status: 'connected',
        connections_count: 1,
        active_marketplaces: []
      }
    };

    mockedAxios.get.mockResolvedValueOnce(mockStatusResponse);

    render(<AmazonConnectionManager {...mockProps} />);

    await waitFor(() => {
      expect(mockProps.onConnectionChange).toHaveBeenCalledWith(
        mockStatusResponse.data
      );
    });
  });
});

// Tests d'intégration plus avancés
describe('AmazonConnectionManager Integration', () => {
  test('complete connection flow simulation', async () => {
    const mockProps = {
      user: { id: 'user123', email: 'test@example.com' },
      token: 'mock_jwt_token',
      onConnectionChange: jest.fn()
    };

    // 1. État initial - non connecté
    const mockStatusResponse1 = {
      data: {
        status: 'none',
        connections_count: 0,
        active_marketplaces: []
      }
    };

    // 2. Après connexion - connecté
    const mockStatusResponse2 = {
      data: {
        status: 'connected',
        connections_count: 1,
        active_marketplaces: [
          {
            connection_id: 'conn123',
            marketplace_id: 'A13V1IB3VIYZZH',
            seller_id: 'seller123'
          }
        ]
      }
    };

    mockedAxios.get
      .mockResolvedValueOnce(mockStatusResponse1)
      .mockResolvedValueOnce(mockStatusResponse2);

    const { rerender } = render(<AmazonConnectionManager {...mockProps} />);

    // Vérifier l'état initial
    await waitFor(() => {
      expect(screen.getByText('Non connecté')).toBeInTheDocument();
    });

    // Simuler une mise à jour après connexion OAuth
    delete window.location;
    window.location = {
      search: '?amazon=connected',
      pathname: '/dashboard'
    };

    window.history = {
      replaceState: jest.fn()
    };

    rerender(<AmazonConnectionManager {...mockProps} />);

    // Vérifier le nouvel état
    await waitFor(() => {
      expect(screen.getByText('Connecté')).toBeInTheDocument();
    });
  });
});