# Cómo crear una nueva conexión WSUNOEE en SIESA (para que "SIGPRO" aparezca en Referencia)

## Contexto

En el log/monitor del conector de SIESA (columna **Referencia**), nuestras llamadas
aparecen como `WebService` en vez de `SIGPRO`. Se investigó y confirmó (probando en
vivo) que ese valor sale del `NombreConexion` que mandamos en el XML `<Importar>` —
hoy configurado en `backend/.env` como `SIESA_WSUNOEE_CONNECTION_NAME=reymon`.

Se intentó cambiarlo directamente a `SIGPRO` sin más: SIESA lo rechazó con
`Error al conectarse a la base de datos. No existe configuración.` — `NombreConexion`
**no es un texto libre**, tiene que existir como conexión registrada del lado del
servidor WSUNOEE antes de poder usarse.

## Qué es una "conexión" en WSUNOEE

Cada `NombreConexion` es un alias a una cadena de conexión de base de datos, registrada
en el servidor del webservice, en el archivo `SiesaWS.config` -> `<connectionStrings>`.
El cliente (SIGPRO) nunca ve ni necesita la cadena de conexión real — solo manda el
alias (`NombreConexion`), y el servidor resuelve la conexión real internamente.

Estado actual confirmado (revisando `SiesaWS.config` del servidor de referencia): **solo
existe una conexión registrada, `reymon`**. No hay ninguna llamada `SIGPRO` porque
nadie la ha creado todavía.

## Por qué no renombrar/tocar `reymon`

`reymon` es la conexión que ya está en uso por la integración TEP en producción — no
se debe renombrar ni eliminar (rompería el envío de documentos hasta que el `.env`
tuviera el nuevo nombre exacto, y no hay garantía de poder revertirlo fácil). Además,
en la página de administración del servidor (`WFConexion.aspx`, ver abajo) el botón
**"Eliminar" viene deshabilitado por defecto** para la conexión ya en uso — consistente
con no tocar `reymon`.

**El camino correcto es crear una conexión NUEVA llamada `SIGPRO`, en paralelo a
`reymon`** (mismos datos de base de datos — es la misma BD, solo un alias distinto para
que el log/monitor identifique el origen), no reemplazar la existente.

## Cómo crearla — dos formas

Ambas requieren acceso administrativo al servidor WSUNOEE (`10.0.0.4:8508` en este
ambiente) y **red interna/VPN** — las credenciales de base de datos viajan en texto
plano en ambos métodos.

### Opción A — Formulario web (recomendado, más simple)

El servidor expone una página de administración de conexiones:

```
http://10.0.0.4:8508/WSUNOEE/WFConexion.aspx
```

Formulario "Configuración conexión base de datos" con estos campos:

| Campo en el formulario | Corresponde a |
|---|---|
| Nombre Conexión | El alias nuevo — usar `SIGPRO` |
| Tipo BD | `SQL Server` (mismo motor que usa `reymon` hoy) |
| Nombre Servidor | El mismo servidor de BD que usa `reymon` (pedir al administrador si no se tiene a mano — **no está en este repo**, vive solo en `SiesaWS.config` del servidor) |
| Nombre BD | El mismo catálogo/base de datos que usa `reymon` |
| Usuario / Password | Las mismas credenciales de BD que usa `reymon` (o unas nuevas si el administrador prefiere aislar el acceso) |
| Núm conexión importación | Número de conexión interno para `ImportarXML` — pedir al administrador el valor correcto para esta instalación (no es arbitrario) |

Botones: **Probar** (valida la conexión antes de guardar) -> **Aplicar** (crea/guarda).

### Opción B — SOAP `CrearConexionXML` (uso administrativo, no para scripts de negocio)

Mismo webservice WSUNOEE, operación `CrearConexionXML(pvstrxmlConexion: string)`.
XML de entrada (`Conexion.xsd`):

```xml
<Conexion>
  <NombreConexion>SIGPRO</NombreConexion>
  <TipoBD>SQL</TipoBD>                  <!-- SQL=SQL Server, ORA=Oracle -->
  <NombreBD>...</NombreBD>              <!-- igual que reymon -->
  <NombreServidorBD>...</NombreServidorBD>  <!-- igual que reymon -->
  <UsuarioBD>...</UsuarioBD>
  <ClaveBD>...</ClaveBD>                <!-- credencial en texto plano dentro del XML -->
  <NumConexionImpo>...</NumConexionImpo>
</Conexion>
```

**Nunca invocar esto desde un script/endpoint de negocio de SIGPRO** — es de uso
administrativo puntual, y el XML viaja con la clave de BD en texto plano. Si se usa,
hacerlo una sola vez, manualmente, desde una máquina en la red interna, y no loguear
el XML en ningún lado.

## Después de crearla

Una vez que `SIGPRO` exista como conexión en el servidor (confirmado con el botón
"Probar" del formulario, o repitiendo la prueba que ya hicimos), el cambio en SIGPRO es
de una sola línea en `backend/.env`:

```
SIESA_WSUNOEE_CONNECTION_NAME=SIGPRO
```

Reiniciar `runserver` (las variables de entorno se leen al arrancar) y probar el
endpoint `POST /api/v1/integration/tep/send/` (ver
`documentation/SIESA_TEP_ENDPOINT.md`) — si responde `ok: true`, revisar en el
log/monitor de SIESA que la fila muestre `SIGPRO` en Referencia.

## Seguridad

- No commitear ni pegar en ningún doc de este repo las credenciales reales de la base
  de datos (usuario/clave que usa `reymon`, ni las que se usen para `SIGPRO`).
- `SiesaWS.config` del servidor **nunca** debe copiarse a este repo — contiene
  credenciales reales en base64 (no es cifrado, es solo codificación).
- Hacer esto solo sobre red interna/VPN, nunca desde una red pública.
