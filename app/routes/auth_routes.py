from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DBSession

from datetime import datetime, timezone
from app.models import User, Role, Session as SessionModel

from fastapi import Cookie
from app.auth.cookies import (
    create_session,
    set_session_cookie,
    clear_session_cookie,
    COOKIE_NAME,
)
from app.models import User, Role, Session as SessionModel

from app.database import get_db
from app.models import User, Role
from app.schemas import (
    UserRegister,
    UserOut,
    LoginRequest,
    TokenResponse,
    AuthType,
)
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.cookies import create_session, set_session_cookie

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: DBSession = Depends(get_db)):
    # Verificar si el email ya existe
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # Crear el usuario
    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=Role.USUARIO,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



@router.post("/login", response_model=None)
def login(
    payload: LoginRequest,
    response: Response,
    db: DBSession = Depends(get_db),
):
    # 1. Buscar usuario
    user = db.query(User).filter(User.email == payload.email).first()

    # 2. Verificar existencia y contraseña (mismo mensaje para no filtrar info)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # 3. Verificar que la cuenta esté activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    # 4. Modo cookie
    if payload.auth_type == AuthType.COOKIE:
        session = create_session(db, user)
        set_session_cookie(response, session)
        return UserOut.model_validate(user)

    # 5. Modo JWT
    token, expires_in = create_access_token(user)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DBSession = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    # Si hay cookie, borrar la sesión de la BD
    if session_id:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            db.delete(session)
            db.commit()

    # Borrar la cookie del cliente siempre
    clear_session_cookie(response)
    return None