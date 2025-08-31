"""
Publishers Factory - Initialisation de tous les publishers ECOMSIMPLY
"""

from typing import Dict
from ..constants import STORES
from .base import GenericMockPublisher, IdempotencyStore


def get_all_publishers(idem_store: IdempotencyStore) -> Dict[str, GenericMockPublisher]:
    """
    Crée tous les publishers pour les stores supportés
    
    Args:
        idem_store: Store d'idempotence partagé
        
    Returns:
        Dict mapping store_name → GenericMockPublisher
    """
    
    return {store: GenericMockPublisher(store, idem_store) for store in STORES}


def get_publisher(store_name: str, idem_store: IdempotencyStore) -> GenericMockPublisher:
    """
    Crée un publisher spécifique
    
    Args:
        store_name: Nom du store
        idem_store: Store d'idempotence
        
    Returns:
        GenericMockPublisher configuré
        
    Raises:
        ValueError: Si store non supporté
    """
    
    if store_name not in STORES:
        raise ValueError(f"Store '{store_name}' non supporté. Stores disponibles: {STORES}")
    
    return GenericMockPublisher(store_name, idem_store)


def get_supported_stores() -> list:
    """Retourne la liste des stores supportés"""
    return STORES.copy()


__all__ = [
    'get_all_publishers',
    'get_publisher', 
    'get_supported_stores',
    'GenericMockPublisher',
    'IdempotencyStore'
]