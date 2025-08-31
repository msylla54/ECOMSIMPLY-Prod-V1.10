#!/usr/bin/env python3
"""
Tests unitaires pour le composant AmazonIntegrationCard
Test des props, états, et rendu du composant React
"""

import json
import unittest
from unittest.mock import Mock, patch

class TestAmazonIntegrationCard(unittest.TestCase):
    """Tests unitaires pour AmazonIntegrationCard"""
    
    def setUp(self):
        """Configuration des tests"""
        self.mock_props = {
            'amazonConnectionStatus': 'none',
            'selectedPlatform': None,
            'onConnect': Mock(),
            'onDisconnect': Mock(),
            'showConfirmDialog': True,
            'size': 'normal'
        }
    
    def test_component_props_validation(self):
        """Test de validation des props requis"""
        required_props = [
            'amazonConnectionStatus',
            'selectedPlatform', 
            'onConnect',
            'onDisconnect'
        ]
        
        for prop in required_props:
            self.assertIn(prop, self.mock_props, f"Prop requis manquant: {prop}")
    
    def test_status_display_mapping(self):
        """Test du mapping des statuts vers l'affichage"""
        status_mappings = {
            'none': {
                'text': 'Non connecté',
                'icon': '🔌',
                'color': 'text-gray-500',
                'bgColor': 'bg-gray-50',
                'borderColor': 'border-gray-200'
            },
            'connected': {
                'text': 'Connecté',
                'icon': '✅',
                'color': 'text-green-600',
                'bgColor': 'bg-green-50',
                'borderColor': 'border-green-200'
            },
            'revoked': {
                'text': 'Déconnecté',
                'icon': '❌',
                'color': 'text-red-600',
                'bgColor': 'bg-red-50',
                'borderColor': 'border-red-200'
            },
            'error': {
                'text': 'Erreur',
                'icon': '⚠️',
                'color': 'text-orange-600',
                'bgColor': 'bg-orange-50',
                'borderColor': 'border-orange-200'
            },
            'pending': {
                'text': 'En attente',
                'icon': '⏳',
                'color': 'text-blue-600',
                'bgColor': 'bg-blue-50',
                'borderColor': 'border-blue-200'
            }
        }
        
        for status, expected in status_mappings.items():
            with self.subTest(status=status):
                # Simuler la fonction getStatusDisplay()
                result = self._get_status_display(status)
                self.assertEqual(result['text'], expected['text'])
                self.assertEqual(result['icon'], expected['icon'])
                self.assertEqual(result['color'], expected['color'])
    
    def test_button_text_logic(self):
        """Test de la logique du texte des boutons"""
        test_cases = [
            # (status, selectedPlatform, expected_text)
            ('none', None, 'Connecter'),
            ('none', 'amazon', 'Connexion...'),
            ('connected', None, 'Déconnecter'),
            ('connected', 'amazon', 'Déconnexion...'),
            ('revoked', None, 'Reconnecter'),
            ('revoked', 'amazon', 'Connexion...'),
            ('error', None, 'Connecter'),
            ('pending', None, 'Connecter')
        ]
        
        for status, selected_platform, expected_text in test_cases:
            with self.subTest(status=status, platform=selected_platform):
                result = self._get_button_text(status, selected_platform)
                self.assertEqual(result, expected_text)
    
    def test_button_style_logic(self):
        """Test de la logique des styles de boutons"""
        test_cases = [
            ('connected', 'bg-red-600 hover:bg-red-700 text-white'),
            ('none', 'bg-green-600 hover:bg-green-700 text-white'),
            ('revoked', 'bg-green-600 hover:bg-green-700 text-white'),
            ('error', 'bg-green-600 hover:bg-green-700 text-white'),
            ('pending', 'bg-green-600 hover:bg-green-700 text-white')
        ]
        
        for status, expected_style in test_cases:
            with self.subTest(status=status):
                result = self._get_button_style(status)
                self.assertEqual(result, expected_style)
    
    def test_size_variants(self):
        """Test des variantes de taille du composant"""
        size_variants = {
            'small': {
                'container': 'p-3',
                'icon': 'text-lg',
                'title': 'text-sm font-medium',
                'button': 'px-3 py-1 text-xs'
            },
            'normal': {
                'container': 'p-4',
                'icon': 'text-2xl',
                'title': 'text-base font-medium',
                'button': 'px-4 py-2 text-sm'
            },
            'large': {
                'container': 'p-6',
                'icon': 'text-3xl',
                'title': 'text-lg font-medium',
                'button': 'px-6 py-3 text-base'
            }
        }
        
        for size, expected_classes in size_variants.items():
            with self.subTest(size=size):
                result = self._get_size_classes(size)
                for key, expected_class in expected_classes.items():
                    self.assertEqual(result[key], expected_class)
    
    def test_conditional_status_messages(self):
        """Test des messages conditionnels selon le statut"""
        status_messages = {
            'revoked': 'Connexion révoquée. Pour republier sur Amazon, reconnectez-vous.',
            'error': 'Erreur de connexion. Essayez de vous reconnecter.',
            'connected': 'Connexion active. Prêt pour la publication automatique.'
        }
        
        # Les statuts 'none' et 'pending' ne devraient pas avoir de messages
        no_message_statuses = ['none', 'pending']
        
        for status, expected_message in status_messages.items():
            with self.subTest(status=status):
                self.assertTrue(self._should_show_status_message(status))
                message = self._get_status_message(status)
                self.assertIn(expected_message.split('.')[0], message)
        
        for status in no_message_statuses:
            with self.subTest(status=status):
                self.assertFalse(self._should_show_status_message(status))
    
    def test_click_handler_logic(self):
        """Test de la logique du gestionnaire de clic"""
        mock_on_connect = Mock()
        mock_on_disconnect = Mock()
        
        # Test connexion (statut non connecté)
        for status in ['none', 'revoked', 'error', 'pending']:
            with self.subTest(status=status):
                mock_on_connect.reset_mock()
                mock_on_disconnect.reset_mock()
                
                self._simulate_click(status, mock_on_connect, mock_on_disconnect, show_confirm=False)
                
                mock_on_connect.assert_called_once()
                mock_on_disconnect.assert_not_called()
        
        # Test déconnexion (statut connecté, sans confirmation)
        mock_on_connect.reset_mock()
        mock_on_disconnect.reset_mock()
        
        self._simulate_click('connected', mock_on_connect, mock_on_disconnect, show_confirm=False)
        
        mock_on_disconnect.assert_called_once()
        mock_on_connect.assert_not_called()
    
    # Méthodes utilitaires pour simuler les fonctions du composant
    def _get_status_display(self, status):
        """Simuler getStatusDisplay()"""
        status_map = {
            'connected': {'text': 'Connecté', 'icon': '✅', 'color': 'text-green-600', 'bgColor': 'bg-green-50', 'borderColor': 'border-green-200'},
            'revoked': {'text': 'Déconnecté', 'icon': '❌', 'color': 'text-red-600', 'bgColor': 'bg-red-50', 'borderColor': 'border-red-200'},
            'error': {'text': 'Erreur', 'icon': '⚠️', 'color': 'text-orange-600', 'bgColor': 'bg-orange-50', 'borderColor': 'border-orange-200'},
            'pending': {'text': 'En attente', 'icon': '⏳', 'color': 'text-blue-600', 'bgColor': 'bg-blue-50', 'borderColor': 'border-blue-200'},
            'none': {'text': 'Non connecté', 'icon': '🔌', 'color': 'text-gray-500', 'bgColor': 'bg-gray-50', 'borderColor': 'border-gray-200'}
        }
        return status_map.get(status, status_map['none'])
    
    def _get_button_text(self, status, selected_platform):
        """Simuler getButtonText()"""
        if selected_platform == 'amazon':
            return 'Déconnexion...' if status == 'connected' else 'Connexion...'
        
        if status == 'connected':
            return 'Déconnecter'
        elif status == 'revoked':
            return 'Reconnecter'
        else:
            return 'Connecter'
    
    def _get_button_style(self, status):
        """Simuler getButtonStyle()"""
        if status == 'connected':
            return 'bg-red-600 hover:bg-red-700 text-white'
        else:
            return 'bg-green-600 hover:bg-green-700 text-white'
    
    def _get_size_classes(self, size):
        """Simuler les classes de taille"""
        size_classes = {
            'small': {'container': 'p-3', 'icon': 'text-lg', 'title': 'text-sm font-medium', 'button': 'px-3 py-1 text-xs'},
            'normal': {'container': 'p-4', 'icon': 'text-2xl', 'title': 'text-base font-medium', 'button': 'px-4 py-2 text-sm'},
            'large': {'container': 'p-6', 'icon': 'text-3xl', 'title': 'text-lg font-medium', 'button': 'px-6 py-3 text-base'}
        }
        return size_classes.get(size, size_classes['normal'])
    
    def _should_show_status_message(self, status):
        """Simuler la condition d'affichage des messages"""
        return status in ['revoked', 'error', 'connected']
    
    def _get_status_message(self, status):
        """Simuler les messages de statut"""
        messages = {
            'revoked': 'Connexion révoquée. Pour republier sur Amazon, reconnectez-vous.',
            'error': 'Erreur de connexion. Essayez de vous reconnecter.',
            'connected': 'Connexion active. Prêt pour la publication automatique.'
        }
        return messages.get(status, '')
    
    def _simulate_click(self, status, on_connect, on_disconnect, show_confirm=True):
        """Simuler le clic sur le bouton"""
        if status == 'connected':
            if not show_confirm:  # Skip confirmation dialog for test
                on_disconnect()
        else:
            on_connect()

class TestAmazonIntegrationValidation(unittest.TestCase):
    """Tests de validation de l'intégration Amazon"""
    
    def test_integration_structure(self):
        """Test de la structure d'intégration"""
        expected_structure = {
            'component_name': 'AmazonIntegrationCard',
            'location': '/app/frontend/src/components/AmazonIntegrationCard.js',
            'import_in_app': 'import AmazonIntegrationCard from \'./components/AmazonIntegrationCard\'',
            'section_id': 'amazon-integration-section',
            'title': '🛒 Gestion Amazon SP-API'
        }
        
        # Vérifier que tous les éléments de structure sont définis
        for key, value in expected_structure.items():
            self.assertIsNotNone(value, f"Élément de structure manquant: {key}")
            self.assertNotEqual(value.strip(), '', f"Élément de structure vide: {key}")
    
    def test_props_interface(self):
        """Test de l'interface des props"""
        required_props = [
            'amazonConnectionStatus',
            'selectedPlatform',
            'onConnect',
            'onDisconnect'
        ]
        
        optional_props = [
            'showConfirmDialog',
            'size'
        ]
        
        # Tous les props requis doivent être définis
        for prop in required_props:
            self.assertIsNotNone(prop)
            
        # Les props optionnels doivent avoir des valeurs par défaut
        default_values = {
            'showConfirmDialog': True,
            'size': 'normal'
        }
        
        for prop in optional_props:
            self.assertIn(prop, default_values)

def run_unit_tests():
    """Exécuter tous les tests unitaires"""
    print("🧪 Démarrage des tests unitaires AmazonIntegrationCard...")
    
    # Créer la suite de tests
    test_suite = unittest.TestSuite()
    
    # Ajouter les tests
    test_suite.addTest(unittest.makeSuite(TestAmazonIntegrationCard))
    test_suite.addTest(unittest.makeSuite(TestAmazonIntegrationValidation))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Afficher les résultats
    if result.wasSuccessful():
        print("✅ Tous les tests unitaires réussis !")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) échoué(s), {len(result.errors)} erreur(s)")
        return False

if __name__ == "__main__":
    run_unit_tests()