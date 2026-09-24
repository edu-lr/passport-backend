# PassPort Inc. — Backend de Autenticación y Sesiones

Backend de seguridad para la app de gestión de identidad digital PassPort Inc.
Implementa registro, login, sesiones con cookies, autenticación con JWT, RBAC,
y protecciones contra XSS, CSRF, fuerza bruta y cookies inseguras.

## Stack

- Python 3 + FastAPI
- SQLAlchemy + SQLite
- passlib[bcrypt] para hashing de contraseñas
- python-jose para JWT
- itsdangerous para tokens CSRF
- slowapi para rate limiting

## Flujo de autenticación

1. **Registro**
   - El usuario envía email + contraseña.
   - Se valida el email y la fortaleza mínima de la contraseña.
   - La contraseña se hashea con bcrypt y se guarda en la BD.
   - El usuario se crea con rol `Usuario` por defecto.

2. **Login**
   - El usuario envía email + contraseña + `auth_type` (`cookie` o `jwt`).
   - Se verifica la contraseña contra el hash.
   - Se controlan intentos fallidos (bloqueo temporal si se excede).
   - **Si `auth_type = cookie`**: el servidor crea un `session_id`, lo guarda
     en la BD con expiración y lo envía en una cookie con flags
     `HttpOnly`, `Secure` y `SameSite`.
   - **Si `auth_type = jwt`**: el servidor genera un JWT firmado con
     `sub`, `role`, `iat`, `exp` y lo devuelve al cliente.

3. **Uso autenticado**
   - **Cookie**: el navegador envía la cookie automáticamente; el backend
     busca la sesión en la BD y carga el usuario.
   - **JWT**: el cliente envía `Authorization: Bearer <token>`; el backend
     verifica la firma y extrae al usuario.

4. **Logout**
   - **Cookie**: el servidor elimina la sesión de la BD y borra la cookie.
   - **JWT**: el cliente descarta el token; el servidor no mantiene estado.

## Roles (RBAC)

- **Usuario**
  - Acceso a sus propios datos.
  - Rutas estándar de la aplicación.
- **Administrador**
  - Todo lo de Usuario.
  - Eliminar datos de otros usuarios.
  - Ver intentos fallidos de login.

## Seguridad aplicada

- **Hashing**: contraseñas con bcrypt (nunca en texto plano).
- **Cifrado**: datos sensibles dentro de tokens con `cryptography`.
- **XSS**: validación y escapado de entradas + cabeceras de seguridad.
- **CSRF**: token por sesión, validado en métodos que cambian estado
  (POST, PUT, PATCH, DELETE).
- **Fuerza bruta**: bloqueo temporal tras N intentos fallidos.
- **Cookies**: flags `HttpOnly`, `Secure` y `SameSite`.
- **Cabeceras**: `Authorization`, `Set-Cookie`, `Content-Security-Policy`,
  `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`.

## Estructura del proyecto

- `app/main.py` — entrada de FastAPI, montaje de rutas y middlewares.
- `app/config.py` — lectura de variables de entorno.
- `app/database.py` — engine, sesión y base declarativa de SQLAlchemy.
- `app/models/` — tablas: User, Session, LoginAttempt.
- `app/schemas/` — validación de entrada/salida con Pydantic.
- `app/auth/` — hashing, JWT, cookies, dependencias de auth.
- `app/routes/` — endpoints públicos, de usuario y de admin.
- `app/middlewares/` — CSRF y cabeceras de seguridad.