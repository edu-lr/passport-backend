import secrets
from datetime import datetime, timedelta

from fastapi import Response, Request, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.config import SESSION_EXPIRE_HOURS, SECURE_COOKIE
from app.models import Session, User

COOKIE_NAME = "passport_session"
CSRF_COOKIE_NAME = "csrf_token"


def create_session(db: DBSession, user: User) -> Session:
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    # utcnow() → naive, coherente con cómo SQLite guarda las fechas
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)

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
    # Ambas fechas naive → se pueden restar
    max_age = int((session.expires_at - datetime.utcnow()).total_seconds())

    response.set_cookie(
        key=COOKIE_NAME,
        value=session.id,
        max_age=max_age,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="lax",
        path="/",
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=session.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=SECURE_COOKIE,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


def validate_csrf(request: Request, session: Session) -> None:
    header_token = request.headers.get("X-CSRF-Token")
    if not header_token or not secrets.compare_digest(header_token, session.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token inválido o ausente",
        )