#!/usr/bin/env python3
"""
Configuration DNS Vercel - api.ecomsimply.com
Automatise la configuration DNS dans Vercel pour pointer vers Railway
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from pathlib import Path

class VercelDNSConfigurator:
    def __init__(self):
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.project_id = os.getenv("VERCEL_PROJECT_ID") 
        self.domain = "ecomsimply.com"
        self.subdomain = "api"
        self.full_domain = f"{self.subdomain}.{self.domain}"
        
        # Lire l'URL Railway depuis le fichier
        railway_url_file = Path("/app/ecomsimply-deploy/RAILWAY_BACKEND_URL.txt")
        if railway_url_file.exists():
            self.railway_url = railway_url_file.read_text().strip()
        else:
            self.railway_url = None
        
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.vercel_token}"},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def validate_config(self):
        """Valide la configuration requise"""
        issues = []
        
        if not self.vercel_token:
            issues.append("VERCEL_TOKEN non défini")
        
        if not self.railway_url:
            issues.append("URL Railway non trouvée - Exécuter d'abord configure_railway_backend.sh")
            
        if issues:
            print("❌ Configuration manquante:")
            for issue in issues:
                print(f"   • {issue}")
            print("\nPour obtenir VERCEL_TOKEN:")
            print("1. Aller sur https://vercel.com/account/tokens")
            print("2. Créer un nouveau token")
            print("3. export VERCEL_TOKEN=your_token")
            return False
        
        return True

    async def get_domains(self):
        """Récupère la liste des domaines Vercel"""
        try:
            async with self.session.get("https://api.vercel.com/v6/domains") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("domains", [])
                else:
                    print(f"❌ Erreur récupération domaines: {resp.status}")
                    return []
        except Exception as e:
            print(f"❌ Erreur API Vercel: {e}")
            return []

    async def get_dns_records(self):
        """Récupère les enregistrements DNS pour le domaine"""
        try:
            async with self.session.get(f"https://api.vercel.com/v2/domains/{self.domain}/records") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("records", [])
                else:
                    print(f"❌ Erreur récupération DNS: {resp.status}")
                    return []
        except Exception as e:
            print(f"❌ Erreur DNS API: {e}")
            return []

    async def create_dns_record(self):
        """Crée l'enregistrement DNS CNAME pour api.ecomsimply.com"""
        record_data = {
            "name": self.subdomain,
            "type": "CNAME",
            "value": self.railway_url,
            "ttl": 300
        }
        
        try:
            async with self.session.post(
                f"https://api.vercel.com/v2/domains/{self.domain}/records",
                json=record_data
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    print(f"✅ Enregistrement DNS créé: {self.full_domain} → {self.railway_url}")
                    return data
                else:
                    error_data = await resp.json()
                    print(f"❌ Erreur création DNS: {resp.status}")
                    print(f"   Détails: {error_data}")
                    return None
        except Exception as e:
            print(f"❌ Erreur création DNS: {e}")
            return None

    async def check_existing_record(self):
        """Vérifie si un enregistrement DNS existe déjà"""
        records = await self.get_dns_records()
        
        for record in records:
            if record.get("name") == self.subdomain and record.get("type") == "CNAME":
                print(f"ℹ️  Enregistrement DNS existant trouvé:")
                print(f"   {self.full_domain} → {record.get('value')}")
                return record
        
        return None

    async def update_dns_record(self, record_id):
        """Met à jour un enregistrement DNS existant"""
        record_data = {
            "name": self.subdomain,  
            "type": "CNAME",
            "value": self.railway_url,
            "ttl": 300
        }
        
        try:
            async with self.session.patch(
                f"https://api.vercel.com/v2/domains/{self.domain}/records/{record_id}",
                json=record_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Enregistrement DNS mis à jour: {self.full_domain} → {self.railway_url}")
                    return data
                else:
                    error_data = await resp.json()
                    print(f"❌ Erreur mise à jour DNS: {resp.status}")
                    print(f"   Détails: {error_data}")
                    return None
        except Exception as e:
            print(f"❌ Erreur mise à jour DNS: {e}")
            return None

    async def validate_dns_propagation(self):
        """Valide la propagation DNS"""
        import subprocess
        
        print("🔍 Validation de la propagation DNS...")
        
        try:
            # Test nslookup
            result = subprocess.run(
                ["nslookup", self.full_domain],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ DNS résolu avec nslookup")
                print(f"   Résultat: {result.stdout.strip()}")
            else:
                print("⚠️ DNS pas encore propagé (nslookup)")
                
        except Exception as e:
            print(f"⚠️ Erreur validation DNS: {e}")

        # Test HTTP
        try:
            health_url = f"https://{self.full_domain}/api/health"
            async with self.session.get(health_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Backend accessible via DNS: {health_url}")
                    print(f"   Status: {data.get('status', 'unknown')}")
                else:
                    print(f"⚠️ Backend non accessible: {resp.status}")
        except Exception as e:
            print(f"⚠️ Test HTTP DNS échoué: {e}")

    async def configure_dns(self):
        """Configure le DNS Vercel"""
        print("🌐 CONFIGURATION DNS VERCEL")
        print(f"Domaine: {self.full_domain}")
        print(f"Destination: {self.railway_url}")
        print("-" * 50)
        
        # Vérifier domaine principal
        domains = await self.get_domains()
        domain_found = any(d.get("name") == self.domain for d in domains)
        
        if not domain_found:
            print(f"❌ Domaine {self.domain} non trouvé dans Vercel")
            print("Vérifiez que le domaine est bien configuré dans Vercel")
            return False
        
        print(f"✅ Domaine {self.domain} trouvé dans Vercel")
        
        # Vérifier enregistrement existant
        existing_record = await self.check_existing_record()
        
        if existing_record:
            if existing_record.get("value") == self.railway_url:
                print("✅ Enregistrement DNS déjà correct")
                return True
            else:
                print("🔄 Mise à jour de l'enregistrement DNS...")
                result = await self.update_dns_record(existing_record.get("id"))
                return result is not None
        else:
            print("🆕 Création nouvel enregistrement DNS...")
            result = await self.create_dns_record()
            return result is not None

    async def run(self):
        """Exécute la configuration DNS complète"""
        print("🌐 CONFIGURATION DNS VERCEL - api.ecomsimply.com")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.validate_config():
            return False
        
        print(f"🎯 Configuration DNS: {self.full_domain} → {self.railway_url}")
        print()
        
        success = await self.configure_dns()
        
        if success:
            print("\n⏳ Attente propagation DNS (30s)...")
            await asyncio.sleep(30)
            
            await self.validate_dns_propagation()
            print("\n🎉 ✅ CONFIGURATION DNS TERMINÉE")
            print(f"🔗 Test: https://{self.full_domain}/api/health")
            
            # Sauvegarder la configuration
            dns_config = {
                "domain": self.full_domain,
                "railway_url": self.railway_url,
                "configured_at": datetime.now().isoformat(),
                "status": "configured"
            }
            
            with open("/app/ecomsimply-deploy/DNS_CONFIG.json", "w") as f:
                json.dump(dns_config, f, indent=2)
            
            return True
        else:
            print("\n❌ 🔴 CONFIGURATION DNS ÉCHOUÉE")
            return False

async def main():
    """Point d'entrée principal"""
    
    # Vérifier si VERCEL_TOKEN est défini
    if not os.getenv("VERCEL_TOKEN"):
        print("⚠️ VERCEL_TOKEN non défini")
        print("Pour configuration manuelle:")
        print("1. Aller sur Vercel Dashboard → ecomsimply.com → Settings → Domains")
        print("2. Ajouter sous-domaine: api.ecomsimply.com")
        print("3. Configurer CNAME vers Railway URL")
        print()
        
        # Lire l'URL Railway quand même
        railway_url_file = Path("/app/ecomsimply-deploy/RAILWAY_BACKEND_URL.txt")
        if railway_url_file.exists():
            railway_url = railway_url_file.read_text().strip()
            print(f"🎯 URL Railway à utiliser: {railway_url}")
            
        return False
    
    async with VercelDNSConfigurator() as configurator:
        try:
            success = await configurator.run()
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"❌ Erreur critique: {e}")
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())