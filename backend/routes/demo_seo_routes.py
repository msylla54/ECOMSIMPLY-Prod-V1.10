"""
Demo SEO Routes - Endpoints publics pour tester l'interface SEO Amazon
Routes démo pour validation frontend sans authentification

Author: ECOMSIMPLY
Date: 2025-01-01
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo/amazon/seo", tags=["demo-seo"])

class DemoProduct(BaseModel):
    """Modèle produit pour la démo"""
    product_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: str = "électronique"
    features: List[str] = []
    benefits: List[str] = []
    size: Optional[str] = None
    color: Optional[str] = None

class DemoListing(BaseModel):
    """Modèle listing pour validation"""
    title: str
    bullets: List[str]
    description: str
    backend_keywords: Optional[str] = ""
    images: List[str] = []
    brand: Optional[str] = ""
    model: Optional[str] = ""
    category: str = "électronique"

@router.post("/generate")
async def demo_generate_seo_listing(product: DemoProduct):
    """
    Démo génération listing SEO Amazon A9/A10
    Endpoint public pour tester l'interface sans authentification
    """
    try:
        logger.info(f"🧪 Demo SEO generation for: {product.product_name}")
        
        # Simulation génération SEO optimisée
        demo_listing = {
            "title": f"{product.brand or 'Apple'} {product.product_name} - {product.size or '6,1 pouces'} {product.color or 'Titane Naturel'}",
            "bullets": [
                f"✓ PERFORMANCE: {product.features[0] if product.features else 'Puce A17 Pro avec performances exceptionnelles'}",
                f"✓ AFFICHAGE: {product.features[1] if len(product.features) > 1 else 'Écran Super Retina XDR haute résolution'}",
                f"✓ PHOTO: {product.features[2] if len(product.features) > 2 else 'Système caméra triple 48MP qualité pro'}",
                f"✓ DESIGN: {product.benefits[0] if product.benefits else 'Design premium en titane ultra-résistant'}",
                f"✓ CONNECTIVITÉ: {product.benefits[1] if len(product.benefits) > 1 else 'USB-C universel et 5G ultra-rapide'}"
            ],
            "description": f"""
DÉCOUVREZ LE {product.product_name.upper()}

CARACTÉRISTIQUES PRINCIPALES:
• {product.features[0] if product.features else 'Puce A17 Pro révolutionnaire'}
• {product.features[1] if len(product.features) > 1 else 'Écran Super Retina XDR 6,1 pouces'}
• {product.features[2] if len(product.features) > 2 else 'Système caméra Pro triple 48MP'}

BÉNÉFICES UTILISATEUR:
• {product.benefits[0] if product.benefits else 'Performances gaming exceptionnelles'}
• {product.benefits[1] if len(product.benefits) > 1 else 'Photos et vidéos qualité professionnelle'}
• {product.benefits[2] if len(product.benefits) > 2 else 'Autonomie toute la journée'}

UTILISATION IDÉALE:
Parfait pour les professionnels créatifs, gamers exigeants et utilisateurs premium recherchant performance et style. 
Compatible avec tous les accessoires {product.brand or 'Apple'} et écosystème intégré.

GARANTIE ET SUPPORT:
Garantie constructeur incluse avec support technique premium.
""",
            "backend_keywords": f"{product.product_name.lower()} {product.brand or 'apple'} {product.category} smartphone premium titane pro camera 5g usb-c",
            "images": [
                f"https://example.com/{product.product_name.lower().replace(' ', '-')}-main.jpg",
                f"https://example.com/{product.product_name.lower().replace(' ', '-')}-side.jpg", 
                f"https://example.com/{product.product_name.lower().replace(' ', '-')}-camera.jpg"
            ]
        }
        
        # Validation A9/A10 automatique
        validation = {
            "status": "approved" if len(demo_listing["title"]) <= 200 else "warning",
            "score": 95 if len(demo_listing["title"]) <= 200 and len(demo_listing["bullets"]) == 5 else 85,
            "reasons": [],
            "warnings": [],
            "suggestions": [
                "Titre optimisé pour recherche Amazon",
                "5 bullets structurés par bénéfice",
                "Description riche et engageante",
                "Mots-clés backend optimisés"
            ]
        }
        
        # Ajout warnings si nécessaire
        if len(demo_listing["title"]) > 150:
            validation["warnings"].append("Titre pourrait être raccourci pour optimisation mobile")
        
        if not any("✓" in bullet for bullet in demo_listing["bullets"]):
            validation["suggestions"].append("Ajouter des symboles visuels (✓) dans les bullets")
        
        # Métadonnées 
        metadata = {
            "brand": product.brand or "Apple",
            "model": product.model or "iPhone 15 Pro",
            "category": product.category,
            "a9_a10_compliant": True,
            "seo_optimized": True,
            "generation_time": "2.3s",
            "ai_confidence": 0.96
        }
        
        return {
            "success": True,
            "message": "Listing SEO Amazon généré avec succès",
            "data": {
                "listing": demo_listing,
                "validation": validation,
                "metadata": metadata
            }
        }
        
    except Exception as e:
        logger.error(f"Demo SEO generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo generation failed: {str(e)}")

@router.post("/validate")
async def demo_validate_listing(listing: DemoListing):
    """
    Démo validation listing existant A9/A10
    """
    try:
        logger.info(f"🧪 Demo validation for listing: {listing.title[:50]}...")
        
        # Validation A9/A10
        issues = []
        warnings = []
        suggestions = []
        
        # Titre validation
        title_length = len(listing.title)
        if title_length > 200:
            issues.append(f"Titre trop long: {title_length}/200 caractères")
        elif title_length > 150:
            warnings.append("Titre long mais conforme - optimisation mobile recommandée")
        
        # Bullets validation  
        bullets_count = len(listing.bullets)
        if bullets_count != 5:
            issues.append(f"Nombre de bullets incorrect: {bullets_count}/5 requis")
        
        bullets_too_long = [i for i, bullet in enumerate(listing.bullets) if len(bullet) > 255]
        if bullets_too_long:
            issues.append(f"Bullets trop longs (indices {bullets_too_long}): max 255 caractères")
        
        # Description validation
        desc_length = len(listing.description)
        if desc_length < 100:
            issues.append(f"Description trop courte: {desc_length}/100 caractères minimum")
        elif desc_length > 2000:
            issues.append(f"Description trop longue: {desc_length}/2000 caractères maximum")
        
        # Backend keywords validation
        keywords_bytes = len(listing.backend_keywords.encode('utf-8'))
        if keywords_bytes > 250:
            issues.append(f"Mots-clés backend trop longs: {keywords_bytes}/250 bytes")
        
        # Score calculation
        if issues:
            status = "rejected"
            score = max(30, 70 - len(issues) * 15)
        elif warnings:
            status = "warning"  
            score = 85
        else:
            status = "approved"
            score = 95
        
        # Suggestions automatiques
        if not any("✓" in bullet for bullet in listing.bullets):
            suggestions.append("Ajouter des symboles visuels (✓) dans les bullets pour améliorer la lisibilité")
        
        if listing.brand.lower() not in listing.title.lower():
            suggestions.append("Inclure le nom de marque dans le titre pour l'optimisation SEO")
        
        validation_result = {
            "status": status,
            "score": score,
            "reasons": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "compliance": {
                "title_compliant": title_length <= 200,
                "bullets_compliant": bullets_count == 5 and not bullets_too_long,
                "description_compliant": 100 <= desc_length <= 2000,
                "keywords_compliant": keywords_bytes <= 250
            }
        }
        
        return {
            "success": True,
            "message": f"Validation terminée - Status: {status}",
            "data": {
                "validation": validation_result,
                "listing_analysis": {
                    "title_length": title_length,
                    "bullets_count": bullets_count, 
                    "description_length": desc_length,
                    "keywords_bytes": keywords_bytes
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Demo validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo validation failed: {str(e)}")

@router.post("/optimize")
async def demo_optimize_listing(listing: DemoListing):
    """
    Démo optimisation listing A9/A10
    """
    try:
        logger.info(f"🧪 Demo optimization for: {listing.title[:50]}...")
        
        # Créer version optimisée
        optimized_listing = {
            "title": listing.title[:180] if len(listing.title) > 180 else listing.title,
            "bullets": [bullet[:240] if len(bullet) > 240 else bullet for bullet in listing.bullets[:5]],
            "description": listing.description[:1800] if len(listing.description) > 1800 else listing.description,
            "backend_keywords": listing.backend_keywords[:200] if len(listing.backend_keywords.encode('utf-8')) > 200 else listing.backend_keywords
        }
        
        # Améliorer les bullets si nécessaire
        if not any("✓" in bullet for bullet in optimized_listing["bullets"]):
            optimized_listing["bullets"] = [f"✓ {bullet.lstrip('• -')}" for bullet in optimized_listing["bullets"]]
        
        # Calcul des scores
        original_score = 75  # Score simulé original
        optimized_score = 92  # Score simulé optimisé
        improvement = optimized_score - original_score
        
        recommendations = {
            "should_update": improvement > 5,
            "score_improvement": improvement,
            "changes_made": [
                "Titre raccourci pour conformité mobile",
                "Bullets formatés avec symboles visuels", 
                "Description optimisée pour engagement",
                "Mots-clés backend affinés"
            ]
        }
        
        return {
            "success": True,
            "message": f"Optimisation terminée - Amélioration: +{improvement} points",
            "data": {
                "original": {
                    "listing": dict(listing),
                    "validation": {"score": original_score, "status": "warning"}
                },
                "optimized": {
                    "listing": optimized_listing,
                    "validation": {"score": optimized_score, "status": "approved"}
                },
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Demo optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo optimization failed: {str(e)}")

@router.get("/rules")
async def demo_amazon_rules():
    """Règles Amazon A9/A10 pour référence"""
    return {
        "success": True,
        "data": {
            "amazon_a9_a10_rules": {
                "title": {
                    "max_length": 200,
                    "format": "{Brand} {Model} {Key Feature} {Size} {Color}",
                    "required": True
                },
                "bullets": {
                    "count": 5,
                    "max_length_each": 255,
                    "format": "✓ [CATEGORY]: [Benefit]",
                    "required": True
                },
                "description": {
                    "min_length": 100,
                    "max_length": 2000,
                    "structure": "CARACTÉRISTIQUES + BÉNÉFICES + UTILISATION",
                    "required": True
                },
                "backend_keywords": {
                    "max_bytes": 250,
                    "language": "FR/EN mixed",
                    "no_competitor_brands": True,
                    "required": False
                },
                "images": {
                    "min_resolution": "1000x1000px",
                    "main_background": "white",
                    "format": "JPEG/PNG",
                    "required": True
                }
            }
        }
    }