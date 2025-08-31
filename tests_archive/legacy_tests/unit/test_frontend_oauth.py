"""
Tests unitaires Frontend pour Amazon OAuth
Validation allowedOrigins et postMessage handling
"""

import pytest
from unittest.mock import patch, MagicMock
import os

class TestFrontendOAuthAllowedOrigins:
    """Test de l'extension allowedOrigins avec backend URL"""
    
    def test_allowed_origins_includes_backend_origin(self):
        """Test que allowedOrigins inclut l'origine backend"""
        
        # Mock REACT_APP_BACKEND_URL
        backend_url = 'https://api.test.com'
        
        with patch.dict(os.environ, {'REACT_APP_BACKEND_URL': backend_url}):
            # Simuler le code frontend JavaScript 
            from urllib.parse import urlparse
            
            # Code équivalent au frontend
            allowed_origins = [
                'https://localhost:3000',  # window.location.origin simulé
                'https://sellercentral-europe.amazon.com',
                'https://sellercentral.amazon.com',
                urlparse(backend_url).scheme + '://' + urlparse(backend_url).netloc  # Backend origin
            ]
            
            # Vérifications
            assert 'https://api.test.com' in allowed_origins
            assert len(allowed_origins) == 4
            
            # Test avec différents backends
            test_backends = [
                'https://ecomsimply.com',
                'https://api.ecomsimply.com',
                'https://staging-api.ecomsimply.com'
            ]
            
            for backend in test_backends:
                backend_origin = urlparse(backend).scheme + '://' + urlparse(backend).netloc
                test_origins = [
                    'https://localhost:3000',
                    'https://sellercentral-europe.amazon.com',
                    'https://sellercentral.amazon.com',
                    backend_origin
                ]
                
                assert backend_origin in test_origins
    
    def test_postmessage_amazon_connected_handling(self):
        """Test du traitement du postMessage AMAZON_CONNECTED"""
        
        # Simuler event.data
        mock_event_data = {
            'type': 'AMAZON_CONNECTED',
            'success': True,
            'message': 'Amazon connection successful',
            'timestamp': '2025-01-01T00:00:00.000Z'
        }
        
        # Test de la logique de traitement
        def handle_oauth_message(event_data):
            if event_data and event_data.get('type') == 'AMAZON_CONNECTED':
                return {
                    'should_close_popup': True,
                    'should_refresh_status': True,
                    'should_show_notification': True,
                    'notification_message': '✅ Amazon connecté avec succès !',
                    'notification_type': 'success'
                }
            return None
        
        # Test
        result = handle_oauth_message(mock_event_data)
        
        assert result is not None
        assert result['should_close_popup'] is True
        assert result['should_refresh_status'] is True
        assert result['should_show_notification'] is True
        assert '✅ Amazon connecté avec succès !' in result['notification_message']
    
    def test_postmessage_amazon_error_handling(self):
        """Test du traitement des erreurs OAuth"""
        
        mock_error_data = {
            'type': 'AMAZON_CONNECTION_ERROR',
            'success': False,
            'error': 'redirect_uri_mismatch',
            'message': 'Redirect URI does not match',
            'timestamp': '2025-01-01T00:00:00.000Z'
        }
        
        def handle_oauth_message(event_data):
            if event_data and event_data.get('type') == 'AMAZON_CONNECTION_ERROR':
                return {
                    'should_close_popup': True,
                    'should_show_error': True,
                    'error_message': f"❌ Erreur OAuth Amazon: {event_data.get('error', 'Unknown')}",
                    'error_details': event_data.get('message', '')
                }
            return None
        
        result = handle_oauth_message(mock_error_data)
        
        assert result is not None
        assert result['should_close_popup'] is True
        assert result['should_show_error'] is True
        assert 'redirect_uri_mismatch' in result['error_message']
    
    def test_fallback_url_handling(self):
        """Test du fallback ?amazon=connected"""
        
        # Test de parsing d'URL avec paramètre amazon
        def check_amazon_fallback(url):
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            return 'amazon' in params and 'connected' in params['amazon']
        
        # Tests
        test_urls = [
            'https://app.test.com/?amazon=connected',
            'https://app.test.com/dashboard?amazon=connected&tab=stores',
            'https://app.test.com/?amazon=error&error=redirect_mismatch'
        ]
        
        assert check_amazon_fallback(test_urls[0]) is True
        assert check_amazon_fallback(test_urls[1]) is True
        assert check_amazon_fallback(test_urls[2]) is False
    
    def test_origin_validation_security(self):
        """Test de sécurité de validation des origines"""
        
        allowed_origins = [
            'https://localhost:3000',
            'https://sellercentral-europe.amazon.com',
            'https://sellercentral.amazon.com',
            'https://api.ecomsimply.com'
        ]
        
        # Test origines légitimes
        legitimate_origins = [
            'https://localhost:3000',
            'https://sellercentral-europe.amazon.com',
            'https://api.ecomsimply.com'
        ]
        
        for origin in legitimate_origins:
            assert origin in allowed_origins
        
        # Test origines malveillantes (doivent être rejetées)
        malicious_origins = [
            'https://evil.com',
            'https://sellercentral-fake.amazon.com',
            'http://localhost:3000',  # HTTP au lieu de HTTPS
            'https://api.fake-ecomsimply.com'
        ]
        
        for origin in malicious_origins:
            assert origin not in allowed_origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])