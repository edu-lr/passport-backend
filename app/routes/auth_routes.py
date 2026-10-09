from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import User, Role, Session as SessionModel
from app.schemas import (
    UserRegister,
    UserOut,
    LoginRequest,
    TokenResponse,
    AuthType,
)
from app.auth.brute_force import (
    check_lockout,
    register_failed_attempt,
    reset_attempts,
)
from app.auth.cookies import (
    create_session,
    set_session_cookie,
    clear_session_cookie,
    COOKIE_NAME,
)
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: DBSession = Depends(get_db)):
    
    # Verificar si el email ya existe
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(   # lanzar error si sí
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # Crear el usuario si no
    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=Role.USUARIO,
        is_active=True,
    )

    # anñadir a la db y devolver el nuevo usuario
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



@router.post("/login", response_model=None)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DBSession = Depends(get_db),
):
    # IP del cliente
    ip = request.client.host if request.client else "unknown"

    # 1. Verificar bloqueo antes de nada
    check_lockout(db, payload.email, ip)

    # 2. Buscar usuario
    user = db.query(User).filter(User.email == payload.email).first()

    # 3. Verificar credenciales
    if not user or not verify_password(payload.password, user.password_hash):
        register_failed_attempt(db, payload.email, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # 4. Cuenta activa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    # 5. Login exitoso → limpiar intentos
    reset_attempts(db, payload.email, ip)

    # 6. Modo cookie
    if payload.auth_type == AuthType.COOKIE:
        session = create_session(db, user)
        set_session_cookie(response, session)
        return UserOut.model_validate(user)

    # 7. Modo JWT
    token, expires_in = create_access_token(user)
    return TokenResponse(access_token=token, expires_in=expires_in)


# Borrar session en caso de cookie
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