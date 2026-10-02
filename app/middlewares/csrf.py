import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.database import SessionLocal
from app.models import Session as SessionModel
from app.auth.cookies import COOKIE_NAME

# Métodos que NO cambian estado → no requieren CSRF
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Rutas exentas (no hay sesión todavía)
EXEMPT_PATHS = {"/auth/login", "/auth/register"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Solo validar métodos que cambian estado
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # 2. Rutas exentas
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # 3. Si viene por JWT (Authorization: Bearer), no aplica CSRF
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        # 4. Si no hay cookie de sesión, no hay nada que proteger
        session_id = request.cookies.get(COOKIE_NAME)
        if not session_id:
            return await call_next(request)

        # 5. Buscar la sesión en la BD y validar CSRF
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                header_token = request.headers.get("X-CSRF-Token")
                if not header_token or not secrets.compare_digest(header_token, session.csrf_token):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token inválido o ausente"},
                    )
        finally:
            db.close()

        return await call_next(request)