# Amazon SP-API OAuth Authentication Module
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

logger = logging.getLogger(__name__)

class AmazonOAuthService:
    """Amazon SP-API OAuth 2.0 Authentication Service"""
    
    def __init__(self):
        # Configuration OAuth Amazon
        self.client_id = os.environ.get('AMAZON_LWA_CLIENT_ID')
        self.client_secret = os.environ.get('AMAZON_LWA_CLIENT_SECRET')
        self.encryption_key = os.environ.get('AMAZON_REFRESH_TOKEN_ENCRYPTION_KEY')
        
        if not all([self.client_id, self.client_secret, self.encryption_key]):
            logger.error("❌ Missing required Amazon OAuth configuration")
            raise ValueError("Missing required Amazon OAuth environment variables")
        
        # Endpoints OAuth Amazon par région
        self.oauth_endpoints = {
            'na': {
                'authorize': 'https://sellercentral.amazon.com/apps/authorize/consent',
                'token': 'https://api.amazon.com/auth/o2/token'
            },
            'eu': {
                'authorize': 'https://sellercentral-europe.amazon.com/apps/authorize/consent', 
                'token': 'https://api.amazon.com/auth/o2/token'
            },
            'fe': {
                'authorize': 'https://sellercentral-japan.amazon.com/apps/authorize/consent',
                'token': 'https://api.amazon.com/auth/o2/token'
            }
        }
        
        logger.info("✅ Amazon OAuth service initialized")
    
    def generate_oauth_url(self, marketplace_id: str, region: str = 'eu', 
                          redirect_uri: str = None) -> Dict[str, str]:
        """
        Génère l'URL OAuth Amazon avec state sécurisé
        
        Args:
            marketplace_id: ID du marketplace Amazon
            region: Région Amazon (eu, na, fe)
            redirect_uri: URL de redirection après OAuth
            
        Returns:
            Dict contenant l'URL et le state généré
        """
        try:
            # Générer state sécurisé pour CSRF protection
            state = self._generate_secure_state()
            
            # URL de redirection par défaut
            if not redirect_uri:
                base_url = os.environ.get('APP_BASE_URL', 'https://app.ecomsimply.com')
                redirect_uri = f"{base_url}/api/amazon/callback"
            
            # Paramètres OAuth
            oauth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': redirect_uri,
                'state': state,
                'scope': 'sellingpartnerapi::notifications',
                'version': 'beta'
            }
            
            # Construire l'URL d'autorisation
            endpoint = self.oauth_endpoints[region]['authorize']
            oauth_url = f"{endpoint}?{urlencode(oauth_params)}"
            
            logger.info(f"✅ OAuth URL generated for marketplace {marketplace_id}")
            
            return {
                'authorization_url': oauth_url,
                'state': state,
                'expires_at': datetime.utcnow() + timedelta(minutes=15),
                'region': region,
                'marketplace_id': marketplace_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate OAuth URL: {str(e)}")
            raise
    
    async def exchange_code_for_tokens(self, code: str, state: str, 
                                     region: str = 'eu') -> Dict[str, Any]:
        """
        Échange le code OAuth contre les tokens Amazon
        
        Args:
            code: Code d'autorisation reçu d'Amazon
            state: State OAuth pour validation CSRF
            region: Région Amazon
            
        Returns:
            Dict contenant les tokens et métadonnées
        """
        try:
            logger.info("🔄 Exchanging OAuth code for tokens")
            
            # Vérifier HMAC du state
            if not self._verify_state(state):
                raise ValueError("Invalid OAuth state - potential CSRF attack")
            
            # Préparer les données pour l'échange
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # Headers pour la requête
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'User-Agent': 'ECOMSIMPLY-SP-API/1.0'
            }
            
            # Échanger le code contre les tokens
            token_endpoint = self.oauth_endpoints[region]['token']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_endpoint,
                    data=urlencode(token_data),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        tokens = await response.json()
                        
                        # Validation des tokens reçus
                        if not all(k in tokens for k in ['access_token', 'refresh_token']):
                            raise ValueError("Invalid token response from Amazon")
                        
                        logger.info("✅ Tokens successfully retrieved from Amazon")
                        
                        return {
                            'access_token': tokens['access_token'],
                            'refresh_token': tokens['refresh_token'],
                            'token_type': tokens.get('token_type', 'bearer'),
                            'expires_in': tokens.get('expires_in', 3600),
                            'scope': tokens.get('scope', ''),
                            'retrieved_at': datetime.utcnow()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Token exchange failed: {response.status} - {error_text}")
                        raise Exception(f"Amazon token exchange failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Token exchange error: {str(e)}")
            raise
    
    def encrypt_refresh_token(self, refresh_token: str, user_id: str) -> Dict[str, str]:
        """
        Chiffre le refresh token avec AES-GCM
        
        Args:
            refresh_token: Token à chiffrer
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
            ciphertext = aesgcm.encrypt(nonce, refresh_token.encode(), None)
            
            return {
                'encrypted_token': base64.b64encode(ciphertext).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'encryption_method': 'AES-GCM',
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Token encryption failed: {str(e)}")
            raise
    
    def decrypt_refresh_token(self, encrypted_data: Dict[str, str], 
                            user_id: str) -> str:
        """
        Déchiffre le refresh token
        
        Args:
            encrypted_data: Données chiffrées
            user_id: ID utilisateur pour le salt
            
        Returns:
            Refresh token déchiffré
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
    
    def _generate_secure_state(self) -> str:
        """Génère un state OAuth sécurisé avec HMAC"""
        # Générer un token aléatoire
        random_token = secrets.token_urlsafe(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Créer HMAC signature
        data = f"{random_token}:{timestamp}"
        signature = hashlib.hmac.new(
            self.client_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Encoder le state final
        state_data = f"{data}:{signature}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()
    
    def _verify_state(self, state: str) -> bool:
        """Vérifie la validité du state OAuth"""
        try:
            # Décoder le state
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            parts = decoded.split(':')
            
            if len(parts) != 3:
                return False
            
            random_token, timestamp, signature = parts
            data = f"{random_token}:{timestamp}"
            
            # Vérifier la signature HMAC
            expected_sig = hashlib.hmac.new(
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

    def verify_lwa_signature(self, payload: str, signature: str) -> bool:
        """
        Vérifie la signature HMAC des webhooks Amazon LWA
        
        Args:
            payload: Corps de la requête
            signature: Signature HMAC reçue
            
        Returns:
            True si la signature est valide
        """
        try:
            # Calculer la signature attendue
            expected_signature = hashlib.hmac.new(
                self.client_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Comparaison sécurisée
            return secrets.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"❌ LWA signature verification failed: {str(e)}")
            return False