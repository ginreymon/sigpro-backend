# Despliegue Django Backend en IIS — SGIPRO

**Stack:** Django 5.2 · Python 3.12 · SQL Server · wfastcgi  
**Ruta servidor:** `C:\inetpub\wwwroot\SIGPRO\backend`  
**Puerto IIS:** `8100`

---

## Prerrequisitos

- Windows Server con IIS instalado
- Python 3.12 instalado en `C:\Program Files\Python312\`
- ODBC Driver 17 for SQL Server instalado
- CMD abierto como **Administrador**

---

## 1. Activar CGI en IIS

```cmd
dism /online /enable-feature /featureName:IIS-CGI /all
```

---

## 2. Copiar proyecto al servidor

Estructura esperada en el servidor:

```
C:\inetpub\wwwroot\SIGPRO\backend\
  apps\
  config\
  core\
  staticfiles\
  venv\
  .env
  manage.py
  requirements.txt
  web.config
```

---

## 3. Crear venv e instalar dependencias

```cmd
"C:\Program Files\Python312\python.exe" -m venv C:\inetpub\wwwroot\SIGPRO\backend\venv

C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\pip.exe install -r C:\inetpub\wwwroot\SIGPRO\backend\requirements.txt

C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\pip.exe install wfastcgi
```

Verificar que wfastcgi quedó en el venv:

```cmd
dir C:\inetpub\wwwroot\SIGPRO\backend\venv\Lib\site-packages\wfastcgi.py
```

---

## 4. Configurar .env

Crear `C:\inetpub\wwwroot\SIGPRO\backend\.env`:

```env
APP_DEBUG=False
SECRET_KEY=tu_secret_key_aqui

DATABASE_NAME=SIGPRO_TEST
DATABASE_USER=usuario_db
DATABASE_PASS=contraseña_db
DATABASE_HOST=ip_servidor_sql

ALLOWED_HOSTS=localhost,127.0.0.1,ip_del_servidor
```

---

## 5. Collectstatic

```cmd
C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\python.exe C:\inetpub\wwwroot\SIGPRO\backend\manage.py collectstatic --noinput
```

---

## 6. Registrar FastCGI en IIS

```cmd
%windir%\system32\inetsrv\appcmd.exe set config /section:system.webServer/fastCGI "/+[fullPath='C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\python.exe',arguments='C:\inetpub\wwwroot\SIGPRO\backend\venv\Lib\site-packages\wfastcgi.py',signalBeforeTerminateSeconds='30']"
```

---

## 7. Crear web.config

Crear `C:\inetpub\wwwroot\SIGPRO\backend\web.config` con este contenido:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <modules>
      <remove name="WebDAVModule" />
    </modules>
    <handlers>
      <remove name="WebDAV" />
      <add name="Python FastCGI"
           path="*"
           verb="GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"
           modules="FastCgiModule"
           scriptProcessor="C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\python.exe|C:\inetpub\wwwroot\SIGPRO\backend\venv\Lib\site-packages\wfastcgi.py"
           resourceType="Unspecified"
           requireAccess="Script" />
    </handlers>
    <staticContent>
      <mimeMap fileExtension="." mimeType="text/plain" />
    </staticContent>
    <security>
      <requestFiltering>
        <verbs allowUnlisted="true">
          <add verb="GET" allowed="true" />
          <add verb="POST" allowed="true" />
          <add verb="PUT" allowed="true" />
          <add verb="PATCH" allowed="true" />
          <add verb="DELETE" allowed="true" />
          <add verb="HEAD" allowed="true" />
          <add verb="OPTIONS" allowed="true" />
        </verbs>
      </requestFiltering>
    </security>
  </system.webServer>
  <appSettings>
    <add key="WSGI_HANDLER" value="config.wsgi.application" />
    <add key="PYTHONPATH" value="C:\inetpub\wwwroot\SIGPRO\backend;C:\inetpub\wwwroot\SIGPRO\backend\venv\Lib\site-packages" />
    <add key="DJANGO_SETTINGS_MODULE" value="config.settings" />
  </appSettings>
</configuration>
```

---

## 8. Configurar IIS Manager

### 8.1 Application Pool

IIS Manager → **Application Pools** → clic derecho → **Add Application Pool**

| Campo | Valor |
|-------|-------|
| Name | `SGIPRO-Backend` |
| .NET CLR version | **No Managed Code** |
| Managed pipeline | Integrated |

### 8.2 Sitio

IIS Manager → **Sites** → clic derecho → **Add Website**

| Campo | Valor |
|-------|-------|
| Site name | `SGIPRO-Backend` |
| Application pool | `SGIPRO-Backend` |
| Physical path | `C:\inetpub\wwwroot\SIGPRO\backend` |
| Port | `8100` |
| Host name | (dejar vacío) |

---

## 9. Permisos

```cmd
icacls "C:\inetpub\wwwroot\SIGPRO\backend" /grant "IIS AppPool\SGIPRO-Backend:(OI)(CI)RX" /T
```

El app pool también necesita **escritura** en `logs\` (`django.log` y `api_requests.log`). La carpeta no viene en el repo (está en `.gitignore`): crearla y dar permiso:

```cmd
mkdir C:\inetpub\wwwroot\SIGPRO\backend\logs
icacls "C:\inetpub\wwwroot\SIGPRO\backend\logs" /grant "IIS AppPool\SGIPRO-Backend:(OI)(CI)M" /T
```

---

## 10. Iniciar / Reiniciar app pool

```cmd
%windir%\system32\inetsrv\appcmd stop apppool /apppool.name:"SGIPRO-Backend"
%windir%\system32\inetsrv\appcmd start apppool /apppool.name:"SGIPRO-Backend"
```

---

## 11. Verificar

Navegar a:
```
http://localhost:8100/api/v1/
```

Respuesta esperada: `401 Unauthorized` — Django responde correctamente.

---

## Actualizar despliegue (cambios futuros)

```cmd
:: 1. Copiar archivos actualizados al servidor

:: 2. Si hay nuevos paquetes
C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\pip.exe install -r C:\inetpub\wwwroot\SIGPRO\backend\requirements.txt

:: 3. Si hay migraciones
C:\inetpub\wwwroot\SIGPRO\backend\venv\Scripts\python.exe C:\inetpub\wwwroot\SIGPRO\backend\manage.py migrate

:: 4. Reiniciar app pool
%windir%\system32\inetsrv\appcmd stop apppool /apppool.name:"SGIPRO-Backend"
%windir%\system32\inetsrv\appcmd start apppool /apppool.name:"SGIPRO-Backend"
```

---

## Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| `500 - scriptProcessor no encontrado` | FastCGI no registrado o ruta incorrecta | Paso 6 — verificar ruta exacta del venv |
| `500 - acceso denegado` | Permisos NTFS incorrectos | Paso 9 — correr icacls |
| `500` al arrancar / no se crea `api_requests.log` | App pool sin escritura en `logs\` | Paso 9 — icacls con `M` sobre `logs` |
| `STATIC_ROOT not set` | Falta en settings.py | Agregar `STATIC_ROOT = BASE_DIR / 'staticfiles'` |
| `ALLOWED_HOSTS error` | IP no en .env | Agregar IP a `ALLOWED_HOSTS` en `.env` |
| `venv bloqueado al borrar` | IIS usa el proceso | Detener app pool → borrar → recrear |
| `pip instala en system Python` | venv roto | Borrar venv con `iisreset /stop` + `rmdir /s /q venv` y recrear |

---

---

# Despliegue Angular Frontend en IIS — SGIPRO

**Stack:** Angular 21 · IIS URL Rewrite Module  
**Ruta servidor:** `C:\inetpub\wwwroot\SIGPRO\frontend`  
**Puerto IIS:** `80`

---

## Prerrequisitos

- IIS instalado con módulo **URL Rewrite** ([descarga](https://www.iis.net/downloads/microsoft/url-rewrite))
- Build de Angular generado (`npm run build`) — archivos en `dist/`
- CMD abierto como **Administrador**

Verificar que URL Rewrite está instalado:

```cmd
%windir%\system32\inetsrv\appcmd list module /name:RewriteModule
```

Respuesta esperada: `MODULE "RewriteModule" ...`

---

## 1. Copiar build al servidor

Estructura esperada en el servidor:

```
C:\inetpub\wwwroot\SIGPRO\frontend\
  index.html
  main-XXXXXXXX.js
  styles-XXXXXXXX.css
  favicon.ico
  web.config
```

---

## 2. Crear web.config

Crear `C:\inetpub\wwwroot\SIGPRO\frontend\web.config` con este contenido:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Angular SPA" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
    <httpErrors errorMode="Custom" existingResponse="PassThrough" />
  </system.webServer>
</configuration>
```

La regla redirige toda ruta desconocida a `index.html` — necesario para que Angular Router funcione al refrescar o navegar directamente por URL.

---

## 3. Configurar IIS Manager

### 3.1 Application Pool

IIS Manager → **Application Pools** → clic derecho → **Add Application Pool**

| Campo | Valor |
|-------|-------|
| Name | `SGIPRO-Frontend` |
| .NET CLR version | **No Managed Code** |
| Managed pipeline | Integrated |

### 3.2 Sitio

IIS Manager → **Sites** → clic derecho → **Add Website**

| Campo | Valor |
|-------|-------|
| Site name | `SGIPRO-Frontend` |
| Application pool | `SGIPRO-Frontend` |
| Physical path | `C:\inetpub\wwwroot\SIGPRO\frontend` |
| Port | `80` |
| Host name | (dejar vacío o dominio si aplica) |

---

## 4. Permisos

```cmd
icacls "C:\inetpub\wwwroot\SIGPRO\frontend" /grant "IIS AppPool\SGIPRO-Frontend:(OI)(CI)R" /T
```

---

## 5. Verificar

Navegar a:
```
http://localhost/
```

- Carga la app Angular correctamente
- Refrescar en cualquier ruta (`/produccion`, `/login`) → no devuelve 404

---

## Actualizar despliegue (cambios futuros)

```cmd
:: 1. Generar nuevo build en máquina de desarrollo
::    npm run build  (desde frontend/)

:: 2. Copiar contenido de dist/ a servidor (reemplazar archivos)
::    Los nombres de .js y .css cambian por hash en cada build

:: 3. No es necesario reiniciar IIS — archivos estáticos
```

---

## Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| `404` al refrescar ruta Angular | URL Rewrite no instalado o web.config ausente | Instalar módulo + verificar web.config en Paso 2 |
| `500.19` al iniciar sitio | web.config con error de sintaxis o módulo faltante | Validar XML + verificar URL Rewrite instalado |
| Pantalla en blanco, errores en consola | Rutas de assets rotas (base href incorrecto) | Verificar `base href="/"` en `index.html` |
| `RewriteModule` no encontrado | URL Rewrite no instalado | Descargar e instalar desde iis.net |
