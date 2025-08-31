#!/usr/bin/env python3
"""
Tests d'intégration pour la déconnexion Amazon
Test du cycle complet: connexion → déconnexion → reconnexion
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

# Ajout du path backend pour les imports
import sys
sys.path.append('/app/backend')

from services.amazon_connection_service import AmazonConnectionService
from models.amazon_spapi import AmazonConnection, ConnectionStatus, SPAPIRegion

@pytest.mark.asyncio
class TestAmazonDisconnectIntegration:
    """Tests d'intégration pour la déconnexion Amazon"""
    
    def setup_method(self):
        """Setup pour chaque test"""
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.amazon_connections = self.mock_collection
        self.service = AmazonConnectionService(self.mock_db)
        
    async def test_disconnect_connection_success(self):
        """Test de déconnexion réussie d'une connexion"""
        # Arrange
        connection_id = "test-connection-123"
        user_id = "test-user-456"
        
        # Mock successful update
        self.mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        # Act
        result = await self.service.disconnect_connection(connection_id, user_id)
        
        # Assert
        assert result is True
        
        # Vérifier que update_one a été appelé avec les bons paramètres
        self.mock_collection.update_one.assert_called_once()
        call_args = self.mock_collection.update_one.call_args
        
        # Vérifier le filtre (premier argument)
        filter_dict = call_args[0][0]
        assert filter_dict['id'] == connection_id
        assert filter_dict['user_id'] == user_id
        
        # Vérifier la mise à jour (deuxième argument)
        update_dict = call_args[0][1]['$set']
        assert update_dict['status'] == ConnectionStatus.REVOKED
        assert update_dict['encrypted_refresh_token'] == ""
        assert update_dict['token_encryption_nonce'] == ""
        assert update_dict['error_message'] == "Connection revoked by user"
        assert 'updated_at' in update_dict
    
    async def test_disconnect_connection_not_found(self):
        """Test de déconnexion d'une connexion inexistante"""
        # Arrange
        connection_id = "nonexistent-connection"
        user_id = "test-user-456"
        
        # Mock no update (connection not found)
        self.mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        
        # Act
        result = await self.service.disconnect_connection(connection_id, user_id)
        
        # Assert
        assert result is False
    
    async def test_disconnect_connection_exception_handling(self):
        """Test de gestion d'exception lors de la déconnexion"""
        # Arrange
        connection_id = "test-connection-123"
        user_id = "test-user-456"
        
        # Mock exception during update
        self.mock_collection.update_one = AsyncMock(side_effect=Exception("Database error"))
        
        # Act
        result = await self.service.disconnect_connection(connection_id, user_id)
        
        # Assert
        assert result is False
    
    async def test_get_user_connections_after_disconnect(self):
        """Test de récupération des connexions utilisateur après déconnexion"""
        # Arrange
        user_id = "test-user-456"
        
        # Mock data avec connexion révoquée
        mock_connection_data = {
            'id': 'test-connection-123',
            'user_id': user_id,
            'region': 'eu',
            'marketplace_id': 'A13V1IB3VIYZZH',
            'seller_id': 'TEST_SELLER',
            'encrypted_refresh_token': '',  # Token supprimé
            'token_encryption_nonce': '',   # Nonce supprimé
            'encryption_key_id': 'test-key',
            'status': ConnectionStatus.REVOKED,
            'connected_at': None,
            'last_used_at': datetime.utcnow() - timedelta(minutes=5),
            'error_message': 'Connection revoked by user',
            'retry_count': 0,
            'oauth_state': None,
            'oauth_state_expires': None,
            'created_at': datetime.utcnow() - timedelta(hours=1),
            'updated_at': datetime.utcnow(),
            'connection_metadata': {}
        }
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[mock_connection_data])
        self.mock_collection.find = MagicMock(return_value=mock_cursor)
        
        # Act
        connections = await self.service.get_user_connections(user_id)
        
        # Assert
        assert len(connections) == 1
        connection = connections[0]
        assert connection.connection_id == 'test-connection-123'
        assert connection.status == ConnectionStatus.REVOKED
        assert connection.connected_at is None  # Pas connecté si révoqué
        
    async def test_multi_tenant_security(self):
        """Test de sécurité multi-tenant - un utilisateur ne peut pas déconnecter les connexions d'un autre"""
        # Arrange
        connection_id = "test-connection-123"
        wrong_user_id = "wrong-user-789"
        
        # Mock aucune mise à jour car l'utilisateur ne possède pas la connexion
        self.mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        
        # Act
        result = await self.service.disconnect_connection(connection_id, wrong_user_id)
        
        # Assert
        assert result is False
        
        # Vérifier que le filtre inclut bien l'user_id pour la sécurité
        self.mock_collection.update_one.assert_called_once()
        call_args = self.mock_collection.update_one.call_args
        filter_dict = call_args[0][0]
        assert filter_dict['user_id'] == wrong_user_id

if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])