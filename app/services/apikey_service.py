import secrets
import hashlib
import json
from datetime import datetime
from typing import Optional
from loguru import logger
from app.core.redis_client import redis_client
from app.core.config import settings


# Redis key prefixes
API_KEY_PREFIX = "apikey:"
DEVELOPER_PREFIX = "developer:"


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def register_developer(email: str, name: str) -> dict:
    """
    Register a new developer and generate API key.
    
    Args:
        email: Developer's email (used as unique identifier)
        name: Developer's name
    
    Returns:
        dict with api_key (only shown once!) and developer info
    """
    # Check if developer already exists
    existing = get_developer_by_email(email)
    if existing:
        raise ValueError(f"Developer with email {email} already registered")
    
    # Generate new API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Developer data
    developer_data = {
        "email": email,
        "name": name,
        "api_key_hash": api_key_hash,
        "created_at": datetime.utcnow().isoformat(),
        "last_used_at": None,
        "request_count": 0,
        "is_active": True
    }
    
    # Store in Redis
    # 1. Developer info by email
    redis_client.connection.set(
        f"{DEVELOPER_PREFIX}{email}",
        json.dumps(developer_data)
    )
    
    # 2. API key hash -> email mapping (for fast lookup)
    redis_client.connection.set(
        f"{API_KEY_PREFIX}{api_key_hash}",
        email
    )
    
    logger.info(f"Registered new developer | email={email} name={name}")
    
    return {
        "email": email,
        "name": name,
        "api_key": api_key,  # Only returned once!
        "created_at": developer_data["created_at"],
        "message": "API key generated successfully. Save it securely - it won't be shown again!"
    }


def get_developer_by_email(email: str) -> Optional[dict]:
    """Get developer info by email."""
    data = redis_client.connection.get(f"{DEVELOPER_PREFIX}{email}")
    if data:
        return json.loads(data)
    return None


def get_developer_by_api_key(api_key: str) -> Optional[dict]:
    """Get developer info by API key."""
    api_key_hash = hash_api_key(api_key)
    
    # Get email from API key hash
    email = redis_client.connection.get(f"{API_KEY_PREFIX}{api_key_hash}")
    if not email:
        return None
    
    # Decode if bytes
    if isinstance(email, bytes):
        email = email.decode('utf-8')
    
    return get_developer_by_email(email)


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key and update usage stats.
    
    Returns:
        True if valid and active, False otherwise
    """
    developer = get_developer_by_api_key(api_key)
    
    if not developer:
        return False
    
    if not developer.get("is_active", False):
        return False
    
    # Update usage stats
    developer["last_used_at"] = datetime.utcnow().isoformat()
    developer["request_count"] = developer.get("request_count", 0) + 1
    
    redis_client.connection.set(
        f"{DEVELOPER_PREFIX}{developer['email']}",
        json.dumps(developer)
    )
    
    return True


def regenerate_api_key(email: str) -> dict:
    """
    Regenerate API key for existing developer.
    
    Args:
        email: Developer's email
    
    Returns:
        dict with new api_key
    """
    developer = get_developer_by_email(email)
    if not developer:
        raise ValueError(f"Developer with email {email} not found")
    
    # Remove old API key mapping
    old_hash = developer["api_key_hash"]
    redis_client.connection.delete(f"{API_KEY_PREFIX}{old_hash}")
    
    # Generate new API key
    new_api_key = generate_api_key()
    new_hash = hash_api_key(new_api_key)
    
    # Update developer data
    developer["api_key_hash"] = new_hash
    developer["regenerated_at"] = datetime.utcnow().isoformat()
    
    # Save updates
    redis_client.connection.set(
        f"{DEVELOPER_PREFIX}{email}",
        json.dumps(developer)
    )
    
    # Create new API key mapping
    redis_client.connection.set(
        f"{API_KEY_PREFIX}{new_hash}",
        email
    )
    
    logger.info(f"Regenerated API key | email={email}")
    
    return {
        "email": email,
        "api_key": new_api_key,
        "regenerated_at": developer["regenerated_at"],
        "message": "New API key generated. Old key is now invalid."
    }


def revoke_api_key(email: str) -> dict:
    """
    Revoke/deactivate developer's API key.
    
    Args:
        email: Developer's email
    
    Returns:
        dict with status
    """
    developer = get_developer_by_email(email)
    if not developer:
        raise ValueError(f"Developer with email {email} not found")
    
    # Deactivate
    developer["is_active"] = False
    developer["revoked_at"] = datetime.utcnow().isoformat()
    
    redis_client.connection.set(
        f"{DEVELOPER_PREFIX}{email}",
        json.dumps(developer)
    )
    
    logger.info(f"Revoked API key | email={email}")
    
    return {
        "email": email,
        "is_active": False,
        "revoked_at": developer["revoked_at"],
        "message": "API key has been revoked."
    }


def get_developer_stats(email: str) -> Optional[dict]:
    """Get developer's usage statistics."""
    developer = get_developer_by_email(email)
    if not developer:
        return None
    
    # Don't expose the hash
    return {
        "email": developer["email"],
        "name": developer["name"],
        "created_at": developer["created_at"],
        "last_used_at": developer.get("last_used_at"),
        "request_count": developer.get("request_count", 0),
        "is_active": developer.get("is_active", True)
    }
