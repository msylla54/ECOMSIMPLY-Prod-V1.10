#!/usr/bin/env python3
"""
Script pour supprimer l'endpoint emergency après validation réussie
"""
import re
import sys

def remove_emergency_endpoint():
    """Remove emergency endpoint from server.py"""
    try:
        server_file = "/app/ecomsimply-deploy/backend/server.py"
        
        # Read current content
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Find and remove emergency endpoint
        # Pattern to match the entire emergency endpoint function
        pattern = r'@app\.post\("/api/emergency/create-admin"\).*?async def emergency_create_admin\(\):.*?return \{"ok": False, "error": str\(e\)\}'
        
        # Remove the endpoint (including all its content)
        emergency_start = content.find('@app.post("/api/emergency/create-admin")')
        if emergency_start == -1:
            print("❌ Emergency endpoint not found")
            return False
        
        # Find the end of the function (next @app decorator or end of emergency function)
        emergency_end = content.find('@app.get("/api/debug/env")', emergency_start)
        if emergency_end == -1:
            print("❌ Could not find end of emergency endpoint")
            return False
        
        # Remove the emergency endpoint
        new_content = content[:emergency_start] + content[emergency_end:]
        
        # Write back the modified content
        with open(server_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Emergency endpoint removed successfully")
        print("🔒 Production security restored")
        return True
        
    except Exception as e:
        print(f"❌ Error removing emergency endpoint: {e}")
        return False

def main():
    print("🔒 SUPPRESSION ENDPOINT EMERGENCY")
    print("=" * 50)
    
    success = remove_emergency_endpoint()
    
    if success:
        print("\n✅ SÉCURITÉ RENFORCÉE:")
        print("- Endpoint /api/emergency/create-admin supprimé")
        print("- Production sécurisée contre accès non autorisé")
        print("- Authentification admin uniquement via bootstrap sécurisé")
        
        print("\n🔄 PROCHAINES ÉTAPES:")
        print("1. Commit les changements")
        print("2. Push vers GitHub")
        print("3. Déploiement automatique Vercel")
    else:
        print("\n❌ Échec suppression endpoint emergency")
        print("💡 Vérifier manuellement le fichier server.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)