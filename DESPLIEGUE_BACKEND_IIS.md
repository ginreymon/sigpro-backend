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
| `STATIC_ROOT not set` | Falta en settings.py | Agregar `STATIC_ROOT = BASE_DIR / 'staticfiles'` |
| `ALLOWED_HOSTS error` | IP no en .env | Agregar IP a `ALLOWED_HOSTS` en `.env` |
| `venv bloqueado al borrar` | IIS usa el proceso | Detener app pool → borrar → recrear |
| `pip instala en system Python` | venv roto | Borrar venv con `iisreset /stop` + `rmdir /s /q venv` y recrear |
