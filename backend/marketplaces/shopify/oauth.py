# Shopify OAuth Authentication Module
import os
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
import json
from urllib.parse import urlencode, quote_plus
import hmac

logger = logging.getLogger(__name__)

class ShopifyOAuthService:
    """Shopify OAuth 2.0 Authentication Service"""
    
    def __init__(self):
        # Configuration OAuth Shopify
        self.client_id = os.environ.get('SHOPIFY_CLIENT_ID')
        self.client_secret = os.environ.get('SHOPIFY_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('SHOPIFY_REDIRECT_URI')
        self.scopes = os.environ.get('SHOPIFY_SCOPES', 'read_products,write_products,read_orders')
        self.encryption_key = os.environ.get('SHOPIFY_ACCESS_TOKEN_ENCRYPTION_KEY')
        
        if not all([self.client_id, self.client_secret, self.encryption_key]):
            logger.error("❌ Missing required Shopify OAuth configuration")
            raise ValueError("Missing required Shopify OAuth environment variables")
        
        # Default redirect URI if not provided
        if not self.redirect_uri:
            base_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
            self.redirect_uri = f"{base_url}/api/shopify/callback"
        
        logger.info("✅ Shopify OAuth service initialized")
    
    def generate_install_url(self, shop_domain: str, user_id: str) -> Dict[str, str]:
        """
        Génère l'URL d'installation Shopify avec state sécurisé
        
        Args:
            shop_domain: Domaine de la boutique Shopify (ex: monshop.myshopify.com)
            user_id: ID utilisateur ECOMSIMPLY
            
        Returns:
            Dict contenant l'URL et le state généré
        """
        try:
            # Générer state sécurisé pour CSRF protection
            state = self._generate_secure_state(user_id)
            
            # Valider et nettoyer le domaine
            clean_shop = self._validate_shop_domain(shop_domain)
            
            # Paramètres OAuth Shopify
            oauth_params = {
                'client_id': self.client_id,
                'scope': self.scopes,
                'redirect_uri': self.redirect_uri,
                'state': state,
                'response_type': 'code'
            }
            
            # Construire l'URL d'installation
            install_url = f"https://{clean_shop}/admin/oauth/authorize?{urlencode(oauth_params)}"
            
            logger.info(f"✅ Shopify install URL generated for shop {clean_shop}")
            
            return {
                'install_url': install_url,
                'state': state,
                'shop_domain': clean_shop,
                'expires_at': datetime.utcnow() + timedelta(minutes=15),
                'scopes': self.scopes
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate install URL: {str(e)}")
            raise
    
    async def exchange_code_for_token(self, shop_domain: str, code: str, 
                                    state: str, user_id: str) -> Dict[str, Any]:
        """
        Échange le code OAuth contre un access token Shopify
        
        Args:
            shop_domain: Domaine de la boutique
            code: Code d'autorisation reçu de Shopify
            state: State OAuth pour validation CSRF
            user_id: ID utilisateur pour vérification
            
        Returns:
            Dict contenant le token et les métadonnées
        """
        try:
            logger.info(f"🔄 Exchanging OAuth code for token - shop: {shop_domain}")
            
            # Vérifier HMAC du state
            if not self._verify_state(state, user_id):
                raise ValueError("Invalid OAuth state - potential CSRF attack")
            
            # Valider le domaine de boutique
            clean_shop = self._validate_shop_domain(shop_domain)
            
            # Préparer les données pour l'échange
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code
            }
            
            # Headers pour la requête
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'ECOMSIMPLY-Shopify/1.0'
            }
            
            # Échanger le code contre le token
            token_endpoint = f"https://{clean_shop}/admin/oauth/access_token"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_endpoint,
                    json=token_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Validation du token reçu
                        if 'access_token' not in token_response:
                            raise ValueError("Invalid token response from Shopify")
                        
                        logger.info("✅ Access token successfully retrieved from Shopify")
                        
                        return {
                            'access_token': token_response['access_token'],
                            'scope': token_response.get('scope', self.scopes),
                            'shop_domain': clean_shop,
                            'retrieved_at': datetime.utcnow()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Token exchange failed: {response.status} - {error_text}")
                        raise Exception(f"Shopify token exchange failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Token exchange error: {str(e)}")
            raise
    
    def encrypt_access_token(self, access_token: str, user_id: str) -> Dict[str, str]:
        """
        Chiffre l'access token avec AES-GCM
        
        Args:
            access_token: Token à chiffrer
            user_id: ID utilisateur pour le salt
            
        Returns:
            Dict contenant le token chiffré et les métadonnées
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            
            # Générer une clé dérivée
            salt = hashlib.sha256(f"{user_id}:{self.encryption_key}".encode()).digest()[:16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(self.encryption_key.encode())
            
            # Chiffrer avec AES-GCM
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, access_token.encode(), None)
            
            return {
                'encrypted_token': base64.b64encode(ciphertext).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'encryption_method': 'AES-GCM',
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Token encryption failed: {str(e)}")
            raise
    
    def decrypt_access_token(self, encrypted_data: Dict[str, str], 
                           user_id: str) -> str:
        """
        Déchiffre l'access token
        
        Args:
            encrypted_data: Données chiffrées
            user_id: ID utilisateur pour le salt
            
        Returns:
            Access token déchiffré
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            
            # Reconstituer la clé dérivée
            salt = hashlib.sha256(f"{user_id}:{self.encryption_key}".encode()).digest()[:16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(self.encryption_key.encode())
            
            # Déchiffrer
            aesgcm = AESGCM(key)
            nonce = base64.b64decode(encrypted_data['nonce'])
            ciphertext = base64.b64decode(encrypted_data['encrypted_token'])
            
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"❌ Token decryption failed: {str(e)}")
            raise
    
    def verify_webhook_signature(self, data: str, signature: str) -> bool:
        """
        Vérifie la signature HMAC des webhooks Shopify
        
        Args:
            data: Corps de la requête
            signature: Signature HMAC reçue (X-Shopify-Hmac-Sha256)
            
        Returns:
            True si la signature est valide
        """
        try:
            # Calculer la signature attendue
            expected_signature = base64.b64encode(
                hmac.new(
                    self.client_secret.encode(),
                    data.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            # Comparaison sécurisée
            return secrets.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"❌ Webhook signature verification failed: {str(e)}")
            return False
    
    def _generate_secure_state(self, user_id: str) -> str:
        """Génère un state OAuth sécurisé avec HMAC"""
        # Générer un token aléatoire
        random_token = secrets.token_urlsafe(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Créer HMAC signature avec user_id inclus
        data = f"{random_token}:{timestamp}:{user_id}"
        signature = hmac.new(
            self.client_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Encoder le state final
        state_data = f"{data}:{signature}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()
    
    def _verify_state(self, state: str, user_id: str) -> bool:
        """Vérifie la validité du state OAuth"""
        try:
            # Décoder le state
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            parts = decoded.split(':')
            
            if len(parts) != 4:
                return False
            
            random_token, timestamp, state_user_id, signature = parts
            
            # Vérifier que l'user_id correspond
            if state_user_id != user_id:
                logger.warning("⚠️ State user_id mismatch")
                return False
            
            data = f"{random_token}:{timestamp}:{state_user_id}"
            
            # Vérifier la signature HMAC
            expected_sig = hmac.new(
                self.client_secret.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not secrets.compare_digest(signature, expected_sig):
                return False
            
            # Vérifier l'expiration (15 minutes max)
            state_time = datetime.utcfromtimestamp(int(timestamp))
            if datetime.utcnow() - state_time > timedelta(minutes=15):
                logger.warning("⚠️ OAuth state expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ State verification failed: {str(e)}")
            return False
    
    def _validate_shop_domain(self, shop_domain: str) -> str:
        """
        Valide et nettoie le domaine de boutique Shopify
        
        Args:
            shop_domain: Domaine brut à valider
            
        Returns:
            Domaine nettoyé et validé
        """
        if not shop_domain:
            raise ValueError("Shop domain is required")
        
        # Supprimer les espaces et convertir en minuscules
        shop = shop_domain.strip().lower()
        
        # Supprimer les protocoles s'ils sont présents
        shop = shop.replace('https://', '').replace('http://', '')
        
        # Supprimer les chemins s'ils sont présents
        shop = shop.split('/')[0]
        
        # Ajouter .myshopify.com si ce n'est pas déjà présent
        if not shop.endswith('.myshopify.com'):
            if '.' in shop:
                # Si c'est déjà un domaine personnalisé, le garder tel quel
                # mais nous devons utiliser .myshopify.com pour l'OAuth
                shop_name = shop.split('.')[0]
                shop = f"{shop_name}.myshopify.com"
            else:
                # C'est juste le nom de la boutique
                shop = f"{shop}.myshopify.com"
        
        # Validation finale du format
        if not shop.endswith('.myshopify.com') or len(shop) < 15:  # min: "a.myshopify.com"
            raise ValueError("Invalid shop domain format")
        
        return shop