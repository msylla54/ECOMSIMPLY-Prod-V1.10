"""
Image Management Service - ECOMSIMPLY Bloc 3 Phase 3
Gestion centralisée des configurations d'images et logique de génération conditionnelle
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from .logging_service import log_info, log_error, log_operation
from .image_generation_service import ImageGenerationService


class ImageManagementService:
    """
    Service de gestion des images avec configuration utilisateur
    Implémente la logique Bloc 3 - Phase 3
    """
    
    def __init__(self):
        self.image_generation_service = ImageGenerationService()
    
    async def should_generate_images(self, user_config: Dict[str, Any]) -> bool:
        """
        Détermine si les images doivent être générées selon la configuration utilisateur
        
        Args:
            user_config: Configuration utilisateur avec generate_images
            
        Returns:
            bool: True si les images doivent être générées
        """
        generate_images = user_config.get('generate_images', True)
        user_id = user_config.get('user_id')
        user_plan = user_config.get('subscription_plan', 'gratuit')
        
        log_info(
            "Vérification configuration génération images",
            user_id=user_id,
            user_plan=user_plan,
            service="ImageManagementService",
            operation="should_generate_images",
            generate_images=generate_images
        )
        
        return generate_images
    
    async def generate_product_images_conditional(
        self,
        product_name: str,
        product_description: str,
        user_config: Dict[str, Any],
        number_of_images: int = 1,
        image_style: str = "studio",
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = "fr"
    ) -> List[str]:
        """
        Génération conditionnelle d'images selon la configuration utilisateur
        
        Args:
            product_name: Nom du produit
            product_description: Description du produit
            user_config: Configuration utilisateur
            number_of_images: Nombre d'images à générer
            image_style: Style d'image
            category: Catégorie du produit
            use_case: Cas d'usage
            language: Langue
            
        Returns:
            List[str]: Liste des images base64 ou liste vide si pas de génération
        """
        user_id = user_config.get('user_id')
        user_plan = user_config.get('subscription_plan', 'gratuit')
        
        # Vérifier si la génération d'images est activée
        if not await self.should_generate_images(user_config):
            log_info(
                "Génération d'images désactivée par configuration utilisateur",
                user_id=user_id,
                user_plan=user_plan,
                product_name=product_name,
                service="ImageManagementService",
                operation="generate_conditional",
                reason="generate_images_disabled"
            )
            return []
        
        # Génération d'images activée
        log_info(
            "Génération d'images activée - démarrage",
            user_id=user_id,
            user_plan=user_plan,
            product_name=product_name,
            service="ImageManagementService",
            operation="generate_conditional",
            number_of_images=number_of_images
        )
        
        try:
            generated_images = await self.image_generation_service.generate_images(
                product_name=product_name,
                product_description=product_description,
                number_of_images=number_of_images,
                image_style=image_style,
                category=category,
                use_case=use_case,
                language=language,
                user_plan=user_plan,
                user_id=user_id
            )
            
            log_operation(
                "ImageManagementService",
                "generate_conditional",
                "success",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                images_generated=len(generated_images),
                images_requested=number_of_images
            )
            
            return generated_images
            
        except Exception as e:
            log_error(
                "Erreur génération images conditionnelle",
                user_id=user_id,
                product_name=product_name,
                user_plan=user_plan,
                error_source="ImageManagementService.generate_conditional",
                exception=e
            )
            return []
    
    def should_include_images_in_publication(
        self,
        publication_type: str,  # 'auto' ou 'manual'
        user_config: Dict[str, Any],
        product_sheet_has_images: bool = False
    ) -> bool:
        """
        Détermine si les images doivent être incluses dans la publication
        
        Args:
            publication_type: Type de publication ('auto' ou 'manual')
            user_config: Configuration utilisateur
            product_sheet_has_images: True si la fiche a des images générées
            
        Returns:
            bool: True si les images doivent être incluses
        """
        user_id = user_config.get('user_id')
        user_plan = user_config.get('subscription_plan', 'gratuit')
        generate_images = user_config.get('generate_images', True)
        include_images_manual = user_config.get('include_images_manual', True)
        
        log_info(
            "Évaluation inclusion images en publication",
            user_id=user_id,
            user_plan=user_plan,
            service="ImageManagementService",
            operation="should_include_images",
            publication_type=publication_type,
            generate_images=generate_images,
            include_images_manual=include_images_manual,
            product_has_images=product_sheet_has_images
        )
        
        # Règle 1: Publication automatique → toujours exclure les images
        if publication_type == 'auto':
            log_info(
                "Publication automatique - images exclues par défaut",
                user_id=user_id,
                service="ImageManagementService",
                publication_type=publication_type,
                decision="exclude_auto"
            )
            return False
        
        # Règle 2: Publication manuelle
        if publication_type == 'manual':
            # Si generate_images == false → aucune image dans la fiche
            if not generate_images:
                log_info(
                    "generate_images=false - aucune image disponible",
                    user_id=user_id,
                    service="ImageManagementService",
                    publication_type=publication_type,
                    decision="no_images_generated"
                )
                return False
            
            # Si generate_images == true → respecter le switch utilisateur
            if generate_images and product_sheet_has_images:
                decision = include_images_manual
                log_info(
                    f"Publication manuelle avec images - switch utilisateur: {decision}",
                    user_id=user_id,
                    service="ImageManagementService",
                    publication_type=publication_type,
                    decision="user_switch",
                    include_images=decision
                )
                return decision
            
            # Pas d'images dans la fiche même si generate_images=true
            log_info(
                "Pas d'images dans cette fiche spécifique",
                user_id=user_id,
                service="ImageManagementService",
                publication_type=publication_type,
                decision="no_images_in_sheet"
            )
            return False
        
        # Type de publication non reconnu
        log_error(
            f"Type de publication non reconnu: {publication_type}",
            user_id=user_id,
            service="ImageManagementService",
            error_source="should_include_images",
            publication_type=publication_type
        )
        return False
    
    def filter_product_sheet_content(
        self,
        product_sheet: Dict[str, Any], 
        user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filtre le contenu de la fiche produit selon la configuration d'images
        
        Args:
            product_sheet: Fiche produit complète
            user_config: Configuration utilisateur
            
        Returns:
            Dict: Fiche produit filtrée
        """
        user_id = user_config.get('user_id')
        generate_images = user_config.get('generate_images', True)
        
        # Si generate_images=false, supprimer tous les blocs/placeholders d'images
        if not generate_images:
            log_info(
                "Suppression des blocs images de la fiche (generate_images=false)",
                user_id=user_id,
                service="ImageManagementService",
                operation="filter_content"
            )
            
            # Créer une copie de la fiche sans les champs d'images
            filtered_sheet = product_sheet.copy()
            
            # Supprimer les champs liés aux images
            fields_to_remove = ['images', 'product_images', 'generated_images', 'image_placeholders']
            for field in fields_to_remove:
                if field in filtered_sheet:
                    del filtered_sheet[field]
            
            # Marquer que cette fiche n'a pas d'images
            filtered_sheet['has_images'] = False
            filtered_sheet['images_filtered_reason'] = 'generate_images_disabled'
            
            return filtered_sheet
        
        # Si generate_images=true, garder la fiche telle quelle
        log_info(
            "Conservation des images dans la fiche (generate_images=true)",
            user_id=user_id,
            service="ImageManagementService",
            operation="filter_content"
        )
        
        product_sheet['has_images'] = 'images' in product_sheet and len(product_sheet.get('images', [])) > 0
        return product_sheet
    
    async def get_user_image_preferences(self, user_id: str, db) -> Dict[str, Any]:
        """
        Récupère les préférences d'images d'un utilisateur depuis la base de données
        
        Args:
            user_id: ID de l'utilisateur
            db: MongoDB database instance
            
        Returns:
            Dict: Préférences d'images de l'utilisateur
        """
        try:
            user_data = await db.users.find_one({"id": user_id})
            if not user_data:
                log_error(
                    "Utilisateur non trouvé pour récupération préférences images",
                    user_id=user_id,
                    error_source="ImageManagementService.get_user_image_preferences"
                )
                return {
                    'user_id': user_id,
                    'generate_images': True,  # Valeur par défaut
                    'include_images_manual': True,  # Valeur par défaut
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            return {
                'user_id': user_id,
                'generate_images': user_data.get('generate_images', True),
                'include_images_manual': user_data.get('include_images_manual', True),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error(
                "Erreur récupération préférences images depuis BD",
                user_id=user_id,
                error_source="ImageManagementService.get_user_image_preferences",
                exception=e
            )
            # Return defaults in case of error
            return {
                'user_id': user_id,
                'generate_images': True,
                'include_images_manual': True,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def update_user_image_preferences(
        self, 
        user_id: str, 
        db,
        generate_images: Optional[bool] = None,
        include_images_manual: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Met à jour les préférences d'images d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            db: MongoDB database instance
            generate_images: Nouvelle valeur pour generate_images
            include_images_manual: Nouvelle valeur pour include_images_manual
            
        Returns:
            Dict: Préférences mises à jour
        """
        log_info(
            "Mise à jour préférences images utilisateur",
            user_id=user_id,
            service="ImageManagementService",
            operation="update_preferences",
            generate_images=generate_images,
            include_images_manual=include_images_manual
        )
        
        try:
            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            
            if generate_images is not None:
                update_data["generate_images"] = generate_images
                
            if include_images_manual is not None:
                update_data["include_images_manual"] = include_images_manual
            
            # Update in database
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                log_error(
                    "Utilisateur non trouvé pour mise à jour préférences images",
                    user_id=user_id,
                    error_source="ImageManagementService.update_user_image_preferences"
                )
                raise Exception(f"Utilisateur {user_id} non trouvé")
            
            log_info(
                "Préférences images mises à jour avec succès",
                user_id=user_id,
                service="ImageManagementService",
                updated_fields=list(update_data.keys())
            )
            
            # Return updated preferences
            updated_prefs = {
                'user_id': user_id,
                'updated_at': update_data['updated_at'].isoformat()
            }
            
            if generate_images is not None:
                updated_prefs['generate_images'] = generate_images
            
            if include_images_manual is not None:
                updated_prefs['include_images_manual'] = include_images_manual
            
            return updated_prefs
            
        except Exception as e:
            log_error(
                "Erreur mise à jour préférences images en BD",
                user_id=user_id,
                error_source="ImageManagementService.update_user_image_preferences",
                exception=e
            )
            raise


# Instance globale du service
image_management_service = ImageManagementService()