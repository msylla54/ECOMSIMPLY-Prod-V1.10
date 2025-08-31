# Amazon SEO Service - Optimisation pour algorithme A9/A10 d'Amazon
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AmazonSEOValidation:
    """Résultat de validation SEO Amazon"""
    is_valid: bool
    score: float
    issues: List[str]
    recommendations: List[str]
    optimized_content: Optional[Dict[str, Any]] = None

class AmazonSEORules:
    """
    Service d'optimisation SEO pour Amazon selon les règles A9/A10
    
    Règles Amazon SP-API:
    - Titre: ≤ 200 caractères, mots-clés stratégiques, pas de promo
    - Bullet Points: 5 points, bénéfices clairs, mots-clés variés
    - Description: riche, lisible, HTML minimal autorisé
    - Backend Keywords: ≤ 250 bytes, pas de doublons, pas de marques concurrentes
    - Images: principale ≥ 1000px, fond blanc obligatoire
    """
    
    # Configuration SEO Amazon
    MAX_TITLE_LENGTH = 200
    REQUIRED_BULLET_POINTS = 5
    MAX_BULLET_LENGTH = 255
    MAX_BACKEND_KEYWORDS_BYTES = 250
    MIN_IMAGE_SIZE = 1000
    
    # Mots interdits Amazon
    FORBIDDEN_WORDS = {
        'best', 'meilleur', 'top', 'numéro 1', '#1', 'nouveau', 'new',
        'livraison gratuite', 'free shipping', 'promo', 'solde', 'réduction',
        'offre spéciale', 'limited time', 'exclusive', 'garanti', 'guarantee'
    }
    
    # Marques concurrentes interdites
    COMPETITOR_BRANDS = {
        'apple', 'samsung', 'nike', 'adidas', 'sony', 'lg', 'canon', 'nikon'
    }
    
    def __init__(self):
        """Initialise le service SEO Amazon"""
        logger.info("✅ Amazon SEO Service initialized")
    
    def optimize_title(self, product_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Optimise le titre selon les règles Amazon A9/A10
        
        Format optimal: [Marque] [Modèle] [Caractéristique Clé] [Taille/Capacité] [Couleur]
        
        Args:
            product_data: Données produit à optimiser
            
        Returns:
            Tuple (titre_optimisé, recommandations)
        """
        try:
            recommendations = []
            
            # Récupération des données
            brand = product_data.get('brand', '').strip()
            product_name = product_data.get('product_name', '').strip()
            key_features = product_data.get('key_features', [])
            category = product_data.get('category', '').strip()
            
            # Construction du titre optimisé
            title_parts = []
            
            # 1. Marque (si disponible)
            if brand:
                title_parts.append(brand)
            else:
                recommendations.append("Ajoutez une marque pour améliorer la visibilité")
            
            # 2. Nom du produit principal
            if product_name:
                # Nettoyer le nom (supprimer mots interdits)
                cleaned_name = self._clean_forbidden_words(product_name)
                title_parts.append(cleaned_name)
            
            # 3. Caractéristiques clés (les 2 plus importantes)
            if key_features:
                key_features_str = ' '.join(key_features[:2])
                cleaned_features = self._clean_forbidden_words(key_features_str)
                if cleaned_features:
                    title_parts.append(cleaned_features)
            
            # 4. Catégorie (si pertinente)
            if category and category.lower() not in product_name.lower():
                title_parts.append(category)
            
            # Construction finale
            optimized_title = ' '.join(title_parts)
            
            # Validation longueur
            if len(optimized_title) > self.MAX_TITLE_LENGTH:
                # Truncate intelligemment
                optimized_title = optimized_title[:self.MAX_TITLE_LENGTH-3] + '...'
                recommendations.append(f"Titre tronqué à {self.MAX_TITLE_LENGTH} caractères")
            
            # Validation mots-clés
            if len(optimized_title.split()) < 3:
                recommendations.append("Ajoutez plus de mots-clés descriptifs")
            
            # Validation caractères spéciaux
            if any(char in optimized_title for char in ['™', '®', '©']):
                recommendations.append("Évitez les symboles ™, ®, © dans le titre")
            
            logger.info(f"🔤 Titre Amazon optimisé: {len(optimized_title)} caractères")
            return optimized_title, recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation titre Amazon: {e}")
            return product_data.get('product_name', 'Produit'), ["Erreur d'optimisation"]
    
    def generate_bullet_points(self, product_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Génère 5 bullet points optimisés pour Amazon
        
        Structure optimale par bullet:
        - Point 1: Bénéfice principal + mot-clé primaire
        - Point 2: Caractéristiques techniques + mots-clés secondaires  
        - Point 3: Usage/application + mots-clés de niche
        - Point 4: Qualité/durabilité + mots-clés émotionnels
        - Point 5: Compatibilité/dimensions + mots-clés techniques
        
        Args:
            product_data: Données produit
            
        Returns:
            Tuple (bullet_points, recommandations)
        """
        try:
            recommendations = []
            bullet_points = []
            
            description = product_data.get('description', '')
            features = product_data.get('key_features', [])
            benefits = product_data.get('benefits', [])
            specifications = product_data.get('specifications', {})
            
            # Template pour différents types de produits
            templates = self._get_bullet_templates(product_data.get('category', ''))
            
            # Bullet Point 1: Bénéfice principal
            if benefits:
                bullet1 = f"✓ AVANTAGE PRINCIPAL: {benefits[0]}"
                bullet_points.append(self._optimize_bullet_point(bullet1))
            elif description:
                primary_benefit = description[:100] + "..." if len(description) > 100 else description
                bullet1 = f"✓ {primary_benefit}"
                bullet_points.append(self._optimize_bullet_point(bullet1))
            
            # Bullet Point 2: Caractéristiques techniques
            if features:
                tech_features = ' | '.join(features[:3])
                bullet2 = f"📋 CARACTÉRISTIQUES: {tech_features}"
                bullet_points.append(self._optimize_bullet_point(bullet2))
            
            # Bullet Point 3: Usage et applications
            usage_bullet = self._generate_usage_bullet(product_data)
            if usage_bullet:
                bullet_points.append(usage_bullet)
            
            # Bullet Point 4: Qualité et durabilité
            quality_bullet = self._generate_quality_bullet(product_data)
            if quality_bullet:
                bullet_points.append(quality_bullet)
            
            # Bullet Point 5: Spécifications et compatibilité
            if specifications:
                spec_items = list(specifications.items())[:2]
                spec_text = ' | '.join([f"{k}: {v}" for k, v in spec_items])
                bullet5 = f"⚙️ SPÉCIFICATIONS: {spec_text}"
                bullet_points.append(self._optimize_bullet_point(bullet5))
            
            # Compléter avec des bullets génériques si nécessaire
            while len(bullet_points) < self.REQUIRED_BULLET_POINTS:
                generic_bullet = self._generate_generic_bullet(len(bullet_points) + 1, product_data)
                bullet_points.append(generic_bullet)
            
            # Validation finale
            for i, bullet in enumerate(bullet_points):
                if len(bullet) > self.MAX_BULLET_LENGTH:
                    bullet_points[i] = bullet[:self.MAX_BULLET_LENGTH-3] + '...'
                    recommendations.append(f"Bullet point {i+1} tronqué")
            
            logger.info(f"🔹 {len(bullet_points)} bullet points Amazon générés")
            return bullet_points[:self.REQUIRED_BULLET_POINTS], recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur génération bullet points: {e}")
            return self._get_fallback_bullets(product_data), ["Erreur de génération"]
    
    def optimize_description(self, product_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Optimise la description produit pour Amazon A+
        
        Structure optimale:
        - Paragraphe d'accroche avec mots-clés primaires
        - Section avantages avec émojis
        - Section techniques avec spécifications
        - Section usage et compatibilité
        - Call-to-action subtil
        
        Args:
            product_data: Données produit
            
        Returns:
            Tuple (description_optimisée, recommandations)
        """
        try:
            recommendations = []
            sections = []
            
            product_name = product_data.get('product_name', 'Ce produit')
            description = product_data.get('description', '')
            features = product_data.get('key_features', [])
            benefits = product_data.get('benefits', [])
            
            # Section 1: Accroche avec mots-clés
            hook_section = f"""
<h3>🌟 Découvrez {product_name}</h3>
<p>{description[:200]}{"..." if len(description) > 200 else ""}</p>
"""
            sections.append(hook_section)
            
            # Section 2: Avantages principaux
            if benefits:
                benefits_section = "<h4>✅ Avantages Clés</h4>\n<ul>\n"
                for benefit in benefits[:4]:
                    benefits_section += f"<li>{benefit}</li>\n"
                benefits_section += "</ul>\n"
                sections.append(benefits_section)
            
            # Section 3: Caractéristiques techniques
            if features:
                features_section = "<h4>⚙️ Caractéristiques</h4>\n<ul>\n"
                for feature in features[:5]:
                    features_section += f"<li>{feature}</li>\n"
                features_section += "</ul>\n"
                sections.append(features_section)
            
            # Section 4: Usage et applications
            usage_section = f"""
<h4>🎯 Utilisation</h4>
<p>Parfait pour un usage quotidien, {product_name} s'adapte à tous vos besoins. 
Que ce soit pour un usage professionnel ou personnel, ce produit vous accompagne 
avec fiabilité et performance.</p>
"""
            sections.append(usage_section)
            
            # Assemblage final
            optimized_description = '\n'.join(sections)
            
            # Nettoyage HTML (Amazon accepte un HTML limité)
            optimized_description = self._clean_html_for_amazon(optimized_description)
            
            # Validation longueur (Amazon recommande 1000-2000 caractères)
            char_count = len(optimized_description)
            if char_count < 500:
                recommendations.append("Description courte - ajoutez plus de détails")
            elif char_count > 2000:
                recommendations.append("Description longue - condensez le contenu")
            
            logger.info(f"📝 Description Amazon optimisée: {char_count} caractères")
            return optimized_description, recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation description: {e}")
            return description, ["Erreur d'optimisation"]
    
    def generate_backend_keywords(self, product_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Génère les mots-clés backend Amazon (Search Terms)
        
        Règles critiques:
        - Maximum 250 bytes total
        - Pas de doublons
        - Pas de marques concurrentes
        - Pas de termes du titre/bullets
        - Séparés par des espaces (pas de virgules)
        - Inclure synonymes et variantes
        
        Args:
            product_data: Données produit
            
        Returns:
            Tuple (keywords_string, recommandations)
        """
        try:
            recommendations = []
            keywords = set()
            
            # Collecte des mots-clés de base
            product_name = product_data.get('product_name', '').lower()
            category = product_data.get('category', '').lower()
            description = product_data.get('description', '').lower()
            features = [f.lower() for f in product_data.get('key_features', [])]
            
            # Extraction des mots-clés du titre existant (pour éviter doublons)
            existing_title_words = set(re.findall(r'\w+', product_name))
            
            # Génération de synonymes et variantes
            category_synonyms = self._get_category_synonyms(category)
            keywords.update(category_synonyms)
            
            # Mots-clés de caractéristiques
            for feature in features:
                feature_words = re.findall(r'\w+', feature)
                for word in feature_words:
                    if len(word) > 3 and word not in existing_title_words:
                        keywords.add(word)
            
            # Mots-clés d'usage
            usage_keywords = self._generate_usage_keywords(product_data)
            keywords.update(usage_keywords)
            
            # Mots-clés émotionnels/bénéfices
            benefit_keywords = self._generate_benefit_keywords(product_data)
            keywords.update(benefit_keywords)
            
            # Nettoyage et filtrage
            filtered_keywords = set()
            for keyword in keywords:
                # Supprimer mots interdits
                if not any(forbidden in keyword.lower() for forbidden in self.FORBIDDEN_WORDS):
                    # Supprimer marques concurrentes
                    if not any(brand in keyword.lower() for brand in self.COMPETITOR_BRANDS):
                        # Supprimer mots trop courts
                        if len(keyword) > 2:
                            filtered_keywords.add(keyword)
            
            # Construction de la chaîne finale
            keywords_list = list(filtered_keywords)
            keywords_string = ' '.join(keywords_list)
            
            # Validation taille (250 bytes max)
            keywords_bytes = len(keywords_string.encode('utf-8'))
            if keywords_bytes > self.MAX_BACKEND_KEYWORDS_BYTES:
                # Tronquer intelligemment
                truncated_keywords = []
                current_bytes = 0
                
                for keyword in keywords_list:
                    keyword_bytes = len(keyword.encode('utf-8')) + 1  # +1 pour l'espace
                    if current_bytes + keyword_bytes <= self.MAX_BACKEND_KEYWORDS_BYTES:
                        truncated_keywords.append(keyword)
                        current_bytes += keyword_bytes
                    else:
                        break
                
                keywords_string = ' '.join(truncated_keywords)
                recommendations.append(f"Mots-clés tronqués pour respecter la limite de {self.MAX_BACKEND_KEYWORDS_BYTES} bytes")
            
            logger.info(f"🔍 {len(filtered_keywords)} mots-clés backend générés ({keywords_bytes} bytes)")
            return keywords_string, recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur génération mots-clés backend: {e}")
            return "", ["Erreur de génération"]
    
    def validate_listing(self, listing_data: Dict[str, Any]) -> AmazonSEOValidation:
        """
        Validation complète d'une liste Amazon selon les règles SEO A9/A10
        
        Args:
            listing_data: Données de la liste Amazon
            
        Returns:
            AmazonSEOValidation avec score et recommandations
        """
        try:
            issues = []
            recommendations = []
            score_components = []
            
            title = listing_data.get('title', '')
            bullet_points = listing_data.get('bullet_points', [])
            description = listing_data.get('description', '')
            backend_keywords = listing_data.get('backend_keywords', '')
            images = listing_data.get('images', [])
            
            # Validation du titre (25 points)
            title_score = self._validate_title(title, issues, recommendations)
            score_components.append(title_score * 0.25)
            
            # Validation des bullet points (30 points)
            bullets_score = self._validate_bullet_points(bullet_points, issues, recommendations)
            score_components.append(bullets_score * 0.30)
            
            # Validation de la description (20 points)
            desc_score = self._validate_description(description, issues, recommendations)
            score_components.append(desc_score * 0.20)
            
            # Validation des mots-clés backend (15 points)
            keywords_score = self._validate_backend_keywords(backend_keywords, issues, recommendations)
            score_components.append(keywords_score * 0.15)
            
            # Validation des images (10 points)
            images_score = self._validate_images(images, issues, recommendations)
            score_components.append(images_score * 0.10)
            
            # Score final
            total_score = sum(score_components)
            is_valid = total_score >= 0.7  # 70% minimum pour validation
            
            logger.info(f"📊 Validation Amazon SEO: {total_score:.2f}/1.0 ({len(issues)} issues)")
            
            return AmazonSEOValidation(
                is_valid=is_valid,
                score=total_score,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur validation listing Amazon: {e}")
            return AmazonSEOValidation(
                is_valid=False,
                score=0.0,
                issues=["Erreur de validation"],
                recommendations=["Contactez le support"]
            )
    
    # Méthodes utilitaires privées
    
    def _clean_forbidden_words(self, text: str) -> str:
        """Supprime les mots interdits par Amazon"""
        for word in self.FORBIDDEN_WORDS:
            text = re.sub(rf'\b{re.escape(word)}\b', '', text, flags=re.IGNORECASE)
        return ' '.join(text.split())  # Nettoie les espaces multiples
    
    def _get_bullet_templates(self, category: str) -> Dict[str, str]:
        """Retourne des templates de bullets selon la catégorie"""
        templates = {
            'electronique': {
                'template1': '⚡ PERFORMANCE: {feature} - Technologie avancée pour {benefit}',
                'template2': '🔧 COMPATIBILITÉ: Compatible avec {compatibility} - {usage}',
                'template3': '🛡️ QUALITÉ: Certification {cert} - Garantie {warranty}',
            },
            'mode': {
                'template1': '👕 STYLE: {design} - Parfait pour {occasion}',
                'template2': '🧵 MATIÈRE: {material} - Confort et durabilité',
                'template3': '📏 TAILLE: Taille {size} - Coupe {fit}',
            },
            'default': {
                'template1': '✨ AVANTAGE: {feature} pour {benefit}',
                'template2': '🎯 USAGE: Idéal pour {usage}',
                'template3': '🏆 QUALITÉ: {quality_aspect}',
            }
        }
        return templates.get(category, templates['default'])
    
    def _optimize_bullet_point(self, bullet: str) -> str:
        """Optimise un bullet point individuel"""
        # Nettoyer les mots interdits
        cleaned = self._clean_forbidden_words(bullet)
        
        # S'assurer qu'il commence par un émoji ou symbole
        if not re.match(r'^[✓✅🔹⚡🎯🏆📋⚙️🛡️]', cleaned):
            cleaned = f"✓ {cleaned}"
        
        return cleaned[:self.MAX_BULLET_LENGTH]
    
    def _generate_usage_bullet(self, product_data: Dict[str, Any]) -> str:
        """Génère un bullet point d'usage"""
        category = product_data.get('category', '')
        usage_templates = {
            'electronique': '🎯 USAGE: Parfait pour gaming, travail et divertissement quotidien',
            'mode': '👗 OCCASION: Idéal pour travail, sorties et événements spéciaux',
            'maison': '🏠 UTILISATION: Améliore votre confort quotidien et décoration',
            'default': '🎯 APPLICATION: Polyvalent pour tous vos besoins quotidiens'
        }
        return usage_templates.get(category, usage_templates['default'])
    
    def _generate_quality_bullet(self, product_data: Dict[str, Any]) -> str:
        """Génère un bullet point de qualité"""
        return "🏆 QUALITÉ PREMIUM: Matériaux durables et finition soignée pour une longévité optimale"
    
    def _generate_generic_bullet(self, index: int, product_data: Dict[str, Any]) -> str:
        """Génère un bullet générique selon l'index"""
        generics = [
            "✨ INNOVATION: Design moderne et fonctionnalités avancées",
            "🔒 FIABILITÉ: Testé et approuvé pour une utilisation intensive",
            "🎁 SATISFACTION: Garantie satisfaction client - Support technique inclus",
            "🌟 EXCELLENCE: Produit de qualité supérieure aux normes strictes",
            "💎 PREMIUM: Finition haut de gamme et attention aux détails"
        ]
        return generics[index % len(generics)]
    
    def _get_fallback_bullets(self, product_data: Dict[str, Any]) -> List[str]:
        """Bullets de secours en cas d'erreur"""
        product_name = product_data.get('product_name', 'Ce produit')
        return [
            f"✓ QUALITÉ: {product_name} de haute qualité",
            f"✓ PERFORMANCE: Conçu pour vos besoins quotidiens",
            f"✓ DURABILITÉ: Matériaux résistants et durables",
            f"✓ FACILITÉ: Simple d'utilisation et d'entretien",
            f"✓ GARANTIE: Satisfaction client garantie"
        ]
    
    def _clean_html_for_amazon(self, html: str) -> str:
        """Nettoie le HTML pour Amazon (tags autorisés seulement)"""
        allowed_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'h3', 'h4']
        # Implémentation simplifiée - en production, utiliser BeautifulSoup
        return html
    
    def _get_category_synonyms(self, category: str) -> set:
        """Retourne des synonymes pour une catégorie"""
        synonyms_map = {
            'electronique': {'tech', 'numérique', 'digital', 'gadget', 'appareil'},
            'mode': {'vêtement', 'style', 'fashion', 'tendance', 'look'},
            'maison': {'décoration', 'intérieur', 'habitat', 'domicile', 'foyer'},
        }
        return synonyms_map.get(category, set())
    
    def _generate_usage_keywords(self, product_data: Dict[str, Any]) -> set:
        """Génère des mots-clés d'usage"""
        return {'quotidien', 'pratique', 'utile', 'efficace', 'polyvalent'}
    
    def _generate_benefit_keywords(self, product_data: Dict[str, Any]) -> set:
        """Génère des mots-clés de bénéfices optimisés"""
        base_keywords = {'confort', 'performance', 'qualité', 'durabilité', 'fiabilité'}
        
        # Ajouter des mots-clés spécifiques selon la catégorie
        category = product_data.get('category', '').lower()
        if 'electronique' in category:
            base_keywords.update({'technologie', 'innovation', 'connectivité'})
        elif 'mode' in category:
            base_keywords.update({'style', 'tendance', 'élégance'})
        
        return base_keywords
    
    def _validate_title(self, title: str, issues: List[str], recommendations: List[str]) -> float:
        """Valide le titre et retourne un score 0-1"""
        score = 1.0
        
        if not title:
            issues.append("Titre manquant")
            return 0.0
        
        if len(title) > self.MAX_TITLE_LENGTH:
            issues.append(f"Titre trop long ({len(title)}/{self.MAX_TITLE_LENGTH} caractères)")
            score -= 0.3
        
        if len(title) < 50:
            recommendations.append("Titre court - ajoutez plus de mots-clés")
            score -= 0.1
        
        # Vérifier mots interdits
        forbidden_found = [word for word in self.FORBIDDEN_WORDS if word.lower() in title.lower()]
        if forbidden_found:
            issues.append(f"Mots interdits trouvés: {', '.join(forbidden_found)}")
            score -= 0.4
        
        return max(score, 0.0)
    
    def _validate_bullet_points(self, bullets: List[str], issues: List[str], recommendations: List[str]) -> float:
        """Valide les bullet points et retourne un score 0-1"""
        if len(bullets) != self.REQUIRED_BULLET_POINTS:
            issues.append(f"{len(bullets)}/5 bullet points (5 requis)")
            return 0.0
        
        score = 1.0
        for i, bullet in enumerate(bullets):
            if len(bullet) > self.MAX_BULLET_LENGTH:
                issues.append(f"Bullet {i+1} trop long")
                score -= 0.1
            
            if len(bullet) < 20:
                recommendations.append(f"Bullet {i+1} trop court")
                score -= 0.05
        
        return max(score, 0.0)
    
    def _validate_description(self, description: str, issues: List[str], recommendations: List[str]) -> float:
        """Valide la description et retourne un score 0-1"""
        score = 1.0
        
        if not description:
            issues.append("Description manquante")
            return 0.0
        
        if len(description) < 500:
            recommendations.append("Description courte - ajoutez plus de détails")
            score -= 0.2
        
        if len(description) > 2000:
            recommendations.append("Description longue - condensez")
            score -= 0.1
        
        return max(score, 0.0)
    
    def _validate_backend_keywords(self, keywords: str, issues: List[str], recommendations: List[str]) -> float:
        """Valide les mots-clés backend et retourne un score 0-1"""
        score = 1.0
        
        if not keywords:
            issues.append("Mots-clés backend manquants")
            return 0.0
        
        keywords_bytes = len(keywords.encode('utf-8'))
        if keywords_bytes > self.MAX_BACKEND_KEYWORDS_BYTES:
            issues.append(f"Mots-clés trop longs ({keywords_bytes}/{self.MAX_BACKEND_KEYWORDS_BYTES} bytes)")
            score -= 0.3
        
        return max(score, 0.0)
    
    def _validate_images(self, images: List[Dict], issues: List[str], recommendations: List[str]) -> float:
        """Valide les images et retourne un score 0-1"""
        score = 1.0
        
        if not images:
            issues.append("Aucune image fournie")
            return 0.0
        
        # Vérifier image principale
        main_image = images[0] if images else None
        if main_image:
            width = main_image.get('width', 0)
            height = main_image.get('height', 0)
            
            if width < self.MIN_IMAGE_SIZE or height < self.MIN_IMAGE_SIZE:
                issues.append(f"Image principale trop petite ({width}x{height}, minimum {self.MIN_IMAGE_SIZE}px)")
                score -= 0.5
        
        return max(score, 0.0)