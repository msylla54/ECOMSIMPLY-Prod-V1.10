#!/usr/bin/env python3
"""
Test étendu des statistiques dynamiques avec génération de fiche produit
pour vérifier le suivi de l'utilisation mensuelle.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class ExtendedDynamicStatsTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_user_creation(self):
        """Test création d'utilisateur avec données spécifiques"""
        self.log("🔄 Test création utilisateur testdynamique2@example.com...")
        
        user_data = {
            "email": "testdynamique2@example.com",
            "name": "Test Dynamique Extended", 
            "password": "TestPass123!",
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                self.log(f"✅ Utilisateur créé: {self.user_data.get('name')}")
                self.log(f"🆔 User ID: {self.user_data.get('id')}")
                return True
            else:
                self.log(f"❌ Échec création utilisateur: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur création utilisateur: {str(e)}", "ERROR")
            return False
    
    def test_initial_stats(self):
        """Test statistiques initiales (avant génération)"""
        self.log("🔄 Test statistiques initiales...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                
                self.log("📊 Statistiques initiales:")
                self.log(f"  📌 sheets_this_month: {stats.get('sheets_this_month')}")
                self.log(f"  📌 total_sheets: {stats.get('total_sheets')}")
                self.log(f"  📌 account_created: {stats.get('account_created')}")
                
                # Vérifier que les compteurs sont à zéro
                if stats.get('sheets_this_month') == 0 and stats.get('total_sheets') == 0:
                    self.log("✅ Statistiques initiales correctes (zéro)")
                    return True
                else:
                    self.log("❌ Statistiques initiales incorrectes", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Échec API /stats: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test stats initiales: {str(e)}", "ERROR")
            return False
    
    def test_product_sheet_generation(self):
        """Test génération d'une fiche produit"""
        self.log("🔄 Test génération fiche produit...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        product_data = {
            "product_name": "Montre Connectée Test",
            "product_description": "Montre intelligente avec suivi fitness et notifications",
            "generate_image": False,  # Pas d'image pour test rapide
            "number_of_images": 1,
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/generate-sheet", json=product_data, headers=headers)
            
            if response.status_code == 200:
                sheet = response.json()
                
                self.log("✅ Fiche produit générée avec succès")
                self.log(f"  📌 Titre: {sheet.get('generated_title', 'N/A')}")
                self.log(f"  📌 ID: {sheet.get('id', 'N/A')}")
                self.log(f"  📌 IA générée: {sheet.get('is_ai_generated', 'N/A')}")
                
                return True
            else:
                self.log(f"❌ Échec génération fiche: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur génération fiche: {str(e)}", "ERROR")
            return False
    
    def test_updated_stats(self):
        """Test statistiques après génération"""
        self.log("🔄 Test statistiques après génération...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                
                self.log("📊 Statistiques après génération:")
                self.log(f"  📌 sheets_this_month: {stats.get('sheets_this_month')}")
                self.log(f"  📌 total_sheets: {stats.get('total_sheets')}")
                self.log(f"  📌 account_created: {stats.get('account_created')}")
                
                # Vérifier que les compteurs ont été mis à jour
                sheets_this_month = stats.get('sheets_this_month', 0)
                total_sheets = stats.get('total_sheets', 0)
                
                if sheets_this_month == 1 and total_sheets == 1:
                    self.log("✅ Statistiques mises à jour correctement")
                    self.log("✅ Suivi mensuel fonctionnel")
                    self.log("✅ Compteur total fonctionnel")
                    return True
                else:
                    self.log(f"❌ Statistiques incorrectes: mensuel={sheets_this_month}, total={total_sheets}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Échec API /stats: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test stats mises à jour: {str(e)}", "ERROR")
            return False
    
    def run_complete_test(self):
        """Exécute le test complet étendu"""
        self.log("🚀 Début du test étendu des statistiques dynamiques")
        self.log("=" * 70)
        
        # Test 1: Création utilisateur
        if not self.test_user_creation():
            self.log("❌ Test échoué à l'étape création utilisateur", "ERROR")
            return False
        
        self.log("-" * 50)
        
        # Test 2: Statistiques initiales
        if not self.test_initial_stats():
            self.log("❌ Test échoué à l'étape statistiques initiales", "ERROR")
            return False
        
        self.log("-" * 50)
        
        # Test 3: Génération fiche produit
        if not self.test_product_sheet_generation():
            self.log("❌ Test échoué à l'étape génération fiche", "ERROR")
            return False
        
        self.log("-" * 50)
        
        # Test 4: Statistiques mises à jour
        if not self.test_updated_stats():
            self.log("❌ Test échoué à l'étape statistiques mises à jour", "ERROR")
            return False
        
        self.log("=" * 70)
        self.log("🎉 Test étendu des statistiques dynamiques RÉUSSI!")
        self.log("✅ Utilisateur créé avec succès")
        self.log("✅ Statistiques initiales correctes")
        self.log("✅ Génération de fiche fonctionnelle")
        self.log("✅ Mise à jour des statistiques fonctionnelle")
        self.log("✅ Suivi dynamique complet opérationnel")
        
        return True

def main():
    """Point d'entrée principal"""
    tester = ExtendedDynamicStatsTest()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 RÉSULTAT: Test étendu des statistiques dynamiques RÉUSSI")
        exit(0)
    else:
        print("\n💥 RÉSULTAT: Test étendu des statistiques dynamiques ÉCHOUÉ")
        exit(1)

if __name__ == "__main__":
    main()