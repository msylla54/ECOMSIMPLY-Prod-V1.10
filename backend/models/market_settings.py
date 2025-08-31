"""
Modèles pour le scraping prix multi-pays et règles de publication
ECOMSIMPLY Bloc 4 — Phase 4: Market Settings & Price Guards
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class MarketSettings(BaseModel):
    """
    Configuration des paramètres de marché par boutique
    Gère les settings pays, devise, et price guards
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    shop_id: Optional[str] = None  # ID de la boutique e-commerce liée
    
    # Configuration géographique
    country_code: str = Field(..., description="Code pays ISO 3166-1 alpha-2 (FR, GB, US)")
    currency_preference: str = Field(..., description="Devise préférée (EUR, GBP, USD)")
    
    # État d'activation
    enabled: bool = Field(default=True, description="Activer le scraping pour ce marché")
    
    # Price Guards - Fourchette absolue
    price_publish_min: Optional[float] = Field(None, description="Prix minimum pour auto-publication", ge=0)
    price_publish_max: Optional[float] = Field(None, description="Prix maximum pour auto-publication", ge=0)
    
    # Price Guards - Variance relative
    price_variance_threshold: float = Field(default=0.20, description="Seuil de variance relative (défaut 20%)", ge=0, le=1)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('country_code')
    def validate_country_code(cls, v):
        """Valider le code pays supporté"""
        supported_countries = ['FR', 'GB', 'US']
        if v.upper() not in supported_countries:
            raise ValueError(f"Code pays non supporté: {v}. Supportés: {supported_countries}")
        return v.upper()
    
    @validator('currency_preference')
    def validate_currency(cls, v):
        """Valider la devise supportée"""
        supported_currencies = ['EUR', 'GBP', 'USD']
        if v.upper() not in supported_currencies:
            raise ValueError(f"Devise non supportée: {v}. Supportées: {supported_currencies}")
        return v.upper()
    
    @validator('price_publish_max')
    def validate_price_range(cls, v, values):
        """Valider que max > min si les deux sont définis"""
        if v is not None and values.get('price_publish_min') is not None:
            if v <= values['price_publish_min']:
                raise ValueError("Le prix maximum doit être supérieur au prix minimum")
        return v


class MarketSource(BaseModel):
    """
    Configuration des sources de scraping par pays
    Définit quelles sources utiliser selon le marché
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    country_code: str = Field(..., description="Code pays (FR, GB, US)")
    source_name: str = Field(..., description="Nom de la source (Amazon.fr, Fnac, etc.)")
    source_type: str = Field(..., description="Type de source (ecommerce, aggregator)")
    base_url: str = Field(..., description="URL de base pour le scraping")
    
    # Configuration source
    enabled: bool = Field(default=True, description="Source activée")
    priority: int = Field(default=1, description="Priorité (1=haute, 5=basse)", ge=1, le=5)
    
    # Configuration technique
    rate_limit_per_minute: int = Field(default=10, description="Limite de requêtes par minute")
    timeout_ms: int = Field(default=12000, description="Timeout en millisecondes")
    retry_count: int = Field(default=3, description="Nombre de tentatives")
    
    # Sélecteurs CSS pour le scraping
    price_selectors: List[str] = Field(default_factory=list, description="Sélecteurs CSS pour le prix")
    currency_selectors: List[str] = Field(default_factory=list, description="Sélecteurs CSS pour la devise")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_successful_scrape: Optional[datetime] = None
    success_rate: float = Field(default=0.0, description="Taux de succès (0.0-1.0)", ge=0, le=1)


class PriceSnapshot(BaseModel):
    """
    Instantané d'un prix collecté depuis une source
    Stocke les données brutes de scraping avec horodatage
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(..., description="ID de corrélation (shop_id + sku + country)")
    
    # Identification produit
    sku: Optional[str] = Field(None, description="SKU ou identifiant produit")
    product_name: str = Field(..., description="Nom du produit")
    
    # Identification géographique
    country_code: str = Field(..., description="Code pays de collecte")
    source_name: str = Field(..., description="Source de collecte")
    
    # Données prix
    price: float = Field(..., description="Prix collecté", ge=0)
    currency: str = Field(..., description="Devise du prix")
    price_eur: Optional[float] = Field(None, description="Prix converti en EUR si applicable")
    
    # Métadonnées de collecte
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    scrape_duration_ms: Optional[int] = Field(None, description="Durée du scraping en ms")
    success: bool = Field(default=True, description="Collecte réussie")
    error_message: Optional[str] = Field(None, description="Message d'erreur si échec")
    
    # Données contextuelles
    source_url: Optional[str] = Field(None, description="URL de la page scrapée")
    user_agent: Optional[str] = Field(None, description="User-Agent utilisé")


class PriceAggregation(BaseModel):
    """
    Résultat d'agrégation des prix pour un produit/pays
    Contient le prix de référence et les statistiques
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(..., description="ID de corrélation")
    
    # Identification
    product_name: str = Field(..., description="Nom du produit")
    country_code: str = Field(..., description="Code pays")
    currency: str = Field(..., description="Devise de référence")
    
    # Prix agrégés
    reference_price: float = Field(..., description="Prix de référence (médiane)", ge=0)
    min_price: float = Field(..., description="Prix minimum trouvé", ge=0)
    max_price: float = Field(..., description="Prix maximum trouvé", ge=0)
    avg_price: float = Field(..., description="Prix moyen", ge=0)
    price_variance: float = Field(..., description="Variance des prix (écart-type/moyenne)", ge=0)
    
    # Statistiques de collecte
    sources_count: int = Field(..., description="Nombre de sources utilisées", ge=1)
    successful_sources: int = Field(..., description="Nombre de sources réussies", ge=1)
    collection_success_rate: float = Field(..., description="Taux de succès de collecte", ge=0, le=1)
    
    # Price Guards évaluation
    within_absolute_bounds: bool = Field(..., description="Dans les bornes absolues min/max")
    within_variance_threshold: bool = Field(..., description="Variance sous le seuil")
    publish_recommendation: str = Field(..., description="Recommandation: APPROVE, PENDING_REVIEW, REJECT")
    
    # Métadonnées
    aggregated_at: datetime = Field(default_factory=datetime.utcnow)
    snapshots_used: List[str] = Field(default_factory=list, description="IDs des snapshots utilisés")
    
    # Détails pour debug
    aggregation_method: str = Field(default="median", description="Méthode d'agrégation utilisée")
    quality_score: float = Field(default=0.0, description="Score de qualité des données", ge=0, le=1)


class ExchangeRate(BaseModel):
    """
    Taux de change pour conversion des devises
    Cache les taux avec TTL pour éviter les appels répétés
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Devises
    base_currency: str = Field(..., description="Devise de base")
    target_currency: str = Field(..., description="Devise cible")
    rate: float = Field(..., description="Taux de change", gt=0)
    
    # Métadonnées
    provider: str = Field(..., description="Fournisseur du taux (exchangerate.host, OXR)")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Date d'expiration du cache")
    
    # Qualité des données
    reliability_score: float = Field(default=1.0, description="Score de fiabilité", ge=0, le=1)


# Configuration des sources par défaut
DEFAULT_MARKET_SOURCES = {
    "FR": [
        {
            "source_name": "Amazon.fr",
            "source_type": "ecommerce",
            "base_url": "https://www.amazon.fr",
            "priority": 1,
            "price_selectors": [".a-price-whole", ".a-offscreen", "[data-a-size='xl'] .a-price"],
            "currency_selectors": [".a-price-symbol"]
        },
        {
            "source_name": "Fnac",
            "source_type": "ecommerce", 
            "base_url": "https://www.fnac.com",
            "priority": 2,
            "price_selectors": [".f-priceBox-price", ".price"],
            "currency_selectors": [".f-priceBox-currency"]
        },
        {
            "source_name": "Darty",
            "source_type": "ecommerce",
            "base_url": "https://www.darty.com",
            "priority": 3,
            "price_selectors": [".darty_prix", ".product_price"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Cdiscount", 
            "source_type": "ecommerce",
            "base_url": "https://www.cdiscount.com",
            "priority": 3,
            "price_selectors": [".price", ".fpPrice"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Google Shopping FR",
            "source_type": "aggregator",
            "base_url": "https://www.google.fr/shopping",
            "priority": 4,
            "price_selectors": ["[data-value]", ".price"],
            "currency_selectors": [".currency"]
        }
    ],
    "GB": [
        {
            "source_name": "Amazon.co.uk",
            "source_type": "ecommerce",
            "base_url": "https://www.amazon.co.uk",
            "priority": 1,
            "price_selectors": [".a-price-whole", ".a-offscreen"],
            "currency_selectors": [".a-price-symbol"]
        },
        {
            "source_name": "Argos",
            "source_type": "ecommerce",
            "base_url": "https://www.argos.co.uk",
            "priority": 2,
            "price_selectors": [".price", ".product-price"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Currys",
            "source_type": "ecommerce",
            "base_url": "https://www.currys.co.uk",
            "priority": 2,
            "price_selectors": [".price", ".current-price"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Google Shopping UK",
            "source_type": "aggregator", 
            "base_url": "https://www.google.co.uk/shopping",
            "priority": 4,
            "price_selectors": ["[data-value]", ".price"],
            "currency_selectors": [".currency"]
        }
    ],
    "US": [
        {
            "source_name": "Amazon.com",
            "source_type": "ecommerce",
            "base_url": "https://www.amazon.com",
            "priority": 1,
            "price_selectors": [".a-price-whole", ".a-offscreen"],
            "currency_selectors": [".a-price-symbol"]
        },
        {
            "source_name": "BestBuy",
            "source_type": "ecommerce",
            "base_url": "https://www.bestbuy.com",
            "priority": 2,
            "price_selectors": [".price", ".sr-only"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Walmart",
            "source_type": "ecommerce",
            "base_url": "https://www.walmart.com", 
            "priority": 2,
            "price_selectors": ["[data-automation-id='product-price']"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Target",
            "source_type": "ecommerce",
            "base_url": "https://www.target.com",
            "priority": 3,
            "price_selectors": ["[data-test='product-price']"],
            "currency_selectors": [".currency"]
        },
        {
            "source_name": "Google Shopping US",
            "source_type": "aggregator",
            "base_url": "https://www.google.com/shopping",
            "priority": 4,
            "price_selectors": ["[data-value]", ".price"],
            "currency_selectors": [".currency"]
        }
    ]
}

# Mapping des devises par défaut par pays
DEFAULT_CURRENCY_BY_COUNTRY = {
    "FR": "EUR",
    "GB": "GBP", 
    "US": "USD"
}