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

El servidor genera logs automáticamente en `backend/logs/`:

| Archivo | Contenido |
|---|---|
| `django.log` | Log general de Django (errores con traceback, `production`, `integration`) |
| `api_requests.log` | Una línea por llamada a `/api/v1/` (middleware `core.request_log.ApiRequestLogMiddleware`) |

Formato de `api_requests.log`:

```
2026-10-19 14:35:46,316 WARNING GET /api/v1/core/menu/ status=401 duration_ms=5.0 user=anonymous ip=127.0.0.1 bytes=104
```

- Campos: método, ruta + query, `status`, `duration_ms`, `user` (`id:username` o `anonymous`), `ip` (respeta `X-Forwarded-For`), `bytes` de la respuesta.
- Nivel según el status: `INFO` (< 400), `WARNING` (4xx), `ERROR` (5xx). Las excepciones no controladas también quedan como `ERROR` con status 500; el traceback completo queda en `django.log`.
- Solo se registran rutas bajo `/api/v1/`. No se registran `/admin/`, `/api/docs/`, `/api/schema/` ni `/api/redoc/`.
- Nunca se registran cuerpos de request/response (login y tokens llevan credenciales).
- Para omitir rutas de alta frecuencia: `API_REQUEST_LOG_EXCLUDED_PATHS` en `config/settings.py` (rutas exactas).
- Rotación: 5 MB, 5 respaldos.

Ver el log en vivo (PowerShell):

```powershell
Get-Content backend\logspi_requests.log -Wait -Tail 50
```
