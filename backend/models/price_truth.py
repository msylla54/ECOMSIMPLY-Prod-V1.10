"""
Modèles Pydantic pour le système PriceTruth - Vérification de prix en temps réel
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorDatabase


class ConsensusPriceStatus(str, Enum):
    """Statut du consensus de prix"""
    VALID = "valid"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    OUTLIER_DETECTED = "outlier_detected"
    STALE_DATA = "stale_data"


class PriceSource(BaseModel):
    """Source individuelle de prix"""
    name: str = Field(..., description="Nom de la source (amazon, google_shopping, cdiscount, fnac)")
    price: Decimal = Field(..., description="Prix trouvé")
    currency: str = Field(default="EUR", description="Devise")
    url: str = Field(..., description="URL de la page produit")
    screenshot: Optional[str] = Field(None, description="Chemin vers screenshot PNG")
    selector: str = Field(..., description="Sélecteur CSS utilisé")
    ts: datetime = Field(default_factory=datetime.now, description="Timestamp de récupération")
    success: bool = Field(default=True, description="Succès de l'extraction")
    error_message: Optional[str] = Field(None, description="Message d'erreur si échec")

    @validator('price', pre=True)
    def validate_price(cls, v):
        """Convertit le prix en Decimal pour éviter les erreurs de float"""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PriceConsensus(BaseModel):
    """Consensus calculé sur les prix"""
    method: str = Field(default="median_trim", description="Méthode de consensus utilisée")
    agreeing_sources: int = Field(..., description="Nombre de sources concordantes")
    median_price: Optional[Decimal] = Field(None, description="Prix médian calculé")
    stdev: Optional[float] = Field(None, description="Écart-type des prix")
    outliers: List[str] = Field(default_factory=list, description="Sources détectées comme outliers")
    tolerance_pct: float = Field(default=3.0, description="Tolérance en % pour le consensus")
    status: ConsensusPriceStatus = Field(..., description="Statut du consensus")

    @validator('median_price', pre=True)
    def validate_median_price(cls, v):
        """Convertit le prix médian en Decimal"""
        if v is not None and isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class PriceTruth(BaseModel):
    """Modèle principal pour une vérité de prix"""
    sku: str = Field(..., description="SKU ou identifiant produit")
    query: str = Field(..., description="Requête de recherche utilisée")
    currency: str = Field(default="EUR", description="Devise finale")
    value: Optional[Decimal] = Field(None, description="Prix final validé (si consensus OK)")
    sources: List[PriceSource] = Field(default_factory=list, description="Sources de prix consultées")
    consensus: PriceConsensus = Field(..., description="Consensus calculé")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp de mise à jour")
    ttl_hours: int = Field(default=6, description="TTL en heures (freshness SLA)")
    
    # Métadonnées additionnelles
    product_name: Optional[str] = Field(None, description="Nom du produit")
    category: Optional[str] = Field(None, description="Catégorie produit")
    brand: Optional[str] = Field(None, description="Marque")
    
    @validator('value', pre=True)
    def validate_value(cls, v):
        """Convertit la valeur finale en Decimal"""
        if v is not None and isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @property
    def is_fresh(self) -> bool:
        """Vérifie si les données sont encore fraîches (< TTL)"""
        now = datetime.now()
        elapsed_hours = (now - self.updated_at).total_seconds() / 3600
        return elapsed_hours < self.ttl_hours

    @property
    def has_valid_consensus(self) -> bool:
        """Vérifie si le consensus est valide"""
        return (
            self.consensus.status == ConsensusPriceStatus.VALID and
            self.consensus.agreeing_sources >= 2 and
            self.value is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour MongoDB"""
        data = self.dict()
        # Convertir les Decimal en float pour MongoDB
        if data.get('value'):
            data['value'] = float(data['value'])
        if data.get('consensus', {}).get('median_price'):
            data['consensus']['median_price'] = float(data['consensus']['median_price'])
        for source in data.get('sources', []):
            if source.get('price'):
                source['price'] = float(source['price'])
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceTruth':
        """Crée une instance depuis un dictionnaire MongoDB"""
        # Convertir les float en Decimal
        if data.get('value'):
            data['value'] = Decimal(str(data['value']))
        if data.get('consensus', {}).get('median_price'):
            data['consensus']['median_price'] = Decimal(str(data['consensus']['median_price']))
        for source in data.get('sources', []):
            if source.get('price'):
                source['price'] = Decimal(str(source['price']))
        return cls(**data)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None,
            datetime: lambda v: v.isoformat()
        }


class PriceTruthResponse(BaseModel):
    """Réponse API pour les prix vérifiés"""
    sku: str
    query: str
    price: Optional[float] = Field(None, description="Prix final (None si pas de consensus)")
    currency: str = Field(default="EUR")
    status: ConsensusPriceStatus
    sources_count: int = Field(..., description="Nombre de sources consultées")
    agreeing_sources: int = Field(..., description="Nombre de sources concordantes")
    updated_at: datetime
    is_fresh: bool = Field(..., description="Données < TTL")
    next_update_eta: Optional[datetime] = Field(None, description="Prochaine mise à jour estimée")
    
    # Détails pour debug/admin
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Détails des sources (si demandé)")
    consensus_details: Optional[Dict[str, Any]] = Field(None, description="Détails du consensus (si demandé)")


class PriceTruthRefreshRequest(BaseModel):
    """Requête de rafraîchissement forcé"""
    sku: Optional[str] = None
    query: Optional[str] = None
    force: bool = Field(default=False, description="Forcer même si les données sont fraîches")
    sources: Optional[List[str]] = Field(None, description="Sources spécifiques à utiliser")


# Configuration de la base de données MongoDB
class PriceTruthDatabase:
    """Gestionnaire de base de données pour PriceTruth"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.prices_truth
    
    async def ensure_indexes(self):
        """Crée les index nécessaires"""
        await self.collection.create_index("sku", unique=False)
        await self.collection.create_index("updated_at")
        await self.collection.create_index([("sku", 1), ("updated_at", -1)])
        await self.collection.create_index("query")
    
    async def upsert_price_truth(self, price_truth: PriceTruth) -> bool:
        """Insert ou update une vérité de prix"""
        try:
            result = await self.collection.replace_one(
                {"sku": price_truth.sku},
                price_truth.to_dict(),
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            print(f"❌ Erreur upsert PriceTruth: {e}")
            return False
    
    async def get_price_truth(self, sku: str) -> Optional[PriceTruth]:
        """Récupère une vérité de prix par SKU"""
        try:
            data = await self.collection.find_one({"sku": sku})
            if data:
                # Supprimer l'_id MongoDB pour éviter les problèmes
                data.pop('_id', None)
                return PriceTruth.from_dict(data)
            return None
        except Exception as e:
            print(f"❌ Erreur get PriceTruth: {e}")
            return None
    
    async def search_by_query(self, query: str) -> Optional[PriceTruth]:
        """Recherche par requête"""
        try:
            data = await self.collection.find_one(
                {"query": {"$regex": query, "$options": "i"}}
            )
            if data:
                data.pop('_id', None)
                return PriceTruth.from_dict(data)
            return None
        except Exception as e:
            print(f"❌ Erreur search PriceTruth: {e}")
            return None
    
    async def get_stale_records(self, ttl_hours: int = 6) -> List[PriceTruth]:
        """Récupère les enregistrements périmés pour refresh"""
        try:
            cutoff = datetime.now()
            cutoff = cutoff.replace(hour=cutoff.hour - ttl_hours)
            
            cursor = self.collection.find({"updated_at": {"$lt": cutoff}})
            records = []
            async for data in cursor:
                data.pop('_id', None)
                records.append(PriceTruth.from_dict(data))
            return records
        except Exception as e:
            print(f"❌ Erreur get_stale_records: {e}")
            return []