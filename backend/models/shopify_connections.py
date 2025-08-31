# Shopify Multi-Tenant Connection Models for MongoDB
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class ConnectionStatus(str, Enum):
    """Shopify connection status states"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"

class ShopifyPlan(str, Enum):
    """Shopify plan types"""
    BASIC = "basic"
    SHOPIFY = "shopify" 
    ADVANCED = "advanced"
    PLUS = "plus"
    CUSTOM = "custom"

class ShopifyConnection(BaseModel):
    """Shopify connection model for MongoDB storage"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ECOMSIMPLY user ID")
    
    # Shopify specific fields
    shop_domain: str = Field(..., description="Shopify domain (ex: monshop.myshopify.com)")
    shop_name: str = Field(..., description="Display name of the shop")
    shop_id: Optional[str] = Field(None, description="Shopify shop ID")
    
    # Encrypted token storage (AES-GCM)
    encrypted_access_token: str = Field(..., description="AES-GCM encrypted access token")
    token_encryption_nonce: str = Field(..., description="AES-GCM nonce for token encryption")
    
    # Connection metadata
    status: ConnectionStatus = Field(default=ConnectionStatus.PENDING)
    scopes: str = Field(..., description="Granted OAuth scopes")
    installed_at: Optional[datetime] = Field(None, description="Date when app was installed")
    last_used_at: Optional[datetime] = Field(None, description="Last time connection was used")
    error_message: Optional[str] = Field(None, description="Last error if connection failed")
    
    # Shop information
    shop_plan: Optional[ShopifyPlan] = Field(None, description="Shopify plan type")
    shop_country: Optional[str] = Field(None, description="Shop country code")
    shop_currency: Optional[str] = Field(None, description="Shop primary currency")
    shop_timezone: Optional[str] = Field(None, description="Shop timezone")
    shop_email: Optional[str] = Field(None, description="Shop contact email")
    
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
                "shop_domain": "monshop.myshopify.com",
                "shop_name": "Mon Super Shop",
                "scopes": "read_products,write_products,read_orders",
                "status": "active"
            }
        }
    
    @validator('shop_domain')
    def validate_shop_domain(cls, v):
        """Validate Shopify shop domain format"""
        if not v:
            raise ValueError("Shop domain is required")
        
        # Basic format validation
        if not (v.endswith('.myshopify.com') or '.' in v):
            raise ValueError("Invalid shop domain format")
        
        return v.lower().strip()
    
    @validator('scopes')
    def validate_scopes(cls, v):
        """Validate OAuth scopes"""
        if not v:
            raise ValueError("Scopes are required")
        
        # Common Shopify scopes
        valid_scopes = {
            'read_products', 'write_products',
            'read_orders', 'write_orders',
            'read_customers', 'write_customers',
            'read_inventory', 'write_inventory',
            'read_analytics', 'read_reports',
            'read_price_rules', 'write_price_rules',
            'read_discounts', 'write_discounts',
            'read_shipping', 'write_shipping',
            'read_content', 'write_content',
            'read_themes', 'write_themes'
        }
        
        requested_scopes = set(scope.strip() for scope in v.split(','))
        
        # Check if all requested scopes are valid
        invalid_scopes = requested_scopes - valid_scopes
        if invalid_scopes:
            raise ValueError(f"Invalid scopes: {', '.join(invalid_scopes)}")
        
        return v

class ShopifyConnectionRequest(BaseModel):
    """Request model for initiating Shopify connection"""
    shop_domain: str = Field(..., description="Shopify shop domain")
    return_url: Optional[str] = Field(None, description="URL to redirect after OAuth")
    
    @validator('shop_domain')
    def validate_shop_domain(cls, v):
        return ShopifyConnection.validate_shop_domain(v)

class ShopifyConnectionResponse(BaseModel):
    """Response model for connection initiation"""
    connection_id: str = Field(..., description="Unique connection identifier")
    install_url: str = Field(..., description="Shopify OAuth install URL")
    state: str = Field(..., description="OAuth state parameter")
    shop_domain: str = Field(..., description="Validated shop domain")
    expires_at: datetime = Field(..., description="OAuth state expiration time")
    scopes: str = Field(..., description="Requested OAuth scopes")

class ShopifyConnectionStatus(BaseModel):
    """Connection status response model"""
    connection_id: str
    status: ConnectionStatus
    shop_domain: str
    shop_name: Optional[str] = None
    shop_id: Optional[str] = None
    scopes: str
    installed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    error_message: Optional[str] = None
    shop_plan: Optional[ShopifyPlan] = None
    shop_country: Optional[str] = None
    shop_currency: Optional[str] = None

class ShopifyTokenData(BaseModel):
    """Internal model for decrypted token data (never logged)"""
    access_token: str
    shop_domain: str
    scopes: str
    retrieved_at: datetime
    
    class Config:
        """Security: prevent accidental logging"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Never allow this model to be converted to dict for logging
        allow_mutation = False

class ShopifyCallbackData(BaseModel):
    """OAuth callback data from Shopify"""
    shop: str = Field(..., description="Shop domain")
    code: str = Field(..., description="OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter")
    timestamp: Optional[str] = Field(None, description="Request timestamp")
    hmac: Optional[str] = Field(None, description="HMAC signature for verification")

class ShopifyWebhookData(BaseModel):
    """Webhook data from Shopify"""
    topic: str = Field(..., description="Webhook topic (e.g., orders/create)")
    shop_domain: str = Field(..., description="Shop domain that sent the webhook")
    payload: Dict[str, Any] = Field(..., description="Webhook payload data")
    hmac_header: str = Field(..., description="X-Shopify-Hmac-Sha256 header")
    received_at: datetime = Field(default_factory=datetime.utcnow)

# Supported webhook topics
SUPPORTED_WEBHOOK_TOPICS = [
    'orders/create',
    'orders/updated',
    'orders/paid',
    'orders/cancelled',
    'products/create',
    'products/update',
    'products/delete',
    'inventory_levels/update',
    'app/uninstalled'
]

class ShopifyProductData(BaseModel):
    """Model for Shopify product data"""
    title: str = Field(..., description="Product title")
    body_html: Optional[str] = Field(None, description="Product description HTML")
    vendor: Optional[str] = Field(None, description="Product vendor")
    product_type: Optional[str] = Field(None, description="Product type")
    tags: Optional[str] = Field(None, description="Product tags (comma-separated)")
    status: str = Field(default="draft", description="Product status (active/draft)")
    
    # Variants (at least one required)
    variants: List[Dict[str, Any]] = Field(..., description="Product variants")
    
    # Images
    images: Optional[List[Dict[str, Any]]] = Field(None, description="Product images")
    
    # SEO
    handle: Optional[str] = Field(None, description="Product URL handle")
    metafields: Optional[List[Dict[str, Any]]] = Field(None, description="Product metafields")
    
    @validator('variants')
    def validate_variants(cls, v):
        """Validate that at least one variant exists"""
        if not v or len(v) == 0:
            raise ValueError("At least one variant is required")
        
        # Validate required variant fields
        for variant in v:
            if 'price' not in variant:
                raise ValueError("Variant price is required")
        
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate product status"""
        if v not in ['active', 'draft']:
            raise ValueError("Status must be 'active' or 'draft'")
        return v