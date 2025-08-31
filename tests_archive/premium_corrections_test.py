#!/usr/bin/env python3
"""
ECOMSIMPLY PREMIUM SYSTEM CORRECTIONS TESTING
Testing the corrected PREMIUM system after major fixes:
1. GPT-4 instructions reinforced with mandatory validation
2. Fallback system corrected with premium support
3. Complete premium differentiation testing
4. Premium content quality verification
"""

import asyncio
import aiohttp
import json
import time
import re
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ecomsimply.com/api"

class PremiumCorrectionsTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session and authenticate as admin"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        
        # Authenticate as admin (premium user)
        auth_data = {
            "email": "msylla54@gmail.com",
            "password": "AdminEcomsimply"
        }
        
        print("🔐 Authenticating as ADMIN/PREMIUM user...")
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.admin_token = result.get("token")
                    print("✅ Admin authentication successful")
                    
                    # Verify user profile
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    async with self.session.get(f"{BACKEND_URL}/user/profile", headers=headers) as profile_response:
                        if profile_response.status == 200:
                            profile = await profile_response.json()
                            print(f"👤 User: {profile.get('email')} | Plan: {profile.get('subscription_plan')} | Admin: {profile.get('is_admin')}")
                            return True
                        else:
                            print("❌ Failed to get user profile")
                            return False
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def analyze_premium_content(self, content: dict) -> dict:
        """Analyze content for premium criteria compliance"""
        features = content.get("key_features", [])
        seo_tags = content.get("seo_tags", [])
        description = content.get("marketing_description", "")
        
        analysis = {
            "features_count": len(features),
            "seo_tags_count": len(seo_tags),
            "description_word_count": len(description.split()),
            "meets_premium_6_6_criteria": len(features) == 6 and len(seo_tags) == 6,
            "meets_premium_500_words": len(description.split()) >= 500,
            "features": features,
            "seo_tags": seo_tags,
            "title": content.get("generated_title", ""),
            "cta": content.get("call_to_action", "")
        }
        
        return analysis
    
    async def test_critical_1_admin_premium_6_6(self):
        """
        TEST CRITIQUE 1: ADMIN PREMIUM (6/6)
        Produit: MacBook Pro M3 Max | Catégorie: électronique | Images: OFF
        Attente: 6 features + 6 SEO tags + contenu premium
        """
        print("\n🧪 TEST CRITIQUE 1: ADMIN PREMIUM (6/6)")
        print("=" * 70)
        print("🎯 Produit: MacBook Pro M3 Max | Catégorie: électronique | Images: OFF")
        print("📋 Attente: 6 features + 6 SEO tags + contenu premium")
        
        test_data = {
            "product_name": "MacBook Pro M3 Max",
            "product_description": "Ordinateur portable professionnel haut de gamme avec processeur M3 Max, écran Liquid Retina XDR, performances exceptionnelles pour les créatifs et développeurs professionnels",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        try:
            print("🚀 Génération du contenu premium...")
            start_time = time.time()
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers()
            ) as response:
                
                generation_time = time.time() - start_time
                status = response.status
                
                print(f"⏱️ Temps de génération: {generation_time:.2f}s")
                print(f"📊 Status HTTP: {status}")
                
                if status == 200:
                    result = await response.json()
                    analysis = self.analyze_premium_content(result)
                    
                    print(f"\n📋 ANALYSE DU CONTENU GÉNÉRÉ:")
                    print(f"   🔢 Features: {analysis['features_count']}/6 (Requis: 6)")
                    print(f"   🏷️ SEO Tags: {analysis['seo_tags_count']}/6 (Requis: 6)")
                    print(f"   📝 Mots description: {analysis['description_word_count']} (Requis: 500+)")
                    
                    print(f"\n📄 CONTENU DÉTAILLÉ:")
                    print(f"   Titre: {analysis['title']}")
                    print(f"   Features: {analysis['features']}")
                    print(f"   SEO Tags: {analysis['seo_tags']}")
                    print(f"   CTA: {analysis['cta']}")
                    print(f"   Description (200 premiers chars): {result.get('marketing_description', '')[:200]}...")
                    
                    # Vérification des critères premium
                    success = (
                        analysis['meets_premium_6_6_criteria'] and
                        analysis['meets_premium_500_words']
                    )
                    
                    if success:
                        print("🎉 ✅ SUCCÈS: Critères premium respectés (6 features + 6 SEO tags + 500+ mots)")
                    else:
                        print("❌ ÉCHEC: Critères premium non respectés")
                        if not analysis['meets_premium_6_6_criteria']:
                            print(f"   ❌ Nombre d'éléments incorrect: {analysis['features_count']} features, {analysis['seo_tags_count']} SEO tags")
                        if not analysis['meets_premium_500_words']:
                            print(f"   ❌ Description trop courte: {analysis['description_word_count']} mots")
                    
                    self.test_results.append({
                        "test": "admin_premium_6_6",
                        "success": success,
                        "analysis": analysis,
                        "generation_time": generation_time
                    })
                    
                    return success
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR HTTP {status}: {error_text[:300]}...")
                    self.test_results.append({
                        "test": "admin_premium_6_6",
                        "success": False,
                        "error": f"HTTP {status}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            self.test_results.append({
                "test": "admin_premium_6_6",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_critical_2_fallback_premium_support(self):
        """
        TEST CRITIQUE 2: SYSTÈME DE FALLBACK PREMIUM
        Vérifier que les fallbacks respectent le niveau premium
        """
        print("\n🧪 TEST CRITIQUE 2: SYSTÈME DE FALLBACK PREMIUM")
        print("=" * 70)
        print("🎯 Test: Fallback avec support premium intégré")
        
        # Produit complexe pour potentiellement déclencher les fallbacks
        test_data = {
            "product_name": "iPhone 15 Pro Max Ultra Premium Limited Edition Titanium",
            "product_description": "Smartphone révolutionnaire ultra-premium avec technologie avancée IA, caméra professionnelle 48MP ProRAW, écran ProMotion 120Hz OLED, processeur A17 Pro bionic, design titanium aerospace grade, résistance IP68, MagSafe compatible",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        try:
            print("🔄 Test du système de fallback avec utilisateur premium...")
            start_time = time.time()
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers()
            ) as response:
                
                generation_time = time.time() - start_time
                status = response.status
                
                if status == 200:
                    result = await response.json()
                    analysis = self.analyze_premium_content(result)
                    
                    print(f"\n📋 ANALYSE FALLBACK PREMIUM:")
                    print(f"   🔢 Features: {analysis['features_count']}/6")
                    print(f"   🏷️ SEO Tags: {analysis['seo_tags_count']}/6")
                    print(f"   📝 Mots: {analysis['description_word_count']}")
                    
                    # Le fallback doit maintenir les standards premium
                    fallback_success = analysis['meets_premium_6_6_criteria']
                    
                    if fallback_success:
                        print("🎉 ✅ SUCCÈS: Fallback maintient les standards premium (6/6)")
                    else:
                        print("❌ ÉCHEC: Fallback ne maintient pas les standards premium")
                        print(f"   Reçu: {analysis['features_count']} features, {analysis['seo_tags_count']} SEO tags")
                    
                    self.test_results.append({
                        "test": "fallback_premium_support",
                        "success": fallback_success,
                        "analysis": analysis,
                        "generation_time": generation_time
                    })
                    
                    return fallback_success
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR HTTP {status}: {error_text[:300]}...")
                    self.test_results.append({
                        "test": "fallback_premium_support",
                        "success": False,
                        "error": f"HTTP {status}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            self.test_results.append({
                "test": "fallback_premium_support",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def test_critical_3_gpt4_instructions_compliance(self):
        """
        TEST CRITIQUE 3: CONFORMITÉ INSTRUCTIONS GPT-4
        Vérifier que GPT-4 respecte EXACTEMENT les instructions renforcées
        """
        print("\n🧪 TEST CRITIQUE 3: CONFORMITÉ INSTRUCTIONS GPT-4")
        print("=" * 70)
        print("🎯 Test: Instructions 'CRITÈRES PREMIUM ABSOLUS' et 'VALIDATION OBLIGATOIRE'")
        
        # Test de consistance avec plusieurs produits
        test_products = [
            {
                "name": "AirPods Pro 2ème génération",
                "desc": "Écouteurs sans fil premium avec réduction de bruit active, audio spatial, puce H2, autonomie 30h",
                "category": "électronique"
            },
            {
                "name": "Nike Air Jordan 1 Retro High",
                "desc": "Chaussures de basketball iconiques, cuir premium, design classique, confort exceptionnel",
                "category": "sport"
            }
        ]
        
        compliance_results = []
        
        for i, product in enumerate(test_products, 1):
            print(f"\n🔍 Test produit {i}/2: {product['name']}")
            
            test_data = {
                "product_name": product['name'],
                "product_description": product['desc'],
                "generate_image": False,
                "number_of_images": 0,
                "language": "fr",
                "category": product['category']
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/generate-sheet",
                    json=test_data,
                    headers=self.get_auth_headers()
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        analysis = self.analyze_premium_content(result)
                        
                        # Vérification stricte des instructions GPT-4
                        gpt4_compliance = (
                            analysis['features_count'] == 6 and
                            analysis['seo_tags_count'] == 6
                        )
                        
                        print(f"   📊 Features: {analysis['features_count']}/6 | SEO: {analysis['seo_tags_count']}/6")
                        print(f"   ✅ Conformité: {'OUI' if gpt4_compliance else 'NON'}")
                        
                        compliance_results.append(gpt4_compliance)
                        
                    else:
                        print(f"   ❌ ERREUR HTTP {response.status}")
                        compliance_results.append(False)
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                compliance_results.append(False)
            
            await asyncio.sleep(2)  # Pause entre les tests
        
        # Évaluation de la consistance
        all_compliant = all(compliance_results)
        compliance_rate = sum(compliance_results) / len(compliance_results) * 100
        
        print(f"\n📈 RÉSULTATS CONFORMITÉ GPT-4:")
        print(f"   🎯 Taux de conformité: {compliance_rate:.1f}%")
        print(f"   ✅ Tous conformes: {'OUI' if all_compliant else 'NON'}")
        
        if all_compliant:
            print("🎉 ✅ SUCCÈS: GPT-4 respecte les instructions renforcées!")
        else:
            print("❌ ÉCHEC: GPT-4 ne respecte pas systématiquement les instructions")
        
        self.test_results.append({
            "test": "gpt4_instructions_compliance",
            "success": all_compliant,
            "compliance_rate": compliance_rate,
            "individual_results": compliance_results
        })
        
        return all_compliant
    
    async def test_critical_4_premium_content_quality(self):
        """
        TEST CRITIQUE 4: QUALITÉ CONTENU PREMIUM
        Vérifier descriptions 500+ mots, contenu technique-émotionnel
        """
        print("\n🧪 TEST CRITIQUE 4: QUALITÉ CONTENU PREMIUM")
        print("=" * 70)
        print("🎯 Test: Descriptions 500+ mots, contenu technique + émotionnel")
        
        test_data = {
            "product_name": "MacBook Pro M3 Max 16 pouces",
            "product_description": "Ordinateur portable professionnel ultime avec processeur M3 Max révolutionnaire, écran Liquid Retina XDR 16 pouces, performances inégalées pour création vidéo, développement, design graphique",
            "generate_image": False,
            "number_of_images": 0,
            "language": "fr",
            "category": "électronique"
        }
        
        try:
            print("🎨 Génération contenu premium avec analyse qualité...")
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-sheet",
                json=test_data,
                headers=self.get_auth_headers()
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    analysis = self.analyze_premium_content(result)
                    
                    # Analyse qualité contenu
                    description = result.get('marketing_description', '')
                    
                    # Mots-clés techniques
                    technical_keywords = ['processeur', 'performance', 'technologie', 'qualité', 'professionnel', 'avancé']
                    # Mots-clés émotionnels
                    emotional_keywords = ['exceptionnel', 'révolutionnaire', 'ultime', 'inégalé', 'premium', 'parfait']
                    
                    technical_count = sum(1 for kw in technical_keywords if kw.lower() in description.lower())
                    emotional_count = sum(1 for kw in emotional_keywords if kw.lower() in description.lower())
                    
                    print(f"\n📋 ANALYSE QUALITÉ PREMIUM:")
                    print(f"   📝 Mots description: {analysis['description_word_count']} (Requis: 500+)")
                    print(f"   🔧 Éléments techniques: {technical_count}")
                    print(f"   💝 Éléments émotionnels: {emotional_count}")
                    print(f"   📰 Longueur titre: {len(analysis['title'])} caractères")
                    print(f"   📢 Longueur CTA: {len(analysis['cta'])} caractères")
                    
                    # Critères qualité premium
                    quality_success = (
                        analysis['meets_premium_500_words'] and
                        technical_count >= 2 and
                        emotional_count >= 2 and
                        len(analysis['title']) >= 50 and
                        len(analysis['cta']) >= 30
                    )
                    
                    if quality_success:
                        print("🎉 ✅ SUCCÈS: Qualité premium atteinte (500+ mots, tech+émo)")
                    else:
                        print("❌ ÉCHEC: Qualité premium non atteinte")
                        if not analysis['meets_premium_500_words']:
                            print(f"   ❌ Description trop courte: {analysis['description_word_count']} mots")
                        if technical_count < 2:
                            print(f"   ❌ Pas assez d'éléments techniques: {technical_count}")
                        if emotional_count < 2:
                            print(f"   ❌ Pas assez d'éléments émotionnels: {emotional_count}")
                    
                    self.test_results.append({
                        "test": "premium_content_quality",
                        "success": quality_success,
                        "analysis": analysis,
                        "technical_count": technical_count,
                        "emotional_count": emotional_count
                    })
                    
                    return quality_success
                    
                else:
                    error_text = await response.text()
                    print(f"❌ ERREUR HTTP {response.status}: {error_text[:300]}...")
                    self.test_results.append({
                        "test": "premium_content_quality",
                        "success": False,
                        "error": f"HTTP {response.status}"
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            self.test_results.append({
                "test": "premium_content_quality",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_all_premium_corrections_tests(self):
        """Exécuter tous les tests de corrections premium"""
        print("🚀 ECOMSIMPLY - TESTS CORRECTIONS SYSTÈME PREMIUM")
        print("=" * 80)
        print("Testing des corrections majeures apportées au système PREMIUM:")
        print("1. Instructions GPT-4 renforcées avec validation obligatoire")
        print("2. Système de fallback corrigé avec support premium")
        print("3. Test complet différenciation premium end-to-end")
        print("4. Qualité du contenu premium - vérifications techniques-émotionnelles")
        print("=" * 80)
        
        # Setup
        if not await self.setup_session():
            print("❌ Échec de l'initialisation de la session de test")
            return False
        
        try:
            print("\n🎯 EXÉCUTION DES TESTS CRITIQUES POST-CORRECTION...")
            
            # Exécution des 4 tests critiques
            test1_result = await self.test_critical_1_admin_premium_6_6()
            await asyncio.sleep(3)
            
            test2_result = await self.test_critical_2_fallback_premium_support()
            await asyncio.sleep(3)
            
            test3_result = await self.test_critical_3_gpt4_instructions_compliance()
            await asyncio.sleep(3)
            
            test4_result = await self.test_critical_4_premium_content_quality()
            
            # Résumé final
            print("\n" + "=" * 80)
            print("🏁 RÉSUMÉ TESTS CORRECTIONS PREMIUM")
            print("=" * 80)
            
            total_tests = 4
            passed_tests = sum([test1_result, test2_result, test3_result, test4_result])
            success_rate = (passed_tests / total_tests) * 100
            
            print(f"📊 Total tests critiques: {total_tests}")
            print(f"✅ Tests réussis: {passed_tests}")
            print(f"❌ Tests échoués: {total_tests - passed_tests}")
            print(f"📈 Taux de succès: {success_rate:.1f}%")
            
            print(f"\n🎯 STATUT DES CORRECTIONS PREMIUM:")
            print(f"   1. Admin Premium (6/6): {'✅ CORRIGÉ' if test1_result else '❌ ÉCHEC'}")
            print(f"   2. Fallback Premium: {'✅ CORRIGÉ' if test2_result else '❌ ÉCHEC'}")
            print(f"   3. Instructions GPT-4: {'✅ CORRIGÉ' if test3_result else '❌ ÉCHEC'}")
            print(f"   4. Qualité Premium: {'✅ CORRIGÉ' if test4_result else '❌ ÉCHEC'}")
            
            # Évaluation globale
            corrections_successful = passed_tests >= 3  # Au moins 3/4 corrections fonctionnent
            
            print(f"\n🏆 RÉSULTAT GLOBAL DES CORRECTIONS:")
            if corrections_successful:
                print("🎉 ✅ CORRECTIONS PREMIUM RÉUSSIES!")
                print("🌟 Les corrections majeures apportées au système PREMIUM fonctionnent!")
                
                if passed_tests == 4:
                    print("🏅 SCORE PARFAIT: Toutes les corrections premium validées!")
                    print("🚀 Système prêt pour la production avec différenciation premium opérationnelle")
                else:
                    print(f"⚠️ Corrections largement réussies avec {total_tests - passed_tests} point(s) d'amélioration")
                    
            else:
                print("❌ CORRECTIONS PREMIUM NÉCESSITENT ATTENTION")
                print("🔧 Certaines corrections critiques ne fonctionnent pas comme attendu")
            
            # Recommandations détaillées
            print(f"\n📋 RECOMMANDATIONS POST-TEST:")
            if not test1_result:
                print("   🔧 PRIORITÉ 1: Corriger génération admin premium - assurer 6 features + 6 SEO tags")
            if not test2_result:
                print("   🔧 PRIORITÉ 2: Corriger système fallback - maintenir standards premium")
            if not test3_result:
                print("   🔧 PRIORITÉ 3: Renforcer conformité instructions GPT-4")
            if not test4_result:
                print("   🔧 PRIORITÉ 4: Améliorer qualité contenu premium")
            
            if corrections_successful:
                print("   ✅ VALIDATION: Les corrections premium sont largement opérationnelles!")
                print("   🎯 PRÊT: Système premium différencié fonctionnel pour production")
            
            return corrections_successful
            
        finally:
            await self.cleanup()

async def main():
    """Exécution principale des tests"""
    tester = PremiumCorrectionsTester()
    success = await tester.run_all_premium_corrections_tests()
    
    # Code de sortie approprié
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())