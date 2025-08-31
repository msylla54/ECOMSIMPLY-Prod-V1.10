# 📋 EXTRACTION SEO AUTOMATIQUE - PARTIE 2: ENDPOINT PRINCIPAL

## 🎯 POINT D'ENTRÉE API POUR LA GÉNÉRATION AUTOMATIQUE

### Endpoint Principal (`/app/backend/server.py` - Route `/api/generate-sheet`)

```python
@api_router.post("/generate-sheet")
async def generate_product_sheet_endpoint(
    request: GenerateProductSheetRequest,
    current_user: User = Depends(get_current_user)
):
    """
    ✅ ENDPOINT PRINCIPAL : Génération de fiche produit complète avec SEO automatique
    Point d'entrée unique pour tous les services de génération automatique
    
    WORKFLOW COMPLET:
    1. Scraping parallèle (prix concurrents + SEO + tendances)
    2. Routing IA dynamique selon plan utilisateur 
    3. Génération de contenu avec GPT
    4. Enrichissement avec 20 tags SEO uniques (diversité Jaccard)
    5. Génération d'images IA (FAL.ai Flux Pro)
    6. Assemblage et sauvegarde en base
    7. Retour avec métadonnées complètes
    """
    
    start_time = time.time()
    user_id = current_user.id
    user_plan = current_user.subscription_plan
    
    log_info(
        "🚀 GÉNÉRATION FICHE PRODUIT - Démarrage",
        user_id=user_id,
        product_name=request.product_name,
        user_plan=user_plan,
        operation="generate_sheet_endpoint",
        generate_image=request.generate_image,
        number_of_images=request.number_of_images,
        language=request.language,
        category=request.category
    )
    
    try:
        # ✅ PHASE 1: Initialisation des services
        seo_service = SEOScrapingService()
        gpt_service = GPTContentService()
        image_service = ImageGenerationService()
        
        # ✅ PHASE 2: Scraping parallèle des données SEO et prix
        print(f"🔄 LANCEMENT SCRAPING PARALLÈLE...")
        scraping_tasks = [
            seo_service.scrape_competitor_prices(request.product_name, request.category),
            seo_service.scrape_seo_data(request.product_name, request.category),
            seo_service.fetch_trending_keywords(request.product_name, request.category, user_id)
        ]
        
        price_data, seo_data, trending_data = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        
        # Validation des résultats de scraping
        if isinstance(price_data, Exception):
            log_error("Échec scraping prix", user_id=user_id, exception=price_data)
            price_data = None
        
        if isinstance(seo_data, Exception):
            log_error("Échec scraping SEO", user_id=user_id, exception=seo_data)
            seo_data = None
        
        if isinstance(trending_data, Exception):
            log_error("Échec récupération tendances", user_id=user_id, exception=trending_data)
            trending_data = None
        
        # ✅ PHASE 3: Génération de contenu avec routing IA
        print(f"🤖 GÉNÉRATION CONTENU GPT avec routing plan {user_plan}...")
        content_result = await gpt_service.generate_product_content(
            product_name=request.product_name,
            product_description=request.product_description,
            category=request.category,
            use_case=request.use_case,
            language=request.language,
            user_plan=user_plan,
            user_id=user_id,
            price_data=price_data,
            seo_data=seo_data,
            trending_data=trending_data
        )
        
        # ✅ PHASE 4: Génération d'images parallèle (si demandé)
        generated_images = []
        if request.generate_image and request.number_of_images > 0:
            print(f"📸 GÉNÉRATION {request.number_of_images} IMAGES...")
            generated_images = await image_service.generate_images(
                product_name=request.product_name,
                product_description=request.product_description,
                number_of_images=request.number_of_images,
                image_style=request.image_style,
                category=request.category,
                use_case=request.use_case,
                language=request.language,
                user_plan=user_plan,
                user_id=user_id
            )
        
        # ✅ PHASE 5: Assemblage et sauvegarde
        generation_time = time.time() - start_time
        generation_id = str(uuid.uuid4())
        
        # Création de l'objet ProductSheet pour la base de données
        product_sheet = ProductSheet(
            id=generation_id,
            user_id=user_id,
            product_name=request.product_name,
            original_description=request.product_description,
            category=request.category,
            generated_title=content_result.get("generated_title", request.product_name),
            marketing_description=content_result.get("marketing_description", request.product_description),
            key_features=content_result.get("key_features", []),
            seo_tags=content_result.get("seo_tags", []),
            price_suggestions=content_result.get("price_suggestions", "Prix à définir"),
            target_audience=content_result.get("target_audience", "Audience générale"),
            call_to_action=content_result.get("call_to_action", "Commandez maintenant !"),
            product_images_base64=generated_images,
            number_of_images_generated=len(generated_images),
            created_at=datetime.utcnow(),
            is_ai_generated=content_result.get("is_ai_generated", True),
            generation_time=generation_time
        )
        
        # Sauvegarde en base de données
        try:
            await db.product_sheets.insert_one(product_sheet.dict())
            log_info(
                "✅ Fiche produit sauvegardée en BDD",
                user_id=user_id,
                product_name=request.product_name,
                generation_id=generation_id,
                operation="database_save"
            )
        except Exception as db_error:
            log_error(
                "❌ Erreur sauvegarde BDD",
                user_id=user_id,
                product_name=request.product_name,
                error_source="database_save",
                exception=db_error
            )
        
        # ✅ PHASE 6: Construction de la réponse avec métadonnées complètes
        response = ProductSheetResponse(
            generated_title=content_result.get("generated_title", request.product_name),
            marketing_description=content_result.get("marketing_description", request.product_description),
            key_features=content_result.get("key_features", []),
            seo_tags=content_result.get("seo_tags", []),
            price_suggestions=content_result.get("price_suggestions", "Prix à définir"),
            target_audience=content_result.get("target_audience", "Audience générale"),
            call_to_action=content_result.get("call_to_action", "Commandez maintenant !"),
            category=request.category,
            generated_images=generated_images,
            generation_time=generation_time,
            generation_id=generation_id,
            
            # ✅ TÂCHE 1: Métadonnées routing IA
            model_used=content_result.get("model_used"),
            generation_method=content_result.get("generation_method"),
            fallback_level=content_result.get("fallback_level"),
            primary_model=content_result.get("primary_model"),
            fallback_model=content_result.get("fallback_model"),
            model_route=content_result.get("model_route"),
            cost_guard_triggered=content_result.get("cost_guard_triggered"),
            
            # ✅ TÂCHE 2: Métadonnées SEO tags
            seo_tags_count=content_result.get("seo_tags_count"),
            seo_tags_source=content_result.get("seo_tags_source"),
            seo_diversity_score=content_result.get("seo_diversity_score"),
            seo_source_breakdown=content_result.get("seo_source_breakdown"),
            seo_validation_passed=content_result.get("seo_validation_passed"),
            seo_target_reached=content_result.get("seo_target_reached")
        )
        
        # Log de succès avec métriques complètes
        log_operation(
            "GenerateSheetEndpoint",
            "complete_generation",
            "success",
            duration_ms=generation_time * 1000,
            user_id=user_id,
            product_name=request.product_name,
            user_plan=user_plan,
            generation_id=generation_id,
            images_generated=len(generated_images),
            seo_tags_generated=len(content_result.get("seo_tags", [])),
            model_used=content_result.get("model_used"),
            cost_guard_triggered=content_result.get("cost_guard_triggered", False)
        )
        
        return response
        
    except Exception as e:
        generation_time = time.time() - start_time
        log_error(
            "❌ ERREUR CRITIQUE génération fiche produit",
            user_id=user_id,
            product_name=request.product_name,
            user_plan=user_plan,
            error_source="generate_sheet_endpoint",
            exception=e,
            duration_ms=generation_time * 1000
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de la fiche produit: {str(e)}"
        )
```

## 🔧 MODÈLES DE DONNÉES PYDANTIC

### Modèles de Requête et Réponse

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
import uuid

class GenerateProductSheetRequest(BaseModel):
    """Modèle de requête pour la génération de fiche produit avec validation avancée"""
    
    product_name: str = Field(..., min_length=5, max_length=200, description="Nom du produit (5-200 caractères)")
    product_description: str = Field(..., min_length=10, max_length=2000, description="Description du produit (10-2000 caractères)")
    generate_image: bool = True
    number_of_images: int = Field(default=1, ge=0, le=5, description="Nombre d'images à générer (0-5)")
    language: str = Field(default="fr", description="Langue de génération (fr, en, de, es, pt)")
    category: Optional[str] = Field(default=None, max_length=100, description="Catégorie du produit")
    use_case: Optional[str] = Field(default=None, max_length=300, description="Cas d'usage spécifique")
    image_style: str = Field(default="studio", pattern=r"^(studio|lifestyle|detailed|technical|emotional)$", description="Style des images")
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Validation avancée du nom de produit"""
        if not v or not v.strip():
            raise ValueError("Le nom du produit ne peut pas être vide")
        
        # Nettoyer les espaces
        v = v.strip()
        
        # Vérifier la longueur après nettoyage
        if len(v) < 5:
            raise ValueError("Le nom du produit doit contenir au moins 5 caractères (espaces exclus)")
        
        if len(v) > 200:
            raise ValueError("Le nom du produit ne peut pas dépasser 200 caractères")
        
        # Vérifier les caractères interdits
        forbidden_chars = ['<', '>', '{', '}', '[', ']', '|', '\\', '^', '`']
        if any(char in v for char in forbidden_chars):
            raise ValueError(f"Le nom du produit contient des caractères interdits: {', '.join(forbidden_chars)}")
        
        # Vérifier qu'il ne s'agit pas seulement de caractères spéciaux
        if not re.search(r'[a-zA-Z0-9\u00C0-\u017F]', v):  # Inclut les accents
            raise ValueError("Le nom du produit doit contenir au moins des lettres ou chiffres")
        
        return v
    
    @validator('language')
    def validate_language(cls, v):
        """Validation de la langue supportée"""
        supported_languages = ['fr', 'en', 'de', 'es', 'pt']
        
        if v not in supported_languages:
            raise ValueError(f"Langue non supportée '{v}'. Langues disponibles: {', '.join(supported_languages)}")
        
        return v
    
    @validator('number_of_images')
    def validate_number_of_images(cls, v, values):
        """Validation du nombre d'images avec contexte"""
        # Vérifier la cohérence avec generate_image
        generate_image = values.get('generate_image', True)
        
        if not generate_image:
            # Si generate_image est False, number_of_images doit être 0
            if v != 0:
                raise ValueError("Si generate_image est False, le nombre d'images doit être 0")
        else:
            # Si generate_image est True, number_of_images doit être entre 1 et 5
            if v < 1 or v > 5:
                raise ValueError("Le nombre d'images doit être entre 1 et 5")
        
        return v

class ProductSheetResponse(BaseModel):
    """Modèle de réponse avec métadonnées complètes SEO et routing IA"""
    
    # Contenu généré
    generated_title: str
    marketing_description: str
    key_features: List[str]
    seo_tags: List[str]
    price_suggestions: str
    target_audience: str
    call_to_action: str
    category: Optional[str] = None
    generated_images: List[str] = []
    generation_time: float
    generation_id: Optional[str] = None
    
    # ✅ TÂCHE 1: Champs de routing IA
    model_used: Optional[str] = None                    # Modèle IA effectivement utilisé
    generation_method: Optional[str] = None             # Méthode de génération
    fallback_level: Optional[int] = None                # Niveau de fallback (1, 2, 3, 4)
    primary_model: Optional[str] = None                 # Modèle principal configuré
    fallback_model: Optional[str] = None                # Modèle de fallback configuré
    model_route: Optional[str] = None                   # Route complète des modèles
    cost_guard_triggered: Optional[bool] = None         # Cost guard déclenché
    
    # ✅ TÂCHE 2: Champs SEO tags
    seo_tags_count: Optional[int] = None                # Nombre de tags générés
    seo_tags_source: Optional[str] = None               # Source des tags ("mixed", "ai_static", "trending")
    seo_diversity_score: Optional[float] = None         # Score de diversité Jaccard
    seo_source_breakdown: Optional[Dict] = None         # Répartition par source
    seo_validation_passed: Optional[bool] = None        # Validation format passée
    seo_target_reached: Optional[bool] = None           # 20 tags atteints

class ProductSheet(BaseModel):
    """Modèle de base de données pour les fiches produit générées"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_name: str
    original_description: Optional[str] = None          # ✅ CORRECTION: Rendre optionnel pour compatibilité
    category: Optional[str] = None                      # Product category for SEO optimization
    generated_title: str
    marketing_description: str
    key_features: List[str]
    seo_tags: List[str]
    price_suggestions: str
    target_audience: str
    call_to_action: str
    product_images_base64: List[str] = []               # Multiple images support
    number_of_images_generated: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_ai_generated: bool = False
    generation_time: Optional[float] = None             # Time in seconds to generate the sheet
```

## 📊 EXEMPLE DE WORKFLOW COMPLET

### Scénario: Génération fiche "iPhone 15 Pro"

```python
# 1. REQUÊTE UTILISATEUR
request_data = {
    "product_name": "iPhone 15 Pro",
    "product_description": "Smartphone haut de gamme avec processeur A17 Pro, appareil photo 48MP et écran Super Retina XDR",
    "generate_image": True,
    "number_of_images": 2,
    "language": "fr",
    "category": "smartphone",
    "use_case": "photographie professionnelle",
    "image_style": "studio"
}

# 2. RÉPONSE AVEC MÉTADONNÉES
response_data = {
    "generated_title": "iPhone 15 Pro - Smartphone Pro avec A17 Pro et Photo 48MP Ultra",
    "marketing_description": "Découvrez l'iPhone 15 Pro, le smartphone qui révolutionne...",
    "key_features": [
        "Processeur A17 Pro révolutionnaire",
        "Système photo Pro 48MP ultra-performant",
        "Écran Super Retina XDR 6,1 pouces",
        "Design en titane premium",
        "Batterie longue durée optimisée"
    ],
    "seo_tags": [
        "iphone-15-pro", "smartphone-premium", "photo-pro", "a17-pro", 
        "titanium-design", "super-retina", "apple-2024", "5g-advanced",
        "camera-48mp", "pro-photography", "mobile-gaming", "fast-charging",
        "usb-c", "action-button", "dynamic-island", "face-id",
        "magsafe-compatible", "wireless-charging", "water-resistant", "eco-friendly"
    ],
    "price_suggestions": "Prix recommandé: 1179€ (stratégie premium selon analyse concurrentielle)",
    "target_audience": "Professionnels créatifs, photographes mobiles, utilisateurs power",
    "call_to_action": "Commandez votre iPhone 15 Pro maintenant et profitez de la livraison gratuite !",
    "category": "smartphone",
    "generated_images": ["iVBORw0KGgoAAAANSUhEUgAA...", "iVBORw0KGgoAAAANSUhEUgAA..."],
    "generation_time": 12.45,
    "generation_id": "a7b3c2d1-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    
    # Métadonnées routing IA
    "model_used": "gpt-4o",
    "generation_method": "routing_primary", 
    "fallback_level": 1,
    "primary_model": "gpt-4o",
    "fallback_model": "gpt-4-turbo",
    "model_route": "gpt-4o -> gpt-4-turbo",
    "cost_guard_triggered": False,
    
    # Métadonnées SEO tags
    "seo_tags_count": 20,
    "seo_tags_source": "mixed",
    "seo_diversity_score": 0.847,
    "seo_source_breakdown": {
        "trending": 3,
        "ai": 5,
        "static": 12
    },
    "seo_validation_passed": True,
    "seo_target_reached": True
}
```

## 🔄 INTÉGRATION AVEC LES PLATEFORMES E-COMMERCE

### Endpoints de Publication Automatique

```python
@api_router.post("/publish-to-shopify")
async def publish_to_shopify_endpoint(
    sheet_id: str,
    store_credentials: ShopifyCredentials,
    current_user: User = Depends(get_current_user)
):
    """Publication automatique sur Shopify avec SEO optimisé"""
    
    # Récupération de la fiche générée
    sheet = await db.product_sheets.find_one({"id": sheet_id, "user_id": current_user.id})
    if not sheet:
        raise HTTPException(status_code=404, detail="Fiche produit introuvable")
    
    # Mapping des champs pour Shopify
    shopify_product = {
        "title": sheet["generated_title"],
        "body_html": f"<p>{sheet['marketing_description']}</p>",
        "tags": ", ".join(sheet["seo_tags"]),
        "product_type": sheet.get("category", ""),
        "vendor": "ECOMSIMPLY",
        "images": [
            {"src": f"data:image/png;base64,{img}"} 
            for img in sheet["product_images_base64"]
        ],
        "variants": [{
            "title": "Default",
            "price": extract_price_from_suggestions(sheet["price_suggestions"]),
            "inventory_management": "shopify",
            "inventory_policy": "deny"
        }],
        "metafields": [
            {
                "namespace": "ecomsimply",
                "key": "seo_diversity_score",
                "value": str(sheet.get("seo_diversity_score", 0)),
                "type": "number_decimal"
            },
            {
                "namespace": "ecomsimply", 
                "key": "generation_method",
                "value": sheet.get("generation_method", "unknown"),
                "type": "single_line_text_field"
            }
        ]
    }
    
    # Appel API Shopify
    try:
        shopify_client = ShopifyClient(store_credentials)
        result = await shopify_client.create_product(shopify_product)
        
        log_info(
            "✅ Produit publié sur Shopify",
            user_id=current_user.id,
            sheet_id=sheet_id,
            shopify_product_id=result["id"],
            operation="shopify_publish"
        )
        
        return {"success": True, "shopify_product_id": result["id"]}
        
    except Exception as e:
        log_error(
            "❌ Erreur publication Shopify",
            user_id=current_user.id,
            sheet_id=sheet_id,
            error_source="shopify_publish",
            exception=e
        )
        raise HTTPException(status_code=500, detail=f"Erreur Shopify: {str(e)}")
```

---

## 📈 MÉTRIQUES ET MONITORING

### Dashboard Analytics

```python
@api_router.get("/analytics/seo-performance")
async def get_seo_performance_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Analytics des performances SEO automatique"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Agrégation des données
    pipeline = [
        {"$match": {
            "user_id": current_user.id,
            "created_at": {"$gte": cutoff_date}
        }},
        {"$group": {
            "_id": None,
            "total_sheets": {"$sum": 1},
            "avg_seo_tags": {"$avg": {"$size": "$seo_tags"}},
            "avg_generation_time": {"$avg": "$generation_time"},
            "ai_generated_count": {"$sum": {"$cond": ["$is_ai_generated", 1, 0]}},
            "categories": {"$addToSet": "$category"},
            "total_images": {"$sum": "$number_of_images_generated"}
        }}
    ]
    
    result = await db.product_sheets.aggregate(pipeline).to_list(1)
    
    if not result:
        return {"message": "Aucune donnée disponible"}
    
    data = result[0]
    
    return {
        "period_days": days,
        "total_sheets_generated": data["total_sheets"],
        "average_seo_tags_per_sheet": round(data["avg_seo_tags"], 1),
        "average_generation_time_seconds": round(data["avg_generation_time"], 2),
        "ai_generation_rate": round((data["ai_generated_count"] / data["total_sheets"]) * 100, 1),
        "categories_used": data["categories"],
        "total_images_generated": data["total_images"],
        "productivity_score": calculate_productivity_score(data)
    }

def calculate_productivity_score(data: Dict) -> float:
    """Calcule un score de productivité basé sur les métriques"""
    
    # Facteurs de score
    sheets_factor = min(data["total_sheets"] / 10, 1.0)  # Max à 10 fiches
    speed_factor = max(0, 1 - (data["avg_generation_time"] / 30))  # Pénalité si > 30s
    ai_factor = data["ai_generated_count"] / data["total_sheets"]  # Bonus IA
    
    score = (sheets_factor * 0.4 + speed_factor * 0.3 + ai_factor * 0.3) * 100
    
    return round(score, 1)
```

---

Ce système complet permet une gestion automatique et optimisée des SEO sur les boutiques e-commerce avec des métriques avancées et une intégration native aux principales plateformes.