# Amazon SP-API Multi-Tenant MongoDB Models
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class AmazonRegion(str, Enum):
    """Régions Amazon SP-API supportées"""
    NA = "na"  # North America (US, CA, MX)
    EU = "eu"  # Europe (DE, ES, FR, IT, UK, etc.)
    FE = "fe"  # Far East (JP, etc.)

class ConnectionStatus(str, Enum):
    """États de connexion SP-API"""
    PENDING = "pending"      # En attente d'OAuth
    CONNECTED = "connected"  # Connexion active
    ERROR = "error"          # Erreur de connexion
    REVOKED = "revoked"      # Connexion révoquée

class AmazonConnection(BaseModel):
    """
    Modèle de connexion Amazon multi-tenant pour MongoDB
    Chaque utilisateur peut avoir plusieurs connexions (multi-marketplace)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identification utilisateur et marketplace
    user_id: str = Field(..., description="ID utilisateur ECOMSIMPLY")
    marketplace_id: str = Field(..., description="ID marketplace Amazon (ex: A13V1IB3VIYZZH)")
    seller_id: Optional[str] = Field(None, description="Seller Partner ID Amazon")
    region: AmazonRegion = Field(..., description="Région Amazon (eu/na/fe)")
    
    # Tokens chiffrés (AES-GCM)
    encrypted_refresh_token: Optional[str] = Field(None, description="Refresh token chiffré")
    token_encryption_nonce: Optional[str] = Field(None, description="Nonce pour déchiffrement")
    token_encryption_method: str = Field(default="AES-GCM", description="Méthode de chiffrement")
    
    # État de la connexion
    status: ConnectionStatus = Field(default=ConnectionStatus.PENDING)
    connected_at: Optional[datetime] = Field(None, description="Date de connexion réussie")
    last_used_at: Optional[datetime] = Field(None, description="Dernière utilisation")
    error_message: Optional[str] = Field(None, description="Message d'erreur si échec")
    
    # OAuth state management
    oauth_state: Optional[str] = Field(None, description="State OAuth pour sécurité CSRF")
    oauth_state_expires: Optional[datetime] = Field(None, description="Expiration du state")
    
    # Métadonnées
    connection_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Configuration Pydantic"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "user_id": "user_123456",
                "marketplace_id": "A13V1IB3VIYZZH",
                "seller_id": "A1B2C3D4E5F6G7",
                "region": "eu",
                "status": "connected"
            }
        }
    
    @validator('marketplace_id')
    def validate_marketplace_id(cls, v):
        """Validation des marketplace IDs Amazon"""
        valid_marketplaces = {
            # North America
            'ATVPDKIKX0DER': 'US',
            'A2EUQ1WTGCTBG2': 'CA',
            'A1AM78C64UM0Y8': 'MX',
            
            # Europe
            'A1PA6795UKMFR9': 'DE',
            'A1RKKUPIHCS9HS': 'ES', 
            'A13V1IB3VIYZZH': 'FR',
            'APJ6JRA9NG5V4': 'IT',
            'A1F83G8C2ARO7P': 'UK',
            'A21TJRUUN4KGV': 'IN',
            
            # Far East
            'A1VC38T7YXB528': 'JP',
            'ARBP9OOSHTCHU': 'EG'
        }
        
        if v not in valid_marketplaces:
            raise ValueError(
                f"Marketplace ID invalide '{v}'. "
                f"IDs supportés: {list(valid_marketplaces.keys())}"
            )
        return v
    
    @validator('region')
    def validate_region_marketplace_consistency(cls, v, values):
        """Vérifier la cohérence région-marketplace"""
        marketplace_id = values.get('marketplace_id')
        if not marketplace_id:
            return v
        
        # Mapping marketplace → région
        marketplace_regions = {
            'ATVPDKIKX0DER': AmazonRegion.NA,  # US
            'A2EUQ1WTGCTBG2': AmazonRegion.NA, # CA  
            'A1AM78C64UM0Y8': AmazonRegion.NA, # MX
            
            'A1PA6795UKMFR9': AmazonRegion.EU, # DE
            'A1RKKUPIHCS9HS': AmazonRegion.EU, # ES
            'A13V1IB3VIYZZH': AmazonRegion.EU, # FR
            'APJ6JRA9NG5V4': AmazonRegion.EU,  # IT
            'A1F83G8C2ARO7P': AmazonRegion.EU, # UK
            'A21TJRUUN4KGV': AmazonRegion.EU,  # IN
            
            'A1VC38T7YXB528': AmazonRegion.FE, # JP
            'ARBP9OOSHTCHU': AmazonRegion.FE   # EG
        }
        
        expected_region = marketplace_regions.get(marketplace_id)
        if expected_region and v != expected_region:
            raise ValueError(
                f"Région '{v}' incompatible avec marketplace '{marketplace_id}'. "
                f"Région attendue: '{expected_region}'"
            )
        
        return v

class ConnectionRequest(BaseModel):
    """Requête de création de connexion Amazon"""
    marketplace_id: str = Field(..., description="ID du marketplace Amazon")
    region: Optional[AmazonRegion] = Field(None, description="Région (auto-détectée si non fournie)")
    
    @validator('marketplace_id')
    def validate_marketplace_id(cls, v):
        return AmazonConnection.validate_marketplace_id(v)

class ConnectionResponse(BaseModel):
    """Réponse de création de connexion"""
    connection_id: str = Field(..., description="ID unique de la connexion")
    authorization_url: str = Field(..., description="URL d'autorisation Amazon")
    state: str = Field(..., description="State OAuth pour sécurité CSRF")
    expires_at: datetime = Field(..., description="Expiration du state OAuth")
    marketplace_id: str = Field(..., description="ID du marketplace")
    region: str = Field(..., description="Région Amazon")

class ConnectionStatus(BaseModel):
    """Status d'une connexion existante"""
    connection_id: str
    user_id: str
    marketplace_id: str
    seller_id: Optional[str] = None
    region: str
    status: str
    connected_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    error_message: Optional[str] = None

class OAuthCallback(BaseModel):
    """Données de callback OAuth Amazon"""
    state: str = Field(..., description="State OAuth pour validation CSRF")
    selling_partner_id: str = Field(..., description="ID du partenaire vendeur")
    spapi_oauth_code: str = Field(..., description="Code d'autorisation OAuth")
    mws_auth_token: Optional[str] = Field(None, description="Token MWS si app hybride")

class TokenData(BaseModel):
    """
    Données de tokens Amazon (JAMAIS loggé)
    Modèle interne uniquement pour manipulation sécurisée
    """
    access_token: str = Field(..., description="Token d'accès Amazon")
    refresh_token: str = Field(..., description="Token de rafraîchissement")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(default=3600, description="Durée de validité en secondes")
    expires_at: datetime = Field(..., description="Date d'expiration calculée")
    scope: Optional[str] = Field(None, description="Portée des autorisations")
    
    class Config:
        """Configuration de sécurité - empêche le logging accidentel"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Ne jamais permettre la sérialisation accidentelle
        allow_mutation = False

class AmazonMarketplace(BaseModel):
    """Informations sur un marketplace Amazon"""
    marketplace_id: str
    country_code: str
    currency: str
    name: str
    region: AmazonRegion
    
    class Config:
        schema_extra = {
            "example": {
                "marketplace_id": "A13V1IB3VIYZZH",
                "country_code": "FR",
                "currency": "EUR", 
                "name": "Amazon.fr",
                "region": "eu"
            }
        }

# Marketplaces supportés par défaut
SUPPORTED_MARKETPLACES = [
    AmazonMarketplace(
        marketplace_id="A13V1IB3VIYZZH",
        country_code="FR",
        currency="EUR",
        name="Amazon.fr",
        region=AmazonRegion.EU
    ),
    AmazonMarketplace(
        marketplace_id="A1PA6795UKMFR9", 
        country_code="DE",
        currency="EUR",
        name="Amazon.de",
        region=AmazonRegion.EU
    ),
    AmazonMarketplace(
        marketplace_id="ATVPDKIKX0DER",
        country_code="US", 
        currency="USD",
        name="Amazon.com",
        region=AmazonRegion.NA
    ),
    AmazonMarketplace(
        marketplace_id="A1F83G8C2ARO7P",
        country_code="UK",
        currency="GBP",
        name="Amazon.co.uk", 
        region=AmazonRegion.EU
    ),
    AmazonMarketplace(
        marketplace_id="APJ6JRA9NG5V4",
        country_code="IT",
        currency="EUR",
        name="Amazon.it",
        region=AmazonRegion.EU
    ),
    AmazonMarketplace(
        marketplace_id="A1RKKUPIHCS9HS",
        country_code="ES",
        currency="EUR", 
        name="Amazon.es",
        region=AmazonRegion.EU
    )
]

class ConnectionHealthCheck(BaseModel):
    """Résultat de vérification de santé des connexions"""
    total_connections: int = Field(default=0)
    active_connections: int = Field(default=0)
    pending_connections: int = Field(default=0)
    error_connections: int = Field(default=0)
    revoked_connections: int = Field(default=0)
    regions_active: List[str] = Field(default_factory=list)
    oldest_connection: Optional[datetime] = None
    newest_connection: Optional[datetime] = None
    health_status: str = Field(default="unknown")
    checked_at: datetime = Field(default_factory=datetime.utcnow)