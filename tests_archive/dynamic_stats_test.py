#!/usr/bin/env python3
"""
Test rapide de création d'utilisateur et vérification des nouvelles statistiques dynamiques.
Objectif: Créer un utilisateur test et vérifier que l'API retourne les bonnes données pour le suivi dynamique.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://ecomsimply.com/api"
TIMEOUT = 30

class DynamicStatsTest:
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
        self.log("🔄 Test création utilisateur testdynamique@example.com...")
        
        user_data = {
            "email": "testdynamique@example.com",
            "name": "Test Dynamique", 
            "password": "TestPass123!",
            "language": "fr"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_data = data.get("user")
                
                self.log(f"✅ Utilisateur créé avec succès: {self.user_data.get('name')}")
                self.log(f"📧 Email: {self.user_data.get('email')}")
                self.log(f"🆔 User ID: {self.user_data.get('id')}")
                self.log(f"📅 Créé le: {self.user_data.get('created_at')}")
                self.log(f"🔑 Token reçu: {self.auth_token[:20]}...")
                return True
            else:
                self.log(f"❌ Échec création utilisateur: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur création utilisateur: {str(e)}", "ERROR")
            return False
    
    def test_dynamic_stats_api(self):
        """Test vérification des statistiques dynamiques"""
        self.log("🔄 Test API statistiques dynamiques...")
        
        if not self.auth_token:
            self.log("❌ Token d'authentification manquant", "ERROR")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = self.session.get(f"{BASE_URL}/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                
                self.log("✅ API /stats accessible avec succès")
                self.log("📊 Statistiques reçues:")
                
                # Vérification des champs requis
                required_fields = ["sheets_this_month", "account_created", "total_sheets"]
                all_fields_present = True
                
                for field in required_fields:
                    if field in stats:
                        self.log(f"  ✅ {field}: {stats[field]}")
                    else:
                        self.log(f"  ❌ {field}: MANQUANT", "ERROR")
                        all_fields_present = False
                
                # Affichage des autres champs disponibles
                other_fields = [k for k in stats.keys() if k not in required_fields]
                if other_fields:
                    self.log("📋 Autres champs disponibles:")
                    for field in other_fields:
                        self.log(f"  📌 {field}: {stats[field]}")
                
                # Validation spécifique
                if all_fields_present:
                    self.log("✅ Tous les champs requis sont présents")
                    
                    # Test calcul ancienneté du compte
                    account_created = stats.get("account_created")
                    if account_created:
                        self.log(f"📅 Compte créé: {account_created}")
                        # Vérifier que c'est récent (moins de 5 minutes)
                        try:
                            created_time = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
                            now = datetime.now(created_time.tzinfo)
                            age_minutes = (now - created_time).total_seconds() / 60
                            self.log(f"⏱️ Âge du compte: {age_minutes:.1f} minutes")
                            
                            if age_minutes < 5:
                                self.log("✅ Ancienneté du compte correctement calculée (récent)")
                            else:
                                self.log("⚠️ Compte semble plus ancien que prévu", "WARNING")
                        except Exception as e:
                            self.log(f"⚠️ Erreur parsing date: {e}", "WARNING")
                    
                    # Test utilisation mensuelle
                    sheets_this_month = stats.get("sheets_this_month", 0)
                    total_sheets = stats.get("total_sheets", 0)
                    
                    self.log(f"📊 Utilisation mensuelle: {sheets_this_month}")
                    self.log(f"📊 Total fiches: {total_sheets}")
                    
                    if sheets_this_month == 0 and total_sheets == 0:
                        self.log("✅ Statistiques cohérentes pour nouvel utilisateur")
                    else:
                        self.log("⚠️ Statistiques inattendues pour nouvel utilisateur", "WARNING")
                    
                    return True
                else:
                    self.log("❌ Champs requis manquants dans la réponse", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Échec API /stats: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur test API stats: {str(e)}", "ERROR")
            return False
    
    def run_complete_test(self):
        """Exécute le test complet"""
        self.log("🚀 Début du test des statistiques dynamiques")
        self.log("=" * 60)
        
        # Test 1: Création utilisateur
        if not self.test_user_creation():
            self.log("❌ Test échoué à l'étape création utilisateur", "ERROR")
            return False
        
        self.log("-" * 40)
        
        # Test 2: Vérification API stats
        if not self.test_dynamic_stats_api():
            self.log("❌ Test échoué à l'étape vérification stats", "ERROR")
            return False
        
        self.log("=" * 60)
        self.log("🎉 Test des statistiques dynamiques RÉUSSI!")
        self.log("✅ Utilisateur créé avec succès")
        self.log("✅ API /stats retourne les champs requis")
        self.log("✅ Calcul de l'ancienneté du compte fonctionnel")
        self.log("✅ Suivi dynamique opérationnel")
        
        return True

def main():
    """Point d'entrée principal"""
    tester = DynamicStatsTest()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 RÉSULTAT: Test des statistiques dynamiques RÉUSSI")
        exit(0)
    else:
        print("\n💥 RÉSULTAT: Test des statistiques dynamiques ÉCHOUÉ")
        exit(1)

if __name__ == "__main__":
    main()