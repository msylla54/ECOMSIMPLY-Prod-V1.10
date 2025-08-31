"""
Constants - Plateformes supportées par ECOMSIMPLY
"""

# Plateformes e-commerce supportées
STORES = [
    "shopify",
    "woocommerce", 
    "prestashop",
    "magento",
    "wix",
    "squarespace",
    "bigcommerce"
]

# Configuration par défaut publication
DEFAULT_PUBLICATION_CONFIG = {
    "active_hours_start": 8,
    "active_hours_end": 20,
    "max_publications_per_hour": 10,
    "cooldown_between_publications": 300,  # 5 minutes
    "batch_size": 3,
    "max_concurrent_workers": 2,
    "max_retries": 3,
    "retry_delay": 1800,  # 30 minutes
    "enable_price_guardrails": True,
    "price_variance_threshold": 0.20,  # 20%
    "min_confidence_score": 0.6
}

# Rate limiting par store (tokens par heure)
STORE_RATE_LIMITS = {
    "shopify": 15,      # Plus généreux car API robuste
    "woocommerce": 12,  # WordPress peut être plus lent
    "prestashop": 10,   # Standard
    "magento": 8,       # Plus conservatif car complexe
    "wix": 6,           # Limited par Wix API
    "squarespace": 5,   # Plus restrictif
    "bigcommerce": 12   # API robuste
}

# Retry policies par store
STORE_RETRY_POLICIES = {
    "shopify": {"max_retries": 5, "base_delay": 1200},     # Plus tolérant
    "woocommerce": {"max_retries": 3, "base_delay": 1800}, # Standard  
    "prestashop": {"max_retries": 3, "base_delay": 1800},
    "magento": {"max_retries": 2, "base_delay": 2400},     # Moins de retries car plus complexe
    "wix": {"max_retries": 2, "base_delay": 3600},         # Plus conservatif
    "squarespace": {"max_retries": 2, "base_delay": 3600},
    "bigcommerce": {"max_retries": 4, "base_delay": 1500}  # Good API
}