"""
CORS Middleware Configuration

Defines allowed origins and CORS settings for the API.
"""

# List of allowed origins for CORS
ALLOWED_ORIGINS = [
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    
    # Vercel deployments (pattern matching not directly supported, handle in main)
    # Production URLs should be added here
]

# CORS configuration
CORS_CONFIG = {
    "allow_origins": ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
    "max_age": 600,  # Cache preflight requests for 10 minutes
}


def is_origin_allowed(origin: str) -> bool:
    """
    Check if an origin is allowed.
    
    Supports both exact matches and Vercel subdomain pattern.
    
    Args:
        origin: The origin to check
        
    Returns:
        True if the origin is allowed
    """
    if origin in ALLOWED_ORIGINS:
        return True
    
    # Allow any Vercel subdomain
    if origin.endswith(".vercel.app"):
        return True
    
    return False
