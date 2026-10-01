from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import User, Session as SessionModel, LoginAttempt
from app.schemas import UserAdminOut
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserAdminOut])
def list_users(
    current_admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Lista todos los usuarios registrados."""
    users = db.query(User).all()
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Elimina un usuario y todas sus sesiones."""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta de administrador",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Borrar sesiones del usuario primero (por FK)
    db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return None


@router.get("/login-attempts")
def list_login_attempts(
    current_admin: User = Depends(require_admin),
    db: DBSession = Depends(get_db),
):
    """Lista los intentos fallidos de login registrados."""
    attempts = db.query(LoginAttempt).all()
    return [
        {
            "id": a.id,
            "email": a.email,
            "ip": a.ip,
            "attempts": a.attempts,
            "locked_until": a.locked_until,
            "updated_at": a.updated_at,
        }
        for a in attempts
    ]