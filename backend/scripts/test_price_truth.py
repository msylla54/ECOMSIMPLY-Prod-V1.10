#!/usr/bin/env python3
"""
Script de test pour le système PriceTruth
"""
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le chemin backend au PYTHONPATH
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import des modules
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from models.price_truth import PriceTruthDatabase
from services.price_truth_service import PriceTruthService

# Charger les variables d'environnement
load_dotenv()


async def test_price_truth_basic():
    """Test basique du système PriceTruth"""
    print("🧪 Test PriceTruth - Recherche de prix pour 'iPhone 15 Pro'")
    print("=" * 60)
    
    # Connexion MongoDB
    try:
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'ecomsimply_production')]
        print("✅ MongoDB connecté")
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return
    
    # Initialiser PriceTruth
    try:
        price_truth_db = PriceTruthDatabase(db)
        service = PriceTruthService(price_truth_db)
        print("✅ Service PriceTruth initialisé")
    except Exception as e:
        print(f"❌ Erreur PriceTruth: {e}")
        return
    
    # Test de recherche
    print("\n🔍 Recherche prix pour 'iPhone 15 Pro'...")
    print("⏳ Cela peut prendre quelques secondes (scraping de 4 sources)...")
    
    try:
        result = await service.get_price_truth(
            query="iPhone 15 Pro",
            force_refresh=True
        )
        
        if result:
            print(f"\n✅ Prix trouvé !")
            print(f"   💰 Prix consensus: {result.price}€" if result.price else "   ⚠️  Aucun consensus")
            print(f"   📊 Sources consultées: {result.sources_count}")
            print(f"   ✔️  Sources concordantes: {result.agreeing_sources}")
            print(f"   🎯 Status: {result.status.value}")
            print(f"   🕒 Données fraîches: {'Oui' if result.is_fresh else 'Non'}")
            print(f"   📅 Mise à jour: {result.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ Aucun résultat obtenu")
    
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        import traceback
        traceback.print_exc()
    
    # Statistiques finales
    print("\n📈 Statistiques du service:")
    try:
        stats = service.get_service_stats()
        print(f"   📊 Requêtes totales: {stats['stats']['total_queries']}")
        print(f"   ✅ Consensus réussis: {stats['stats']['successful_consensus']}")
        print(f"   ❌ Consensus échoués: {stats['stats']['failed_consensus']}")
        print(f"   📋 Sources interrogées: {stats['stats']['sources_queried']}")
        print(f"   🎯 Taux de succès: {stats['stats']['success_rate']}")
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
    
    # Fermer connexion
    client.close()
    print("\n✅ Test terminé")


async def test_price_truth_detailed():
    """Test détaillé avec affichage des sources"""
    print("🧪 Test PriceTruth Détaillé - Affichage des sources")
    print("=" * 60)
    
    # Connexion MongoDB
    try:
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'ecomsimply_production')]
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return
    
    # Initialiser PriceTruth
    try:
        price_truth_db = PriceTruthDatabase(db)
        service = PriceTruthService(price_truth_db)
    except Exception as e:
        print(f"❌ Erreur PriceTruth: {e}")
        return
    
    # Test produit simple
    query = "Samsung Galaxy S24"
    print(f"\n🔍 Recherche détaillée pour '{query}'...")
    
    try:
        # Effectuer la recherche
        result = await service.get_price_truth(query=query, force_refresh=True)
        
        if result:
            print(f"\n📊 RÉSULTATS POUR '{query.upper()}'")
            print("-" * 50)
            print(f"💰 Prix final: {result.price}€" if result.price else "💰 Prix final: Non disponible")
            print(f"🎯 Status: {result.status.value}")
            print(f"📈 Sources consultées: {result.sources_count}")
            print(f"✅ Sources concordantes: {result.agreeing_sources}")
            
            # Récupérer les détails depuis la DB
            price_truth = await service.db.get_price_truth(query)
            if not price_truth:
                price_truth = await service.db.search_by_query(query)
            
            if price_truth and price_truth.sources:
                print(f"\n📋 DÉTAIL DES SOURCES:")
                print("-" * 30)
                for i, source in enumerate(price_truth.sources, 1):
                    status_icon = "✅" if source.success else "❌"
                    price_text = f"{float(source.price)}€" if source.price else "N/A"
                    print(f"{i}. {status_icon} {source.name.upper()}")
                    print(f"   💰 Prix: {price_text}")
                    print(f"   🔗 URL: {source.url[:60]}...")
                    print(f"   🎯 Sélecteur: {source.selector}")
                    if not source.success and source.error_message:
                        print(f"   ❌ Erreur: {source.error_message[:80]}...")
                    print()
            
            if price_truth and price_truth.consensus:
                print(f"📊 CONSENSUS:")
                print("-" * 20)
                print(f"🧮 Méthode: {price_truth.consensus.method}")
                print(f"📍 Prix médian: {float(price_truth.consensus.median_price)}€" if price_truth.consensus.median_price else "📍 Prix médian: N/A")
                print(f"📏 Écart-type: {price_truth.consensus.stdev:.2f}" if price_truth.consensus.stdev else "📏 Écart-type: N/A")
                print(f"🎯 Tolérance: {price_truth.consensus.tolerance_pct}%")
                if price_truth.consensus.outliers:
                    print(f"⚠️  Outliers détectés: {', '.join(price_truth.consensus.outliers)}")
        else:
            print("❌ Aucun résultat")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    client.close()
    print("\n✅ Test détaillé terminé")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "detailed":
        asyncio.run(test_price_truth_detailed())
    else:
        asyncio.run(test_price_truth_basic())