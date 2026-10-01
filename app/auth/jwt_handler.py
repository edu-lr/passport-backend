from datetime import datetime, timedelta, timezone

from jose import  JWTError , jwt

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(user) -> tuple[str, int]:
    """
    Genera un JWT para el usuario.
    Devuelve (token, expires_in_segundos).
    """
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user.id),          # sujeto (id del usuario)
        "email": user.email,
        "role": user.role.value,      # string, no el enum
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict:
    """
    Verifica y decodifica un JWT.
    Lanza JWTError si es inválido o expiró.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])