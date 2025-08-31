#!/usr/bin/env python3
"""
Script démo - Pipeline Scraping Sémantique ECOMSIMPLY
Usage: python scripts/semantic_demo.py <URL>
"""

import asyncio
import sys
import json
import time
from typing import Optional

# Add backend src to path  
sys.path.append('/app/backend/src')

from scraping.transport import RequestCoordinator
from scraping.semantic import SemanticOrchestrator, ProductDTO


class SemanticDemo:
    """Démonstration du pipeline sémantique complet"""
    
    def __init__(self):
        self.coordinator = None
        self.orchestrator = None
    
    async def setup(self):
        """Initialisation avec transport robuste"""
        print("🔧 Initialisation transport layer...")
        
        self.coordinator = RequestCoordinator(
            max_per_host=3,      # Contrainte concurrence
            timeout_s=10.0,      # Contrainte timeout  
            cache_ttl_s=180      # Contrainte cache TTL
        )
        
        self.orchestrator = SemanticOrchestrator(self.coordinator)
        print("✅ Transport layer initialisé")
    
    async def cleanup(self):
        """Nettoyage ressources"""
        if self.coordinator:
            await self.coordinator.close()
    
    async def scrape_product_demo(self, url: str) -> Optional[dict]:
        """Démonstration scraping sémantique avec logs détaillés"""
        
        print(f"\n🔍 SCRAPING SÉMANTIQUE : {url}")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Pipeline sémantique complet
            product_dto = await self.orchestrator.scrape_product_semantic(url)
            
            duration = time.time() - start_time
            
            if not product_dto:
                print("❌ Échec scraping - URL inaccessible ou contenu invalide")
                return None
            
            print(f"✅ Scraping réussi en {duration:.2f}s")
            print()
            
            # Affichage résultats structurés
            await self.display_product_results(product_dto, duration)
            
            # Stats transport et cache
            await self.display_pipeline_stats()
            
            # Retourner données JSON
            return self.product_dto_to_dict(product_dto)
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Erreur après {duration:.2f}s: {e}")
            return None
    
    async def display_product_results(self, product: ProductDTO, duration: float):
        """Affichage formaté des résultats produit"""
        
        print("📋 RÉSULTATS EXTRACTION")
        print("-" * 40)
        
        # Informations principales
        print(f"📝 Titre: {product.title}")
        print(f"💰 Prix: {product.get_price_display()}")
        print(f"🖼️  Images: {len(product.images)} trouvées")
        print(f"📊 Status: {product.status.value.upper()}")
        print(f"🔗 Source: {product.source_url}")
        print(f"⏱️  Durée: {duration:.2f}s")
        
        # Description (tronquée)
        desc_preview = product.description_html[:100].replace('\n', ' ')
        if len(product.description_html) > 100:
            desc_preview += "..."
        print(f"📄 Description: {desc_preview}")
        
        # Prix détaillé si disponible
        if product.price:
            print(f"💵 Prix détaillé: {product.price.amount} {product.price.currency.value}")
            if product.price.original_text:
                print(f"   Texte original: '{product.price.original_text}'")
        
        # Images détails
        if product.images:
            print(f"🖼️  Images détails:")
            for i, img in enumerate(product.images[:3], 1):  # Top 3
                print(f"   {i}. {img.url}")
                print(f"      Alt: {img.alt}")
                if img.width and img.height:
                    print(f"      Dimensions: {img.width}x{img.height}")
                if img.size_bytes:
                    print(f"      Taille: {img.size_bytes:,} bytes")
            
            if len(product.images) > 3:
                print(f"   ... et {len(product.images) - 3} autres images")
        
        # Attributs produit
        if product.attributes:
            print(f"🏷️  Attributs ({len(product.attributes)}):")
            for key, value in list(product.attributes.items())[:5]:
                print(f"   {key}: {value}")
            if len(product.attributes) > 5:
                print(f"   ... et {len(product.attributes) - 5} autres")
        
        # Idempotence 
        print(f"🔐 Signature: {product.payload_signature}")
        print(f"⏰ Timestamp: {product.extraction_timestamp}")
        
        print()
    
    async def display_pipeline_stats(self):
        """Affichage statistiques transport et pipeline"""
        
        print("📊 STATISTIQUES PIPELINE")
        print("-" * 40)
        
        try:
            stats = await self.orchestrator.get_orchestrator_stats()
            
            # Transport layer stats
            transport = stats.get('transport_layer', {})
            if 'proxy_stats' in transport:
                proxy_stats = transport['proxy_stats']
                print(f"🔄 Proxys: {proxy_stats.get('total_proxies', 0)} configurés")
            
            if 'cache_stats' in transport:
                cache_stats = transport['cache_stats']
                print(f"💾 Cache: {cache_stats.get('active_entries', 0)} entrées actives")
                print(f"   TTL: {cache_stats.get('ttl_seconds', 0)}s")
            
            # Image processing stats
            img_stats = stats.get('image_processing', {})
            print(f"🖼️  Images stockées: {img_stats.get('stored_images', 0)}")
            print(f"   Max dimension: {img_stats.get('max_dimension', 0)}px")
            print(f"   Qualité WEBP: {img_stats.get('webp_quality', 0)}%")
            
            # Pipeline config
            config = stats.get('pipeline_config', {})
            print(f"⚙️  Configuration:")
            print(f"   Timeout: {config.get('fetch_timeout', 0)}s")
            print(f"   Concurrence images: {config.get('image_concurrency', 0)}")
            print(f"   Max images/produit: {config.get('max_images_per_product', 0)}")
            
        except Exception as e:
            print(f"⚠️ Erreur stats: {e}")
        
        print()
    
    def product_dto_to_dict(self, product: ProductDTO) -> dict:
        """Conversion ProductDTO → dict JSON serializable"""
        
        return {
            "title": product.title,
            "description_html": product.description_html,
            "price": {
                "amount": float(product.price.amount) if product.price else None,
                "currency": product.price.currency.value if product.price else None,
                "original_text": product.price.original_text if product.price else None
            } if product.price else None,
            "images": [
                {
                    "url": img.url,
                    "alt": img.alt,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": img.size_bytes
                } for img in product.images
            ],
            "source_url": product.source_url,
            "attributes": product.attributes,
            "status": product.status.value,
            "payload_signature": product.payload_signature,
            "extraction_timestamp": product.extraction_timestamp,
            "is_complete": product.is_complete()
        }


async def main():
    """Point d'entrée principal"""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/semantic_demo.py <URL>")
        print("\nExemples:")
        print("  python scripts/semantic_demo.py https://store.apple.com/fr/iphone-15-pro")
        print("  python scripts/semantic_demo.py https://www.amazon.fr/dp/B0CHX1W1XY")
        print("  python scripts/semantic_demo.py https://www.fnac.com/Apple-iPhone-15-Pro/a17832768")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Validation URL basique
    if not url.startswith(('http://', 'https://')):
        print("❌ URL invalide - doit commencer par http:// ou https://")
        sys.exit(1)
    
    print("🚀 ECOMSIMPLY - Démo Pipeline Scraping Sémantique")
    print("=" * 60)
    print(f"URL cible: {url}")
    
    demo = SemanticDemo()
    
    try:
        await demo.setup()
        
        # Scraping principal
        result = await demo.scrape_product_demo(url)
        
        if result:
            print("📄 EXPORT JSON")
            print("-" * 40)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Sauvegarde optionnelle
            output_file = f"/tmp/semantic_result_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Résultat sauvé: {output_file}")
        
        print("\n🎉 Démo terminée avec succès!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur démonstration: {e}")
        sys.exit(1)
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())