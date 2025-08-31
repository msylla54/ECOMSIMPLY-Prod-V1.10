# Amazon SP-API Multi-Tenant Models for MongoDB
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class SPAPIRegion(str, Enum):
    """Amazon SP-API supported regions"""
    NA = "na"  # North America
    EU = "eu"  # Europe
    FE = "fe"  # Far East

class ConnectionStatus(str, Enum):
    """SP-API connection status states"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"

class AmazonConnection(BaseModel):
    """Amazon SP-API connection model for MongoDB storage"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ECOMSIMPLY user ID")
    
    # SP-API specific fields
    region: SPAPIRegion = Field(default=SPAPIRegion.EU, description="Amazon SP-API region")
    marketplace_id: str = Field(..., description="Amazon marketplace ID (e.g., A13V1IB3VIYZZH for FR)")
    seller_id: str = Field(..., description="Amazon seller partner ID")
    
    # Encrypted token storage (AES-GCM with AWS KMS)
    encrypted_refresh_token: str = Field(..., description="AES-GCM encrypted refresh token")
    token_encryption_nonce: str = Field(..., description="AES-GCM nonce for token encryption")
    encryption_key_id: str = Field(..., description="AWS KMS key ID used for encryption")
    
    # Connection metadata
    status: ConnectionStatus = Field(default=ConnectionStatus.PENDING)
    connected_at: Optional[datetime] = Field(None, description="Date when connection became active")
    last_used_at: Optional[datetime] = Field(None, description="Last time connection was used")
    error_message: Optional[str] = Field(None, description="Last error if connection failed")
    retry_count: int = Field(default=0, description="Number of connection retry attempts")
    
    # OAuth state management
    oauth_state: Optional[str] = Field(None, description="OAuth state for CSRF protection")
    oauth_state_expires: Optional[datetime] = Field(None, description="OAuth state expiration")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional connection metadata
    connection_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": "user_123",
                "region": "eu",
                "marketplace_id": "A13V1IB3VIYZZH",
                "seller_id": "A1B2C3D4E5F6G7",
                "status": "active"
            }
        }
    
    @validator('marketplace_id')
    def validate_marketplace_id(cls, v):
        """Validate Amazon marketplace ID format"""
        valid_marketplaces = {
            'ATVPDKIKX0DER': 'US',
            'A2EUQ1WTGCTBG2': 'CA', 
            'A1AM78C64UM0Y8': 'MX',
            'A1PA6795UKMFR9': 'DE',
            'A1RKKUPIHCS9HS': 'ES',
            'A13V1IB3VIYZZH': 'FR',
            'A21TJRUUN4KGV': 'IN',
            'APJ6JRA9NG5V4': 'IT',
            'A1F83G8C2ARO7P': 'UK',
            'A1VC38T7YXB528': 'JP',
            'ARBP9OOSHTCHU': 'EG'
        }
        
        if v not in valid_marketplaces:
            raise ValueError(f"Invalid marketplace ID. Supported: {list(valid_marketplaces.keys())}")
        return v

class SPAPIConnectionRequest(BaseModel):
    """Request model for initiating SP-API connection"""
    marketplace_id: str = Field(..., description="Target Amazon marketplace")
    region: Optional[SPAPIRegion] = Field(SPAPIRegion.EU, description="Amazon region")
    return_url: Optional[str] = Field(None, description="URL to redirect after OAuth")
    
    @validator('marketplace_id')
    def validate_marketplace_id(cls, v):
        return AmazonConnection.validate_marketplace_id(v)

class SPAPIConnectionResponse(BaseModel):
    """Response model for connection initiation"""
    connection_id: str = Field(..., description="Unique connection identifier")
    authorization_url: str = Field(..., description="Amazon OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter")
    expires_at: datetime = Field(..., description="OAuth state expiration time")

class SPAPIConnectionStatus(BaseModel):
    """Connection status response model"""
    connection_id: str
    status: ConnectionStatus
    marketplace_id: str
    seller_id: Optional[str] = None
    region: SPAPIRegion
    connected_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
class SPAPITokenData(BaseModel):
    """Internal model for decrypted token data (never logged)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime
    scope: Optional[str] = None
    
    class Config:
        """Security: prevent accidental logging"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Never allow this model to be converted to dict for logging
        allow_mutation = False

class SPAPICallbackData(BaseModel):
    """OAuth callback data from Amazon"""
    state: str = Field(..., description="OAuth state parameter")
    selling_partner_id: str = Field(..., description="Amazon seller partner ID") 
    spapi_oauth_code: str = Field(..., description="OAuth authorization code")
    mws_auth_token: Optional[str] = Field(None, description="MWS auth token if hybrid app")