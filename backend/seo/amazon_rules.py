"""
SEO Amazon avancé - Règles A9/A10 pour optimisation listings
ECOMSIMPLY Bloc 5 — Phase 5: Amazon SEO Rules

Implémente les règles SEO spécifiques à Amazon pour maximiser la visibilité
selon les algorithmes A9 (recherche) et A10 (recommandations).
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import unicodedata
from urllib.parse import urlparse
import logging

from services.logging_service import log_info, log_error, log_operation


class ListingValidationStatus(Enum):
    """Status de validation d'un listing Amazon"""
    APPROVED = "approved"
    REJECTED = "rejected"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Résultat de validation d'un listing Amazon"""
    status: ListingValidationStatus
    score: float  # Score de 0 à 100
    reasons: List[str]
    warnings: List[str]
    suggestions: List[str]
    details: Dict[str, Any]


@dataclass
class AmazonListing:
    """Structure d'un listing Amazon optimisé"""
    title: str
    bullets: List[str]
    description: str
    backend_keywords: str
    images: List[str]
    brand: Optional[str] = None
    model: Optional[str] = None
    features: List[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None


class AmazonSEORules:
    """
    Classe principale pour les règles SEO Amazon A9/A10
    Génère et valide les listings selon les meilleures pratiques
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ecomsimply.amazon_seo")
        
        # Limites Amazon officielles
        self.TITLE_MAX_LENGTH = 200
        self.BULLET_MAX_LENGTH = 255
        self.BULLETS_COUNT = 5
        self.BACKEND_KEYWORDS_MAX_BYTES = 250
        self.DESCRIPTION_MIN_LENGTH = 100
        self.DESCRIPTION_MAX_LENGTH = 2000
        self.IMAGE_MIN_SIZE = 1000  # pixels
        
        # Mots interdits et promotionnels
        self.FORBIDDEN_WORDS = {
            'promo', 'promotion', 'sale', 'discount', 'offer', 'deal',
            'free', 'gratuit', 'offre', 'réduction', 'solde', 'promo',
            'best', 'meilleur', 'top', 'amazing', 'incredible', 'fantastic'
        }
        
        # Emojis à éviter dans les titres
        self.EMOJI_PATTERN = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\u2600-\u26FF"          # misc symbols
            "\u2700-\u27BF"          # dingbats
            "]+", flags=re.UNICODE
        )
        
        # Marques concurrentes à éviter dans backend keywords
        self.COMPETITOR_BRANDS = [
            'apple', 'samsung', 'sony', 'lg', 'huawei', 'xiaomi',
            'nike', 'adidas', 'puma', 'reebok', 'amazon', 'google',
            'microsoft', 'facebook', 'meta', 'netflix', 'disney'
        ]
        
        # Mots-clés SEO par catégorie (FR/EN)
        self.CATEGORY_KEYWORDS = {
            'électronique': {
                'fr': ['technologie', 'numérique', 'électronique', 'innovation', 'connecté', 'intelligent'],
                'en': ['technology', 'digital', 'electronic', 'smart', 'connected', 'innovative']
            },
            'mode': {
                'fr': ['style', 'fashion', 'tendance', 'élégant', 'confortable', 'qualité'],
                'en': ['style', 'fashion', 'trendy', 'elegant', 'comfortable', 'quality']
            },
            'maison': {
                'fr': ['maison', 'décoration', 'intérieur', 'pratique', 'fonctionnel', 'design'],
                'en': ['home', 'decoration', 'interior', 'practical', 'functional', 'design']
            },
            'sport': {
                'fr': ['sport', 'fitness', 'performance', 'entraînement', 'résistant', 'professionnel'],
                'en': ['sport', 'fitness', 'performance', 'training', 'durable', 'professional']
            }
        }
        
        log_info(
            "Amazon SEO Rules initialisé",
            service="AmazonSEORules",
            title_max_length=self.TITLE_MAX_LENGTH,
            bullets_count=self.BULLETS_COUNT,
            backend_keywords_max_bytes=self.BACKEND_KEYWORDS_MAX_BYTES
        )
    
    def generate_optimized_title(
        self,
        brand: str,
        model: str,
        features: List[str],
        size: Optional[str] = None,
        color: Optional[str] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Génère un titre optimisé selon le format Amazon A9/A10
        Format: {Brand} {Model} {Feature} {Size} {Color}
        Limite: 200 caractères, sans promo/emoji
        """
        title_parts = []
        
        # Brand (obligatoire)
        if brand:
            title_parts.append(self._clean_text(brand))
        
        # Model (obligatoire)
        if model:
            title_parts.append(self._clean_text(model))
        
        # Features principales (max 2-3 pour éviter le spam)
        if features:
            main_features = features[:3]  # Limiter à 3 features principales
            for feature in main_features:
                cleaned_feature = self._clean_text(feature)
                if cleaned_feature:
                    title_parts.append(cleaned_feature)
        
        # Size si spécifié
        if size:
            title_parts.append(self._clean_text(size))
        
        # Color si spécifié
        if color:
            title_parts.append(self._clean_text(color))
        
        # Assemblage du titre
        title = " ".join(title_parts)
        
        # Validation et optimisation finale
        title = self._validate_and_optimize_title(title, category)
        
        log_info(
            "Titre Amazon généré",
            service="AmazonSEORules",
            title_length=len(title),
            brand=brand,
            model=model,
            category=category
        )
        
        return title
    
    def generate_optimized_bullets(
        self,
        product_name: str,
        features: List[str],
        benefits: List[str],
        category: Optional[str] = None,
        target_keywords: List[str] = None
    ) -> List[str]:
        """
        Génère 5 bullets optimisés avec bénéfices clairs et mots-clés pertinents
        Chaque bullet ≤ 255 caractères
        """
        bullets = []
        used_concepts = set()
        
        # Combiner features et benefits
        all_content = (features or []) + (benefits or [])
        target_keywords = target_keywords or []
        
        # Ajouter des mots-clés de catégorie si disponibles
        if category and category.lower() in self.CATEGORY_KEYWORDS:
            cat_keywords = self.CATEGORY_KEYWORDS[category.lower()]
            target_keywords.extend(cat_keywords.get('fr', []))
            target_keywords.extend(cat_keywords.get('en', []))
        
        # Générer bullets avec focus sur les bénéfices
        for i in range(self.BULLETS_COUNT):
            if i < len(all_content):
                base_content = all_content[i]
            else:
                # Générer du contenu supplémentaire si nécessaire
                base_content = self._generate_generic_bullet(i, category)
            
            # Optimiser le bullet
            bullet = self._optimize_bullet(
                base_content,
                target_keywords,
                used_concepts,
                i
            )
            
            bullets.append(bullet)
            
            # Ajouter les concepts utilisés pour éviter la répétition
            used_concepts.update(bullet.lower().split())
        
        log_operation(
            "AmazonSEORules",
            "generate_bullets",
            "success",
            bullets_count=len(bullets),
            category=category,
            target_keywords_count=len(target_keywords)
        )
        
        return bullets
    
    def generate_optimized_description(
        self,
        product_name: str,
        features: List[str],
        benefits: List[str],
        use_cases: List[str] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Génère une description riche et lisible optimisée pour A9/A10
        Entre 100 et 2000 caractères
        """
        description_parts = []
        
        # Introduction accrocheuse
        intro = self._generate_description_intro(product_name, category)
        description_parts.append(intro)
        
        # Section des caractéristiques principales
        if features:
            features_section = self._generate_features_section(features)
            description_parts.append(features_section)
        
        # Section des bénéfices
        if benefits:
            benefits_section = self._generate_benefits_section(benefits)
            description_parts.append(benefits_section)
        
        # Section des cas d'usage
        if use_cases:
            use_cases_section = self._generate_use_cases_section(use_cases)
            description_parts.append(use_cases_section)
        
        # Conclusion avec call-to-action
        conclusion = self._generate_description_conclusion(product_name)
        description_parts.append(conclusion)
        
        # Assemblage final
        description = "\n\n".join(description_parts)
        
        # Validation de longueur
        if len(description) < self.DESCRIPTION_MIN_LENGTH:
            description = self._expand_description(description, product_name, category)
        elif len(description) > self.DESCRIPTION_MAX_LENGTH:
            description = description[:self.DESCRIPTION_MAX_LENGTH-3] + "..."
        
        log_info(
            "Description Amazon générée",
            service="AmazonSEORules",
            description_length=len(description),
            product_name=product_name,
            category=category
        )
        
        return description
    
    def generate_backend_keywords(
        self,
        product_name: str,
        category: Optional[str] = None,
        features: List[str] = None,
        additional_keywords: List[str] = None
    ) -> str:
        """
        Génère des backend keywords optimisés (FR/EN mélangés)
        Limite: 250 bytes, sans marques concurrentes
        """
        keywords = []
        
        # Mots-clés extraits du nom du produit
        product_keywords = self._extract_keywords_from_text(product_name)
        keywords.extend(product_keywords)
        
        # Mots-clés de catégorie (FR + EN)
        if category and category.lower() in self.CATEGORY_KEYWORDS:
            cat_data = self.CATEGORY_KEYWORDS[category.lower()]
            keywords.extend(cat_data.get('fr', []))
            keywords.extend(cat_data.get('en', []))
        
        # Mots-clés des features
        if features:
            for feature in features:
                feature_keywords = self._extract_keywords_from_text(feature)
                keywords.extend(feature_keywords)
        
        # Mots-clés additionnels
        if additional_keywords:
            keywords.extend(additional_keywords)
        
        # Nettoyage et déduplication
        keywords = self._clean_and_dedupe_keywords(keywords)
        
        # Filtrage des marques concurrentes
        keywords = self._filter_competitor_brands(keywords)
        
        # Optimisation pour respecter la limite de 250 bytes
        final_keywords = self._optimize_keywords_length(keywords)
        
        log_operation(
            "AmazonSEORules",
            "generate_backend_keywords",
            "success",
            keywords_count=len(keywords),
            final_length_bytes=len(final_keywords.encode('utf-8')),
            category=category
        )
        
        return final_keywords
    
    def validate_amazon_listing(self, listing: AmazonListing) -> ValidationResult:
        """
        Valide un listing Amazon complet selon les règles A9/A10
        Retourne une décision avec raisons détaillées
        """
        reasons = []
        warnings = []
        suggestions = []
        score = 100.0
        details = {}
        
        log_info(
            "Démarrage validation listing Amazon",
            service="AmazonSEORules",
            title_length=len(listing.title) if listing.title else 0,
            bullets_count=len(listing.bullets) if listing.bullets else 0
        )
        
        # 1. Validation du titre
        title_validation = self._validate_title(listing.title)
        score += title_validation['score_delta']
        reasons.extend(title_validation['reasons'])
        warnings.extend(title_validation['warnings'])
        suggestions.extend(title_validation['suggestions'])
        details['title'] = title_validation['details']
        
        # 2. Validation des bullets
        bullets_validation = self._validate_bullets(listing.bullets)
        score += bullets_validation['score_delta']
        reasons.extend(bullets_validation['reasons'])
        warnings.extend(bullets_validation['warnings'])
        suggestions.extend(bullets_validation['suggestions'])
        details['bullets'] = bullets_validation['details']
        
        # 3. Validation de la description
        description_validation = self._validate_description(listing.description)
        score += description_validation['score_delta']
        reasons.extend(description_validation['reasons'])
        warnings.extend(description_validation['warnings'])
        suggestions.extend(description_validation['suggestions'])
        details['description'] = description_validation['details']
        
        # 4. Validation des backend keywords
        keywords_validation = self._validate_backend_keywords(listing.backend_keywords)
        score += keywords_validation['score_delta']
        reasons.extend(keywords_validation['reasons'])
        warnings.extend(keywords_validation['warnings'])
        suggestions.extend(keywords_validation['suggestions'])
        details['backend_keywords'] = keywords_validation['details']
        
        # 5. Validation des images
        images_validation = self._validate_images(listing.images)
        score += images_validation['score_delta']
        reasons.extend(images_validation['reasons'])
        warnings.extend(images_validation['warnings'])
        suggestions.extend(images_validation['suggestions'])
        details['images'] = images_validation['details']
        
        # Détermination du status final
        score = max(0, min(100, score))  # Limiter entre 0 et 100
        
        if score >= 90 and not any("ERREUR" in reason for reason in reasons):
            status = ListingValidationStatus.APPROVED
        elif score >= 70:
            status = ListingValidationStatus.WARNING
        else:
            status = ListingValidationStatus.REJECTED
        
        result = ValidationResult(
            status=status,
            score=score,
            reasons=reasons,
            warnings=warnings,
            suggestions=suggestions,
            details=details
        )
        
        log_operation(
            "AmazonSEORules",
            "validate_listing",
            status.value,
            final_score=score,
            validation_status=status.value,
            reasons_count=len(reasons),
            warnings_count=len(warnings)
        )
        
        return result
    
    # Méthodes privées d'optimisation et validation
    
    def _clean_text(self, text: str) -> str:
        """Nettoie un texte selon les règles Amazon"""
        if not text:
            return ""
        
        # Supprimer les emojis
        text = self.EMOJI_PATTERN.sub('', text)
        
        # Supprimer les mots interdits
        words = text.split()
        cleaned_words = []
        for word in words:
            if word.lower() not in self.FORBIDDEN_WORDS:
                cleaned_words.append(word)
        
        # Normaliser les caractères
        text = " ".join(cleaned_words)
        text = unicodedata.normalize('NFKD', text)
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _validate_and_optimize_title(self, title: str, category: Optional[str]) -> str:
        """Valide et optimise un titre pour respecter les limites"""
        # Vérifier la longueur
        if len(title) > self.TITLE_MAX_LENGTH:
            # Tronquer intelligemment
            title = self._smart_truncate(title, self.TITLE_MAX_LENGTH)
        
        # Ajouter des mots-clés de catégorie si la place le permet
        if category and len(title) < self.TITLE_MAX_LENGTH - 20:
            category_keywords = self._get_category_keywords(category, 'fr')
            if category_keywords and len(title + " " + category_keywords[0]) <= self.TITLE_MAX_LENGTH:
                title += " " + category_keywords[0]
        
        return title
    
    def _optimize_bullet(
        self,
        base_content: str,
        target_keywords: List[str],
        used_concepts: set,
        bullet_index: int
    ) -> str:
        """Optimise un bullet point individuel"""
        # Commencer par un point fort selon l'index
        starters = [
            "✓ PERFORMANCE:",
            "✓ QUALITÉ:",
            "✓ DESIGN:",
            "✓ UTILISATION:",
            "✓ GARANTIE:"
        ]
        
        starter = starters[bullet_index] if bullet_index < len(starters) else "✓ AVANTAGE:"
        
        # Nettoyer le contenu de base
        content = self._clean_text(base_content)
        
        # Ajouter des mots-clés pertinents non utilisés
        for keyword in target_keywords:
            if (keyword.lower() not in used_concepts and 
                keyword.lower() not in content.lower() and
                len(content + " " + keyword) < 240):  # Laisser de la marge
                content += " " + keyword
                break
        
        # Assembler le bullet
        bullet = f"{starter} {content}"
        
        # Vérifier la longueur et tronquer si nécessaire
        if len(bullet) > self.BULLET_MAX_LENGTH:
            bullet = self._smart_truncate(bullet, self.BULLET_MAX_LENGTH)
        
        return bullet
    
    def _generate_generic_bullet(self, index: int, category: Optional[str]) -> str:
        """Génère un bullet générique quand le contenu manque"""
        generic_bullets = [
            "Conception de haute qualité pour une durabilité exceptionnelle",
            "Facilité d'utilisation avec des fonctionnalités intuitives",
            "Performance optimisée pour une satisfaction maximale",
            "Design élégant s'adaptant à tous les environnements",
            "Garantie et support client de premier niveau"
        ]
        
        if index < len(generic_bullets):
            return generic_bullets[index]
        
        return "Produit conçu selon les plus hauts standards de qualité"
    
    def _generate_description_intro(self, product_name: str, category: Optional[str]) -> str:
        """Génère l'introduction de la description"""
        category_intros = {
            'électronique': f"Découvrez {product_name}, la solution technologique qui révolutionne votre quotidien.",
            'mode': f"Adoptez le style avec {product_name}, l'accessoire indispensable de votre garde-robe.",
            'maison': f"Transformez votre intérieur avec {product_name}, l'alliance parfaite du design et de la fonctionnalité.",
            'sport': f"Atteignez vos objectifs avec {product_name}, votre partenaire performance au quotidien."
        }
        
        if category and category.lower() in category_intros:
            return category_intros[category.lower()]
        
        return f"Découvrez {product_name}, un produit d'exception conçu pour répondre à vos besoins les plus exigeants."
    
    def _generate_features_section(self, features: List[str]) -> str:
        """Génère la section des caractéristiques"""
        if not features:
            return ""
        
        section = "CARACTÉRISTIQUES PRINCIPALES:\n"
        for feature in features[:5]:  # Limiter à 5 features max
            section += f"• {self._clean_text(feature)}\n"
        
        return section.strip()
    
    def _generate_benefits_section(self, benefits: List[str]) -> str:
        """Génère la section des bénéfices"""
        if not benefits:
            return ""
        
        section = "BÉNÉFICES POUR VOUS:\n"
        for benefit in benefits[:5]:  # Limiter à 5 bénéfices max
            section += f"✓ {self._clean_text(benefit)}\n"
        
        return section.strip()
    
    def _generate_use_cases_section(self, use_cases: List[str]) -> str:
        """Génère la section des cas d'usage"""
        if not use_cases:
            return ""
        
        section = "UTILISATIONS RECOMMANDÉES:\n"
        for use_case in use_cases[:3]:  # Limiter à 3 cas d'usage max
            section += f"→ {self._clean_text(use_case)}\n"
        
        return section.strip()
    
    def _generate_description_conclusion(self, product_name: str) -> str:
        """Génère la conclusion de la description"""
        return f"Choisissez {product_name} et rejoignez des milliers de clients satisfaits qui ont fait confiance à notre expertise."
    
    def _expand_description(self, description: str, product_name: str, category: Optional[str]) -> str:
        """Étend une description trop courte"""
        additional_content = [
            f"Ce {product_name} représente l'excellence dans sa catégorie.",
            "Conçu avec des matériaux de première qualité pour une longévité optimale.",
            "Notre équipe d'experts a soigneusement sélectionné chaque détail.",
            "Bénéficiez d'un support client réactif et d'une garantie constructeur."
        ]
        
        for content in additional_content:
            if len(description + "\n\n" + content) <= self.DESCRIPTION_MAX_LENGTH:
                description += "\n\n" + content
            else:
                break
        
        return description
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extrait des mots-clés pertinents d'un texte"""
        if not text:
            return []
        
        # Mots vides à ignorer
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'avec',
            'pour', 'par', 'sur', 'sous', 'dans', 'ce', 'cette', 'ces', 'son',
            'the', 'a', 'an', 'and', 'or', 'with', 'for', 'by', 'on', 'in',
            'this', 'that', 'these', 'those', 'his', 'her', 'its'
        }
        
        # Nettoyer et extraire les mots
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filtrer les mots utiles
        keywords = []
        for word in words:
            if (len(word) >= 3 and 
                word not in stop_words and 
                not word.isdigit()):
                keywords.append(word)
        
        return keywords
    
    def _clean_and_dedupe_keywords(self, keywords: List[str]) -> List[str]:
        """Nettoie et déduplique une liste de mots-clés"""
        cleaned = []
        seen = set()
        
        for keyword in keywords:
            if not keyword:
                continue
            
            # Nettoyer le mot-clé
            clean_kw = re.sub(r'[^\w\s]', '', keyword.lower().strip())
            
            if clean_kw and clean_kw not in seen and len(clean_kw) >= 2:
                cleaned.append(clean_kw)
                seen.add(clean_kw)
        
        return cleaned
    
    def _filter_competitor_brands(self, keywords: List[str]) -> List[str]:
        """Filtre les marques concurrentes des mots-clés"""
        filtered = []
        
        for keyword in keywords:
            is_competitor = False
            for competitor in self.COMPETITOR_BRANDS:
                if competitor.lower() in keyword.lower():
                    is_competitor = True
                    break
            
            if not is_competitor:
                filtered.append(keyword)
        
        return filtered
    
    def _optimize_keywords_length(self, keywords: List[str]) -> str:
        """Optimise la longueur des mots-clés pour respecter 250 bytes"""
        # Joindre avec des espaces
        result = " ".join(keywords)
        
        # Vérifier la longueur en bytes
        while len(result.encode('utf-8')) > self.BACKEND_KEYWORDS_MAX_BYTES and keywords:
            # Supprimer le dernier mot-clé
            keywords.pop()
            result = " ".join(keywords)
        
        return result
    
    def _get_category_keywords(self, category: str, language: str) -> List[str]:
        """Récupère les mots-clés d'une catégorie dans une langue"""
        if category.lower() in self.CATEGORY_KEYWORDS:
            return self.CATEGORY_KEYWORDS[category.lower()].get(language, [])
        return []
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Tronque intelligemment un texte à la longueur maximale"""
        if len(text) <= max_length:
            return text
        
        # Trouver le dernier espace avant la limite
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # Au moins 80% de la longueur cible
            return truncated[:last_space]
        else:
            return truncated[:max_length-3] + "..."
    
    # Méthodes de validation détaillées
    
    def _validate_title(self, title: str) -> Dict[str, Any]:
        """Valide le titre selon les règles Amazon"""
        result = {
            'score_delta': 0,
            'reasons': [],
            'warnings': [],
            'suggestions': [],
            'details': {}
        }
        
        if not title:
            result['score_delta'] = -30
            result['reasons'].append("ERREUR: Titre manquant")
            return result
        
        # Longueur
        if len(title) > self.TITLE_MAX_LENGTH:
            result['score_delta'] = -20
            result['reasons'].append(f"ERREUR: Titre trop long ({len(title)}/{self.TITLE_MAX_LENGTH} caractères)")
        elif len(title) < 50:
            result['score_delta'] = -10
            result['warnings'].append(f"Titre court ({len(title)} caractères), considérez l'allonger")
        
        # Emojis
        if self.EMOJI_PATTERN.search(title):
            result['score_delta'] = -15
            result['reasons'].append("ERREUR: Emojis détectés dans le titre")
        
        # Mots promotionnels
        forbidden_found = []
        for word in self.FORBIDDEN_WORDS:
            if word.lower() in title.lower():
                forbidden_found.append(word)
        
        if forbidden_found:
            result['score_delta'] = -10
            result['warnings'].append(f"Mots promotionnels détectés: {', '.join(forbidden_found)}")
        
        # Structure (Brand Model Feature)
        words = title.split()
        if len(words) < 3:
            result['score_delta'] = -5
            result['suggestions'].append("Considérez ajouter plus d'éléments descriptifs (marque, modèle, caractéristiques)")
        
        result['details'] = {
            'length': len(title),
            'word_count': len(words),
            'forbidden_words': forbidden_found,
            'has_emojis': bool(self.EMOJI_PATTERN.search(title))
        }
        
        return result
    
    def _validate_bullets(self, bullets: List[str]) -> Dict[str, Any]:
        """Valide les bullet points"""
        result = {
            'score_delta': 0,
            'reasons': [],
            'warnings': [],
            'suggestions': [],
            'details': {}
        }
        
        if not bullets:
            result['score_delta'] = -25
            result['reasons'].append("ERREUR: Bullets manquants")
            return result
        
        if len(bullets) != self.BULLETS_COUNT:
            result['score_delta'] = -10
            result['warnings'].append(f"Nombre de bullets incorrect ({len(bullets)}/{self.BULLETS_COUNT})")
        
        bullet_details = []
        for i, bullet in enumerate(bullets):
            bullet_info = {'index': i, 'length': len(bullet)}
            
            if len(bullet) > self.BULLET_MAX_LENGTH:
                result['score_delta'] = -5
                result['reasons'].append(f"ERREUR: Bullet {i+1} trop long ({len(bullet)}/{self.BULLET_MAX_LENGTH} caractères)")
                bullet_info['too_long'] = True
            elif len(bullet) < 20:
                result['score_delta'] = -2
                result['warnings'].append(f"Bullet {i+1} très court ({len(bullet)} caractères)")
                bullet_info['too_short'] = True
            
            bullet_details.append(bullet_info)
        
        result['details'] = {
            'count': len(bullets),
            'bullets': bullet_details
        }
        
        return result
    
    def _validate_description(self, description: str) -> Dict[str, Any]:
        """Valide la description"""
        result = {
            'score_delta': 0,
            'reasons': [],
            'warnings': [],
            'suggestions': [],
            'details': {}
        }
        
        if not description:
            result['score_delta'] = -20
            result['reasons'].append("ERREUR: Description manquante")
            return result
        
        length = len(description)
        
        if length < self.DESCRIPTION_MIN_LENGTH:
            result['score_delta'] = -15
            result['reasons'].append(f"ERREUR: Description trop courte ({length}/{self.DESCRIPTION_MIN_LENGTH} caractères minimum)")
        elif length > self.DESCRIPTION_MAX_LENGTH:
            result['score_delta'] = -10
            result['reasons'].append(f"ERREUR: Description trop longue ({length}/{self.DESCRIPTION_MAX_LENGTH} caractères maximum)")
        
        # Vérifier la structure
        has_sections = any(marker in description for marker in ['CARACTÉRISTIQUES', 'BÉNÉFICES', 'UTILISATION'])
        if not has_sections:
            result['score_delta'] = -5
            result['suggestions'].append("Considérez structurer la description avec des sections claires")
        
        result['details'] = {
            'length': length,
            'has_structure': has_sections,
            'paragraph_count': len(description.split('\n\n'))
        }
        
        return result
    
    def _validate_backend_keywords(self, keywords: str) -> Dict[str, Any]:
        """Valide les backend keywords"""
        result = {
            'score_delta': 0,
            'reasons': [],
            'warnings': [],
            'suggestions': [],
            'details': {}
        }
        
        if not keywords:
            result['score_delta'] = -15
            result['warnings'].append("Backend keywords manquants")
            return result
        
        byte_length = len(keywords.encode('utf-8'))
        if byte_length > self.BACKEND_KEYWORDS_MAX_BYTES:
            result['score_delta'] = -20
            result['reasons'].append(f"ERREUR: Backend keywords trop longs ({byte_length}/{self.BACKEND_KEYWORDS_MAX_BYTES} bytes)")
        
        # Vérifier les marques concurrentes
        competitor_found = []
        for competitor in self.COMPETITOR_BRANDS:
            if competitor.lower() in keywords.lower():
                competitor_found.append(competitor)
        
        if competitor_found:
            result['score_delta'] = -10
            result['warnings'].append(f"Marques concurrentes détectées: {', '.join(competitor_found)}")
        
        # Compter les mots-clés uniques
        unique_keywords = set(keywords.split())
        
        result['details'] = {
            'byte_length': byte_length,
            'word_count': len(keywords.split()),
            'unique_keywords': len(unique_keywords),
            'competitor_brands': competitor_found
        }
        
        return result
    
    def _validate_images(self, images: List[str]) -> Dict[str, Any]:
        """Valide les images (URLs et spécifications)"""
        result = {
            'score_delta': 0,
            'reasons': [],
            'warnings': [],
            'suggestions': [],
            'details': {}
        }
        
        if not images:
            result['score_delta'] = -25
            result['reasons'].append("ERREUR: Aucune image fournie")
            return result
        
        if len(images) < 2:
            result['score_delta'] = -10
            result['warnings'].append("Recommandé d'avoir au moins 2 images")
        
        image_details = []
        for i, image_url in enumerate(images):
            img_info = {'index': i, 'url': image_url}
            
            # Vérifier que c'est une URL valide
            try:
                parsed = urlparse(image_url)
                if not parsed.scheme or not parsed.netloc:
                    result['score_delta'] = -5
                    result['warnings'].append(f"Image {i+1}: URL invalide")
                    img_info['valid_url'] = False
                else:
                    img_info['valid_url'] = True
            except:
                result['score_delta'] = -5
                result['warnings'].append(f"Image {i+1}: URL malformée")
                img_info['valid_url'] = False
            
            # Pour l'image principale (index 0), règles plus strictes
            if i == 0:
                result['suggestions'].append("Image principale: vérifiez qu'elle fait ≥1000px et a un fond blanc")
                img_info['is_main'] = True
            
            image_details.append(img_info)
        
        result['details'] = {
            'count': len(images),
            'images': image_details
        }
        
        return result


# Instance globale du service
amazon_seo_rules = AmazonSEORules()

def get_amazon_seo_rules() -> AmazonSEORules:
    """Factory pour obtenir l'instance du service SEO Amazon"""
    return amazon_seo_rules