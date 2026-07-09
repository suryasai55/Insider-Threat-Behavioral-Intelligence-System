from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from utils.response import api_error

def roles_required(*roles):
    """
    Decorator to restrict route access to specific roles.
    Expects JWT claims to contain the 'role' key.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # Ensure a valid JWT is present
                verify_jwt_in_request()
                
                # Fetch claims from the JWT
                claims = get_jwt()
                user_role = claims.get("role")
                
                # Standardize inputs to prevent case sensitivity mismatches
                normalized_roles = [r.upper() for r in roles]
                
                # If ADMIN is required, support ADMINISTRATOR as an alias
                if "ADMIN" in normalized_roles and "ADMINISTRATOR" not in normalized_roles:
                    normalized_roles.append("ADMINISTRATOR")
                
                if not user_role or user_role.upper() not in normalized_roles:
                    return api_error(
                        message="Access denied. You do not have the required permissions.",
                        status_code=403
                    )
                
                return fn(*args, **kwargs)
            except Exception as e:
                return api_error(
                    message="Authentication credentials invalid or missing.",
                    errors={"detail": str(e)},
                    status_code=401
                )
        return wrapper
    return decorator
