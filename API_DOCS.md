# Documentación de la API — SIGPRO

## Requisitos previos

1. Entorno virtual activado y dependencias instaladas:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Archivo `.env` configurado con las variables requeridas:
   ```
   SECRET_KEY=...
   DATABASE_NAME=...
   DATABASE_USER=...
   DATABASE_PASS=...
   DATABASE_HOST=...
   ```

3. Servidor corriendo:
   ```powershell
   python manage.py runserver
   ```

---

## Acceder a la documentación

Con el servidor en `localhost:8000`, abrir en el navegador:

| Interfaz | URL | Descripción |
|---|---|---|
| Swagger UI | http://localhost:8000/api/docs/ | Interactiva — permite probar endpoints |
| ReDoc | http://localhost:8000/api/redoc/ | Solo lectura — mejor para compartir |
| Schema JSON | http://localhost:8000/api/schema/ | OpenAPI 3.0 en formato descargable |

---

## Autenticar en Swagger UI

1. Abrir `http://localhost:8000/api/docs/`
2. Obtener token en `POST /api/v1/auth/token/` con usuario y contraseña
3. Copiar el valor de `access` del response
4. Hacer clic en **Authorize** (botón arriba a la derecha)
5. Pegar el token con el prefijo `Bearer`:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
6. Confirmar con **Authorize** — todos los endpoints quedan autenticados

---

## Logs

El servidor genera logs automáticamente en:
```
backend/logs/django.log
```
