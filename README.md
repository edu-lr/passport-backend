# PassPort Inc. — Auth Backend

Backend de autenticación y gestión de sesiones para **PassPort Inc.** (challenge técnico).

**Stack:** Python 3 · FastAPI · SQLAlchemy · SQLite · bcrypt · JWT → JWE (jwcrypto)

## Quick start

```powershell
# Activar entorno virtual e instalar dependencias
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Levantar la API
uvicorn app.main:app --reload
```

Documentación interactiva: `http://127.0.0.1:8000/docs`

### Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `JWT_SECRET_KEY` | Clave de firma JWT (HS256) |
| `DATABASE_URL` | Conexión a la BD (`sqlite:///./passport.db`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración del token (30) |
| `SESSION_EXPIRE_HOURS` | Duración de la sesión por cookie (24) |
| `MAX_LOGIN_ATTEMPTS` | Intentos fallidos antes del bloqueo (5) |
| `LOCKOUT_MINUTES` | Minutos de bloqueo (15) |
| `ENV` | `dev` / `prod` (controla cookie `Secure` y HSTS) |

## Endpoints

| Método | Ruta | Auth | Rol |
|---|---|---|---|
| POST | `/auth/register` | No | — |
| POST | `/auth/login` | No | — (`auth_type`: `cookie` o `jwt`) |
| POST | `/auth/logout` | Cookie + CSRF | Cualquiera |
| GET | `/users/me` | Cookie o JWT | Usuario |
| GET | `/users/me/sessions` | Cookie o JWT | Usuario |
| GET | `/admin/users` | Cookie o JWT | Administrador |
| DELETE | `/admin/users/{id}` | Cookie o JWT | Administrador |
| GET | `/admin/login-attempts` | Cookie o JWT | Administrador |
| GET | `/health` | No | — |

## Cumplimiento de los objetivos obligatorios

| # | Requerimiento | Dónde se cumple |
|---|---|---|
| 1 | **Registro con email + contraseña** | `POST /auth/register` (`routes/auth_routes.py`). `email` validado con `EmailStr`; `password` con mínimo 8 caracteres y rechazo de `<`/`>` (`schemas/user.py`). |
| 2 | **Hash de contraseñas con bcrypt** | `auth/hashing.py` — bcrypt con **12 rounds** vía passlib. La contraseña nunca se guarda en texto plano ni se escapa (el hash se calcula sobre el valor exacto). |
| 3 | **Sesiones con cookies (crear, mantener, eliminar)** | `auth/cookies.py`. Al loguearse con `auth_type=cookie` se crea la sesión en la BD y la cookie `passport_session` guarda **solo un identificador aleatorio** (`secrets.token_urlsafe(32)`), ningún dato del usuario. Se mantiene validando `expires_at` en cada request y se elimina en `/auth/logout` (BD + cookies). |
| 4 | **Autenticación con tokens JWT** | `auth/jwt_handler.py` con `auth_type=jwt`: devuelve `access_token` (expira en 30 min) que se envía como `Authorization: Bearer`. |
| 5 | **RBAC: roles Usuario y Administrador** | Enum `Role` en `models/user.py` (todo registro nace como `usuario`). Dependencias `require_user` / `require_admin` en `auth/dependencies.py`. El router `/admin/*` completo exige rol Administrador (403 en caso contrario). |
| 6 | **Cifrado de datos sensibles en tokens** | Migración JWT → **JWE** (`alg=dir`, `enc=A256GCM`, jwcrypto): el payload (`sub`, `email`, `role`, `iat`, `exp`) viaja **cifrado**, no solo firmado. No es legible en jwt.io. |
| 7 | **Protección XSS (filtrado/escapado)** | Rechazo de `<`/`>` en contraseñas (`schemas/user.py`), `EmailStr` valida formato estricto, salida siempre en JSON y header `Content-Security-Policy` que bloquea scripts inline. `_sanitize` queda como utilidad para futuros campos de texto. |
| 8 | **Protección CSRF (tokens únicos por sesión)** | **Double Submit Cookie**: cookie `csrf_token` (legible por JS) que el cliente reenvía como header `X-CSRF-Token`. `middlewares/csrf.py` lo compara con `secrets.compare_digest` contra el token guardado en la sesión (403 si no coincide). No aplica a métodos safe ni a auth por Bearer. |
| 9 | **Bloqueo por fuerza bruta** | `auth/brute_force.py` + tabla `login_attempts`: 5 intentos fallidos por par **email+IP** → bloqueo de 15 min con respuesta **429** y header `Retry-After`. Un login exitoso resetea el contador. Auditoría en `GET /admin/login-attempts`. |
| 10 | **Cookies HttpOnly y Secure** | `set_session_cookie()` (`auth/cookies.py`): `passport_session` con `HttpOnly` (invisible para JS, anti-robo por XSS), `Secure` activo cuando `ENV=prod` (solo viaja por HTTPS) y `SameSite=lax` como capa extra anti-CSRF. |

## Flujos de autenticación

### Modo Cookie (sesión server-side)
1. `POST /auth/login` con `auth_type=cookie` → se crea la sesión en la BD y se devuelven 2 cookies: `passport_session` (HttpOnly) y `csrf_token` (legible por JS).
2. Requests siguientes: el navegador envía la cookie automáticamente + el frontend copia `csrf_token` al header `X-CSRF-Token` en métodos que mutan estado.
3. `POST /auth/logout` → se borra la sesión de la BD y ambas cookies.

### Modo JWT/JWE (stateless)
1. `POST /auth/login` con `auth_type=jwt` → devuelve `{access_token, token_type, expires_in}`.
2. Requests siguientes: header `Authorization: Bearer <token>` (exento de CSRF, no usa cookies).
3. El token expira solo (30 min); no requiere logout en el servidor.

## Estructura del proyecto

```
app/
├── main.py                 # App FastAPI: registra middlewares y routers
├── config.py               # Variables de entorno (.env)
├── database.py             # Engine SQLAlchemy, SessionLocal, get_db
├── models/                 # Tablas: User, Session, LoginAttempt
├── schemas/                # Validación de entrada/salida (Pydantic)
├── auth/                   # Seguridad: hashing, jwt_handler, cookies,
│                           #   dependencies (RBAC), brute_force
├── routes/                 # Endpoints: auth, users, admin
└── middlewares/            # CSRFMiddleware, SecurityHeadersMiddleware
scripts/                    # Utilidades (create_admin.py)
```
