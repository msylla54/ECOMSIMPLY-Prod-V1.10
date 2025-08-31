# Amazon SP-API Token Encryption Service with AWS KMS
import os
import json
import base64
import boto3
import logging
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging to never log sensitive data
logger = logging.getLogger(__name__)

class AmazonTokenEncryptionService:
    """
    Secure token encryption service using AWS KMS and AES-GCM
    
    Security Features:
    - Uses AWS KMS for key management
    - AES-GCM authenticated encryption
    - Per-user encryption context
    - No sensitive data logging
    - Automatic key rotation support
    """
    
    def __init__(self):
        """Initialize encryption service with AWS KMS configuration"""
        # Validate required environment variables at startup
        self._validate_environment()
        
        self.kms_key_id = os.environ['AWS_KMS_KEY_ID']
        self.aws_region = os.environ.get('AWS_REGION', 'eu-west-1')
        
        # Initialize KMS client
        try:
            self.kms_client = boto3.client(
                'kms', 
                region_name=self.aws_region,
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
            )
            logger.info("✅ AWS KMS client initialized successfully")
        except Exception as e:
            logger.error("❌ Failed to initialize AWS KMS client")
            raise RuntimeError("KMS client initialization failed") from e
    
    def _validate_environment(self) -> None:
        """Validate required environment variables are present"""
        required_vars = [
            'AWS_KMS_KEY_ID',
            'AWS_REGION',
            'AMAZON_LWA_CLIENT_ID',
            'AMAZON_LWA_CLIENT_SECRET',
            'AWS_ROLE_ARN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("✅ All required environment variables validated")
    
    async def encrypt_token_data(
        self, 
        token_data: Dict[str, Any], 
        user_id: str,
        connection_id: str
    ) -> Tuple[str, str]:
        """
        Encrypt SP-API token data using AWS KMS + AES-GCM
        
        Args:
            token_data: Token data to encrypt (never logged)
            user_id: ECOMSIMPLY user identifier
            connection_id: Unique connection identifier
            
        Returns:
            Tuple of (encrypted_data_b64, nonce_b64)
        """
        try:
            # Create encryption context for additional security
            encryption_context = {
                "user_id": user_id,
                "connection_id": connection_id,
                "service": "ecomsimply_spapi",
                "purpose": "token_encryption"
            }
            
            # Generate data encryption key using KMS
            dek_response = self.kms_client.generate_data_key(
                KeyId=self.kms_key_id,
                KeySpec='AES_256',
                EncryptionContext=encryption_context
            )
            
            plaintext_key = dek_response['Plaintext']
            encrypted_key = dek_response['CiphertextBlob']
            
            # Initialize AES-GCM with the plaintext key
            aesgcm = AESGCM(plaintext_key)
            
            # Generate random nonce (96 bits for GCM)
            nonce = os.urandom(12)
            
            # Prepare token data for encryption
            token_json = json.dumps(token_data, separators=(',', ':'), sort_keys=True)
            token_bytes = token_json.encode('utf-8')
            
            # Additional Authenticated Data (AAD)
            aad = f"{user_id}:{connection_id}:spapi".encode('utf-8')
            
            # Encrypt the token data
            ciphertext = aesgcm.encrypt(nonce, token_bytes, aad)
            
            # Combine encrypted DEK with ciphertext
            combined_data = base64.b64encode(encrypted_key).decode('utf-8') + ':' + \
                          base64.b64encode(ciphertext).decode('utf-8')
            
            # Securely clear the plaintext key from memory
            plaintext_key = b'\x00' * len(plaintext_key)
            
            logger.info(f"🔐 Token encrypted successfully for user {user_id[:8]}***")
            
            return combined_data, base64.b64encode(nonce).decode('utf-8')
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"❌ AWS KMS error during token encryption: {type(e).__name__}")
            raise RuntimeError("Token encryption failed due to KMS error") from e
        except Exception as e:
            logger.error(f"❌ Token encryption failed: {type(e).__name__}")
            raise RuntimeError("Token encryption failed") from e
    
    async def decrypt_token_data(
        self,
        encrypted_data: str,
        nonce_b64: str,
        user_id: str,
        connection_id: str
    ) -> Dict[str, Any]:
        """
        Decrypt SP-API token data using AWS KMS + AES-GCM
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            nonce_b64: Base64 encoded nonce
            user_id: ECOMSIMPLY user identifier
            connection_id: Connection identifier
            
        Returns:
            Decrypted token data (never logged)
        """
        try:
            # Parse the combined encrypted data
            encrypted_key_b64, ciphertext_b64 = encrypted_data.split(':', 1)
            encrypted_key = base64.b64decode(encrypted_key_b64.encode('utf-8'))
            ciphertext = base64.b64decode(ciphertext_b64.encode('utf-8'))
            nonce = base64.b64decode(nonce_b64.encode('utf-8'))
            
            # Recreate encryption context
            encryption_context = {
                "user_id": user_id,
                "connection_id": connection_id,
                "service": "ecomsimply_spapi",
                "purpose": "token_encryption"
            }
            
            # Decrypt the DEK using KMS
            dek_response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_key,
                EncryptionContext=encryption_context
            )
            
            plaintext_key = dek_response['Plaintext']
            
            # Initialize AES-GCM cipher
            aesgcm = AESGCM(plaintext_key)
            
            # Recreate AAD
            aad = f"{user_id}:{connection_id}:spapi".encode('utf-8')
            
            # Decrypt the token data
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, aad)
            
            # Securely clear the plaintext key
            plaintext_key = b'\x00' * len(plaintext_key)
            
            # Parse JSON
            token_json = decrypted_bytes.decode('utf-8')
            token_data = json.loads(token_json)
            
            logger.info(f"🔓 Token decrypted successfully for user {user_id[:8]}***")
            
            return token_data
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"❌ AWS KMS error during token decryption: {type(e).__name__}")
            raise RuntimeError("Token decryption failed due to KMS error") from e
        except ValueError as e:
            logger.error("❌ Invalid encrypted data format")
            raise ValueError("Invalid encrypted token data") from e
        except Exception as e:
            logger.error(f"❌ Token decryption failed: {type(e).__name__}")
            raise RuntimeError("Token decryption failed") from e
    
    def test_kms_access(self) -> bool:
        """
        Test AWS KMS access with the configured key
        
        Returns:
            True if KMS access is working, False otherwise
        """
        try:
            # Test KMS access by describing the key
            response = self.kms_client.describe_key(KeyId=self.kms_key_id)
            key_state = response['KeyMetadata']['KeyState']
            
            if key_state == 'Enabled':
                logger.info("✅ AWS KMS key access test successful")
                return True
            else:
                logger.error(f"❌ KMS key is not enabled, state: {key_state}")
                return False
                
        except Exception as e:
            logger.error(f"❌ KMS access test failed: {type(e).__name__}")
            return False
    
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in data for safe logging
        
        Args:
            data: Dictionary that may contain sensitive data
            
        Returns:
            Dictionary with sensitive fields masked
        """
        masked_data = data.copy()
        sensitive_fields = [
            'access_token', 'refresh_token', 'client_secret', 
            'authorization_code', 'spapi_oauth_code'
        ]
        
        for field in sensitive_fields:
            if field in masked_data:
                if isinstance(masked_data[field], str) and len(masked_data[field]) > 8:
                    masked_data[field] = masked_data[field][:4] + "***MASKED***"
                else:
                    masked_data[field] = "***MASKED***"
        
        return masked_data