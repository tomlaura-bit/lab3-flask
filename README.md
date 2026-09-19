# Laboratorio 3: aplicación Flask

Aplicación de administración con Flask, PostgreSQL, verificación de acceso por correo y operaciones CRUD sobre `usuarios`. La cuenta de acceso se guarda en `admins`, una tabla independiente de los usuarios gestionados. El campo `rol` de `usuarios` es un dato del CRUD.

## Ejecución con Docker

1. Copia `.env.example` a `.env` y cambia `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` y los valores `SMTP_*` según tu proveedor de correo. `ADMIN_EMAIL` debe ser una dirección a la que tengas acceso.
2. Ejecuta `docker compose up --build`.
3. Abre <http://localhost:5000>. Inicia sesión con `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
4. Revisa la bandeja de entrada de `ADMIN_EMAIL` para obtener el código.

El ejemplo usa Gmail mediante SMTP autenticado y STARTTLS. Activa la verificación en dos pasos de tu cuenta de Google y crea una contraseña de aplicación en <https://myaccount.google.com/apppasswords>. Coloca esa contraseña en `SMTP_PASSWORD`; no uses tu contraseña habitual de Gmail. En algunas cuentas de trabajo o con Protección Avanzada, Google no ofrece contraseñas de aplicación. El código caduca a los 10 minutos y permite un máximo de cinco intentos. Si el envío falla, la aplicación muestra un error y no concede acceso.

## Estructura

- `app.py`: rutas, login, verificación por correo y CRUD.
- `schema.sql`: definición de ambas tablas PostgreSQL.
- `templates/` y `static/`: páginas y estilos.
- `Dockerfile` y `docker-compose.yml`: despliegue local.

Al iniciar, la aplicación crea las tablas si faltan y registra el administrador definido en `.env` si aún no existe. `schema.sql` permite revisar o aplicar el esquema de forma independiente. Cambiar las credenciales en `.env` después del primer inicio no modifica la cuenta ya creada.

## Demostración sugerida, máximo cinco minutos

1. Mostrar `docker compose up --build` y los servicios web y PostgreSQL activos.
2. Mostrar un intento fallido de login. Iniciar sesión como administrador, abrir el correo recibido y completar el código.
3. Crear un usuario, mostrarlo en la tabla y editar su nombre o rol.
4. Eliminar al usuario con confirmación y mostrar `README.md`, `schema.sql` y `docker-compose.yml`.

Repositorio público: <https://github.com/tomlaura-bit/lab3-flask>. El archivo `.env` no se publica porque contiene credenciales. El video demostrativo debe grabarse y compartirse mediante un enlace accesible.
