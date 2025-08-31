# Amazon Listing Validators - Phase 2
import logging
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationStatus(str, Enum):
    """États de validation Amazon"""
    APPROVED = "APPROVED"
    PENDING_REVIEW = "PENDING_REVIEW" 
    REJECTED = "REJECTED"

class AmazonListingValidator:
    """
    Validateur de fiches produits Amazon selon les règles officielles
    Vérifie conformité avant publication via SP-API
    """
    
    def __init__(self):
        # Règles de validation Amazon mises à jour 2025
        self.validation_rules = {
            'title': {
                'min_length': 15,
                'max_length': 200,
                'forbidden_words': [
                    'best', 'cheapest', 'guarantee', 'free shipping', 
                    'sale', 'deal', 'promotion', 'discount', 'offer'
                ],
                'forbidden_chars': ['!', '?', '*', '+', '=', '<', '>', '@']
            },
            'bullets': {
                'min_count': 1,
                'max_count': 5,
                'max_length': 255,
                'min_length': 10
            },
            'description': {
                'min_length': 50,
                'max_length': 2000,
                'allowed_html_tags': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 
                                    'ul', 'ol', 'li', 'strong', 'b', 'em', 'i']
            },
            'keywords': {
                'max_bytes': 250,
                'min_count': 3,
                'max_count': 50
            },
            'images': {
                'min_count': 1,
                'max_count': 9,
                'min_resolution': 1000,
                'max_file_size_mb': 10,
                'allowed_formats': ['jpg', 'jpeg', 'png', 'gif']
            },
            'brand': {
                'min_length': 2,
                'max_length': 50,
                'pattern': r'^[A-Za-z0-9\s\-\.&]+$'
            }
        }
        
        logger.info("✅ Amazon Listing Validator initialized")
    
    def validate_complete_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation complète d'une fiche produit Amazon
        
        Args:
            listing_data: Données de la fiche à valider
            
        Returns:
            Dict contenant le statut, score et détails de validation
        """
        try:
            logger.info("🔍 Starting complete listing validation")
            
            validation_results = {
                'validation_id': f"val_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'validated_at': datetime.utcnow().isoformat(),
                'overall_status': ValidationStatus.APPROVED,
                'validation_score': 0.0,
                'details': {},
                'warnings': [],
                'errors': [],
                'critical_issues': []
            }
            
            # Validation par composant
            validators = [
                ('title', self._validate_title),
                ('bullets', self._validate_bullets),
                ('description', self._validate_description),
                ('keywords', self._validate_keywords),
                ('images', self._validate_images),
                ('brand', self._validate_brand)
            ]
            
            total_score = 0.0
            max_possible_score = len(validators) * 100
            
            for component_name, validator_func in validators:
                try:
                    component_data = self._extract_component_data(listing_data, component_name)
                    result = validator_func(component_data)
                    
                    validation_results['details'][component_name] = result
                    total_score += result['score']
                    
                    # Collecter erreurs et warnings
                    validation_results['warnings'].extend(result.get('warnings', []))
                    validation_results['errors'].extend(result.get('errors', []))
                    
                    if result['status'] == ValidationStatus.REJECTED:
                        validation_results['critical_issues'].extend(result.get('errors', []))
                        
                except Exception as e:
                    logger.error(f"❌ Validation failed for {component_name}: {str(e)}")
                    validation_results['errors'].append(f"{component_name}: {str(e)}")
            
            # Calcul du score final
            validation_results['validation_score'] = round((total_score / max_possible_score) * 100, 1)
            
            # Détermination du statut global
            validation_results['overall_status'] = self._determine_overall_status(
                validation_results['validation_score'],
                validation_results['critical_issues'],
                validation_results['errors']
            )
            
            logger.info(f"✅ Validation complete - Status: {validation_results['overall_status']}, Score: {validation_results['validation_score']}%")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Complete validation failed: {str(e)}")
            return {
                'validation_id': f"val_error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'overall_status': ValidationStatus.REJECTED,
                'validation_score': 0.0,
                'errors': [f"Validation system error: {str(e)}"]
            }
    
    def _validate_title(self, title: str) -> Dict[str, Any]:
        """Valide le titre selon les règles Amazon"""
        result = {
            'component': 'title',
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not title or not isinstance(title, str):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Title is required and must be a string")
            return result
        
        title = title.strip()
        
        # Validation de longueur
        if len(title) < self.validation_rules['title']['min_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Title too short (min {self.validation_rules['title']['min_length']} chars)")
        
        elif len(title) > self.validation_rules['title']['max_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Title too long (max {self.validation_rules['title']['max_length']} chars)")
        
        # Validation mots interdits
        forbidden_found = []
        for word in self.validation_rules['title']['forbidden_words']:
            if word.lower() in title.lower():
                forbidden_found.append(word)
        
        if forbidden_found:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 20.0
            result['errors'].append(f"Forbidden words found: {', '.join(forbidden_found)}")
        
        # Validation caractères interdits
        forbidden_chars = []
        for char in self.validation_rules['title']['forbidden_chars']:
            if char in title:
                forbidden_chars.append(char)
        
        if forbidden_chars:
            result['status'] = ValidationStatus.PENDING_REVIEW
            result['score'] = 60.0
            result['warnings'].append(f"Special characters found: {', '.join(forbidden_chars)}")
        
        # Validation structure (Brand + Product)
        if len(title.split()) < 2:
            result['warnings'].append("Title should include brand and product name")
            result['score'] = max(result['score'] - 20, 0)
        
        # Validation capitalisation
        if title.isupper() or title.islower():
            result['warnings'].append("Title should use proper capitalization")
            result['score'] = max(result['score'] - 10, 0)
        
        return result
    
    def _validate_bullets(self, bullets: List[str]) -> Dict[str, Any]:
        """Valide les bullet points"""
        result = {
            'component': 'bullets',
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not bullets or not isinstance(bullets, list):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Bullets are required and must be a list")
            return result
        
        # Validation nombre de bullets
        if len(bullets) < self.validation_rules['bullets']['min_count']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"At least {self.validation_rules['bullets']['min_count']} bullet point required")
        
        elif len(bullets) > self.validation_rules['bullets']['max_count']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Maximum {self.validation_rules['bullets']['max_count']} bullet points allowed")
        
        # Validation de chaque bullet
        for i, bullet in enumerate(bullets):
            if not bullet or not isinstance(bullet, str):
                result['errors'].append(f"Bullet {i+1} is empty or invalid")
                result['score'] = max(result['score'] - 20, 0)
                continue
            
            bullet = bullet.strip()
            
            # Validation longueur
            if len(bullet) < self.validation_rules['bullets']['min_length']:
                result['warnings'].append(f"Bullet {i+1} is too short")
                result['score'] = max(result['score'] - 10, 0)
            
            elif len(bullet) > self.validation_rules['bullets']['max_length']:
                result['errors'].append(f"Bullet {i+1} is too long (max {self.validation_rules['bullets']['max_length']} chars)")
                result['score'] = max(result['score'] - 20, 0)
            
            # Validation contenu (doit être descriptif)
            if len(bullet.split()) < 3:
                result['warnings'].append(f"Bullet {i+1} should be more descriptive")
                result['score'] = max(result['score'] - 5, 0)
        
        # Si trop d'erreurs, rejeter
        if result['score'] < 50:
            result['status'] = ValidationStatus.REJECTED
        elif result['score'] < 80:
            result['status'] = ValidationStatus.PENDING_REVIEW
        
        return result
    
    def _validate_description(self, description: str) -> Dict[str, Any]:
        """Valide la description HTML"""
        result = {
            'component': 'description',
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not description or not isinstance(description, str):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Description is required")
            return result
        
        # Validation longueur
        text_length = len(re.sub(r'<[^>]+>', '', description))  # Sans HTML
        
        if text_length < self.validation_rules['description']['min_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Description too short (min {self.validation_rules['description']['min_length']} chars)")
        
        elif len(description) > self.validation_rules['description']['max_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Description too long (max {self.validation_rules['description']['max_length']} chars)")
        
        # Validation HTML
        html_validation = self._validate_html_tags(description)
        if not html_validation['valid']:
            result['status'] = ValidationStatus.PENDING_REVIEW
            result['score'] = 60.0
            result['warnings'].extend(html_validation['warnings'])
        
        # Validation structure
        if '<h' not in description:
            result['warnings'].append("Description should include headers for better readability")
            result['score'] = max(result['score'] - 10, 0)
        
        if '<ul>' not in description and '<ol>' not in description:
            result['warnings'].append("Description should include lists for better structure")
            result['score'] = max(result['score'] - 5, 0)
        
        return result
    
    def _validate_keywords(self, keywords: str) -> Dict[str, Any]:
        """Valide les mots-clés backend"""
        result = {
            'component': 'keywords', 
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not keywords or not isinstance(keywords, str):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Keywords are required")
            return result
        
        # Validation taille en bytes
        byte_size = len(keywords.encode('utf-8'))
        if byte_size > self.validation_rules['keywords']['max_bytes']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Keywords exceed {self.validation_rules['keywords']['max_bytes']} bytes (current: {byte_size})")
        
        # Validation nombre de mots-clés
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        if len(keyword_list) < self.validation_rules['keywords']['min_count']:
            result['warnings'].append(f"Consider adding more keywords (min {self.validation_rules['keywords']['min_count']})")
            result['score'] = max(result['score'] - 20, 0)
        
        elif len(keyword_list) > self.validation_rules['keywords']['max_count']:
            result['warnings'].append(f"Too many keywords (max {self.validation_rules['keywords']['max_count']})")
            result['score'] = max(result['score'] - 10, 0)
        
        # Validation qualité des mots-clés
        short_keywords = [kw for kw in keyword_list if len(kw) < 3]
        if short_keywords:
            result['warnings'].append(f"Some keywords are too short: {', '.join(short_keywords[:3])}")
            result['score'] = max(result['score'] - 5, 0)
        
        return result
    
    def _validate_images(self, images_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les exigences images"""
        result = {
            'component': 'images',
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not images_data or not isinstance(images_data, dict):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Image requirements are missing")
            return result
        
        # Vérifier image principale
        main_image = images_data.get('main_image')
        if not main_image or not main_image.get('required'):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Main image is required")
        
        # Vérifier nombre total d'images
        total_images = images_data.get('total_count', 1)
        
        if total_images < self.validation_rules['images']['min_count']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"At least {self.validation_rules['images']['min_count']} image required")
        
        elif total_images > self.validation_rules['images']['max_count']:
            result['warnings'].append(f"Maximum {self.validation_rules['images']['max_count']} images recommended")
            result['score'] = max(result['score'] - 10, 0)
        
        # Vérifier exigences techniques
        validation_rules = images_data.get('validation_rules', {})
        min_resolution = validation_rules.get('min_resolution', 1000)
        
        if min_resolution < self.validation_rules['images']['min_resolution']:
            result['errors'].append(f"Minimum resolution should be {self.validation_rules['images']['min_resolution']}px")
            result['score'] = max(result['score'] - 30, 0)
        
        return result
    
    def _validate_brand(self, brand: str) -> Dict[str, Any]:
        """Valide le nom de marque"""
        result = {
            'component': 'brand',
            'status': ValidationStatus.APPROVED,
            'score': 100.0,
            'warnings': [],
            'errors': []
        }
        
        if not brand or not isinstance(brand, str):
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append("Brand is required")
            return result
        
        brand = brand.strip()
        
        # Validation longueur
        if len(brand) < self.validation_rules['brand']['min_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Brand name too short (min {self.validation_rules['brand']['min_length']} chars)")
        
        elif len(brand) > self.validation_rules['brand']['max_length']:
            result['status'] = ValidationStatus.REJECTED
            result['score'] = 0.0
            result['errors'].append(f"Brand name too long (max {self.validation_rules['brand']['max_length']} chars)")
        
        # Validation format
        pattern = re.compile(self.validation_rules['brand']['pattern'])
        if not pattern.match(brand):
            result['warnings'].append("Brand contains special characters")
            result['score'] = max(result['score'] - 20, 0)
        
        return result
    
    def _validate_html_tags(self, html_content: str) -> Dict[str, Any]:
        """Valide les tags HTML autorisés"""
        allowed_tags = self.validation_rules['description']['allowed_html_tags']
        
        # Extraire tous les tags HTML
        tags = re.findall(r'<(/?)(\w+)[^>]*>', html_content)
        
        invalid_tags = []
        for opening_slash, tag_name in tags:
            if tag_name.lower() not in allowed_tags:
                invalid_tags.append(tag_name)
        
        if invalid_tags:
            return {
                'valid': False,
                'warnings': [f"Invalid HTML tags found: {', '.join(set(invalid_tags))}"]
            }
        
        return {'valid': True, 'warnings': []}
    
    def _extract_component_data(self, listing_data: Dict[str, Any], component: str) -> Any:
        """Extrait les données d'un composant spécifique"""
        seo_content = listing_data.get('seo_content', {})
        product_data = listing_data.get('product_data', {})
        
        component_map = {
            'title': seo_content.get('title', ''),
            'bullets': seo_content.get('bullet_points', []),
            'description': seo_content.get('description', ''),
            'keywords': seo_content.get('backend_keywords', ''),
            'images': seo_content.get('image_requirements', {}),
            'brand': product_data.get('brand', '')
        }
        
        return component_map.get(component)
    
    def _determine_overall_status(self, score: float, critical_issues: List[str], 
                                errors: List[str]) -> ValidationStatus:
        """Détermine le statut global de validation"""
        
        if critical_issues or score < 30:
            return ValidationStatus.REJECTED
        
        elif errors or score < 70:
            return ValidationStatus.PENDING_REVIEW
        
        else:
            return ValidationStatus.APPROVED
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Génère un résumé textuel de la validation"""
        status = validation_result['overall_status']
        score = validation_result['validation_score']
        
        if status == ValidationStatus.APPROVED:
            return f"✅ Fiche approuvée (Score: {score}%) - Prête pour publication"
        
        elif status == ValidationStatus.PENDING_REVIEW:
            return f"⚠️ Révision nécessaire (Score: {score}%) - Corrections mineures requises"
        
        else:
            return f"❌ Fiche rejetée (Score: {score}%) - Corrections majeures requises"