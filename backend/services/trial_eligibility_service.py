# ================================================================================
# ECOMSIMPLY - SERVICE ÉLIGIBILITÉ ESSAI GRATUIT - RÈGLE "UN SEUL ESSAI"
# ================================================================================

import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..models.subscription import User, PlanType
import os

logger = logging.getLogger(__name__)

class TrialEligibilityService:
    """Service pour déterminer l'éligibilité à l'essai gratuit selon règle "un seul essai"."""
    
    def __init__(self):
        self.max_ip_trials = int(os.getenv("MAX_IP_TRIALS", "3"))  # Max trials par IP
        self.trial_cooldown_days = int(os.getenv("TRIAL_COOLDOWN_DAYS", "365"))  # Cooldown entre trials
    
    # ================================================================================
    # 🔍 VÉRIFICATION ÉLIGIBILITÉ PRINCIPALE
    # ================================================================================
    
    async def check_trial_eligibility(
        self, 
        user: User, 
        plan_type: PlanType,
        client_ip: str = None,
        payment_fingerprint: str = None,
        db = None
    ) -> Dict[str, Any]:
        """
        Vérifie l'éligibilité à l'essai gratuit selon plusieurs critères.
        
        Règles d'éligibilité:
        1. L'utilisateur n'a jamais utilisé d'essai (trial_used_at)
        2. Le fingerprint de paiement n'est pas connu
        3. L'email normalisé n'a pas déjà utilisé d'essai (multi-comptes)
        4. L'IP n'a pas dépassé la limite de trials (optionnel)
        """
        try:
            eligibility_checks = []
            
            # 1. Vérifier si l'utilisateur a déjà utilisé un essai
            user_check = await self._check_user_trial_history(user)
            eligibility_checks.append(user_check)
            
            # 2. Vérifier le fingerprint de paiement (si fourni)
            if payment_fingerprint:
                fingerprint_check = await self._check_payment_fingerprint(payment_fingerprint, db)
                eligibility_checks.append(fingerprint_check)
            
            # 3. Vérifier l'email normalisé pour détection multi-comptes
            email_check = await self._check_email_eligibility(user.email, db)
            eligibility_checks.append(email_check)
            
            # 4. Vérifier les limites IP (optionnel)
            if client_ip:
                ip_check = await self._check_ip_eligibility(client_ip, db)
                eligibility_checks.append(ip_check)
            
            # Déterminer l'éligibilité finale
            eligible = all(check["eligible"] for check in eligibility_checks)
            blocking_reason = next((check["reason"] for check in eligibility_checks if not check["eligible"]), None)
            
            result = {
                "eligible": eligible,
                "reason": blocking_reason or "eligible_for_trial",
                "plan_type": plan_type,
                "checks_performed": len(eligibility_checks),
                "user_id_hash": self._hash_user_id(user.id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log sans PII
            logger.info(
                f"🎯 Trial eligibility check: eligible={eligible}, "
                f"reason={result['reason']}, plan={plan_type}, "
                f"user_hash={result['user_id_hash'][:8]}..., "
                f"checks={len(eligibility_checks)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking trial eligibility: {str(e)}")
            # En cas d'erreur, refuser l'essai par sécurité
            return {
                "eligible": False,
                "reason": "eligibility_check_error",
                "plan_type": plan_type,
                "error": True,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # ================================================================================
    # 🔍 VÉRIFICATIONS INDIVIDUELLES
    # ================================================================================
    
    async def _check_user_trial_history(self, user: User) -> Dict[str, Any]:
        """Vérifie si l'utilisateur a déjà utilisé un essai."""
        
        # Vérifier le flag trial_used_at
        if hasattr(user, 'trial_used_at') and user.trial_used_at:
            days_since_trial = (datetime.utcnow() - user.trial_used_at).days
            
            if days_since_trial < self.trial_cooldown_days:
                return {
                    "eligible": False,
                    "reason": "trial_already_used",
                    "details": f"Trial used {days_since_trial} days ago"
                }
        
        # Vérifier le flag legacy has_used_trial
        if user.has_used_trial:
            return {
                "eligible": False,
                "reason": "trial_already_used_legacy",
                "details": "Legacy trial flag set"
            }
        
        return {
            "eligible": True,
            "reason": "user_trial_history_ok"
        }
    
    async def _check_payment_fingerprint(self, fingerprint: str, db) -> Dict[str, Any]:
        """Vérifie si le fingerprint de paiement est déjà connu."""
        try:
            if not db:
                return {"eligible": True, "reason": "no_db_connection"}
            
            # Hasher le fingerprint pour la recherche
            fingerprint_hash = self._hash_fingerprint(fingerprint)
            
            # Chercher dans la collection des fingerprints utilisés pour les trials
            existing_trial = await db.trial_fingerprints.find_one({
                "fingerprint_hash": fingerprint_hash,
                "trial_used": True
            })
            
            if existing_trial:
                return {
                    "eligible": False,
                    "reason": "payment_fingerprint_already_used",
                    "details": f"Fingerprint used on {existing_trial.get('used_at', 'unknown date')}"
                }
            
            return {
                "eligible": True,
                "reason": "payment_fingerprint_ok"
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking payment fingerprint: {e}")
            # En cas d'erreur, être permissif sur ce critère
            return {"eligible": True, "reason": "fingerprint_check_error"}
    
    async def _check_email_eligibility(self, email: str, db) -> Dict[str, Any]:
        """Vérifie si l'email normalisé a déjà utilisé un essai (détection multi-comptes)."""
        try:
            if not db:
                return {"eligible": True, "reason": "no_db_connection"}
            
            # Normaliser et hasher l'email
            email_hash = self._hash_email(email)
            
            # Chercher d'autres utilisateurs avec cet email hash qui ont utilisé un essai
            existing_trial = await db.users.find_one({
                "email_hash": email_hash,
                "$or": [
                    {"has_used_trial": True},
                    {"trial_used_at": {"$ne": None}}
                ]
            })
            
            if existing_trial:
                return {
                    "eligible": False,
                    "reason": "email_already_used_trial",
                    "details": "Email hash found with previous trial usage"
                }
            
            return {
                "eligible": True,
                "reason": "email_eligibility_ok"
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking email eligibility: {e}")
            # En cas d'erreur, être permissif sur ce critère
            return {"eligible": True, "reason": "email_check_error"}
    
    async def _check_ip_eligibility(self, client_ip: str, db) -> Dict[str, Any]:
        """Vérifie les limites d'essais par IP."""
        try:
            if not db:
                return {"eligible": True, "reason": "no_db_connection"}
            
            # Hasher l'IP
            ip_hash = self._hash_ip(client_ip)
            
            # Compter les essais de cette IP dans les derniers jours
            cutoff_date = datetime.utcnow() - timedelta(days=self.trial_cooldown_days)
            
            trial_count = await db.trial_ip_usage.count_documents({
                "ip_hash": ip_hash,
                "trial_started_at": {"$gte": cutoff_date}
            })
            
            if trial_count >= self.max_ip_trials:
                return {
                    "eligible": False,
                    "reason": "ip_trial_limit_exceeded",
                    "details": f"IP has used {trial_count}/{self.max_ip_trials} trials"
                }
            
            return {
                "eligible": True,
                "reason": "ip_eligibility_ok",
                "details": f"IP trials used: {trial_count}/{self.max_ip_trials}"
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking IP eligibility: {e}")
            # En cas d'erreur, être permissif sur ce critère
            return {"eligible": True, "reason": "ip_check_error"}
    
    # ================================================================================
    # 📝 ENREGISTREMENT UTILISATION ESSAI
    # ================================================================================
    
    async def record_trial_usage(
        self, 
        user: User,
        payment_fingerprint: str = None,
        client_ip: str = None,
        plan_type: PlanType = None,
        db = None
    ) -> bool:
        """Enregistre l'utilisation d'un essai gratuit."""
        try:
            current_time = datetime.utcnow()
            
            # 1. Marquer l'utilisateur comme ayant utilisé son essai
            user.trial_used_at = current_time
            user.has_used_trial = True
            
            # 2. Enregistrer le fingerprint de paiement
            if payment_fingerprint and db:
                await db.trial_fingerprints.insert_one({
                    "fingerprint_hash": self._hash_fingerprint(payment_fingerprint),
                    "trial_used": True,
                    "used_at": current_time,
                    "user_id_hash": self._hash_user_id(user.id),
                    "plan_type": plan_type
                })
            
            # 3. Enregistrer l'utilisation IP
            if client_ip and db:
                await db.trial_ip_usage.insert_one({
                    "ip_hash": self._hash_ip(client_ip),
                    "trial_started_at": current_time,
                    "user_id_hash": self._hash_user_id(user.id),
                    "plan_type": plan_type
                })
            
            # 4. Mettre à jour l'email hash si nécessaire
            if db:
                email_hash = self._hash_email(user.email)
                await db.users.update_one(
                    {"id": user.id},
                    {
                        "$set": {
                            "trial_used_at": current_time,
                            "has_used_trial": True,
                            "email_hash": email_hash,
                            "updated_at": current_time
                        }
                    }
                )
            
            logger.info(
                f"✅ Trial usage recorded: user_hash={self._hash_user_id(user.id)[:8]}..., "
                f"plan={plan_type}, timestamp={current_time.isoformat()}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording trial usage: {str(e)}")
            return False
    
    # ================================================================================
    # 🔐 FONCTIONS DE HASHAGE SÉCURISÉES
    # ================================================================================
    
    def _hash_email(self, email: str) -> str:
        """Hash sécurisé de l'email normalisé."""
        normalized_email = email.lower().strip()
        return hashlib.sha256(f"email:{normalized_email}".encode()).hexdigest()
    
    def _hash_fingerprint(self, fingerprint: str) -> str:
        """Hash sécurisé du fingerprint de paiement."""
        return hashlib.sha256(f"fingerprint:{fingerprint}".encode()).hexdigest()
    
    def _hash_ip(self, ip: str) -> str:
        """Hash sécurisé de l'IP."""
        return hashlib.sha256(f"ip:{ip}".encode()).hexdigest()
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash sécurisé de l'ID utilisateur pour les logs."""
        return hashlib.sha256(f"user:{user_id}".encode()).hexdigest()
    
    # ================================================================================
    # 📊 STATISTIQUES ET MONITORING
    # ================================================================================
    
    async def get_trial_statistics(self, db = None) -> Dict[str, Any]:
        """Obtient des statistiques d'utilisation des essais."""
        try:
            if not db:
                return {"error": "no_db_connection"}
            
            # Compter les essais des 30 derniers jours
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_trials = await db.users.count_documents({
                "trial_used_at": {"$gte": thirty_days_ago}
            })
            
            # Compter les essais bloqués par fingerprint
            blocked_fingerprints = await db.trial_fingerprints.count_documents({
                "trial_used": True
            })
            
            # Compter les IPs ayant atteint la limite
            ip_limit_reached = await db.trial_ip_usage.aggregate([
                {
                    "$group": {
                        "_id": "$ip_hash",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "count": {"$gte": self.max_ip_trials}
                    }
                },
                {
                    "$count": "total"
                }
            ]).to_list(length=1)
            
            limited_ips = ip_limit_reached[0]["total"] if ip_limit_reached else 0
            
            return {
                "recent_trials_30d": recent_trials,
                "blocked_fingerprints": blocked_fingerprints,
                "limited_ips": limited_ips,
                "max_ip_trials": self.max_ip_trials,
                "trial_cooldown_days": self.trial_cooldown_days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting trial statistics: {e}")
            return {"error": str(e)}
    
    # ================================================================================
    # 🧹 MAINTENANCE ET NETTOYAGE
    # ================================================================================
    
    async def cleanup_old_records(self, db = None, retention_days: int = 730) -> Dict[str, Any]:
        """Nettoie les anciens enregistrements d'essais."""
        try:
            if not db:
                return {"error": "no_db_connection"}
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Nettoyer les anciens fingerprints
            deleted_fingerprints = await db.trial_fingerprints.delete_many({
                "used_at": {"$lt": cutoff_date}
            })
            
            # Nettoyer les anciens enregistrements IP
            deleted_ips = await db.trial_ip_usage.delete_many({
                "trial_started_at": {"$lt": cutoff_date}
            })
            
            result = {
                "deleted_fingerprints": deleted_fingerprints.deleted_count,
                "deleted_ip_records": deleted_ips.deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"🧹 Trial records cleanup completed: "
                f"fingerprints={result['deleted_fingerprints']}, "
                f"ips={result['deleted_ip_records']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return {"error": str(e)}

# Instance globale du service
trial_eligibility_service = TrialEligibilityService()