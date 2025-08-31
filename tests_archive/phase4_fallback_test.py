#!/usr/bin/env python3
"""
ECOMSIMPLY Backend Testing Suite - PHASE 4 FALLBACK FIELDS VERIFICATION
Test rapide pour vérifier que les champs de fallback sont présents dans les réponses API.

OBJECTIF: Vérifier rapidement que les champs model_used, generation_method, et fallback_level 
sont maintenant présents dans les réponses API.

TEST À EFFECTUER:
1. Créer utilisateur test
2. Générer 1 fiche produit simple
3. Vérifier présence des champs :
   - model_used (doit être "gpt-4o-mini" ou autre)
   - generation_method (doit être "openai_primary" ou autre)  
   - fallback_level (doit être 1 ou autre)

CRITÈRE DE SUCCÈS:
✅ Les 3 champs sont présents et non-null dans la réponse API

Produit test simple : "Smartphone Samsung Galaxy" avec description "Téléphone Android performant"
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class Phase4FallbackTester:
    def __init__(self):
        self.session = None
        self.test_user = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes timeout
        )
        print("✅ Session HTTP initialisée")
        return True
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self, token: str):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def create_test_user(self) -> Dict:
        """Create a test user for Phase 4 testing"""
        
        user_data = {
            "email": f"test_phase4_{int(time.time())}@ecomsimply.test",
            "name": "Test User Phase 4",
            "password": "TestPassword123!"
        }
        
        print(f"👤 Création utilisateur test Phase 4...")
        print(f"   📧 Email: {user_data['email']}")
        
        try:
            # Register user
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=user_data) as response:
                if response.status == 200:
                    register_result = await response.json()
                    print(f"✅ Utilisateur créé avec succès")
                    
                    # Login to get token
                    login_data = {
                        "email": user_data["email"],
                        "password": user_data["password"]
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                        if login_response.status == 200:
                            login_result = await login_response.json()
                            token = login_result.get("token")
                            
                            user_info = {
                                "email": user_data["email"],
                                "token": token,
                                "plan": "gratuit"
                            }
                            
                            self.test_user = user_info
                            print(f"✅ Authentification réussie - Token obtenu")
                            return user_info
                        else:
                            error_text = await login_response.text()
                            print(f"❌ Échec login: {login_response.status} - {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    print(f"❌ Échec création utilisateur: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Exception création utilisateur: {str(e)}")
            return None
    
    async def test_fallback_fields_verification(self):
        """
        TEST PRINCIPAL: Vérification des champs de fallback
        Générer une fiche produit et vérifier la présence des champs requis
        """
        print("\n🧪 TEST PHASE 4: Vérification des champs de fallback")
        print("=" * 70)
        
        if not self.test_user:
            print("❌ Utilisateur test non disponible")
            return False
        
        # Produit test simple comme spécifié
        test_product = {
            "product_name": "Smartphone Samsung Galaxy",
            "product_description": "Téléphone Android performant",
            "generate_image": True,
            "number_of_images": 1,
            "language": "fr",
            "category": "électronique",
            "image_style": "studio"
        }
        
        print(f"📱 Test produit: {test_product['product_name']}")
        print(f"📝 Description: {test_product['product_description']}")
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_product,
                headers=self.get_auth_headers(self.test_user["token"])
            ) as response:
                
                generation_time = time.time() - start_time
                status = response.status
                
                print(f"⏱️ Temps de génération: {generation_time:.2f}s")
                print(f"📊 Status HTTP: {status}")
                
                if status == 200:
                    result = await response.json()
                    
                    print(f"\n🔍 VÉRIFICATION DES CHAMPS DE FALLBACK:")
                    print("-" * 50)
                    
                    # Vérification des champs de fallback requis
                    fallback_fields = {
                        "model_used": result.get("model_used"),
                        "generation_method": result.get("generation_method"),
                        "fallback_level": result.get("fallback_level")
                    }
                    
                    # Affichage des résultats
                    all_fields_present = True
                    for field_name, field_value in fallback_fields.items():
                        if field_value is not None:
                            print(f"✅ {field_name}: {field_value}")
                        else:
                            print(f"❌ {field_name}: MANQUANT (None)")
                            all_fields_present = False
                    
                    print("-" * 50)
                    
                    # Vérification des champs de base pour contexte
                    print(f"\n📋 INFORMATIONS CONTEXTUELLES:")
                    print(f"   📝 Titre généré: {result.get('generated_title', 'N/A')[:50]}...")
                    print(f"   📄 Description: {len(result.get('marketing_description', ''))} caractères")
                    print(f"   🔧 Features: {len(result.get('key_features', []))} éléments")
                    print(f"   🏷️ SEO Tags: {len(result.get('seo_tags', []))} tags")
                    print(f"   🖼️ Images: {len(result.get('generated_images', []))} générées")
                    
                    # Résultat final
                    if all_fields_present:
                        print(f"\n🎉 SUCCÈS PHASE 4: Tous les champs de fallback sont présents!")
                        print(f"   ✅ model_used: {fallback_fields['model_used']}")
                        print(f"   ✅ generation_method: {fallback_fields['generation_method']}")
                        print(f"   ✅ fallback_level: {fallback_fields['fallback_level']}")
                        
                        # Validation des valeurs
                        valid_values = True
                        if not isinstance(fallback_fields['model_used'], str) or not fallback_fields['model_used']:
                            print(f"   ⚠️ model_used devrait être une chaîne non-vide")
                            valid_values = False
                        
                        if not isinstance(fallback_fields['generation_method'], str) or not fallback_fields['generation_method']:
                            print(f"   ⚠️ generation_method devrait être une chaîne non-vide")
                            valid_values = False
                        
                        if not isinstance(fallback_fields['fallback_level'], int) or fallback_fields['fallback_level'] < 1:
                            print(f"   ⚠️ fallback_level devrait être un entier >= 1")
                            valid_values = False
                        
                        if valid_values:
                            print(f"   🎯 Toutes les valeurs sont valides et conformes!")
                        
                        return True
                    else:
                        print(f"\n❌ ÉCHEC PHASE 4: Des champs de fallback sont manquants!")
                        print(f"   🔧 Les champs suivants doivent être ajoutés à la réponse API:")
                        for field_name, field_value in fallback_fields.items():
                            if field_value is None:
                                print(f"      - {field_name}")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR GÉNÉRATION: {status}")
                    print(f"📄 Détails: {error_text[:300]}")
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION GÉNÉRATION: {str(e)}")
            return False
    
    async def run_phase4_test(self):
        """Run Phase 4 fallback fields verification test"""
        print("🚀 ECOMSIMPLY - TEST RAPIDE PHASE 4")
        print("=" * 70)
        print("🎯 OBJECTIF: Vérification des champs de fallback")
        print("📋 CHAMPS À VÉRIFIER: model_used, generation_method, fallback_level")
        print("=" * 70)
        
        # Setup
        if not await self.setup_session():
            print("❌ Failed to setup test session")
            return False
        
        try:
            # Create test user
            print("\n🔧 ÉTAPE 1: Création utilisateur test")
            user_info = await self.create_test_user()
            if not user_info:
                print("❌ Impossible de créer l'utilisateur test")
                return False
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Run fallback fields test
            print("\n🔧 ÉTAPE 2: Test génération avec vérification des champs")
            test_result = await self.test_fallback_fields_verification()
            
            # Final summary
            print("\n" + "=" * 70)
            print("🏁 RÉSUMÉ FINAL - PHASE 4 FALLBACK FIELDS")
            print("=" * 70)
            
            if test_result:
                print("🎉 RÉSULTAT: SUCCÈS COMPLET")
                print("✅ Les 3 champs de fallback sont présents et non-null")
                print("✅ model_used: Modèle IA utilisé identifié")
                print("✅ generation_method: Méthode de génération spécifiée")
                print("✅ fallback_level: Niveau de fallback indiqué")
                print("\n🚀 La Phase 4 est PRODUCTION-READY!")
            else:
                print("❌ RÉSULTAT: ÉCHEC")
                print("❌ Un ou plusieurs champs de fallback sont manquants")
                print("🔧 Correction requise dans le backend pour ajouter les champs manquants")
                print("\n⚠️ La Phase 4 nécessite des corrections avant production")
            
            return test_result
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = Phase4FallbackTester()
    success = await tester.run_phase4_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())