from functools import wraps
from django.http import JsonResponse
from common.security_utils import decode_jwt
from accounts.models import CustomUser
import jwt


def _get_auth_header(request):
    """
    Safely extract the Authorization header.
    Django sometimes stores it as HTTP_AUTHORIZATION.
    """
    auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
    return auth.strip()


def auth_required(view_func):
    """
    Decorator to enforce JWT authentication.
    Attaches `request.user` and `request.user_role` if token is valid.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = _get_auth_header(request)

        if not auth or not auth.startswith("Bearer "):
            return JsonResponse(
                {"error": "unauthorized", "detail": "Missing or invalid Authorization header"},
                status=401,
            )

        token = auth.split(" ", 1)[-1].strip()
        try:
            payload = decode_jwt(token)

            user_id = payload.get("sub")
            if not user_id:
                return JsonResponse(
                    {"error": "unauthorized", "detail": "Token missing 'sub'"},
                    status=401,
                )

            # Attach user object and role to request
            request.user = CustomUser.objects.get(id=int(user_id))
            request.user_role = payload.get("role")

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "unauthorized", "detail": "Token expired"}, status=401)
        except jwt.InvalidSignatureError:
            return JsonResponse({"error": "unauthorized", "detail": "Invalid signature"}, status=401)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "unauthorized", "detail": "User not found"}, status=404)
        except Exception as e:
            # Debugging: log the actual error
            print("JWT decode error:", str(e))
            return JsonResponse({"error": "unauthorized", "detail": "Invalid token"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(roles):
    """
    Decorator to enforce role-based access control.
    Example: @role_required(["admin", "superadmin"])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, "user") or request.user.role not in roles:
                return JsonResponse(
                    {"error": "forbidden", "detail": "Insufficient role"},
                    status=403,
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
