"""
Logging Service - ECOMSIMPLY
Système de logging centralisé et structuré pour tous les services
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

class StructuredLogger:
    """Logger structuré avec contexte utilisateur et métadonnées"""
    
    def __init__(self, service_name: str = "ecomsimply"):
        self.service_name = service_name
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configuration du logger principal"""
        
        # Create logger
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.INFO)
        
        # Éviter les handlers multiples
        if logger.handlers:
            logger.handlers.clear()
        
        # Formatter JSON structuré
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": %(message)s}'
        )
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler fichier (si possible)
        try:
            log_dir = Path("/app/logs")
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler("/app/logs/ecomsimply.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback si impossible d'écrire dans le fichier
            pass
        
        return logger
    
    def _format_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        extra_data: Optional[Dict] = None
    ) -> str:
        """Formatage du message avec contexte structuré"""
        
        log_data = {
            "msg": message,
            "timestamp_iso": datetime.utcnow().isoformat(),
        }
        
        # Contexte utilisateur
        if user_id:
            log_data["user_id"] = user_id
        if product_name:
            log_data["product_name"] = product_name
        if user_plan:
            log_data["user_plan"] = user_plan
        
        # Données supplémentaires
        if extra_data:
            log_data.update(extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def info(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        **kwargs
    ):
        """Log niveau INFO avec contexte"""
        formatted_msg = self._format_message(message, user_id, product_name, user_plan, kwargs)
        self.logger.info(formatted_msg)
    
    def error(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        error_source: Optional[str] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Log niveau ERROR avec contexte et détails d'erreur"""
        
        error_data = kwargs.copy()
        if error_source:
            error_data["error_source"] = error_source
        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_message"] = str(exception)
        
        formatted_msg = self._format_message(message, user_id, product_name, user_plan, error_data)
        self.logger.error(formatted_msg)
    
    def warning(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        **kwargs
    ):
        """Log niveau WARNING avec contexte"""
        formatted_msg = self._format_message(message, user_id, product_name, user_plan, kwargs)
        self.logger.warning(formatted_msg)
    
    def debug(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        **kwargs
    ):
        """Log niveau DEBUG avec contexte"""
        formatted_msg = self._format_message(message, user_id, product_name, user_plan, kwargs)
        self.logger.debug(formatted_msg)
    
    def log_service_start(self, service_name: str, **kwargs):
        """Log de démarrage de service"""
        self.info(
            f"Service {service_name} démarré",
            service_name=service_name,
            **kwargs
        )
    
    def log_service_operation(
        self, 
        service_name: str, 
        operation: str, 
        status: str,
        duration_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        product_name: Optional[str] = None,
        user_plan: Optional[str] = None,
        **kwargs
    ):
        """Log d'opération de service avec durée"""
        
        extra_data = {
            "service_name": service_name,
            "operation": operation,
            "status": status
        }
        
        if duration_ms is not None:
            extra_data["duration_ms"] = duration_ms
        
        extra_data.update(kwargs)
        
        if status == "success":
            self.info(
                f"{service_name}.{operation} completed successfully",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                **extra_data
            )
        elif status == "error":
            self.error(
                f"{service_name}.{operation} failed",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                error_source=f"{service_name}.{operation}",
                **extra_data
            )
        else:
            self.info(
                f"{service_name}.{operation} status: {status}",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                **extra_data
            )

# Instance globale du logger
ecomsimply_logger = StructuredLogger("ecomsimply")

# Fonctions de convenance pour import facile
def log_info(message: str, **kwargs):
    """Log info global"""
    ecomsimply_logger.info(message, **kwargs)

def log_error(message: str, **kwargs):
    """Log error global"""
    ecomsimply_logger.error(message, **kwargs)

def log_warning(message: str, **kwargs):
    """Log warning global"""
    ecomsimply_logger.warning(message, **kwargs)

def log_operation(service_name: str, operation: str, status: str, **kwargs):
    """Log operation global"""
    ecomsimply_logger.log_service_operation(service_name, operation, status, **kwargs)