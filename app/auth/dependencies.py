from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session as DBSession
from jose import JWTError

from app.database import get_db
from app.models import User, Role, Session as SessionModel
from app.auth.cookies import COOKIE_NAME
from app.auth.jwt_handler import decode_access_token


def _get_user_from_session(db: DBSession, session_id: str) -> User:
    """Valida una sesión de cookie y devuelve el usuario."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida",
        )

    # Comparar fechas naive (SQLite guarda sin tz)
    if session.expires_at < datetime.utcnow():
        # Limpieza: borrar la sesión expirada
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada",
        )

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


def _get_user_from_jwt(db: DBSession, token: str) -> User:
    """Valida un JWT y devuelve el usuario."""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


def get_current_user(
    db: DBSession = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None),
) -> User:
    """
    Resuelve la identidad del usuario.
    Prioridad: cookie > JWT.
    Lanza 401 si no hay credenciales válidas.
    """
    user: User | None = None

    # 1. Intentar por cookie
    if session_id:
        user = _get_user_from_session(db, session_id)

    # 2. Si no, intentar por JWT
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        user = _get_user_from_jwt(db, token)

    # 3. Si no hay ninguna credencial
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Verificar cuenta activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    return user


def require_user(current_user: User = Depends(get_current_user)) -> User:
    """Cualquier usuario autenticado y activo."""
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Solo administradores."""
    if current_user.role != Role.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol Administrador",
        )
    return current_user