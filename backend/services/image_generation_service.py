"""
Image Generation Service - ECOMSIMPLY
Gestion unifiée de la génération d'images (FAL.ai, scraping, fallback)
"""

import os
import base64
import asyncio
import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional, Union

# Import du logging structuré
from .logging_service import ecomsimply_logger, log_error, log_info, log_operation

# Import des modules FAL.ai et autres
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False

class ImageGenerationService:
    """Service unifié pour la génération d'images"""
    
    def __init__(self):
        self.fal_key = os.environ.get('FAL_KEY')
        self.ua = UserAgent()
        
    async def generate_images(
        self,
        product_name: str,
        product_description: str,
        number_of_images: int = 1,
        image_style: str = "studio",
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = "fr",
        user_plan: str = "gratuit",
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Point d'entrée principal pour la génération d'images avec logging structuré
        Returns: List of base64 encoded images
        """
        start_time = time.time()
        generated_images = []
        
        # Log de début d'opération
        log_info(
            "Démarrage génération d'images",
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan,
            service="ImageGenerationService",
            operation="generate_images",
            number_of_images=number_of_images,
            image_style=image_style,
            category=category
        )
        
        if number_of_images > 0:
            try:
                # Génération directe avec FAL.ai
                image_tasks = [
                    self._generate_single_image_fal(
                        product_name,
                        product_description,
                        image_style,
                        i + 1,
                        category,
                        use_case,
                        language,
                        user_id
                    )
                    for i in range(number_of_images)
                ]
                
                results = await asyncio.gather(*image_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, str) and len(result) > 1000:
                        generated_images.append(result)
                        log_info(
                            f"Image {i+1} générée avec succès",
                            user_id=user_id,
                            product_name=product_name,
                            user_plan=user_plan,
                            service="ImageGenerationService",
                            image_number=i+1,
                            image_size_bytes=len(result)
                        )
                    else:
                        log_error(
                            f"Échec image {i+1}, tentative fallback",
                            user_id=user_id,
                            product_name=product_name,
                            user_plan=user_plan,
                            error_source="ImageGenerationService.generate_single_image",
                            image_number=i+1,
                            exception=result if isinstance(result, Exception) else None
                        )
                        
                        try:
                            fallback_image = await self._generate_fallback_image(
                                product_name, image_style, user_id
                            )
                            if fallback_image:
                                generated_images.append(fallback_image)
                        except Exception as fallback_error:
                            log_error(
                                f"Échec fallback image {i+1}",
                                user_id=user_id,
                                product_name=product_name,
                                user_plan=user_plan,
                                error_source="ImageGenerationService.generate_fallback",
                                exception=fallback_error
                            )
                
            except Exception as e:
                log_error(
                    "Erreur génération images globale",
                    user_id=user_id,
                    product_name=product_name,
                    user_plan=user_plan,
                    error_source="ImageGenerationService.generate_images",
                    exception=e
                )
                
                # Fallback pour toutes les images
                for i in range(number_of_images):
                    try:
                        fallback_image = await self._generate_fallback_image(
                            product_name, image_style, user_id
                        )
                        if fallback_image:
                            generated_images.append(fallback_image)
                    except Exception as fallback_error:
                        log_error(
                            f"Échec fallback complet image {i+1}",
                            user_id=user_id,
                            product_name=product_name,
                            error_source="ImageGenerationService.fallback_complete",
                            exception=fallback_error
                        )
        
        # Log final avec métriques
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            "ImageGenerationService",
            "generate_images",
            "success" if generated_images else "partial_failure",
            duration_ms=duration_ms,
            user_id=user_id,
            product_name=product_name,
            user_plan=user_plan,
            images_requested=number_of_images,
            images_generated=len(generated_images),
            success_rate=f"{len(generated_images)}/{number_of_images}"
        )
        
        return generated_images
    
    async def _generate_single_image_fal(
        self,
        product_name: str,
        product_description: str,
        image_style: str = "studio",
        image_number: int = 1,
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = "fr",
        user_id: Optional[str] = None
    ) -> str:
        """Génération d'une image via FAL.ai Flux Pro avec gestion d'erreurs robuste"""
        
        if not FAL_AVAILABLE or not self.fal_key:
            error_msg = f"FAL.ai indisponible pour image {image_number}"
            log_error(
                error_msg,
                user_id=user_id,
                product_name=product_name,
                error_source="ImageGenerationService.fal_unavailable",
                image_number=image_number,
                fal_available=FAL_AVAILABLE,
                fal_key_present=bool(self.fal_key)
            )
            raise Exception(error_msg)
        
        # Construction du prompt optimisé
        prompt = self._build_image_prompt(
            product_name, product_description, image_style, category, use_case, language
        )
        
        # Configuration FAL.ai Flux Pro
        fal_config = {
            "prompt": prompt,
            "image_size": "landscape_4_3",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "seed": None,
            "enable_safety_checker": True
        }
        
        start_time = time.time()
        
        try:
            log_info(
                f"Démarrage génération FAL.ai image {image_number}",
                user_id=user_id,
                product_name=product_name,
                service="ImageGenerationService",
                operation="fal_generation",
                image_number=image_number,
                prompt_length=len(prompt),
                config=fal_config
            )
            
            # Import FAL client
            import fal_client
            
            # Appel à FAL.ai Flux Pro
            handler = await fal_client.submit_async("fal-ai/flux-pro", arguments=fal_config)
            result = await handler.get()
            
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                
                # Téléchargement et conversion base64
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url, timeout=30) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            image_base64 = base64.b64encode(image_data).decode('utf-8')
                            
                            if len(image_base64) > 5000:  # Validation taille minimale
                                duration_ms = (time.time() - start_time) * 1000
                                log_operation(
                                    "ImageGenerationService",
                                    "fal_generation",
                                    "success",
                                    duration_ms=duration_ms,
                                    user_id=user_id,
                                    product_name=product_name,
                                    image_number=image_number,
                                    image_size_bytes=len(image_base64),
                                    download_size_bytes=len(image_data)
                                )
                                return image_base64
                            else:
                                raise Exception(f"Image {image_number} trop petite ({len(image_base64)} bytes)")
                        else:
                            raise Exception(f"Échec téléchargement image {image_number} - Status: {response.status}")
            
            raise Exception("Pas de résultat valide de FAL.ai")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error(
                f"Erreur FAL.ai image {image_number}",
                user_id=user_id,
                product_name=product_name,
                error_source="ImageGenerationService.fal_generation",
                exception=e,
                image_number=image_number,
                duration_ms=duration_ms,
                prompt_used=prompt[:100]
            )
            raise
    
    def _build_image_prompt(
        self,
        product_name: str,
        product_description: str,
        image_style: str,
        category: Optional[str] = None,
        use_case: Optional[str] = None,
        language: str = "fr"
    ) -> str:
        """Construction du prompt optimisé pour la génération d'images"""
        
        # Prompts de base par style
        style_prompts = {
            "studio": "professional product photography, white background, studio lighting, commercial quality",
            "lifestyle": "product in real-life setting, natural lighting, lifestyle photography",
            "detailed": "close-up product shot, high detail, macro photography, crisp focus",
            "technical": "technical documentation style, precise angles, detailed specifications",
            "emotional": "emotional appeal, warm lighting, lifestyle context, aspirational"
        }
        
        base_prompt = style_prompts.get(image_style, style_prompts["studio"])
        
        # Construction du prompt contextuel
        if language == "fr":
            prompt = f"Photographie commerciale professionnelle de {product_name}, {product_description[:100]}, {base_prompt}"
            if category:
                prompt += f", catégorie {category}"
            if use_case:
                prompt += f", usage {use_case}"
            prompt += ", haute résolution, qualité e-commerce, focus précis"
        else:
            prompt = f"Professional commercial photography of {product_name}, {product_description[:100]}, {base_prompt}"
            if category:
                prompt += f", {category} category"
            if use_case:
                prompt += f", {use_case} usage"
            prompt += ", high resolution, e-commerce quality, sharp focus"
        
        return prompt[:500]  # Limitation longueur prompt
    
    async def _generate_fallback_image(self, product_name: str, image_style: str, user_id: Optional[str] = None) -> Optional[str]:
        """Génération d'image de fallback avec logging"""
        
        try:
            log_info(
                "Génération image placeholder",
                user_id=user_id,
                product_name=product_name,
                service="ImageGenerationService",
                operation="generate_fallback",
                image_style=image_style
            )
            
            # Création d'un placeholder base64 simple
            import io
            from PIL import Image, ImageDraw, ImageFont
            
            # Création d'une image placeholder 400x300
            img = Image.new('RGB', (400, 300), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Texte de base
            placeholder_text = f"Image: {product_name}"
            try:
                draw.text((50, 150), placeholder_text[:30], fill='#666666')
            except:
                pass
            
            # Conversion en base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            log_info(
                "Image placeholder générée avec succès",
                user_id=user_id,
                product_name=product_name,
                service="ImageGenerationService",
                image_size_bytes=len(image_base64)
            )
            return image_base64
            
        except Exception as e:
            log_error(
                "Erreur génération placeholder",
                user_id=user_id,
                product_name=product_name,
                error_source="ImageGenerationService.generate_fallback",
                exception=e
            )
            return None
    
    async def scrape_product_images(
        self,
        product_name: str,
        category: Optional[str] = None,
        max_images: int = 5
    ) -> List[str]:
        """Scraping d'images produit depuis diverses sources (méthode alternative)"""
        
        print(f"🌐 SCRAPING IMAGES pour: {product_name}")
        
        images = []
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            # Recherche sur quelques sources (implémentation basique)
            search_sources = [
                f"https://www.google.com/search?q={product_name.replace(' ', '+')}&tbm=isch",
            ]
            
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as session:
                for source in search_sources:
                    try:
                        async with session.get(source) as response:
                            if response.status == 200:
                                html = await response.text()
                                # Extraction basique des URLs d'images
                                soup = BeautifulSoup(html, 'html.parser')
                                img_tags = soup.find_all('img', src=True)[:max_images]
                                
                                for img in img_tags:
                                    img_url = img['src']
                                    if img_url.startswith('http') and len(images) < max_images:
                                        try:
                                            # Téléchargement de l'image
                                            async with session.get(img_url) as img_response:
                                                if img_response.status == 200:
                                                    img_data = await img_response.read()
                                                    if len(img_data) > 5000:  # Taille minimale
                                                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                                                        images.append(img_base64)
                                        except:
                                            continue
                        
                        if len(images) >= max_images:
                            break
                            
                    except Exception as e:
                        print(f"❌ Erreur scraping source: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Erreur scraping général: {e}")
        
        print(f"📸 SCRAPING: {len(images)} images récupérées")
        return images


# Instance globale du service
image_generation_service = ImageGenerationService()