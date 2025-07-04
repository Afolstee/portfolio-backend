import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

logger = logging.getLogger(__name__)

class FirebaseConfig:
    """Secure Firebase configuration handler"""
    
    def __init__(self):
        self.db: Optional[firestore.Client] = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize Firebase with multiple fallback methods"""
        if self.is_initialized:
            logger.info("Firebase already initialized")
            return True
        
        try:
            # Check if already initialized
            firebase_admin.get_app()
            logger.info("Firebase app already exists")
            self.is_initialized = True
            self.db = firestore.client()
            return True
        except ValueError:
            pass
        
        # Try different initialization methods
        methods = [
            self._init_from_env_json,
            self._init_from_env_file,
            self._init_from_local_file,
            self._init_with_default_credentials
        ]
        
        for method in methods:
            try:
                if method():
                    self.is_initialized = True
                    self.db = firestore.client()
                    logger.info(f"Firebase initialized successfully with {method.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to initialize with {method.__name__}: {e}")
                continue
        
        logger.error("All Firebase initialization methods failed")
        return False
    
    def _init_from_env_json(self) -> bool:
        """Initialize from JSON string in environment variable"""
        firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not firebase_key:
            return False
        
        try:
            firebase_config = json.loads(firebase_key)
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            logger.info("Initialized from environment JSON")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_KEY: {e}")
            return False
    
    def _init_from_env_file(self) -> bool:
        """Initialize from file path in environment variable"""
        firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if not firebase_key_path:
            return False
        
        if not os.path.exists(firebase_key_path):
            logger.error(f"Firebase service account file not found: {firebase_key_path}")
            return False
        
        try:
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
            logger.info(f"Initialized from file: {firebase_key_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize from file {firebase_key_path}: {e}")
            return False
    
    def _init_from_local_file(self) -> bool:
        """Initialize from local service account file (development only)"""
        # Only try this in development mode
        if os.getenv("ENVIRONMENT", "development") != "development":
            return False
        
        possible_files = [
            "firebase-service-account.json",
            "serviceAccountKey.json",
            "service-account.json"
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                try:
                    cred = credentials.Certificate(file_path)
                    firebase_admin.initialize_app(cred)
                    logger.info(f"Initialized from local file: {file_path}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to initialize from {file_path}: {e}")
                    continue
        
        return False
    
    def _init_with_default_credentials(self) -> bool:
        """Initialize with default credentials (Google Cloud environment)"""
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("Initialized with default credentials")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize with default credentials: {e}")
            return False
    
    def get_db(self) -> Optional[firestore.Client]:
        """Get Firestore database client"""
        if not self.is_initialized:
            if not self.initialize():
                return None
        return self.db
    
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        return self.is_initialized and self.db is not None

# Global instance
firebase_config = FirebaseConfig()

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase - call this once at app startup"""
    return firebase_config.initialize()

# Get database instance
def get_firestore_db():
    """Get Firestore database instance"""
    return firebase_config.get_db()

# Check if Firebase is available
def is_firebase_available():
    """Check if Firebase is properly initialized"""
    return firebase_config.is_available()