#!/usr/bin/env python3
"""
Vérification détaillée des témoignages selon la review request
Vérifier que les 4 témoignages spécifiques sont présents avec la bonne structure
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://ecomsimply.com/api"

async def verify_testimonials():
    """Vérification détaillée des témoignages"""
    print("🔍 VÉRIFICATION DÉTAILLÉE DES TÉMOIGNAGES")
    print("=" * 60)
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Test endpoint public
        print("\n📋 ENDPOINT PUBLIC: /api/testimonials")
        try:
            url = f"{BACKEND_URL}/testimonials"
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        testimonials = data
                    elif isinstance(data, dict) and 'testimonials' in data:
                        testimonials = data['testimonials']
                    else:
                        testimonials = []
                    
                    print(f"Nombre total de témoignages: {len(testimonials)}")
                    
                    # Filtrer les témoignages approuvés
                    approved = [t for t in testimonials if t.get('status') == 'approved']
                    print(f"Témoignages approuvés: {len(approved)}")
                    
                    # Vérifier les noms spécifiques mentionnés dans la review
                    expected_names = ['Marie L.', 'Jean-Pierre M.', 'Sophie D.', 'Laurent K.']
                    found_names = []
                    
                    print("\n📝 DÉTAILS DES TÉMOIGNAGES APPROUVÉS:")
                    for i, testimonial in enumerate(approved, 1):
                        name = testimonial.get('customer_name', 'N/A')
                        rating = testimonial.get('rating', 'N/A')
                        message = testimonial.get('message', 'N/A')
                        status = testimonial.get('status', 'N/A')
                        
                        print(f"\n{i}. {name}")
                        print(f"   Rating: {rating}/5")
                        print(f"   Status: {status}")
                        print(f"   Message: {message[:100]}...")
                        
                        if name in expected_names:
                            found_names.append(name)
                    
                    print(f"\n✅ NOMS ATTENDUS TROUVÉS: {found_names}")
                    print(f"✅ NOMS MANQUANTS: {set(expected_names) - set(found_names)}")
                    
                    # Vérifier la structure des données
                    print(f"\n🔍 VÉRIFICATION STRUCTURE:")
                    if approved:
                        sample = approved[0]
                        required_fields = ['customer_name', 'rating', 'message']
                        
                        for field in required_fields:
                            if field in sample:
                                print(f"✅ {field}: présent")
                            else:
                                print(f"❌ {field}: manquant")
                        
                        print(f"\n📊 CHAMPS DISPONIBLES: {list(sample.keys())}")
                    
                    if len(found_names) >= 4:
                        print(f"\n🎉 SUCCÈS: {len(found_names)}/4 témoignages requis trouvés!")
                    else:
                        print(f"\n⚠️ ATTENTION: Seulement {len(found_names)}/4 témoignages requis trouvés")
                        
                else:
                    print(f"❌ Erreur HTTP: {response.status}")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def main():
    await verify_testimonials()

if __name__ == "__main__":
    asyncio.run(main())