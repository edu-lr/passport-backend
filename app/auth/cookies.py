import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Response
from sqlalchemy.orm import Session as DBSession

from app.config import SESSION_EXPIRE_HOURS, SECURE_COOKIE
from app.models import Session, User

COOKIE_NAME = "passport_session"


def create_session(db: DBSession, user: User) -> Session:
    """
    Crea una sesión persistente para el usuario:
    - Genera un session_id aleatorio.
    - Genera un csrf_token aleatorio (se usará en Fase 6).
    - Guarda la sesión en la BD con expiración.
    """
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRE_HOURS)

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


def set_session_cookie(response: Response, session: Session) -> None:
    """
    Setea la cookie de sesión con flags de seguridad.
    Normaliza expires_at a UTC aware porque SQLite lo guarda como naive.
    """
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    response.set_cookie(
        key=COOKIE_NAME,
        value=session.id,
        max_age=max_age,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="lax",
        path="/",
    )

def clear_session_cookie(response: Response) -> None:
    """Borra la cookie de sesión en el cliente."""
    response.delete_cookie(key=COOKIE_NAME, path="/")