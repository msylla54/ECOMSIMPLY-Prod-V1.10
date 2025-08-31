"""
Routes API pour la gestion des images - ECOMSIMPLY Bloc 3 Phase 3
Endpoints pour configurer les préférences d'images utilisateur
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Import des services et modèles
from services.image_management_service import image_management_service
from services.logging_service import log_info, log_error
from modules.security import get_current_user_from_token

# Configuration
router = APIRouter(prefix="/api/images", tags=["image-management"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'ecomsimply_production')
db = client[db_name]


# ================================================================================
# MODÈLES PYDANTIC
# ================================================================================

class ImagePreferencesResponse(BaseModel):
    """Réponse des préférences d'images utilisateur"""
    user_id: str
    generate_images: bool
    include_images_manual: bool
    last_updated: Optional[str] = None
    subscription_plan: Optional[str] = None


class UpdateImagePreferencesRequest(BaseModel):
    """Requête de mise à jour des préférences d'images"""
    generate_images: Optional[bool] = None
    include_images_manual: Optional[bool] = None


class ImageGenerationTestRequest(BaseModel):
    """Requête de test de génération d'images"""
    product_name: str
    product_description: str
    number_of_images: int = 1
    image_style: str = "studio"
    category: Optional[str] = None
    use_case: Optional[str] = None
    language: str = "fr"


# ================================================================================
# ENDPOINTS PRINCIPAUX
# ================================================================================

@router.get("/preferences", response_model=ImagePreferencesResponse)
async def get_image_preferences(current_user: dict = Depends(get_current_user_from_token)):
    """
    Récupère les préférences d'images de l'utilisateur connecté
    """
    try:
        user_id = current_user['user_id']
        user_plan = current_user.get('subscription_plan', 'gratuit')
        
        log_info(
            "Récupération préférences images",
            user_id=user_id,
            user_plan=user_plan,
            service="ImageManagementRoutes",
            operation="get_preferences"
        )
        
        # Récupérer les préférences depuis la base ou utiliser les valeurs du token
        generate_images = current_user.get('generate_images', True)
        include_images_manual = current_user.get('include_images_manual', True)
        
        return ImagePreferencesResponse(
            user_id=user_id,
            generate_images=generate_images,
            include_images_manual=include_images_manual,
            last_updated=datetime.utcnow().isoformat(),
            subscription_plan=user_plan
        )
        
    except Exception as e:
        log_error(
            "Erreur récupération préférences images",
            user_id=current_user.get('user_id'),
            error_source="ImageManagementRoutes.get_preferences",
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des préférences d'images"
        )


@router.put("/preferences", response_model=ImagePreferencesResponse)
async def update_image_preferences(
    request: UpdateImagePreferencesRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Met à jour les préférences d'images de l'utilisateur connecté
    """
    try:
        user_id = current_user['user_id']
        user_plan = current_user.get('subscription_plan', 'gratuit')
        
        log_info(
            "Mise à jour préférences images",
            user_id=user_id,
            user_plan=user_plan,
            service="ImageManagementRoutes",
            operation="update_preferences",
            generate_images=request.generate_images,
            include_images_manual=request.include_images_manual
        )
        
        # Validation logique métier
        if request.generate_images is False and request.include_images_manual is True:
            # Si on désactive la génération, l'inclusion manuelle n'a pas de sens
            log_info(
                "Auto-correction: include_images_manual désactivé car generate_images=false",
                user_id=user_id,
                service="ImageManagementRoutes"
            )
            request.include_images_manual = False
        
        # Mettre à jour les préférences dans la base de données
        updated_preferences = await image_management_service.update_user_image_preferences(
            user_id=user_id,
            db=db,
            generate_images=request.generate_images,
            include_images_manual=request.include_images_manual
        )
        
        # Préparer la réponse avec les nouvelles valeurs
        new_generate_images = request.generate_images if request.generate_images is not None else current_user.get('generate_images', True)
        new_include_images_manual = request.include_images_manual if request.include_images_manual is not None else current_user.get('include_images_manual', True)
        
        return ImagePreferencesResponse(
            user_id=user_id,
            generate_images=new_generate_images,
            include_images_manual=new_include_images_manual,
            last_updated=updated_preferences.get('updated_at'),
            subscription_plan=user_plan
        )
        
    except Exception as e:
        log_error(
            "Erreur mise à jour préférences images",
            user_id=current_user.get('user_id'),
            error_source="ImageManagementRoutes.update_preferences",
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour des préférences d'images"
        )


@router.post("/test-generation")
async def test_image_generation(
    request: ImageGenerationTestRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Teste la génération d'images selon la configuration utilisateur
    Endpoint utile pour valider les paramètres avant génération de fiche
    """
    try:
        user_id = current_user['user_id']
        user_plan = current_user.get('subscription_plan', 'gratuit')
        
        log_info(
            "Test génération images",
            user_id=user_id,
            user_plan=user_plan,
            product_name=request.product_name,
            service="ImageManagementRoutes",
            operation="test_generation"
        )
        
        # Préparer la configuration utilisateur
        user_config = {
            'user_id': user_id,
            'subscription_plan': user_plan,
            'generate_images': current_user.get('generate_images', True),
            'include_images_manual': current_user.get('include_images_manual', True)
        }
        
        # Tester la génération conditionnelle
        generated_images = await image_management_service.generate_product_images_conditional(
            product_name=request.product_name,
            product_description=request.product_description,
            user_config=user_config,
            number_of_images=request.number_of_images,
            image_style=request.image_style,
            category=request.category,
            use_case=request.use_case,
            language=request.language
        )
        
        return {
            "status": "success",
            "user_config": {
                "generate_images": user_config['generate_images'],
                "include_images_manual": user_config['include_images_manual']
            },
            "images_generated": len(generated_images),
            "images_requested": request.number_of_images,
            "has_images": len(generated_images) > 0,
            "message": f"Génération testée: {len(generated_images)}/{request.number_of_images} images"
        }
        
    except Exception as e:
        log_error(
            "Erreur test génération images",
            user_id=current_user.get('user_id'),
            product_name=request.product_name,
            error_source="ImageManagementRoutes.test_generation",
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du test de génération d'images"
        )


@router.get("/publication-rules")
async def get_publication_rules(current_user: dict = Depends(get_current_user_from_token)):
    """
    Retourne les règles de publication d'images selon la configuration utilisateur
    """
    try:
        user_id = current_user['user_id']
        user_plan = current_user.get('subscription_plan', 'gratuit')
        generate_images = current_user.get('generate_images', True)
        include_images_manual = current_user.get('include_images_manual', True)
        
        log_info(
            "Récupération règles publication images",
            user_id=user_id,
            user_plan=user_plan,
            service="ImageManagementRoutes",
            operation="get_publication_rules"
        )
        
        # Simuler une fiche avec images pour tester les règles
        user_config = {
            'user_id': user_id,
            'subscription_plan': user_plan,
            'generate_images': generate_images,
            'include_images_manual': include_images_manual
        }
        
        # Tester les règles pour différents cas
        auto_publication_includes_images = image_management_service.should_include_images_in_publication(
            publication_type='auto',
            user_config=user_config,
            product_sheet_has_images=True
        )
        
        manual_publication_includes_images = image_management_service.should_include_images_in_publication(
            publication_type='manual',
            user_config=user_config,
            product_sheet_has_images=True
        )
        
        manual_publication_no_images = image_management_service.should_include_images_in_publication(
            publication_type='manual',
            user_config=user_config,
            product_sheet_has_images=False
        )
        
        return {
            "user_config": {
                "generate_images": generate_images,
                "include_images_manual": include_images_manual,
                "subscription_plan": user_plan
            },
            "publication_rules": {
                "auto_publication": {
                    "includes_images": auto_publication_includes_images,
                    "reason": "Images toujours exclues en publication automatique"
                },
                "manual_publication_with_images": {
                    "includes_images": manual_publication_includes_images,
                    "reason": f"Selon switch utilisateur: {include_images_manual}" if generate_images else "Aucune image générée"
                },
                "manual_publication_without_images": {
                    "includes_images": manual_publication_no_images,
                    "reason": "Fiche sans images"
                }
            },
            "ui_controls": {
                "show_generate_images_toggle": True,
                "show_include_images_manual_toggle": generate_images,
                "show_publication_switch": generate_images and include_images_manual
            }
        }
        
    except Exception as e:
        log_error(
            "Erreur récupération règles publication",
            user_id=current_user.get('user_id'),
            error_source="ImageManagementRoutes.get_publication_rules",
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des règles de publication"
        )