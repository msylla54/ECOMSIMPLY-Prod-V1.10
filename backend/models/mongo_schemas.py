# backend/models/mongo_schemas.py
"""
MongoDB Schema Models for ECOMSIMPLY
Pydantic models aligned with MongoDB collections
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic compatibility"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# ==========================================
# USER MODELS
# ==========================================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_admin: bool = False
    isActive: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_admin: Optional[bool] = None
    isActive: Optional[bool] = None
    last_login_at: Optional[datetime] = None

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    passwordHash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# TESTIMONIAL MODELS
# ==========================================

class TestimonialBase(BaseModel):
    authorName: str
    authorRole: str
    content: str
    rating: int = Field(ge=1, le=5)
    avatarUrl: Optional[str] = None
    published: bool = True

class TestimonialCreate(TestimonialBase):
    pass

class TestimonialUpdate(BaseModel):
    authorName: Optional[str] = None
    authorRole: Optional[str] = None
    content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    avatarUrl: Optional[str] = None
    published: Optional[bool] = None

class TestimonialInDB(TestimonialBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# SUBSCRIPTION PLAN MODELS
# ==========================================

class SubscriptionPlanBase(BaseModel):
    plan_id: str
    name: str
    price: float
    currency: str = "EUR"
    period: str = "month"
    features: List[str]
    active: bool = True

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    features: Optional[List[str]] = None
    active: Optional[bool] = None

class SubscriptionPlanInDB(SubscriptionPlanBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# LANGUAGE MODELS
# ==========================================

class LanguageBase(BaseModel):
    code: str
    name: str
    flag: str
    default: bool = False
    active: bool = True

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(BaseModel):
    name: Optional[str] = None
    flag: Optional[str] = None
    default: Optional[bool] = None
    active: Optional[bool] = None

class LanguageInDB(LanguageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# PUBLIC STATS MODELS
# ==========================================

class PublicStatBase(BaseModel):
    key: str
    value: Union[int, float, str]
    category: str = "general"
    display_name: str
    format_type: str = "number"  # number, percentage, text

class PublicStatCreate(PublicStatBase):
    pass

class PublicStatUpdate(BaseModel):
    value: Optional[Union[int, float, str]] = None
    category: Optional[str] = None
    display_name: Optional[str] = None
    format_type: Optional[str] = None

class PublicStatInDB(PublicStatBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# MESSAGE/CONTACT MODELS
# ==========================================

class MessageBase(BaseModel):
    email: EmailStr
    subject: str
    body: str
    source: str = Field(regex="^(contact|chat|support)$")
    status: str = Field(default="new", regex="^(new|read|replied|closed)$")

class MessageCreate(MessageBase):
    userId: Optional[PyObjectId] = None

class MessageUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(new|read|replied|closed)$")
    admin_notes: Optional[str] = None

class MessageInDB(MessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    userId: Optional[PyObjectId] = None
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# AI SESSION MODELS
# ==========================================

class AISessionBase(BaseModel):
    sessionType: str = Field(regex="^(product_generation|seo_optimization|chat|analysis)$")
    model: str
    params: Dict[str, Any] = {}
    
class AISessionCreate(AISessionBase):
    userId: Optional[PyObjectId] = None

class AISessionUpdate(BaseModel):
    closed_at: Optional[datetime] = None
    summary: Optional[str] = None

class AISessionInDB(AISessionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    userId: Optional[PyObjectId] = None
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# AI EVENT MODELS
# ==========================================

class AIEventBase(BaseModel):
    sessionId: PyObjectId
    role: str = Field(regex="^(user|assistant|tool|system)$")
    content: str
    tokens: Optional[int] = None
    latencyMs: Optional[float] = None
    metadata: Dict[str, Any] = {}

class AIEventCreate(AIEventBase):
    pass

class AIEventInDB(AIEventBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# PRODUCT GENERATION MODELS  
# ==========================================

class ProductGenerationInput(BaseModel):
    productData: Dict[str, Any]
    marketplace: str = "amazon"
    language: str = "fr"
    options: Dict[str, Any] = {}

class ProductGenerationResult(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    images: Optional[List[str]] = None
    seo_score: Optional[float] = None
    metadata: Dict[str, Any] = {}

class ProductGenerationBase(BaseModel):
    input: ProductGenerationInput
    status: str = Field(default="pending", regex="^(pending|processing|completed|failed)$")
    cost: Optional[float] = None

class ProductGenerationCreate(ProductGenerationBase):
    userId: PyObjectId

class ProductGenerationUpdate(BaseModel):
    result: Optional[ProductGenerationResult] = None
    status: Optional[str] = Field(None, regex="^(pending|processing|completed|failed)$")
    cost: Optional[float] = None
    error_message: Optional[str] = None
    finished_at: Optional[datetime] = None

class ProductGenerationInDB(ProductGenerationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    userId: PyObjectId
    result: Optional[ProductGenerationResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==========================================
# AFFILIATE CONFIG MODELS
# ==========================================

class AffiliateConfigBase(BaseModel):
    commission_rate: float = Field(ge=0, le=100)
    cookie_duration: int = Field(ge=1, le=365)
    minimum_payout: float = Field(ge=0)
    payment_methods: List[str]
    tracking_enabled: bool = True
    custom_links: bool = True

class AffiliateConfigCreate(AffiliateConfigBase):
    pass

class AffiliateConfigUpdate(BaseModel):
    commission_rate: Optional[float] = Field(None, ge=0, le=100)
    cookie_duration: Optional[int] = Field(None, ge=1, le=365)
    minimum_payout: Optional[float] = Field(None, ge=0)
    payment_methods: Optional[List[str]] = None
    tracking_enabled: Optional[bool] = None
    custom_links: Optional[bool] = None

class AffiliateConfigInDB(AffiliateConfigBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    benefits: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}