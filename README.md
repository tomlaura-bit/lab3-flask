# Laboratorio 3: aplicación Flask

Aplicación de administración con Flask, PostgreSQL, verificación de acceso por correo y operaciones CRUD sobre `usuarios`. La cuenta de acceso se guarda en `admins`, una tabla independiente de los usuarios gestionados. El campo `rol` de `usuarios` es un dato del CRUD.

## Ejecución con Docker

1. Copiar `.env.example` a `.env` y cambiar `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` y los valores `SMTP_*` de gmail. `ADMIN_EMAIL` debe ser un correo vigente.
2. Ejecutar `docker compose up --build`.
3. Abrir <http://localhost:5000>. Inicia sesión con `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
4. Revisar la bandeja de entrada de `ADMIN_EMAIL` para obtener el código.

El ejemplo usa Gmail mediante SMTP autenticado y STARTTLS. Crear una contraseña de aplicación en <https://myaccount.google.com/apppasswords>. Colocar esa contraseña en `SMTP_PASSWORD`. El código caduca a los 10 minutos y permite un máximo de cinco intentos. Si el envío falla, la aplicación muestra un error y no concede acceso.

## Estructura

- `app.py`: rutas, login, verificación por correo y CRUD.
- `schema.sql`: definición de ambas tablas PostgreSQL.
- `templates/` y `static/`: páginas y estilos.
- `Dockerfile` y `docker-compose.yml`: despliegue local.

Al iniciar, la aplicación crea las tablas si faltan y registra el administrador definido en `.env` si aún no existe. `schema.sql` permite revisar o aplicar el esquema de forma independiente. Cambiar las credenciales en `.env` después del primer inicio no modifica la cuenta ya creada.
