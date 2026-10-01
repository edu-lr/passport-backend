from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.config import ENV


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Evita que el navegador adivine el tipo de contenido
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Evita clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # No filtra la URL de origen
        response.headers["Referrer-Policy"] = "no-referrer"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )

        # HSTS solo en producción (requiere HTTPS)
        if ENV != "dev":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response