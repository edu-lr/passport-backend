import os
from dotenv import load_dotenv

# Carga las variables desde el archivo .env
load_dotenv()

# Seguridad
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./passport.db")

# Tiempos de expiración
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", 24))

# Control de fuerza bruta
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", 15))

# Algoritmos
JWT_ALGORITHM = "HS256"
BCRYPT_ROUNDS = 12