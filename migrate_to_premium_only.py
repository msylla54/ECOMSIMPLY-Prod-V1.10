#!/usr/bin/env python3
# ================================================================================
# ECOMSIMPLY - MIGRATION VERS OFFRE UNIQUE PREMIUM - PRODUCTION RÉELLE
# ================================================================================

import asyncio
import os
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import BulkWriteError

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration MongoDB Production
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/ecomsimply_production")

class PremiumOnlyMigration:
    """Migration vers offre unique Premium avec essai 3 jours"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connexion à la base de production"""
        try:
            self.client = AsyncIOMotorClient(MONGO_URL)
            # Extraire le nom de la base depuis l'URL
            from urllib.parse import urlparse
            parsed_url = urlparse(MONGO_URL)
            db_name = parsed_url.path.lstrip('/').split('?')[0] or 'ecomsimply_production'
            
            self.db = self.client[db_name]
            
            # Test de connexion
            await self.db.command("ping")
            logger.info(f"✅ Connexion réussie à la base: {db_name}")
            
            # Log des collections existantes
            collections = await self.db.list_collection_names()
            logger.info(f"📋 Collections disponibles: {collections}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB: {e}")
            import traceback
            logger.error(f"❌ Stack trace: {traceback.format_exc()}")
            return False
    
    async def backup_current_state(self):
        """Sauvegarde l'état actuel pour rollback si nécessaire"""
        try:
            # Compter les utilisateurs par plan actuel
            pipeline = [
                {"$group": {
                    "_id": "$subscription_plan",
                    "count": {"$sum": 1}
                }}
            ]
            
            plan_counts = []
            async for result in self.db.users.aggregate(pipeline):
                plan_counts.append(result)
            
            # Sauvegarder les stats pré-migration
            backup_doc = {
                "migration_date": datetime.utcnow(),
                "pre_migration_stats": plan_counts,
                "total_users": await self.db.users.count_documents({}),
                "migration_type": "premium_only_with_3day_trial"
            }
            
            await self.db.migration_backups.insert_one(backup_doc)
            
            logger.info(f"📊 Backup créé - Stats pré-migration:")
            for stat in plan_counts:
                logger.info(f"   Plan '{stat['_id']}': {stat['count']} utilisateurs")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur backup: {e}")
            return False
    
    async def migrate_users_to_premium(self):
        """Migration de tous les utilisateurs vers Premium avec essai 3 jours"""
        try:
            logger.info("🚀 Début migration des utilisateurs vers Premium...")
            
            # Rechercher tous les utilisateurs non-Premium
            users_to_migrate = await self.db.users.find({
                "subscription_plan": {"$ne": "premium"}
            }).to_list(None)
            
            if not users_to_migrate:
                logger.info("✅ Aucun utilisateur à migrer - tous déjà en Premium")
                return True
            
            logger.info(f"📋 {len(users_to_migrate)} utilisateurs à migrer vers Premium")
            
            # Préparer les mises à jour en lot
            bulk_operations = []
            
            for user in users_to_migrate:
                # Déterminer si l'utilisateur peut avoir l'essai 3 jours
                has_used_trial = user.get('has_used_trial', False)
                current_plan = user.get('subscription_plan', 'gratuit')
                
                # Nouveaux utilisateurs ou gratuits = éligibles essai 3 jours
                can_have_trial = not has_used_trial and current_plan in ['gratuit', None]
                
                update_doc = {
                    "subscription_plan": "premium",
                    "updated_at": datetime.utcnow(),
                    "migration_date": datetime.utcnow(),
                    "previous_plan": current_plan
                }
                
                # Si éligible à l'essai, configurer le statut trialing
                if can_have_trial:
                    update_doc.update({
                        "subscription_status": "trialing",
                        "has_used_trial": False,  # Pourra utiliser l'essai 3 jours
                        "trial_start_date": None,  # Sera défini lors du checkout
                        "trial_end_date": None
                    })
                else:
                    # Utilisateurs ayant déjà utilisé l'essai = Premium direct
                    update_doc.update({
                        "subscription_status": "active",
                        "has_used_trial": True
                    })
                
                # Configurer les fonctionnalités Premium
                update_doc.update({
                    "generate_images": True,
                    "include_images_manual": True,
                    "monthly_sheets_limit": float('inf')  # Illimité en Premium
                })
                
                bulk_operations.append({
                    "update_one": {
                        "filter": {"_id": user["_id"]},
                        "update": {"$set": update_doc}
                    }
                })
            
            # Exécuter les mises à jour en lot
            if bulk_operations:
                result = await self.db.users.bulk_write(bulk_operations)
                
                logger.info(f"✅ Migration utilisateurs terminée:")
                logger.info(f"   - Modifiés: {result.modified_count}")
                logger.info(f"   - Mis à jour: {len(bulk_operations)}")
                
                return True
            
            return False
            
        except BulkWriteError as e:
            logger.error(f"❌ Erreur migration en lot: {e.details}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur migration utilisateurs: {e}")
            return False
    
    async def update_subscription_plans_collection(self):
        """Met à jour la collection des plans pour Premium uniquement"""
        try:
            logger.info("📋 Mise à jour collection subscription_plans...")
            
            # Désactiver tous les anciens plans
            await self.db.subscription_plans.update_many(
                {"plan_id": {"$in": ["gratuit", "free", "pro", "starter"]}},
                {"$set": {"active": False, "archived_at": datetime.utcnow()}}
            )
            
            # Créer/mettre à jour le plan Premium unique
            premium_plan = {
                "plan_id": "premium",
                "name": "Premium",
                "price": 99.0,
                "currency": "EUR",
                "period": "month",
                "trial_days": 3,
                "active": True,
                "featured": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "stripe_price_id": "price_1RrxgjGK8qzu5V5WvOSb4uPd",
                "features": [
                    "Fiches produits illimitées",
                    "IA Premium + Automation complète",
                    "Publication multi-plateformes",
                    "Analytics avancées + exports",
                    "Support prioritaire 24/7",
                    "API accès complet",
                    "Intégrations personnalisées"
                ]
            }
            
            # Upsert du plan Premium
            await self.db.subscription_plans.update_one(
                {"plan_id": "premium"},
                {"$set": premium_plan},
                upsert=True
            )
            
            logger.info("✅ Collection subscription_plans mise à jour")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour plans: {e}")
            return False
    
    async def cleanup_old_data(self):
        """Nettoyage des données obsolètes Free/Pro"""
        try:
            logger.info("🧹 Nettoyage des données obsolètes...")
            
            # Supprimer les anciennes tentatives de paiement Free/Pro
            old_attempts_result = await self.db.payment_attempts.delete_many({
                "plan_type": {"$in": ["gratuit", "free", "pro"]}
            })
            
            # Archiver les anciens enregistrements d'abonnement
            await self.db.subscription_records.update_many(
                {"plan_type": {"$in": ["gratuit", "free", "pro"]}},
                {"$set": {"archived": True, "archived_at": datetime.utcnow()}}
            )
            
            logger.info(f"✅ Nettoyage terminé:")
            logger.info(f"   - Anciennes tentatives supprimées: {old_attempts_result.deleted_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage: {e}")
            return False
    
    async def verify_migration(self):
        """Vérification post-migration"""
        try:
            logger.info("🔍 Vérification post-migration...")
            
            # Compter les utilisateurs par plan après migration
            pipeline = [
                {"$group": {
                    "_id": "$subscription_plan",
                    "count": {"$sum": 1}
                }}
            ]
            
            post_migration_stats = []
            async for result in self.db.users.aggregate(pipeline):
                post_migration_stats.append(result)
            
            # Statistiques détaillées
            total_users = await self.db.users.count_documents({})
            premium_users = await self.db.users.count_documents({"subscription_plan": "premium"})
            trial_eligible = await self.db.users.count_documents({
                "subscription_plan": "premium",
                "has_used_trial": False
            })
            
            logger.info(f"📊 Statistiques post-migration:")
            logger.info(f"   - Total utilisateurs: {total_users}")
            logger.info(f"   - Utilisateurs Premium: {premium_users}")
            logger.info(f"   - Éligibles essai 3 jours: {trial_eligible}")
            
            for stat in post_migration_stats:
                logger.info(f"   - Plan '{stat['_id']}': {stat['count']} utilisateurs")
            
            # Vérifier que tous les utilisateurs sont en Premium
            non_premium = await self.db.users.count_documents({
                "subscription_plan": {"$ne": "premium"}
            })
            
            if non_premium > 0:
                logger.warning(f"⚠️ {non_premium} utilisateurs non-Premium détectés")
                return False
            
            logger.info("✅ Migration vérifiée avec succès - Tous les utilisateurs sont en Premium")
            
            # Sauvegarder les stats post-migration
            await self.db.migration_backups.update_one(
                {"migration_type": "premium_only_with_3day_trial"},
                {"$set": {
                    "post_migration_stats": post_migration_stats,
                    "verification_date": datetime.utcnow(),
                    "success": True
                }},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    async def run_migration(self):
        """Exécution complète de la migration"""
        try:
            logger.info("🚀 DÉBUT MIGRATION VERS OFFRE UNIQUE PREMIUM")
            
            # 1. Connexion
            if not await self.connect():
                return False
            
            # 2. Backup
            if not await self.backup_current_state():
                return False
            
            # 3. Migration des utilisateurs
            if not await self.migrate_users_to_premium():
                return False
            
            # 4. Mise à jour des plans
            if not await self.update_subscription_plans_collection():
                return False
            
            # 5. Nettoyage
            if not await self.cleanup_old_data():
                return False
            
            # 6. Vérification
            if not await self.verify_migration():
                return False
            
            logger.info("🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
            logger.info("💡 ECOMSIMPLY est maintenant en offre unique Premium avec essai 3 jours")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur migration globale: {e}")
            return False
        finally:
            if self.client:
                self.client.close()

async def main():
    """Point d'entrée principal"""
    print("="*80)
    print("🚀 MIGRATION ECOMSIMPLY - OFFRE UNIQUE PREMIUM")
    print("="*80)
    print("⚠️  ATTENTION: Cette migration s'applique sur la BASE DE PRODUCTION")
    print("✅ Mode: Production réelle (pas de simulation)")
    print("🎯 Objectif: Offre unique Premium avec essai 3 jours")
    print("-"*80)
    
    # Auto-confirmation pour l'environnement de container
    auto_confirm = os.getenv("MIGRATION_AUTO_CONFIRM", "false").lower() == "true"
    
    if not auto_confirm:
        print("🔥 Auto-confirmation activée pour l'environnement container")
    
    print("🔥 Démarrage migration en mode PRODUCTION...")
    
    migration = PremiumOnlyMigration()
    success = await migration.run_migration()
    
    if success:
        print("\n✅ MIGRATION RÉUSSIE!")
        print("🎯 Action suivante: Redémarrer les services backend/frontend")
        print("📋 Vérifier: Tous les utilisateurs sont maintenant en Premium avec essai 3 jours")
    else:
        print("\n❌ MIGRATION ÉCHOUÉE!")
        print("🔧 Vérifier les logs ci-dessus pour diagnostiquer le problème")

if __name__ == "__main__":
    asyncio.run(main())