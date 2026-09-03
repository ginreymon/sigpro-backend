# Configuración de Tareas Programadas — SIESA / SIGPRO


## 1. Ejecución perpetua sin depender de credenciales de dominio (`\SIGPRO\`)

**Problema:** la tarea `SIGPRO Eliminar sessiones caducadas` (carpeta `\SIGPRO\`) dependía de una cuenta/contraseña de dominio para su ejecución (`Run whether user is logged on or not`), lo que la exponía a fallar si la contraseña de dominio vence o cambia por política corporativa.

**Solución aplicada:** crear una cuenta **local** (no de dominio) dedicada, con contraseña que no expira, y asignarla como cuenta de ejecución de la tarea.

### 1.1 Crear el usuario local

```powershell
New-LocalUser -Name "SIGPRO_USER" -Password (ConvertTo-SecureString "Siesa#2026Prod!" -AsPlainText -Force) -PasswordNeverExpires -UserMayNotChangePassword
```
**Qué hace:**
- Crea la cuenta local `SIGPRO_USER` (no depende del controlador de dominio).
- `-PasswordNeverExpires`: la contraseña no vence por política de expiración.
- `-UserMayNotChangePassword`: evita que alguien la cambie manualmente por error.

**Credenciales resultantes:**

| Campo | Valor |
|---|---|
| Usuario | `SIGPRO_USER` |
| Contraseña | `Siesa#2026Prod!` |
| Tipo de cuenta | Local (no de dominio) |
| Expira | Nunca |

### 1.2 Asignar la cuenta a la tarea

```powershell
$taskName = "SIGPRO Eliminar sessiones caducadas"
$taskPath = "\SIGPRO\"
$user     = "SIGPRO_USER"
$pass     = "Siesa#2026Prod!"

Set-ScheduledTask -TaskName $taskName -TaskPath $taskPath -User $user -Password $pass
```
**Qué hace:** cambia el "principal" (contexto de seguridad) de la tarea para que se ejecute como `SIGPRO_USER` en vez de la cuenta de dominio anterior. Al pasar la contraseña, Task Scheduler también otorga automáticamente a esa cuenta el permiso **"Iniciar sesión como trabajo por lotes" (Log on as a batch job)**, necesario para que una tarea programada pueda correr con esa identidad.

> Si este paso llegara a fallar con "Acceso denegado" (no fue el caso aquí), el permiso se puede otorgar manualmente vía `secedit` — ver comando de referencia en la sección 6.

### 1.3 Verificar que la cuenta quedó bien asignada

```powershell
$t = Get-ScheduledTask -TaskName $taskName -TaskPath $taskPath
$t.Principal
```
**Qué hace:** muestra el contexto de seguridad configurado en la tarea.

**Resultado confirmado:**
```
LogonType : Password
RunLevel  : Highest
UserId    : SIGPRO_USER
```
✅ La tarea ya no depende de ninguna cuenta ni contraseña de dominio.

### 4.4 Verificar que la tarea es perpetua (sin fecha de vencimiento)

```powershell
$t.Triggers | Select StartBoundary, EndBoundary, Enabled, Repetition
```
**Qué hace:** lista los disparadores (triggers) de la tarea. Si `EndBoundary` está vacío, el disparador nunca expira.

**Resultado confirmado:**

| StartBoundary | EndBoundary | Enabled |
|---|---|---|
| 2026-06-18T23:00:00 | *(vacío)* | True |
| 2026-09-03T11:00:00 | *(vacío)* | True |

✅ Ambos disparadores están habilitados y sin fecha de vencimiento — la tarea seguirá corriendo perpetuamente según su horario.

### 4.5 Pendiente — permisos de carpeta para la nueva cuenta

Antes de dar por cerrado el cambio, falta confirmar que `SIGPRO_USER` tiene permisos de lectura/escritura sobre la carpeta donde vive el ejecutable de esta tarea (si no los tiene, la primera ejecución fallará por permisos NTFS aunque las credenciales estén bien).

```powershell
$t.Actions | Select Execute, Arguments, WorkingDirectory
```
**Qué hace:** muestra la ruta exacta del ejecutable/script que dispara esta tarea.

```powershell
icacls "RUTA_DE_LA_CARPETA_DEL_EXE" /grant "SIGPRO_USER:(OI)(CI)F"
```
**Qué hace:** otorga permisos completos (`F` = Full control) a `SIGPRO_USER` sobre esa carpeta y su contenido (`(OI)(CI)` = se aplica a subcarpetas y archivos existentes y futuros). **Reemplazar `RUTA_DE_LA_CARPETA_DEL_EXE` por el valor real que devuelva el comando anterior antes de correrlo.**

---

## 2. Comandos de referencia rápida

| Acción | Comando |
|---|---|
| Listar tareas de una carpeta | `Get-ScheduledTask -TaskPath "\RUTA\" \| Select TaskName, State` |
| Ver detalle completo de una tarea | `schtasks /query /tn "\RUTA\NOMBRE" /v /fo LIST` |
| Deshabilitar una tarea | `Disable-ScheduledTask -TaskName "NOMBRE" -TaskPath "\RUTA\"` |
| Habilitar una tarea | `Enable-ScheduledTask -TaskName "NOMBRE" -TaskPath "\RUTA\"` |
| Ejecutar una tarea ahora | `Start-ScheduledTask -TaskName "NOMBRE" -TaskPath "\RUTA\"` |
| Detener una tarea en ejecución | `Stop-ScheduledTask -TaskName "NOMBRE" -TaskPath "\RUTA\"` |
| Ver último resultado de ejecución | `Get-ScheduledTaskInfo -TaskName "NOMBRE" -TaskPath "\RUTA\" \| Select LastRunTime, LastTaskResult, NextRunTime` |
| Cambiar la cuenta de ejecución | `Set-ScheduledTask -TaskName "NOMBRE" -TaskPath "\RUTA\" -User "USUARIO" -Password "CLAVE"` |
| Otorgar "Log on as a batch job" manualmente | ```secedit /export /cfg C:\secpol.cfg```<br>```(Get-Content C:\secpol.cfg) -replace "(SeBatchLogonRight = .*)", "`$1,*SID_DEL_USUARIO" \| Set-Content C:\secpol.cfg```<br>```secedit /configure /db secedit.sdb /cfg C:\secpol.cfg /areas USER_RIGHTS``` |
| Dar permisos NTFS a una carpeta | `icacls "RUTA" /grant "USUARIO:(OI)(CI)F"` |

---

## 2. Resumen de estado al cierre de esta sesión

- **Tarea `\SIGPRO\SIGPRO Eliminar sessiones caducadas`:** reconfigurada para correr con la cuenta local `SIGPRO_USER` (sin dependencia de dominio), habilitada, con disparadores perpetuos (sin fecha de vencimiento) confirmados. **Pendiente:** validar/otorgar permisos NTFS de la carpeta del ejecutable (sección 4.5) y confirmar la primera ejecución real con `Get-ScheduledTaskInfo`.
