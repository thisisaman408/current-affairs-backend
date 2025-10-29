"""
Firebase Authentication Integration
Verify ID tokens from mobile app
"""
from firebase_admin import credentials, auth, initialize_app
from src.config import settings
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class FirebaseAuthClient:
    """Firebase Authentication client for token verification"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK using config.py settings"""
        try:
            # Build service account dict from .env variables
            service_account_info = {
                "type": settings.FIREBASE_TYPE or "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if settings.FIREBASE_PRIVATE_KEY else None,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "client_id": settings.FIREBASE_CLIENT_ID,
                "auth_uri": settings.FIREBASE_AUTH_URI or "https://accounts.google.com/o/oauth2/auth",
                "token_uri": settings.FIREBASE_TOKEN_URI or "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_CERT_URL or "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": settings.FIREBASE_CLIENT_CERT_URL,
                "universe_domain": settings.FIREBASE_UNIVERSE_DOMAIN
            }
            
            # Validate required fields
            required_fields = ["project_id", "private_key", "client_email"]
            missing = [f for f in required_fields if not service_account_info.get(f)]
            if missing:
                raise ValueError(f"Missing Firebase config: {', '.join(missing)}")
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_info)
            initialize_app(cred)
            
            logger.info(f"✅ Firebase Admin SDK initialized for project: {settings.FIREBASE_PROJECT_ID}")
            
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            raise
    
    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """
        Verify Firebase ID token from mobile app
        
        Args:
            id_token: JWT token from Firebase Auth (mobile)
        
        Returns:
            Decoded token with user info: {uid, email, name, picture, phone}
            None if verification fails
        """
        try:
            # Verify token with Firebase Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            
            user_info = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "phone": decoded_token.get("phone_number"),
                "email_verified": decoded_token.get("email_verified", False)
            }
            
            logger.info(f"✅ Token verified for user: {user_info['email'] or user_info['uid']}")
            return user_info
            
        except auth.ExpiredIdTokenError:
            logger.error("❌ Expired Firebase ID token")
            return None
        except auth.RevokedIdTokenError:
            logger.error("❌ Revoked Firebase ID token")
            return None
        except auth.InvalidIdTokenError:
            logger.error("❌ Invalid Firebase ID token")
            return None
        except Exception as e:
            logger.error(f"❌ Token verification failed: {e}")
            return None
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Fetch user info from Firebase by UID
        
        Args:
            uid: Firebase user UID
        
        Returns:
            User info dict or None
        """
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "phone_number": user.phone_number,
                "disabled": user.disabled,
                "email_verified": user.email_verified
            }
        except auth.UserNotFoundError:
            logger.error(f"❌ Firebase user not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch user: {e}")
            return None
    
    def verify_token_and_get_user(self, id_token: str) -> Optional[Dict]:
        """
        Convenience method: Verify token and fetch full user info
        
        Args:
            id_token: Firebase ID token
        
        Returns:
            Complete user info or None
        """
        token_data = self.verify_id_token(id_token)
        if not token_data:
            return None
        
        # Fetch full user details from Firebase
        return self.get_user_by_uid(token_data["uid"])

# Global instance (initialized on import)
firebase_auth_client = FirebaseAuthClient()
