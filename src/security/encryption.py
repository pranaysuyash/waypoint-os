"""
Encryption utilities for Waypoint OS.
"""

import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# Load or generate ENCRYPTION_KEY
# In production, this MUST be set in environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Use a stable key for development if not provided
    # WARNING: This is NOT for production
    if os.getenv("DATA_PRIVACY_MODE") == "production":
        raise ValueError("ENCRYPTION_KEY must be set in production mode")
    
    # Static key for dogfood/test consistency
    ENCRYPTION_KEY = b'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='
else:
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

_fernet = Fernet(ENCRYPTION_KEY)


def encrypt(data: str) -> str:
    """Encrypt a string and return base64 string."""
    if not data:
        return data
    return _fernet.encrypt(data.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a base64 string."""
    if not token:
        return token
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception as e:
        logger.warning(f"Decryption failed: {e}")
        return token  # Fallback to original if decryption fails (might be plaintext from old data)
