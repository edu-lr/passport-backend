import secrets
from datetime import datetime, timedelta

from fastapi import Response
from sqlalchemy.orm import Session as DBSession

from app.config import SESSION_EXPIRE_HOURS, SECURE_COOKIE
from app.models import Session, User

COOKIE_NAME = "Cookie"
CSRF_COOKIE_NAME = "csrf_token"


def create_session(db: DBSession, user: User) -> Session:
    # Genera un ID de sesión y un token CSRF aleatorios y seguros
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    # utcnow() → naive (para comparar fechas luego)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)

    # Crea la sesión en la base de datos
    session = Session(
        id=session_id,
        user_id=user.id,
        csrf_token=csrf_token,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# Establece las cookies de sesión en la respuesta
def set_session_cookie(response: Response, session: Session) -> None:
    # Ambas fechas naive → se pueden restar               # total_seconds() → int
    max_age = int((session.expires_at - datetime.utcnow()).total_seconds())

    # Identificador de session
    # httponly=True → no permite acceso desde JavaScript
    response.set_cookie(
        key=COOKIE_NAME,
        value=session.id,
        max_age=max_age,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="lax",
        path="/",
    )
    # Token CSRF
    # httponly=False → permite acceso desde JavaScript
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=session.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=SECURE_COOKIE,
        samesite="lax",
        path="/",
    )

# Borrar cookies de sesión y CSRF token
def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")
