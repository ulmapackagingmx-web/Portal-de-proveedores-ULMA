# 📚 Documentación General del Proyecto DataHub Ulma

Este documento proporciona una visión completa de la arquitectura, funcionamiento y componentes del servicio web DataHub Ulma, una aplicación robusta basada en FastAPI diseñada para la gestión eficiente de documentos y facturas. Incluye un detallado sistema de permisos, capacidades de procesamiento de diversos formatos de archivo y una interfaz de usuario dinámica.

## 🚀 Visión General de la Arquitectura

El proyecto sigue una arquitectura modular, separando las responsabilidades en componentes clave para facilitar el desarrollo, mantenimiento y escalabilidad. Se basa en FastAPI para el backend, SQLAlchemy para la interacción con la base de datos y un frontend HTML/JavaScript ligero.

### 📦 Componentes Principales

1.  **Backend (FastAPI):** El corazón del sistema, encargado de la lógica de negocio, la gestión de la API, la autenticación y la autorización.
2.  **Base de Datos (SQLite/PostgreSQL):** Almacena todos los datos relacionados con usuarios, documentos, historial y proveedores.
3.  **Frontend (HTML/JavaScript):** La interfaz de usuario que permite a los usuarios interactuar con el sistema a través de un navegador web.
4.  **Sistema de Archivos (`uploads/`):** Almacenamiento local para los archivos PDF y XML subidos.

## 📁 Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

```
mi-web-serviceV8/
├── .env.example                       # Archivo de ejemplo para variables de entorno
├── .gitignore                         # Archivos ignorados por Git
├── ACTUALIZAR_GITHUB.md               # Guía para mantener el repositorio de GitHub actualizado
├── CAMBIOS_NUEVOS.md                  # Registro de los cambios y mejoras recientes
├── DOCUMENTACION_GENERAL.md           # Este archivo (documentación exhaustiva)
├── database.py                        # Configuración de la conexión a la base de datos
├── email_processor.py                 # Lógica para procesar correos electrónicos
├── main.py                            # Punto de entrada de la aplicación FastAPI
├── models.py                          # Definición de los modelos de la base de datos (SQLAlchemy)
├── permissions.py                     # Lógica de permisos y roles de usuario
├── render.yaml                        # Configuración para el despliegue en Render.com
├── requirements.txt                   # Lista de dependencias de Python
├── security.py                        # Funciones de seguridad y autenticación (hashing de contraseñas, tokens)
├── USUARIOS_Y_PERMISOS.md             # Documentación detallada de usuarios y sus permisos
├── routers/                           # Directorio que contiene los módulos de enrutamiento de la API
│   ├── documents.py                   # Endpoints para la gestión de documentos (CRUD, estados, exportación)
│   ├── providers.py                   # Endpoints para la gestión de proveedores (CRUD, validación)
│   ├── uploads.py                     # Endpoints para la subida y procesamiento de archivos (XML, Excel, Texto)
│   └── webhook.py                     # Endpoint para la integración con servicios externos (ej. Power Automate)
├── templates/                         # Directorio que contiene las plantillas HTML del frontend
│   └── index.html                     # Interfaz principal del usuario
└── uploads/                           # Directorio para almacenar archivos subidos (generado automáticamente)
```

## 📖 Descripción Detallada de Archivos y Módulos

Aquí se explican en profundidad los archivos clave, sus interconexiones y las áreas donde se pueden realizar modificaciones.

### `main.py`

-   **Función Principal:** Es el corazón de la aplicación FastAPI. Inicializa la aplicación, configura middlewares (como CORS para permitir peticiones desde diferentes orígenes), monta la carpeta de archivos subidos y define los eventos de inicio para la creación de tablas y usuarios por defecto.
-   **Interconexiones:** Importa y utiliza `database.py` (para la conexión a la DB), `models.py` (para los modelos de datos), `security.py` (para hashing de contraseñas), `permissions.py` (para la gestión de roles) y todos los módulos de `routers/` para registrar los endpoints de la API. También sirve el archivo `templates/index.html` como interfaz principal.
-   **Puntos de Modificación Comunes:**
    -   **Configuración de FastAPI:** Línea 25 (`app = FastAPI(...)`) para cambiar el título y la versión de la API.
    -   **Usuarios Iniciales:** Las líneas 41 a 98 definen la lógica para crear usuarios administradores, supervisores y proveedores si la base de datos está vacía. Aquí puedes ajustar los nombres de usuario, contraseñas y las relaciones de subordinación.
    -   **CORS:** Las líneas 30-32 configuran las políticas de Cross-Origin Resource Sharing. Puedes restringir `allow_origins=["*" ]` a dominios específicos para mayor seguridad.

### `models.py`

-   **Función Principal:** Define la estructura de las tablas en la base de datos utilizando SQLAlchemy ORM (Object-Relational Mapping). Contiene las clases `DBUser`, `DBDocument`, `DBHistory` y `DBProvider` con sus respectivas columnas y tipos de datos.
-   **Interconexiones:** Importa `Base` de `database.py`. Es fundamental para todos los módulos que interactúan con la base de datos (routers, security, permissions, email_processor).
-   **Puntos de Modificación Comunes:**
    -   **`DBUser` (Líneas 5-11):** Puedes añadir nuevos campos para los usuarios, como correo electrónico, departamento, información de contacto, etc.
    -   **`DBDocument` (Líneas 13-44):** Aquí se definen los atributos de los documentos/facturas. Puedes añadir campos para nuevas categorías, detalles fiscales adicionales, metadatos, o incluso deshabilitar campos existentes que ya no sean necesarios (comentándolos o eliminándolos con cuidado).
    -   **`DBHistory` (Líneas 52-59):** Permite extender el historial de acciones sobre los documentos si se necesita registrar más detalles.
    -   **`DBProvider` (Líneas 61-74):** Puedes agregar campos para más detalles del proveedor, como dirección fiscal, contacto secundario, etc.
    -   **⚠️ Importante:** Cualquier cambio en los modelos requiere la recreación de la base de datos (`datahub.db` para SQLite) para que los cambios se apliquen. Esto se puede hacer ejecutando el endpoint `/api/reset-db` (solo admin) o eliminando el archivo `datahub.db` y reiniciando la aplicación.

### `database.py`

-   **Función Principal:** Configura la conexión a la base de datos. Por defecto, usa SQLite para desarrollo (`datahub.db`). Proporciona el motor (`engine`) y una función (`get_db()`) para obtener sesiones de base de datos, lo que permite la inyección de dependencias en FastAPI.
-   **Interconexiones:** Es importado por `main.py` y por todos los módulos de `routers/` que necesitan acceder a la base de datos.
-   **Puntos de Modificación Comunes:**
    -   **URL de la Base de Datos (Línea 4):** Puedes cambiar `SQLALCHEMY_DATABASE_URL` para conectar a otras bases de datos como PostgreSQL o MySQL, lo cual es altamente recomendado para entornos de producción para asegurar persistencia y escalabilidad. La guía `ACTUALIZAR_GITHUB.md` incluye instrucciones para configurar PostgreSQL en Render.

### `security.py`

-   **Función Principal:** Gestiona la seguridad de la aplicación, incluyendo el hashing y verificación de contraseñas (usando bcrypt) y la autenticación de usuarios a través de tokens (simulados como nombres de usuario por simplicidad actual).
-   **Interconexiones:** Es importado por `main.py` (para hashear contraseñas de usuarios iniciales) y por `routers/` (a través de `Depends(get_current_user)`) para proteger los endpoints de la API.
-   **Puntos de Modificación Comunes:**
    -   **`get_current_user` (Líneas 18-27):** En un entorno de producción, esta función debería implementar una validación de tokens JWT (JSON Web Tokens) real en lugar de usar el nombre de usuario como token. Aquí se puede integrar una librería JWT para mayor seguridad.
    -   **Algoritmo de Hashing:** Se puede cambiar el contexto de `CryptContext` si se desea usar otro algoritmo de hashing de contraseñas.

### `permissions.py`

-   **Función Principal:** Implementa la lógica de autorización y el sistema de permisos jerárquico del sistema (Admin, Supervisor, Proveedor). Define qué acciones puede realizar cada rol sobre los documentos y proveedores, incluyendo la visibilidad, edición, eliminación y cambio de estado.
-   **Interconexiones:** Es importado por `main.py` (para la información de roles en el login) y por los módulos de `routers/` (`documents.py`, `providers.py`) para aplicar las reglas de negocio en los endpoints protegidos.
-   **Puntos de Modificación Comunes:**
    -   **`obtener_usuarios_permitidos` (Líneas 13-38):** Modifica esta función para cambiar quién puede ver los registros de otros usuarios.
    -   **`puede_editar`, `puede_eliminar`, `puede_autorizar`, `puede_subir_comprobante_pago`, `puede_exportar` (Líneas 40-145):** Estas funciones son cruciales para definir las reglas de negocio. Aquí puedes ajustar o añadir condiciones para cada acción, por ejemplo, permitir que un supervisor elimine un documento en más estados o permitir que un proveedor edite ciertos campos después de la autorización.
    -   **Nuevos Roles:** Si se necesitan más roles (ej. Gerente, Contabilidad), se deben extender las condiciones en estas funciones para incluir la nueva lógica de permisos.

### `email_processor.py`

-   **Función Principal:** Contiene la lógica para conectarse a un servidor de correo (Exchange/Outlook), leer correos electrónicos no leídos y extraer información relevante (XML adjuntos, datos del cuerpo del correo) para crear automáticamente registros de documentos en el sistema.
-   **Interconexiones:** Utiliza `database.py` y `models.py` para persistir los documentos. Depende de las variables de entorno para la configuración de la cuenta de correo.
-   **Puntos de Modificación Comunes:**
    -   **`parsear_cuerpo_correo` (Líneas 36-87):** Si el formato de los correos cambia, aquí se deben ajustar las expresiones regulares (`re.search`) para extraer correctamente los datos como la fecha de pago, moneda o centros de costo.
    -   **`procesar_xml_adjunto` (Líneas 89-123):** Modifica cómo se leen las etiquetas específicas del XML si el formato de las facturas cambia o si se necesitan extraer nuevos campos fiscales.
    -   **`USER_MAPPING` (Línea 22):** Este diccionario en el `.env.example` permite mapear direcciones de correo a usuarios del sistema. Es útil para asignar automáticamente el campo `subido_por` al procesar correos.
    -   **Frecuencia de Procesamiento:** En la sección `if __name__ == "__main__":` (líneas 242-249), puedes configurar si el procesador se ejecuta una vez o en un bucle continuo (ej. cada 5 minutos).

### `render.yaml` y `requirements.txt`

-   **`render.yaml`:** Es el archivo de configuración para el despliegue de la aplicación en la plataforma Render.com. Define cómo se construye el proyecto (`buildCommand`) y cómo se inicia (`startCommand`), además de listar variables de entorno.
-   **`requirements.txt`:** Lista todas las librerías y dependencias de Python necesarias para que el proyecto funcione correctamente (FastAPI, SQLAlchemy, pandas, exchangelib, etc.).
-   **Puntos de Modificación Comunes:**
    -   **`requirements.txt`:** Si añades nuevas librerías a tu proyecto, debes añadirlas aquí para que Render las instale durante el despliegue. Puedes generar este archivo automáticamente con `pip freeze > requirements.txt`.
    -   **`render.yaml`:** Ajusta `PYTHON_VERSION` si usas una versión específica de Python. Agrega o modifica `envVars` para configurar variables de entorno en Render (ej. credenciales de DB, claves secretas).

### `routers/` (Directorio)

Este directorio contiene la lógica de los endpoints de la API, organizados por funcionalidades para mantener el código limpio y modular.

#### `routers/uploads.py`

-   **Función Principal:** Maneja las rutas para subir y procesar documentos en diferentes formatos: XML, texto de correos, archivos Excel y registros manuales. Extrae la información relevante y la guarda en la base de datos, incluyendo la lógica de autoregistro de proveedores.
-   **Interconexiones:** Importa `get_db` de `database.py`, `DBDocument`, `DBUser`, `DBProvider` de `models.py`, `get_current_user` de `security.py` y `registrar_historial` de `documents.py`.
-   **Puntos de Modificación Comunes:**
    -   **`procesar_xml` (Líneas 27-115):** Es donde se define cómo se extraen los datos de los XML. Si cambian las etiquetas o se necesitan más campos fiscales, aquí se deben ajustar las rutas XPath o los atributos (`root.attrib.get`).
    -   **`procesar_texto` (Líneas 117-145):** Contiene las expresiones regulares para extraer información de texto plano. Si el formato de los correos cambia, estas regex deben ser actualizadas.
    -   **`procesar_excel` (Líneas 147-173):** Si el layout del Excel cambia (nombres de columnas), aquí se debe actualizar el `row.get("NombreColumna", ...)`.
    -   **`procesar_manual` (Líneas 175-205):** Permite añadir lógica para guardar nuevos campos si se expande el formulario de registro manual en el frontend.
    -   **`get_or_create_provider` (Líneas 19-25):** Lógica para crear automáticamente un proveedor si no existe al subir un documento, evitando duplicados.

#### `routers/documents.py`

-   **Función Principal:** Proporciona los endpoints para la gestión completa del ciclo de vida de los documentos: lectura, edición, eliminación, subida de PDFs (facturas y comprobantes de pago), cambio de estados (Pendiente, Autorizado, Pagado, Rechazado) y exportación de reportes a Excel. También incluye la gestión del historial de cambios.
-   **Interconexiones:** Depende de `database.py`, `models.py`, `security.py` y `permissions.py` para la lógica de negocio y las validaciones.
-   **Puntos de Modificación Comunes:**
    -   **`eliminar_doc` (Líneas 49-75):** Aquí se aplican las reglas de eliminación (definidas en `permissions.py`). Puedes ajustar la lógica si se requieren más condiciones para borrar.
    -   **`editar_doc` (Líneas 90-119):** Si se añaden nuevos campos a `DBDocument` en `models.py`, deben ser actualizados aquí para que puedan ser editados desde el frontend.
    -   **`avanzar_estado`, `retroceder_estado`, `rechazar_registro`, `enviar_correccion` (Líneas 138-212):** Estas funciones controlan el flujo de estados. Puedes modificar las transiciones permitidas entre estados o añadir nuevos estados si el proceso de negocio lo requiere.
    -   **`descargar_excel` (Líneas 325-382):** Si se añaden nuevos campos a los documentos, se deben incluir en el diccionario `row` para que sean exportables en el reporte de Excel.
    -   **`registrar_historial` (Líneas 23-38):** Permite registrar cualquier acción importante sobre los documentos para tener una trazabilidad completa.

#### `routers/webhook.py`

-   **Función Principal:** Actúa como un receptor (listener) para integraciones con aplicaciones de terceros, como Power Automate. Permite recibir datos de correos electrónicos (incluyendo XML y PDF en base64) para crear automáticamente registros de documentos en el sistema.
-   **Interconexiones:** Utiliza `database.py` y `models.py` para guardar los documentos. Emplea `base64` para decodificar los archivos recibidos.
-   **Puntos de Modificación Comunes:**
    -   **`procesar_correo_webhook` (Líneas 14-145):** Si la estructura del JSON enviado por Power Automate u otra herramienta cambia, aquí se deben ajustar las claves para extraer los datos correctamente.
    -   **`validar_porcentajes` (Líneas 147-159):** Asegura que la distribución de centros de costo siempre sume 100% (o un valor cercano con tolerancia).

#### `routers/providers.py`

-   **Función Principal:** Gestiona las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para la información de los proveedores. Incluye campos para datos bancarios, expediente y estados de validación.
-   **Interconexiones:** Depende de `database.py`, `models.py` y `permissions.py` para la persistencia de datos y las reglas de acceso.
-   **Puntos de Modificación Comunes:**
    -   **`create_provider`, `get_all_providers`, `update_provider`, `delete_provider` (Líneas 12-140):** Aquí puedes añadir, modificar o eliminar campos relacionados con los proveedores, siguiendo la definición en `models.py`. También puedes ajustar las condiciones de permisos para cada operación (ej. permitir que los supervisores solo editen ciertos campos).
    -   **Validación:** Se pueden añadir reglas de validación más estrictas para el RFC, números de cuenta, etc.

### `templates/` (Directorio)

Contiene las plantillas HTML que conforman la interfaz de usuario.

#### `templates/index.html`

-   **Función Principal:** Es la única página del frontend y actúa como una Single Page Application (SPA). Contiene toda la interfaz de usuario, incluyendo el formulario de login, el dashboard principal con la tabla de registros, modales para la edición y creación de documentos/proveedores, filtros, KPIs y la lógica JavaScript para interactuar con el backend.
-   **Interconexiones:** Realiza llamadas a todos los endpoints de la API (`/api/...`) definidos en los módulos de `routers/`. Utiliza `localStorage` para almacenar el token de autenticación y el rol del usuario.
-   **Puntos de Modificación Comunes:**
    -   **Interfaz de Usuario (HTML y Tailwind CSS):** Cualquier cambio visual, diseño de nuevos formularios, botones, tablas, etc., se realiza aquí. Se utiliza Tailwind CSS para un desarrollo rápido y responsive.
    -   **Lógica JavaScript (`<script>` al final):**
        -   **`login()` y `logout()` (Líneas 756-775):** Gestionan el proceso de autenticación.
        -   **`showDashboard()` (Líneas 777-792):** Inicializa el dashboard según el rol del usuario.
        -   **Funciones de Subida (`uploadXML`, `uploadExcel`, `uploadText`, `saveManual`) (Líneas 827-1055):** Controlan el envío de datos al backend. Si se añaden nuevos campos en los formularios, se deben incluir aquí al construir el `FormData` o el `JSON`.
        -   **`fetchData()` y `renderTable()` (Líneas 1350-1588):** Obtienen y renderizan los datos en la tabla principal. Si se añaden nuevos campos en `DBDocument`, deben ser mostrados en `renderTable`.
        -   **`openEdit()` y `saveEdit()` (Líneas 1147-1256):** Gestionan el modal de edición. Deben reflejar los campos del modelo `DBDocument`.
        -   **`cambiarEstado()` (Líneas 1296-1338):** Controla las interacciones para cambiar el estado de los documentos.
        -   **Gestión de Centros de Costo Dinámicos (Líneas 876-990 y 1058-1145):** Permite añadir múltiples centros de costo con porcentajes, incluyendo validación para que sumen 100%. Los `subcatalogos` (Líneas 744-748) pueden ser extendidos aquí.
        -   **`showProvidersView()` y `renderProvidersTable()` (Líneas 1866-1931):** Gestionan la vista de proveedores. Si se añaden nuevos campos a `DBProvider`, deben ser mostrados y gestionados aquí.
        -   **Modales (`edit-modal`, `manual-modal`, `create-provider-modal`, `edit-provider-modal`, etc.):** Se deben actualizar para reflejar los cambios en los modelos de datos y los formularios.

### `USUARIOS_Y_PERMISOS.md`

-   **Función Principal:** Documentación exhaustiva sobre los roles de usuario (`Admin`, `Supervisor`, `Proveedor`), sus credenciales iniciales, la jerarquía de permisos y una matriz detallada de qué acciones puede realizar cada rol. También incluye casos de uso y el flujo de trabajo típico.
-   **Interconexiones:** Es una guía de referencia para entender la lógica implementada en `permissions.py` y `main.py` (creación de usuarios).
-   **Puntos de Modificación Comunes:** Mantener actualizado si se modifican roles, permisos o usuarios por defecto.

### `ACTUALIZAR_GITHUB.md`

-   **Función Principal:** Guía práctica para mantener el repositorio de GitHub actualizado y sincronizado con el código local. Incluye comandos Git para hacer `fetch`, `add`, `commit` y `push`, así como instrucciones para la configuración de PostgreSQL en Render.com.
-   **Interconexiones:** Documento de apoyo para el desarrollador.
-   **Puntos de Modificación Comunes:** Actualizar si cambian las URLs del repositorio o las configuraciones de despliegue.

### `CAMBIOS_NUEVOS.md`

-   **Función Principal:** Un registro de los cambios y mejoras más recientes implementados en el proyecto. Detalla las funcionalidades nuevas, los archivos modificados y las pruebas recomendadas.
-   **Interconexiones:** Es un historial de desarrollo.
-   **Puntos de Modificación Comunes:** Actualizar con cada nueva característica o corrección importante.

### `.env.example` y `.gitignore`

-   **`.env.example`:** Proporciona un modelo de las variables de entorno que la aplicación espera (ej. credenciales de Exchange). Es un ejemplo y no debe contener valores sensibles en producción.
-   **`.gitignore`:** Especifica los archivos y directorios que Git debe ignorar (ej. base de datos local `datahub.db`, la carpeta `uploads/`, variables de entorno sensibles `.env`, cachés de Python `__pycache__`).
-   **Puntos de Modificación Comunes:**
    -   **`.env.example`:** Añadir nuevas variables si la aplicación requiere más configuraciones externas.
    -   **`.gitignore`:** Añadir nuevos patrones si se generan archivos o directorios temporales que no deben ser versionados en Git.

## 💡 Flujo de Trabajo Típico

1.  **Carga de Documentos:** Un **Proveedor** (o un administrador/supervisor) sube un XML, Excel, texto de correo o crea un registro manual. El documento inicialmente se marca como **Pendiente**.

2.  **Revisión y Autorización:** Un **Supervisor** revisa los documentos de sus subordinados. Puede **Autorizar** (cambiando el estado a **Autorizado**) o **Rechazar** (cambiando el estado a **Rechazado**).

3.  **Gestión de Pago:** Un **Administrador** (o un supervisor con permisos específicos) puede subir el comprobante de pago, marcando el documento como **Pagado**.

4.  **Correcciones y Reversiones:**
    -   Si un documento es **Rechazado**, el **Proveedor** puede enviar una corrección, volviendo el estado a **Pendiente**.
    -   Los administradores y supervisores pueden **Revertir** estados para corregir errores.

5.  **Eliminación:** La eliminación de documentos está sujeta a reglas de permisos detalladas (`permissions.py`), que varían según el rol y el estado del documento.

## 📊 Flujo de Datos Gráfico

```mermaid
graph TD
    A[Inicio] --> B{Subir Documento (XML/Excel/Texto/Manual)}
    B --> C[Documento en estado: Pendiente]
    
    C --> D{Supervisor/Admin Revisa}
    D -- "Autorizar" --> E[Documento en estado: Autorizado]
    D -- "Rechazar" --> F[Documento en estado: Rechazado]

    E --> G{Admin/Supervisor Sube Comprobante de Pago}
    G --> H[Documento en estado: Pagado]

    F --> I{Proveedor Corrige}
    I -- "Enviar Corrección" --> C

    H --> J[Fin del ciclo de pago]

    F --> K[Proveedor Elimina si es Rechazado]
    C --> K
    E --> K
    H --> K[Admin Elimina en cualquier estado]
    D -- "Revertir a Pendiente" --> C
    E -- "Revertir a Pendiente" --> C
    H -- "Revertir a Autorizado" --> E
```

## 🔐 Seguridad y Permisos

El sistema implementa un modelo de seguridad robusto:

-   **Autenticación:** Uso de tokens (simulados por username, idealmente JWT en producción) para validar la identidad del usuario.
-   **Autorización:** Un sistema de roles jerárquico (`Admin > Supervisor > Proveedor`) asegura que cada usuario solo acceda y modifique los datos para los que tiene permiso. Las reglas se definen en `permissions.py`.
-   **Hashing de Contraseñas:** Todas las contraseñas se almacenan con hashing bcrypt, nunca en texto plano.

## 🚀 Despliegue y Configuración

El proyecto está diseñado para ser desplegado fácilmente en plataformas como Render.com, con soporte para bases de datos persistentes (PostgreSQL).

-   **Variables de Entorno:** Utiliza archivos `.env` (no versionados) para configuraciones sensibles y credenciales. Ver `.env.example`.
-   **Dependencias:** `requirements.txt` lista todas las librerías necesarias.
-   **Despliegue Continuo:** La integración con GitHub y `render.yaml` facilita el despliegue continuo en Render.com.

## 🛠️ Modificaciones Comunes y Extensiones

### 1. Añadir un Nuevo Campo a los Documentos

1.  **`models.py`:** Añade la nueva columna a la clase `DBDocument`.
    ```python
    class DBDocument:
        # ... campos existentes ...
        nuevo_campo = Column(String, default="") # Ejemplo de nuevo campo
    ```
2.  **Recrear DB:** Borra `datahub.db` (en desarrollo) o resetea la DB en producción (si usas un ORM con migraciones como Alembic, úsalas). Reinicia la aplicación.
3.  **`routers/uploads.py`:** Si el campo se carga desde XML, Excel o texto, ajusta la lógica de extracción en las funciones `procesar_xml`, `procesar_excel` o `procesar_texto`.
4.  **`routers/documents.py`:** Si el campo se puede editar, actualiza la función `editar_doc` para que acepte y guarde el nuevo campo.
5.  **`templates/index.html`:** Modifica el formulario manual/de edición para incluir el nuevo campo y actualiza la función `renderTable` para mostrarlo en la tabla.

### 2. Añadir un Nuevo Rol de Usuario

1.  **`models.py`:** El campo `role` en `DBUser` ya es un String, así que no se requieren cambios si el nuevo rol es simplemente otro String.
2.  **`main.py`:** Si necesitas crear usuarios con este nuevo rol por defecto al inicio, añádelos en la función `startup_event`.
3.  **`permissions.py`:** Implementa la lógica específica para el nuevo rol en las funciones `obtener_usuarios_permitidos`, `puede_editar`, `puede_eliminar`, etc. para definir sus capacidades.
4.  **`templates/index.html`:** Actualiza la función `showDashboard` para adaptar la interfaz según el nuevo rol (ej. mostrar/ocultar botones).

### 3. Cambiar Centros de Costo o Subcatálogos

1.  **`templates/index.html`:** Modifica el objeto `subcatalogos` (Líneas 744-748) para ajustar los centros de costo y sus subcatálogos. Asegúrate de que los formularios de registro manual y edición (`openManualModal`, `openEdit`) reflejen estos cambios.
2.  **`routers/uploads.py`:** Si la lógica de extracción automática (de correos, por ejemplo) debe adaptarse a los nuevos centros/subcatálogos, actualiza las expresiones regulares o la lógica de parsing.

### 4. Modificar Reglas de Negocio (Ej. Validaciones)

-   **`routers/uploads.py`:** Para validaciones al subir documentos (ej. monto máximo para XML/Excel).
-   **`routers/documents.py`:** Para validaciones al editar o cambiar estados (ej. no permitir editar un documento pagado).
-   **`permissions.py`:** Para modificar las reglas de quién puede realizar qué acción (ej. un supervisor solo puede autorizar documentos hasta cierto monto).
-   **`templates/index.html`:** Para validaciones del lado del cliente (JavaScript), como la suma de porcentajes de centros de costo.

## ❓ Soporte y Contacto

Para cualquier duda, problema o sugerencia, consulta la documentación específica de cada módulo o contacta al administrador del sistema.

**Recursos Útiles:**

-   [Documentación de FastAPI](https://fastapi.tiangolo.com/)
-   [Documentación de SQLAlchemy](https://www.sqlalchemy.org/)
-   [Documentación de Render](https://render.com/docs)
-   [Documentación de Tailwind CSS](https://tailwindcss.com/docs)

---

**Última actualización:** 25/05/2026
**Versión del Documento:** 1.0

