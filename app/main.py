from fastapi import FastAPI


from app.database import Base, engine
from app import models  # importa los modelos para que se registren en Base

from app.routes import auth_routes
from app.routes import auth_routes, user_routes, admin_routes

from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.middlewares.csrf import CSRFMiddleware

# Crea las tablas en la BD (si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PassPort Inc. Auth API",
    description="Backend de autenticación y gestión de sesiones.",
    version="0.1.0",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(admin_routes.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}