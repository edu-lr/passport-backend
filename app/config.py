import os
from dotenv import load_dotenv

# Carga las variables desde el archivo .env
load_dotenv()

# Seguridad
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
# Secreto base para derivar la clave de cifrado JWE (A256GCM)
JWE_SECRET_KEY = os.getenv("JWE_SECRET_KEY")

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

# Secure para poder mandar coockies por HTTP
ENV = os.getenv("ENV", "dev")
SECURE_COOKIE = ENV != "dev"