from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import User, Session as SessionModel
from app.schemas import UserOut
from app.auth.dependencies import require_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(require_user)):
    """Devuelve el perfil del usuario autenticado."""
    return current_user


@router.get("/me/sessions")
def get_my_sessions(
    current_user: User = Depends(require_user),
    db: DBSession = Depends(get_db),
):
    """Lista las sesiones activas (no expiradas) del usuario."""
    now = datetime.utcnow()
    sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == current_user.id,
            SessionModel.expires_at > now,
        )
        .all()
    )
    return [
        {
            "id": s.id,
            "created_at": s.created_at,
            "expires_at": s.expires_at,
        }
        for s in sessions
    ]