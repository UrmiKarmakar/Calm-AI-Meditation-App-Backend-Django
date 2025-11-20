# common/jwt_utils.py
import jwt
import datetime
from django.conf import settings
from django.utils import timezone

def issue_jwt(user):
    exp = timezone.now() + datetime.timedelta(minutes=settings.JWT_EXP_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": exp,
        "iat": timezone.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGO)

def decode_jwt(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
