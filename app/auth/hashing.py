from passlib.context import CryptContext

from app.config import BCRYPT_ROUNDS

# Contexto de hashing con bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_ROUNDS,
)

# Se deve usar la version bcrypt==4.0.1 (desactualizada) hay que mejorar eso a futuro 
def hash_password(password: str) -> str:
    """Recibe una contraseña en texto plano y devuelve su hash bcrypt."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra un hash bcrypt."""
    return pwd_context.verify(password, password_hash)