"""
QA Testing Service - ECOMSIMPLY
✅ PHASE 6 - Mode QA avec test de résilience et simulation d'erreurs
"""

import os
import random
import time
import json
from datetime import datetime
from typing import Dict, Optional, List
import logging
from pathlib import Path

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

class QATestingService:
    """Service pour les tests QA avec simulation d'erreurs de résilience"""
    
    def __init__(self):
        # ✅ PHASE 6: Configuration du mode TEST
        self.test_mode = os.environ.get('TEST_MODE', 'False').lower() == 'true'
        self.failure_rate = 0.1  # 1 génération sur 10 (10%)
        self.generation_counter = 0
        
        # Configuration du logger spécialisé pour les tests
        self.qa_logger = self._setup_qa_logger()
        
    def _setup_qa_logger(self):
        """Configuration du logger spécialisé generation_test.log"""
        
        qa_logger = logging.getLogger("qa_testing")
        qa_logger.setLevel(logging.INFO)
        
        # Éviter les handlers multiples
        if qa_logger.handlers:
            qa_logger.handlers.clear()
        
        # Formatter pour les logs QA
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        
        try:
            # Créer le dossier logs si nécessaire
            log_dir = Path("/app/logs")
            log_dir.mkdir(exist_ok=True)
            
            # Handler fichier generation_test.log
            file_handler = logging.FileHandler("/app/logs/generation_test.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            qa_logger.addHandler(file_handler)
            
        except Exception as e:
            # Fallback vers handler console si impossible d'écrire fichier
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            qa_logger.addHandler(console_handler)
        
        return qa_logger
    
    def should_simulate_failure(self, user_id: Optional[str] = None, product_name: Optional[str] = None) -> Dict:
        """
        ✅ PHASE 6: Détermine si on doit simuler un échec pour cette génération
        Retourne: {"simulate": bool, "failure_type": str, "reason": str}
        """
        
        if not self.test_mode:
            return {"simulate": False, "failure_type": None, "reason": "TEST_MODE désactivé"}
        
        self.generation_counter += 1
        
        # 1 génération sur 10 simule un échec
        should_fail = (self.generation_counter % 10 == 0) or (random.random() < self.failure_rate)
        
        if not should_fail:
            return {"simulate": False, "failure_type": None, "reason": f"Génération #{self.generation_counter} - Pas d'échec simulé"}
        
        # Types d'échecs possibles à simuler
        failure_types = [
            "gpt_service_failure",     # Échec GPT-4 et GPT-3.5
            "image_generation_failure", # Échec FAL.ai
            "seo_scraping_failure",    # Échec scraping SEO et prix
            "database_failure"         # Échec sauvegarde base
        ]
        
        failure_type = random.choice(failure_types)
        
        log_info(
            f"MODE QA: Simulation d'échec activée",
            user_id=user_id,
            product_name=product_name,
            service="QATestingService",
            operation="simulate_failure",
            generation_counter=self.generation_counter,
            failure_type=failure_type,
            test_mode=self.test_mode
        )
        
        # Log spécialisé dans generation_test.log
        self.qa_logger.info(f"SIMULATION ACTIVÉE | Génération #{self.generation_counter} | Type: {failure_type} | Produit: {product_name} | User: {user_id}")
        
        return {
            "simulate": True,
            "failure_type": failure_type,
            "reason": f"Génération #{self.generation_counter} - Échec simulé ({failure_type})"
        }
    
    def log_test_result(
        self,
        user_id: str,
        product_name: str,
        simulation_info: Dict,
        fallback_triggered: bool,
        final_success: bool,
        error_details: Optional[str] = None,
        fallback_details: Optional[str] = None,
        generation_time: Optional[float] = None
    ):
        """
        ✅ PHASE 6: Log du résultat de test dans generation_test.log
        """
        
        test_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "product_name": product_name,
            "generation_counter": self.generation_counter,
            "simulation_activated": simulation_info.get("simulate", False),
            "error_simulated": simulation_info.get("failure_type"),
            "fallback_triggered": fallback_triggered,
            "final_success": final_success,
            "generation_time_seconds": generation_time,
            "error_details": error_details,
            "fallback_details": fallback_details
        }
        
        # Log structuré principal
        log_operation(
            "QATestingService",
            "test_result",
            "success" if final_success else "failure",
            **test_result
        )
        
        # Log spécialisé generation_test.log avec format lisible
        status = "✅ SUCCÈS" if final_success else "❌ ÉCHEC"
        fallback_status = "🔄 ACTIVÉ" if fallback_triggered else "➖ NON REQUIS"
        simulation_status = f"⚠️ SIMULÉ ({simulation_info.get('failure_type', 'N/A')})" if simulation_info.get("simulate") else "🔧 NORMAL"
        
        self.qa_logger.info(
            f"RÉSULTAT TEST | {status} | "
            f"Génération #{self.generation_counter} | "
            f"Produit: {product_name[:30]}... | "
            f"Simulation: {simulation_status} | "
            f"Fallback: {fallback_status} | "
            f"Temps: {generation_time:.2f}s" if generation_time else "Temps: N/A"
        )
        
        # Si échec simulé, ajouter détails
        if simulation_info.get("simulate"):
            self.qa_logger.info(
                f"DÉTAILS SIMULATION | "
                f"Type erreur: {simulation_info.get('failure_type')} | "
                f"Fallback déclenché: {'OUI' if fallback_triggered else 'NON'} | "
                f"Récupération: {'RÉUSSIE' if final_success else 'ÉCHOUÉE'}"
            )
            
            if error_details:
                self.qa_logger.info(f"ERREUR SIMULÉE | {error_details}")
            
            if fallback_details:
                self.qa_logger.info(f"FALLBACK UTILISÉ | {fallback_details}")
    
    def create_simulated_exception(self, failure_type: str, context: str = "") -> Exception:
        """
        ✅ PHASE 6: Crée une exception simulée pour les tests
        """
        
        error_messages = {
            "gpt_service_failure": f"TEST QA: Simulation échec GPT service {context}",
            "image_generation_failure": f"TEST QA: Simulation échec génération images {context}",
            "seo_scraping_failure": f"TEST QA: Simulation échec scraping SEO {context}",
            "database_failure": f"TEST QA: Simulation échec base de données {context}"
        }
        
        message = error_messages.get(failure_type, f"TEST QA: Échec simulé {failure_type} {context}")
        
        return Exception(message)
    
    def get_qa_statistics(self) -> Dict:
        """Retourne les statistiques du mode QA"""
        
        return {
            "test_mode_active": self.test_mode,
            "total_generations": self.generation_counter,
            "failure_rate_configured": self.failure_rate,
            "next_forced_failure": 10 - (self.generation_counter % 10),
            "qa_log_path": "/app/logs/generation_test.log"
        }

# Instance globale du service QA
qa_service = QATestingService()