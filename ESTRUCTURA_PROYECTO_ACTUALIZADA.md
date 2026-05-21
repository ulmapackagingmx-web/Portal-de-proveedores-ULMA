# Estructura del Proyecto DataHub Ulma

A continuación, se describe la estructura del proyecto actual de tu servicio web (FastAPI), incluyendo para qué sirve cada archivo, cómo se interconecta con los demás y qué líneas puedes modificar.

## 📁 Raíz del proyecto

### `main.py`
- **¿Qué hace?:** Es el punto de entrada principal de la aplicación FastAPI. Crea la instancia de la aplicación, configura los middlewares (como CORS), y define el evento de inicio donde se crean las tablas de la base de datos y los usuarios iniciales. También contiene la ruta raíz (`/`) que sirve el HTML del frontend, y la ruta de autenticación (`/token`).
- **Conexiones:** Importa dependencias de `database.py`, `models.py`, `security.py`, `permissions.py` y carga todos los enrutadores desde la carpeta `routers/` (`uploads.py`, `documents.py`, `webhook.py`). Lee el archivo `templates/index.html`.
- **¿Qué puedes cambiar?:** 
  - Puedes cambiar el título y la versión de la API en la **línea 23** (`app = FastAPI(...)`).
  - Puedes modificar la lista de usuarios por defecto (admin, supervisores, proveedores) que se crean al iniciar en las **líneas 45 a 81**.
  - Puedes ajustar las configuraciones de CORS en las **líneas 25-27**.

### `models.py`
- **¿Qué hace?:** Define los modelos de la base de datos usando SQLAlchemy. Contiene la definición de las tablas, columnas y tipos de datos.
- **Conexiones:** Hereda la clase `Base` desde `database.py` y es importado por casi todos los demás archivos donde se guardan o consultan datos a la DB.
- **¿Qué puedes cambiar?:**
  - **Líneas 5-11 (`DBUser`):** Puedes agregar nuevas columnas para los usuarios (por ejemplo, correos electrónicos, departamentos, etc.).
  - **Líneas 13-37 (`DBDocument`):** Puedes agregar nuevos campos para los documentos/facturas (por ejemplo, notas adicionales, número de cuenta bancaria, etc.).

### `database.py`
- **¿Qué hace?:** Configura la conexión a la base de datos SQLite y proporciona la función `get_db()` para iniciar sesiones.
- **Conexiones:** Usado en todos los archivos de enrutadores (`routers/`) y `main.py` para inyectar la dependencia de la base de datos a las peticiones.
- **¿Qué puedes cambiar?:**
  - **Línea 4:** Puedes cambiar la URL de la base de datos (por ejemplo, para cambiar a PostgreSQL o MySQL) modificando `SQLALCHEMY_DATABASE_URL = "sqlite:///./datahub.db"`.

### `security.py` / `permissions.py`
- **¿Qué hacen?:** Gestionan toda la lógica de cifrado de contraseñas, validación de tokens JWT (autenticación) y los permisos o roles (autorización) para que cada usuario solo vea o modifique lo que le corresponde.
- **Conexiones:** Se conectan fuertemente con los modelos de usuarios y se inyectan en los endpoints (rutas) de la API para protegerlos de accesos no autorizados.
- **¿Qué puedes cambiar?:**
  - Puedes modificar la expiración del token JWT, la palabra secreta de encriptación o las reglas de quién puede ver qué documentos en las funciones de `permissions.py`.

### `email_processor.py`
- **¿Qué hace?:** Contiene la lógica para extraer información de textos de correos electrónicos. 
- **Conexiones:** Probablemente usado por el módulo de webhook o de subida para interpretar correos automáticamente.

### `render.yaml` y `requirements.txt`
- **¿Qué hacen?:** 
  - `render.yaml` configura cómo se despliega la aplicación en la plataforma Render.com (ej. comandos de inicio y variables de entorno).
  - `requirements.txt` lista las librerías o dependencias de Python necesarias para correr el programa (FastAPI, SQLAlchemy, Pandas, etc.).

---

## 📁 Directorio `routers/`
Contiene la lógica de la API separada por dominios o áreas para mantener el código ordenado y no saturar `main.py`.

### `routers/uploads.py`
- **¿Qué hace?:** Maneja todas las subidas y creaciones de registros. Procesa archivos XML, textos de correos, archivos Excel o ingresos manuales. Extrae la información (como el importe total, nombre, RFC) y la guarda en la base de datos.
- **Conexiones:** Se conecta a `database.py`, importa los modelos de `models.py` y verifica seguridad con `security.py`. Es registrado por `main.py`.
- **¿Qué puedes cambiar?:**
  - **Líneas 18-71 (`procesar_xml`):** Aquí puedes cambiar cómo se leen las etiquetas del XML de la factura (ej. agregar extracción del código postal).
  - **Líneas 73-94 (`procesar_texto`):** Puedes ajustar las expresiones regulares (`re.search()`) para que detecten de forma distinta los montos o nombres del correo electrónico.
  - **Líneas 96-115 (`procesar_excel`):** Puedes cambiar cómo se leen las columnas del Excel (si te cambian el formato, actualizas aquí los nombres de las cabeceras).
  - **Líneas 117-134 (`procesar_manual`):** Puedes agregar lógica para guardar nuevos campos enviados del frontend desde un formulario manual.

### `routers/documents.py`
- **¿Qué hace?:** Contiene los endpoints para leer, actualizar, borrar y exportar los documentos/facturas. También maneja la subida de los PDFs comprobantes, cambios de estado (Aprobado/Rechazado) y descarga de reportes Excel.
- **Conexiones:** Se conecta a la base de datos, valida permisos con `permissions.py` para asegurar que nadie modifique documentos ajenos sin autorización. Es registrado por `main.py`.
- **¿Qué puedes cambiar?:**
  - **Líneas 33-55 (`eliminar_doc`):** Puedes modificar las reglas de borrado (quién o en qué estado se puede borrar un documento).
  - **Líneas 70-90 (`editar_doc`):** Puedes agregar nuevos campos para ser editados en esta función.
  - **Líneas 109-159:** Puedes agregar o cambiar los flujos de estados (actualmente: Pendiente, Autorizado, Pagado, Rechazado).
  - **Líneas 198-217 (`descargar_excel`):** Puedes cambiar qué columnas y nombres se exportan en el reporte de Excel generado para los usuarios.

### `routers/webhook.py`
- **¿Qué hace?:** Generalmente actúa como receptor (listener) para integraciones con aplicaciones de terceros, por ejemplo si un servicio te envía información en tiempo real de correos u otros eventos.

---

## 📁 Directorio `templates/`

### `templates/index.html`
- **¿Qué hace?:** Contiene toda la interfaz de usuario en formato HTML, junto con CSS y JavaScript incrustado para hacer peticiones a la API.
- **Conexiones:** Es enviado al navegador por la ruta principal `/` en `main.py`.
- **¿Qué puedes cambiar?:**
  - ¡Todo lo visual! Puedes cambiar colores, botones, agregar modales, formularios, tablas, o lógica JavaScript de cómo interactúa el usuario con la plataforma en el navegador.

---

## 📁 Directorio `uploads/`
- **¿Qué hace?:** Es la carpeta física en tu servidor o computadora donde se guardan temporal o permanentemente los archivos PDF de comprobantes que suben los usuarios. Esta carpeta es creada automáticamente en `main.py`.