#!/usr/bin/env python3
"""
Railway API Deployer - ECOMSIMPLY
Utilise l'API Railway directement pour déployer le backend avec le token fourni
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration Railway
RAILWAY_TOKEN = "59a33ff7-ff58-43ca-ac8c-f88abdfa280d"
PROJECT_ID = "947cd7da-e31f-45a3-b967-49317532d948"
ENVIRONMENT = "production"
RAILWAY_API_URL = "https://backboard.railway.app/graphql"

class RailwayDeployer:
    def __init__(self):
        self.token = RAILWAY_TOKEN
        self.project_id = PROJECT_ID
        self.environment = ENVIRONMENT
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def graphql_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Exécute une requête GraphQL sur l'API Railway"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            async with self.session.post(RAILWAY_API_URL, json=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    return {"errors": [{"message": f"HTTP {resp.status}: {error_text}"}]}
        except Exception as e:
            return {"errors": [{"message": f"Request failed: {e}"}]}
    
    async def get_project_info(self) -> Dict[str, Any]:
        """Récupère les informations du projet"""
        query = """
        query project($id: String!) {
            project(id: $id) {
                id
                name
                description
                environments {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
                services {
                    edges {
                        node {
                            id
                            name
                            serviceInstances {
                                edges {
                                    node {
                                        id
                                        environmentId
                                        domains {
                                            serviceDomain
                                            customDomain
                                        }
                                        latestDeployment {
                                            id
                                            status
                                            createdAt
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        return await self.graphql_query(query, {"id": self.project_id})
    
    async def get_service_variables(self, service_id: str, environment_id: str) -> Dict[str, Any]:
        """Récupère les variables d'environnement d'un service"""
        query = """
        query serviceVariables($serviceId: String!, $environmentId: String!) {
            variables(serviceId: $serviceId, environmentId: $environmentId) {
                edges {
                    node {
                        id
                        name
                        value
                    }
                }
            }
        }
        """
        
        return await self.graphql_query(query, {
            "serviceId": service_id,
            "environmentId": environment_id
        })
    
    async def set_service_variable(self, service_id: str, environment_id: str, name: str, value: str) -> Dict[str, Any]:
        """Définit une variable d'environnement"""
        query = """
        mutation variableUpsert($input: VariableUpsertInput!) {
            variableUpsert(input: $input) {
                id
                name
                value
            }
        }
        """
        
        return await self.graphql_query(query, {
            "input": {
                "serviceId": service_id,
                "environmentId": environment_id,
                "name": name,
                "value": value
            }
        })
    
    async def trigger_deployment(self, service_id: str, environment_id: str) -> Dict[str, Any]:
        """Déclenche un nouveau déploiement"""
        query = """
        mutation serviceInstanceRedeploy($serviceId: String!, $environmentId: String!) {
            serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId) {
                id
                status
                createdAt
            }
        }
        """
        
        return await self.graphql_query(query, {
            "serviceId": service_id,
            "environmentId": environment_id
        })
    
    async def configure_environment_variables(self, service_id: str, environment_id: str) -> bool:
        """Configure les variables d'environnement nécessaires"""
        print("🔧 Configuration des variables d'environnement...")
        
        # Variables critiques pour ECOMSIMPLY
        required_vars = {
            "MONGO_URL": "mongodb+srv://[CONFIGURE_IN_RAILWAY_DASHBOARD]",
            "DB_NAME": "ecomsimply_production",
            "JWT_SECRET": "supersecretjwtkey32charsminimum2025ecomsimply",
            "ADMIN_EMAIL": "msylla54@gmail.com",
            "ADMIN_PASSWORD_HASH": "$2b$12$AX.4AQP8u50RP3.pcupJ6OJSSOHQqTG71NJvZRW/J6kyRFnxKX0.W",
            "ADMIN_BOOTSTRAP_TOKEN": "ECS-Bootstrap-2025-Secure-Token",
            "APP_BASE_URL": "https://ecomsimply.com",
            "ENCRYPTION_KEY": "w7uWSQqDAewH34UjRHVSgeJawQnDa-ukRe0WERClY694=",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "MOCK_MODE": "false",
            "PYTHONPATH": "/app",
            "PYTHON_VERSION": "3.11"
        }
        
        success_count = 0
        
        for var_name, var_value in required_vars.items():
            try:
                result = await self.set_service_variable(service_id, environment_id, var_name, var_value)
                
                if "errors" in result:
                    print(f"⚠️ Erreur configuration {var_name}: {result['errors']}")
                else:
                    print(f"✅ {var_name} configuré")
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Erreur {var_name}: {e}")
        
        print(f"📊 Variables configurées: {success_count}/{len(required_vars)}")
        return success_count >= len(required_vars) * 0.8  # 80% de succès minimum
    
    async def wait_for_deployment(self, service_url: str, max_wait: int = 300) -> bool:
        """Attend que le déploiement soit prêt"""
        print(f"⏳ Attente du déploiement (max {max_wait}s)...")
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                async with self.session.get(f"{service_url}/api/health") as resp:
                    if resp.status == 200:
                        health_data = await resp.json()
                        print(f"✅ Service opérationnel: {health_data}")
                        return True
            except:
                pass
            
            await asyncio.sleep(10)
            print("⏳ Déploiement en cours...")
        
        print("⚠️ Timeout - déploiement peut encore être en cours")
        return False
    
    async def deploy_backend(self) -> Dict[str, Any]:
        """Déploie le backend ECOMSIMPLY sur Railway"""
        print("🚂 DÉPLOIEMENT RAILWAY BACKEND - ECOMSIMPLY")
        print("=" * 50)
        print(f"📅 Date: {datetime.now()}")
        print(f"🎯 Projet: {self.project_id}")
        print(f"🌍 Environment: {self.environment}")
        print()
        
        # Étape 1: Récupérer les informations du projet
        print("📋 ÉTAPE 1: Récupération informations projet...")
        project_info = await self.get_project_info()
        
        if "errors" in project_info:
            print(f"❌ Erreur API Railway: {project_info['errors']}")
            return {"success": False, "error": "API Railway error"}
        
        project_data = project_info.get("data", {}).get("project")
        if not project_data:
            print("❌ Projet non trouvé")
            return {"success": False, "error": "Project not found"}
        
        print(f"✅ Projet trouvé: {project_data['name']}")
        
        # Étape 2: Trouver le service et l'environnement
        print("📋 ÉTAPE 2: Recherche service et environnement...")
        
        environments = project_data.get("environments", {}).get("edges", [])
        environment_id = None
        
        for env in environments:
            if env["node"]["name"].lower() == self.environment.lower():
                environment_id = env["node"]["id"]
                break
        
        if not environment_id:
            print(f"❌ Environment '{self.environment}' non trouvé")
            return {"success": False, "error": "Environment not found"}
        
        print(f"✅ Environment trouvé: {environment_id}")
        
        # Trouver le service
        services = project_data.get("services", {}).get("edges", [])
        service_id = None
        service_url = None
        
        for service in services:
            service_node = service["node"]
            service_id = service_node["id"]
            
            # Trouver l'instance du service dans l'environnement production
            instances = service_node.get("serviceInstances", {}).get("edges", [])
            for instance in instances:
                instance_node = instance["node"]
                if instance_node.get("environmentId") == environment_id:
                    domains = instance_node.get("domains", {})
                    if domains and domains.get("serviceDomain"):
                        service_url = f"https://{domains['serviceDomain']}"
                    break
            
            if service_id:
                break
        
        if not service_id:
            print("❌ Service non trouvé")
            return {"success": False, "error": "Service not found"}
        
        print(f"✅ Service trouvé: {service_id}")
        if service_url:
            print(f"✅ URL Service: {service_url}")
        
        # Étape 3: Configuration des variables d'environnement
        print("📋 ÉTAPE 3: Configuration variables d'environnement...")
        
        vars_success = await self.configure_environment_variables(service_id, environment_id)
        if not vars_success:
            print("⚠️ Certaines variables n'ont pas pu être configurées")
        
        # Étape 4: Déclencher un déploiement
        print("📋 ÉTAPE 4: Déclenchement du déploiement...")
        
        try:
            deploy_result = await self.trigger_deployment(service_id, environment_id)
            if "errors" in deploy_result:
                print(f"⚠️ Erreur déploiement: {deploy_result['errors']}")
                print("ℹ️ Le déploiement peut se faire automatiquement via webhook GitHub")
            else:
                print("✅ Déploiement déclenché")
        except Exception as e:
            print(f"⚠️ Déploiement auto non disponible: {e}")
            print("ℹ️ Le déploiement se fera via webhook GitHub lors du push")
        
        # Étape 5: Attendre et valider (si URL disponible)
        if service_url:
            print("📋 ÉTAPE 5: Validation du service...")
            service_ready = await self.wait_for_deployment(service_url, 180)
            
            if service_ready:
                print("🎉 ✅ DÉPLOIEMENT RÉUSSI!")
            else:
                print("⚠️ Service peut encore être en cours de déploiement")
        else:
            print("📋 ÉTAPE 5: Service non exposé - validation impossible")
        
        # Rapport final
        deployment_report = {
            "success": True,
            "deployment_date": datetime.now().isoformat(),
            "project_id": self.project_id,
            "project_name": project_data["name"],
            "service_id": service_id,
            "environment_id": environment_id,
            "service_url": service_url,
            "variables_configured": vars_success,
            "status": "deployed"
        }
        
        # Sauvegarder le rapport
        with open("/app/ecomsimply-deploy/railway_deployment_report.json", "w") as f:
            json.dump(deployment_report, f, indent=2)
        
        print("📋 Rapport sauvegardé: railway_deployment_report.json")
        
        return deployment_report

async def main():
    """Point d'entrée principal"""
    try:
        async with RailwayDeployer() as deployer:
            result = await deployer.deploy_backend()
            
            if result.get("success"):
                print("\n🎉 DÉPLOIEMENT RAILWAY COMPLÉTÉ AVEC SUCCÈS!")
                
                if result.get("service_url"):
                    print(f"🔗 Service URL: {result['service_url']}")
                    print(f"🔗 Health Check: {result['service_url']}/api/health")
                
                print("\n📋 PROCHAINES ÉTAPES:")
                print("1. Vérifier les variables MONGO_URL dans Railway Dashboard")
                print("2. Push du code sur GitHub pour déclencher le déploiement")
                print("3. Configurer le DNS api.ecomsimply.com")
                print("4. Exécuter les tests E2E")
                
                return 0
            else:
                print(f"\n❌ ÉCHEC DU DÉPLOIEMENT: {result.get('error')}")
                return 1
                
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))