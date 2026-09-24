from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# Motor de conexión a la base de datos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite
)

# Fábrica de sesiones de BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI que entrega una sesión de BD
    y la cierra al terminar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()