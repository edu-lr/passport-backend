from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.config import MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES
from app.models import LoginAttempt

# obtemer cantidad de intentos de login para un email e ip
def _get_attempt(db: DBSession, email: str, ip: str) -> LoginAttempt | None:
    return (
        db.query(LoginAttempt)
        .filter(LoginAttempt.email == email, LoginAttempt.ip == ip)
        .first()
    )

# Se valida la cantidad de intentos de login para un email
def check_lockout(db: DBSession, email: str, ip: str) -> None:
    """Lanza 429 si el par email+ip está bloqueado."""
    attempt = _get_attempt(db, email, ip)
    if not attempt or not attempt.locked_until:
        return
    # Si el bloqueo aún no ha expirado
    if attempt.locked_until > datetime.utcnow():
        tiempo_restante = int((attempt.locked_until - datetime.utcnow()).total_seconds())

        # Se lanza error 429
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intenta de nuevo en {tiempo_restante} segundos.",
            headers={"Retry-After": str(tiempo_restante)},
        )
    # Si el bloqueo ya expiró, limpiamos la fila
    db.delete(attempt)
    db.commit()


def register_failed_attempt(db: DBSession, email: str, ip: str) -> None:
    """Suma un intento fallido y bloquea si se excede el máximo."""
    attempt = _get_attempt(db, email, ip)

    if not attempt:
        attempt = LoginAttempt(
            email=email,
            ip=ip,
            attempts=1,
            locked_until=None,
        )
        db.add(attempt)
    else:
        attempt.attempts += 1
        if attempt.attempts >= MAX_LOGIN_ATTEMPTS:
            attempt.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)

    db.commit()


def reset_attempts(db: DBSession, email: str, ip: str) -> None:
    """Elimina el registro de intentos tras un login exitoso."""
    attempt = _get_attempt(db, email, ip)
    if attempt:
        db.delete(attempt)
        db.commit()