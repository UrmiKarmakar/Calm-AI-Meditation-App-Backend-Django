# common/decorators.py
from functools import wraps
from django.http import JsonResponse
from .jwt_utils import decode_jwt
from accounts.models import CustomUser
import jwt

def _get_auth_header(request):
    """
    Safely extract the Authorization header.
    Django sometimes stores it as HTTP_AUTHORIZATION.
    """
    auth = request.headers.get("Authorization")
    if not auth:
        auth = request.META.get("HTTP_AUTHORIZATION", "")
    return auth

def auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = _get_auth_header(request)

        if not auth or not auth.startswith("Bearer "):
            return JsonResponse({"error": "Unauthorized"}, status=401)

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_jwt(token)

            user_id = payload.get("sub")
            if not user_id:
                return JsonResponse({"error": "Token missing 'sub'"}, status=401)
            
            # Cast back to int when fetching user
            request.user = CustomUser.objects.get(id=int(user_id))

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except jwt.InvalidSignatureError:
            return JsonResponse({"error": "Invalid signature"}, status=401)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            # Debugging: log the actual error
            print("JWT decode error:", str(e))
            return JsonResponse({"error": "Invalid token"}, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, "user") or request.user.role not in roles:
                return JsonResponse({"error": "Forbidden"}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
