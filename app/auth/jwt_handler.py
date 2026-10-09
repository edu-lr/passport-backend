import base64
import hashlib
import json
import time

from jwcrypto import jwk, jwe

from app.config import JWE_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


# ---------------------------------------------------------------------------
# Clave de cifrado
# ---------------------------------------------------------------------------
def _get_key() -> jwk.JWK:

    # Generar una clave de cifrado de 32 bytes a partir de de la JWE_SECRET_KEY 
    digest = hashlib.sha256(JWE_SECRET_KEY.encode()).digest()   
    
    # Traducir la clave a base64url seguro para url y pasarlo a string
    k = base64.urlsafe_b64encode(digest).decode()  

    # Crear la clave JWK en Secuencia de octetos (contraseña compartida)
    return jwk.JWK(k=k, kty="oct")


# ---------------------------------------------------------------------------
# Emision
# ---------------------------------------------------------------------------
def create_access_token(user) -> tuple[str, int]:

    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = int(time.time())

    # Payload con los datos que tendra el token
    payload = {
        "sub": str(user.id),        # sujeto (id del usuario)
        "email": user.email,
        "role": user.role.value,    # string, no el enum
        "iat": now,                 # emitido en...
        "exp": now + expires_in,    # expira en...
    }

    # Se transforma a JSON y se indican las normas criptograficas
    token = jwe.JWE(
        json.dumps(payload),
        protected={"alg": "dir", "enc": "A256GCM"},
    )
    # se le agrega la "llave" para el cifrado y desifrado
    token.add_recipient(_get_key())

    return token.serialize(compact=True), expires_in


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------
def decode_access_token(token: str) -> dict:

    jwt = jwe.JWE()               # Se instancia el objeto JWE vacio
    jwt.deserialize(token)        # parsea los 5 segmentos; falla si esta malformado
    jwt.decrypt(_get_key())       # descifra; falla si la clave no es o fue alterado
    payload = json.loads(jwt.payload) # se pasa a diccionario PY para poder trabajar

    # Validacion manual de expiracion (jwcrypto no lo hace por nosotros)
    if int(time.time()) >= int(payload.get("exp", 0)):
        raise ValueError("Token expirado")

    return payload
