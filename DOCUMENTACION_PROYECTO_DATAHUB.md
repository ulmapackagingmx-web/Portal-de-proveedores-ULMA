# 🚀 Documentación Integral del Proyecto DataHub Ulma

Este documento proporciona una visión exhaustiva de la arquitectura, funcionamiento y componentes clave del proyecto **DataHub Ulma**. Diseñado como un servicio web robusto en Python utilizando FastAPI, el sistema está enfocado en la gestión eficiente de documentos fiscales, administración de proveedores y automatización de la captura de datos.

## 🎯 Visión General y Propósito

El DataHub Ulma centraliza y simplifica el proceso de gestión de facturas y documentos, ofreciendo una plataforma para la subida de archivos, extracción de datos, flujo de aprobación jerárquico y un módulo para la gestión de proveedores.

### 🌟 Características Principales

*   **Ingesta de Documentos Multi-Formato:** Soporte para XML, Excel, texto plano (correos) y registros manuales.
*   **Procesamiento Automático de Correos:** Conexión a buzones de Exchange para la extracción y registro automático de documentos.
*   **Sistema de Permisos Jerárquico:** Roles definidos (Proveedor, Supervisor, Administrador) con reglas estrictas de acceso y modificación.
*   **Gestión de Ciclo de Vida del Documento:** Flujos de estado (Pendiente, Autorizado, Pagado, Rechazado) con opciones de avance, retroceso y corrección.
*   **Catálogo de Proveedores:** Módulo CRUD para la administración de la información bancaria y documental de los proveedores.
*   **Trazabilidad y Auditoría:** Historial detallado de todas las acciones realizadas sobre cada documento.
*   **Interfaz de Usuario Intuitiva:** Frontend web interactivo para la visualización, filtrado y gestión de registros.
*   **Exportación de Datos:** Capacidad de generar reportes detallados en formato Excel.

### ⚙️ Tecnologías Fundamentales

*   **Backend:** Python 3.9+, FastAPI, SQLAlchemy, `passlib[bcrypt]`, `python-multipart`, `pandas`, `xlsxwriter`, `openpyxl`, `exchangelib`, `python-dotenv`.
*   **Base de Datos:** SQLite (para desarrollo, configurable a PostgreSQL para producción).
*   **Frontend:** HTML, JavaScript, Tailwind CSS, Preline UI, Font Awesome, Toastify-js.

## 📁 Estructura del Proyecto

El proyecto sigue una estructura modular y organizada, facilitando la comprensión y el mantenimiento.

```
.
├── .env.example                       # Archivo de ejemplo para variables de entorno
├── .gitignore                         # Archivos ignorados por Git
├── ACTUALIZAR_GITHUB.md               # Guía para actualizar el repositorio de GitHub
├── CAMBIOS_NUEVOS.md                  # Registro de cambios recientes
├── DEPLOY_GITHUB_RENDER.md            # Documentación para despliegue en Render.com
├── DOCUMENTACION_GENERAL.md           # Documentación general del proyecto (existente)
├── DOCUMENTACION_TECNICA_DETALLADA.md # Documentación técnica profunda (existente)
├── ESTRUCTURA_PROYECTO_ACTUALIZADA.md # Estructura del proyecto (existente)
├── USUARIOS_Y_PERMISOS.md             # Documentación detallada de usuarios y permisos
├── architecture_rules.md              # Reglas de arquitectura (si aplica)
├── database.py                        # Configuración de la conexión a la base de datos
├── email_processor.py                 # Lógica para procesar correos y adjuntos
├── main.py                            # Punto de entrada de la aplicación FastAPI
├── models.py                          # Definición de los modelos de la base de datos
├── permissions.py                     # Lógica de permisos y roles de usuario
├── render.yaml                        # Configuración de despliegue en Render.com
├── requirements.txt                   # Lista de dependencias de Python
├── security.py                        # Funciones de seguridad y autenticación
├── routers/                           # Directorio que contiene los módulos de enrutamiento de la API
│   ├── documents.py                   # Endpoints para la gestión de documentos
│   ├── providers.py                   # Endpoints para la gestión de proveedores
│   ├── uploads.py                     # Endpoints para la subida y procesamiento de archivos
│   └── webhook.py                     # Endpoint para la integración con Power Automate
├── templates/                         # Directorio de plantillas HTML del frontend
│   └── index.html                     # Interfaz principal del usuario (Single Page Application)
└── uploads/                           # Directorio para almacenar archivos subidos (generado automáticamente)
```

## 🧠 Descripción Detallada de Módulos y Puntos de Modificación

A continuación, se detalla la función, interconexiones y áreas clave para modificaciones en cada componente del sistema.

---

### `main.py`
*   **Función Principal:** Es el orquestador de la aplicación FastAPI. Inicializa la API, configura middleware esencial (CORS, StaticFiles), registra todos los routers y gestiona los eventos de inicio (`startup_event`) para la creación de la base de datos y usuarios por defecto. También sirve la interfaz de usuario (`index.html`) y maneja el endpoint de autenticación (`/token`).
*   **Interconexiones:** Importa y utiliza `database.py`, `models.py`, `security.py`, `permissions.py` y todos los módulos dentro de `routers/`. Renderiza `templates/index.html`.
*   **Puntos de Modificación Clave:**
    *   **Configuración de FastAPI:** Modifica el título y la versión de la API en la instancia de `FastAPI` (aprox. línea 25).
    *   **Usuarios Iniciales:** Las definiciones de `DBUser` y la lógica de creación en `@app.on_event("startup")` (aprox. líneas 41-98) son ideales para ajustar usuarios, contraseñas, roles y relaciones de subordinación de prueba.
    *   **CORS:** Ajusta la lista `allow_origins` en `CORSMiddleware` (aprox. líneas 30-32) para restringir el acceso a dominios específicos en producción.
    *   **Routers:** Si agregas nuevos módulos de router, deben ser incluidos aquí con `app.include_router()`.

---

### `models.py`
*   **Función Principal:** Define la estructura de las tablas de la base de datos utilizando el ORM de SQLAlchemy. Contiene las clases `DBUser`, `DBDocument`, `DBHistory` y `DBProvider`, cada una mapeada a una tabla y sus columnas.
*   **Interconexiones:** Importa `Base` de `database.py`. Es la columna vertebral de la persistencia de datos y es utilizado por casi todos los módulos del backend que interactúan con la base de datos.
*   **Puntos de Modificación Clave:**
    *   **`DBUser` (aprox. líneas 5-11):** Añade nuevos campos para usuarios (ej. `email`, `departamento`).
    *   **`DBDocument` (aprox. líneas 13-50):** Expande los atributos de documentos/facturas (ej. `numero_contrato`, `fecha_vencimiento`). Si añades campos aquí, necesitarás ajustar la lógica de `routers/uploads.py` (para la ingesta) y `routers/documents.py` (para edición/visualización).
    *   **`DBHistory` (aprox. líneas 52-59):** Añade campos si necesitas más detalles en el registro de auditoría.
    *   **`DBProvider` (aprox. líneas 61-74):** Añade campos para información adicional de proveedores (ej. `direccion_fiscal`).
    *   **⚠️ Consideración:** Cualquier cambio en los modelos requiere la actualización del esquema de la base de datos. En desarrollo, esto puede significar borrar `datahub.db` y reiniciar. En producción, se recomienda usar una herramienta de migraciones (como Alembic) para gestionar estos cambios.

---

### `database.py`
*   **Función Principal:** Configura la conexión a la base de datos, por defecto SQLite (`datahub.db`). Proporciona el `engine` para la conexión y una función `get_db()` para generar sesiones de base de datos, utilizada para la inyección de dependencias en FastAPI.
*   **Interconexiones:** Es fundamental para `main.py` y todos los módulos en `routers/`.
*   **Puntos de Modificación Clave:**
    *   **`SQLALCHEMY_DATABASE_URL` (aprox. línea 4):** Modifica esta URL para conectar a bases de datos de producción como PostgreSQL o MySQL. La documentación `ACTUALIZAR_GITHUB.md` puede ofrecer más detalles sobre la configuración de PostgreSQL en Render.

---

### `security.py`
*   **Función Principal:** Implementa la seguridad de la aplicación, incluyendo el hashing y verificación de contraseñas con `bcrypt`, y un mecanismo de autenticación de usuarios. Actualmente, utiliza el `username` como un token simplificado para `OAuth2PasswordBearer`.
*   **Interconexiones:** Utilizado por `main.py` (para hashear contraseñas de usuarios iniciales) y por los módulos de `routers/` a través de `Depends(get_current_user)` para proteger los endpoints.
*   **Puntos de Modificación Clave:**
    *   **`get_current_user` (aprox. líneas 18-27):** **CRÍTICO para producción.** Aquí se debe implementar una validación de tokens JWT (JSON Web Tokens) real en lugar de usar el nombre de usuario. Esto implica generar y verificar JWTs firmados.

---

### `permissions.py`
*   **Función Principal:** Implementa la lógica de autorización del sistema, definiendo el sistema de permisos jerárquico (`admin`, `supervisor`, `proveedor`). Controla la visibilidad, edición, eliminación y cambio de estado de documentos y proveedores basándose en el rol del usuario.
*   **Interconexiones:** Utilizado por `main.py` (para obtener la información de permisos en el login) y por los módulos `routers/documents.py` y `routers/providers.py` para aplicar las reglas de negocio en cada endpoint.
*   **Puntos de Modificación Clave:**
    *   **Funciones `obtener_usuarios_permitidos`, `puede_editar`, `puede_eliminar`, `puede_autorizar`, `puede_subir_comprobante_pago`, `puede_exportar` (aprox. líneas 13-145):** Estas funciones son el núcleo del control de acceso. Modifica las condiciones `if/elif` para ajustar las reglas de negocio para cada rol.
    *   **`obtener_info_usuario` (aprox. líneas 147-170):** Si añades nuevos permisos o quieres exponer más información de permisos al frontend, actualiza este diccionario.
    *   **Nuevos Roles:** Si introduces un nuevo rol de usuario, deberás añadir la lógica correspondiente en todas estas funciones.

---

### `email_processor.py`
*   **Función Principal:** Se encarga de conectarse a un servidor de correo Exchange (Office 365), leer correos no leídos y procesar adjuntos (XML y PDF) y el cuerpo del mensaje para extraer datos y crear documentos automáticamente en el sistema.
*   **Interconexiones:** Utiliza `database.py` y `models.py` para la persistencia. Depende de las variables de entorno (`.env`) para la configuración de la cuenta de correo.
*   **Puntos de Modificación Clave:**
    *   **`parsear_cuerpo_correo` (aprox. líneas 36-87):** Adapta las expresiones regulares (`re.search`) si el formato de los correos entrantes cambia para la extracción de `fecha_pago`, `moneda` o `centros_de_costo`.
    *   **`procesar_xml_adjunto` (aprox. líneas 89-123):** Modifica la lógica de parsing de XML si la estructura de los archivos XML adjuntos cambia o si necesitas extraer nuevos campos fiscales.
    *   **`USER_MAPPING` (en `.env.example` y línea 22):** Ajusta este mapeo para asociar direcciones de correo de remitentes a usuarios específicos del sistema.
    *   **Frecuencia de Procesamiento:** La sección `if __name__ == "__main__":` (aprox. líneas 242-249) te permite configurar si el script se ejecuta una vez o en un bucle (`time.sleep`) para un procesamiento continuo.

---

### `render.yaml` y `requirements.txt`
*   **`render.yaml`:** Archivo de configuración para el despliegue en Render.com. Define el entorno, los comandos de construcción (`buildCommand`) y de inicio (`startCommand`), así como las variables de entorno.
*   **`requirements.txt`:** Lista todas las dependencias de Python que el proyecto necesita.
*   **Puntos de Modificación Clave:**
    *   **`requirements.txt`:** Añade cualquier nueva librería de Python que incorpores a tu proyecto. Se recomienda usar `pip freeze > requirements.txt` para mantenerlo actualizado.
    *   **`render.yaml`:** Ajusta `python_version` y las `envVars` para las configuraciones específicas de producción (ej. credenciales de base de datos, `EXCHANGE_EMAIL`, `EXCHANGE_PASSWORD`).

---

### `routers/` (Directorio: Módulos de Enrutamiento)

Este directorio organiza los endpoints de la API por dominio, manteniendo la aplicación modular y fácil de navegar.

#### `routers/uploads.py`
*   **Función Principal:** Gestiona las rutas API para la carga de documentos mediante diferentes métodos: subida de archivos XML, procesamiento de texto plano (correos), importación de archivos Excel y creación de registros manuales. Extrae la información relevante de cada formato y la persiste en la base de datos, incluyendo la lógica de autoregistro de proveedores.
*   **Interconexiones:** Importa `get_db` de `database.py`, `DBDocument`, `DBUser`, `DBProvider` de `models.py`, `get_current_user` de `security.py` y `registrar_historial` de `documents.py`. Es incluido en `main.py`.
*   **Puntos de Modificación Clave:**
    *   **`procesar_xml` (aprox. líneas 27-115):** Si la estructura del XML cambia o necesitas extraer más nodos/atributos, aquí es donde ajustarás el parsing.
    *   **`procesar_texto` (aprox. líneas 117-145):** Modifica las expresiones regulares si el formato del texto a extraer cambia (ej. nuevos patrones para montos, nombres, folios).
    *   **`procesar_excel` (aprox. líneas 147-173):** Si el layout de las columnas del Excel cambia, actualiza los nombres de las claves (`row.get("NombreColumna")`).
    *   **`procesar_manual` (aprox. líneas 175-205):** Si el formulario de registro manual en el frontend añade nuevos campos, actualiza este endpoint para recibirlos y guardarlos en `DBDocument`.
    *   **`get_or_create_provider` (aprox. líneas 19-25):** Controla la lógica de cómo se crean automáticamente los proveedores si no existen al subir documentos.

#### `routers/documents.py`
*   **Función Principal:** Implementa los endpoints CRUD (Crear, Leer, Actualizar, Borrar) y operaciones avanzadas para los documentos. Esto incluye la visualización de la lista, edición de detalles, eliminación (con reglas de permiso), subida de PDFs (comprobantes de factura y pago), gestión del ciclo de vida (avance/retroceso/rechazo de estados) y la exportación de datos a Excel. También registra el historial de cambios.
*   **Interconexiones:** Depende de `database.py`, `models.py`, `security.py` y `permissions.py` para la lógica de negocio y las validaciones de acceso. Es incluido en `main.py`.
*   **Puntos de Modificación Clave:**
    *   **`eliminar_doc` (aprox. líneas 49-75):** Modifica las condiciones de eliminación si las reglas de negocio cambian (ej. permitir eliminar en más estados).
    *   **`editar_doc` (aprox. líneas 90-119):** Si has añadido nuevos campos en `DBDocument`, deben ser actualizados aquí para que puedan ser editados.
    *   **Flujo de Estados (`avanzar_estado`, `retroceder_estado`, `rechazar_registro`, `enviar_correccion`) (aprox. líneas 138-212):** Ajusta las transiciones de estado y las validaciones de permisos según el flujo de trabajo deseado.
    *   **`descargar_excel` (aprox. líneas 325-382):** Si agregas nuevos campos a `DBDocument` o `DBProvider` que quieras incluir en el reporte de Excel, actualiza el diccionario `row` dentro de esta función.
    *   **`registrar_historial` (aprox. líneas 23-38):** Permite personalizar los eventos que se registran en el historial de cada documento.
    *   **`ver_datos` (aprox. líneas 230-323):** Modifica la lógica de filtrado y cálculo de KPIs si se necesitan nuevas opciones de búsqueda o métricas.

#### `routers/webhook.py`
*   **Función Principal:** Actúa como un endpoint de escucha (`listener`) para recibir datos de servicios externos, como Power Automate. Permite la ingesta de información de correos (incluyendo XML y PDF en base64) para crear registros de documentos en el sistema de manera programática.
*   **Interconexiones:** Utiliza `database.py` y `models.py` para la persistencia. Usa `base64` para decodificar los archivos adjuntos.
*   **Puntos de Modificación Clave:**
    *   **`procesar_correo_webhook` (aprox. líneas 14-145):** Si la estructura del JSON enviado por el servicio externo cambia, aquí deberás ajustar cómo se extraen los `datos` del `Body`.
    *   **`validar_porcentajes` (aprox. líneas 147-159):** Modifica la lógica si necesitas diferentes reglas para la validación de la suma de porcentajes de centros de costo.

#### `routers/providers.py`
*   **Función Principal:** Gestiona las operaciones CRUD para el catálogo de proveedores. Permite crear, listar, actualizar y eliminar registros de `DBProvider`, incluyendo sus datos bancarios, estado del expediente y validaciones.
*   **Interconexiones:** Depende de `database.py`, `models.py` y `permissions.py` para la persistencia y la aplicación de las reglas de acceso específicas de proveedores. Es incluido en `main.py`.
*   **Puntos de Modificación Clave:**
    *   **`create_provider`, `get_all_providers`, `update_provider`, `delete_provider` (aprox. líneas 12-140):** Si has añadido nuevos campos en `DBProvider` en `models.py`, actualiza estas funciones para gestionarlos (creación, edición, visualización).
    *   **Lógica de Permisos (dentro de cada función):** Ajusta las llamadas a `permissions.py` (ej. `puede_editar_proveedor`) si las reglas de quién puede gestionar proveedores cambian.
    *   **Validaciones:** Puedes añadir validaciones de formato para RFC, CLABE, etc.

---

### `templates/index.html` (Frontend)
*   **Función Principal:** Es la interfaz de usuario completa (Single Page Application) que permite a los usuarios interactuar con el backend. Incluye la lógica de login, el dashboard principal con la tabla de documentos, modales para diversas operaciones (edición, registro manual, gestión de proveedores, historial, exportación), filtros, KPIs y la lógica JavaScript para todas las interacciones con la API.
*   **Interconexiones:** Realiza llamadas asíncronas (fetch API) a todos los endpoints del backend (`/api/...`). Utiliza `localStorage` para gestionar la sesión del usuario (token, rol).
*   **Puntos de Modificación Clave:**
    *   **Diseño (HTML y Tailwind CSS):** Modifica la estructura HTML y las clases de Tailwind CSS para cualquier cambio visual, diseño de formularios, tablas, modales, etc.
    *   **Lógica JavaScript:**
        *   **Autenticación (`login()`, `logout()`, `showDashboard()`):** Adapta si la lógica de autenticación del backend cambia o si deseas diferentes comportamientos en el frontend al iniciar sesión/cerrar.
        *   **Funciones de Subida (`uploadXML`, `uploadExcel`, `uploadText`, `saveManual`):** Si agregas nuevos campos a los formularios de subida, actualiza estas funciones para construir correctamente el `FormData` o el objeto JSON a enviar al backend.
        *   **Renderizado de Tabla (`fetchData()`, `renderTable()`):** Si has añadido nuevos campos a `DBDocument`, asegúrate de que se muestren en la tabla principal y en el modal de edición.
        *   **Gestión de Centros de Costo Dinámicos (funciones con `agregarCentro...`, `updateSubcatalogo...`, `calcularTotal...`, `obtenerCentros...`):** Modifica `subcatalogos` (aprox. línea 744) para actualizar las opciones de centros y subcatálogos. Ajusta la lógica si cambian los requisitos de cómo se distribuyen los porcentajes.
        *   **Gestión de Proveedores (`fetchProviders`, `openCreateProviderModal`, `saveNewProvider`, `openEditProvider`, `saveEditedProvider`):** Actualiza estas funciones si la API de proveedores o los formularios de proveedor cambian (nuevos campos, validaciones).
        *   **Lógica de Permisos en Frontend (`showDashboard` y otros):** El frontend ya oculta/muestra elementos basados en `userRole`. Ajusta esta lógica si los nuevos roles requieren diferentes visualizaciones.

---

### `uploads/` (Directorio)
*   **Función Principal:** Es la carpeta del sistema de archivos donde se almacenan físicamente los documentos PDF y otros archivos subidos por los usuarios o generados por el sistema (como los comprobantes de pago).
*   **Interconexiones:** La aplicación FastAPI monta este directorio como un recurso estático (`/uploads`) en `main.py` para permitir la descarga de archivos. Los routers `documents.py` y `webhook.py` guardan y recuperan archivos de aquí.
*   **Puntos de Modificación Clave:** Generalmente, no se modifica directamente el código aquí, sino que se gestiona su ubicación y tamaño máximo a través de configuraciones del servidor o del sistema de archivos. En un entorno de producción, es común que esta carpeta sea reemplazada por un sistema de almacenamiento en la nube (ej. S3 de AWS) para mayor escalabilidad y durabilidad.

---

## 📊 Flujo de Datos y Roles (Gráfico)

```mermaid
graph TD
    subgraph Frontend (templates/index.html)
        FL[Login] --> FD{Dashboard: Cargar / Ver Documentos / Ver Proveedores}
        FD -- "Formulario Manual" --> FM[Modal Manual]
        FD -- "Editar Doc" --> FE[Modal Edición Doc]
        FD -- "Crear Prov" --> FCP[Modal Crear Prov]
        FD -- "Editar Prov" --> FEP[Modal Editar Prov]
        FD -- "Filtros / Búsqueda" --> FS[Filtros y Búsqueda]
        FD -- "Exportar Excel" --> FX[Modal Exportar Excel]
    end

    subgraph Backend (FastAPI: main.py, routers/*)
        BL[API: /token] --> BLU[Auth: get_current_user]
        BU[API: /api/subir-*] --> BUP[Uploader: procesar_*]
        BD[API: /api/documentos/*] --> BDP[Docs: CRUD, estados, PDFs]
        BP[API: /api/providers/*] --> BPP[Providers: CRUD, validación]
        BW[API: /api/webhook/procesar-correo] --> BWP[Webhook: procesar_correo_webhook]
    end

    subgraph Core Logic (security.py, permissions.py, email_processor.py, models.py, database.py)
        CLP[Permissions: Roles y Reglas]
        CLS[Security: Hashing, Autenticación]
        CLE[Email: Procesamiento automático]
        CLM[Models: DBUser, DBDocument, DBHistory, DBProvider]
        CLD[Database: Conexión y Sesiones]
    end

    subgraph Data Storage
        DS_DB[datahub.db (SQLite/PostgreSQL)]
        DS_FS[uploads/ (Archivos PDF, XML)]
    end

    FL -- "Credenciales" --> BL
    BLU -- "Verifica Token" --> FD
    BLU -- "Rol y Permisos" --> CLP

    FM -- "Enviar Datos" --> BUP
    FE -- "Guardar Cambios" --> BDP
    FCP -- "Guardar Prov" --> BPP
    FEP -- "Guardar Edición Prov" --> BPP
    FS -- "Aplicar Filtros" --> BDP
    FX -- "Solicitar Exportación" --> BDP

    CLE -- "Detecta correos [DATAHUB]" --> BWP
    BWP -- "XML/PDF base64" --> DS_FS
    BWP -- "Datos extraídos" --> CLM

    BUP -- "Datos extraídos" --> CLM
    BDP -- "Acciones CRUD" --> CLM
    BPP -- "Acciones CRUD" --> CLM

    CLM <--> CLD
    CLM <--> DS_DB
    BUP -- "Guarda PDF/XML" --> DS_FS
    BDP -- "Accede PDF/XML" --> DS_FS

    CLP <--> BDP
    CLP <--> BPP

    style FL fill:#f9f9f9,stroke:#333,stroke-width:2px
    style FD fill:#e0f7fa,stroke:#0097a7,stroke-width:2px
    style FM fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style FE fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style FCP fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style FEP fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style FS fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style FX fill:#ffebee,stroke:#f44336,stroke-width:2px

    style BL fill:#f5f5f5,stroke:#424242,stroke-width:2px
    style BU fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style BD fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style BP fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style BW fill:#e8f5e9,stroke:#4caf50,stroke-width:2px

    style CLP fill:#fff8e1,stroke:#ffc107,stroke-width:2px
    style CLS fill:#fff8e1,stroke:#ffc107,stroke-width:2px
    style CLE fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    style CLM fill:#f0f4c3,stroke:#cddc39,stroke-width:2px
    style CLD fill:#f0f4c3,stroke:#cddc39,stroke-width:2px

    style DS_DB fill:#cfd8dc,stroke:#607d8b,stroke-width:2px
    style DS_FS fill:#cfd8dc,stroke:#607d8b,stroke-width:2px

```

---

## 🔐 Seguridad y Modelo de Roles

El sistema implementa un modelo de control de acceso basado en roles (RBAC) jerárquico.

### Roles Definidos:

1.  **👑 Admin:**
    *   **Acceso Total:** Puede ver, editar, eliminar y autorizar *cualquier* registro y gestionar *cualquier* proveedor.
    *   **Funciones Exclusivas:** Es el único que puede subir comprobantes de pago, y tiene acceso a herramientas de administración como el `reset-db`.
    *   **Subordinados:** Puede ver y gestionar todos los usuarios y sus documentos.
2.  **👔 Supervisor:**
    *   **Acceso a Propios y Subordinados:** Puede ver y editar sus propios documentos y los de los usuarios listados en su campo `subordinados`.
    *   **Gestión de Documentos:** Puede autorizar, rechazar, retroceder estados de los documentos de sus *subordinados* (pero no los suyos propios). Puede eliminar documentos de subordinados si están en estado "Pendiente".
    *   **Gestión de Proveedores:** Puede ver la lista de proveedores y editar sus datos (sin poder eliminar).
    *   **Funciones Exclusivas:** Puede exportar datos a Excel. No puede subir comprobantes de pago.
3.  **👤 Proveedor:**
    *   **Acceso Restringido:** Solo puede ver, editar y eliminar sus *propios* registros.
    *   **Edición/Eliminación:** Solo puede eliminar sus propios registros si están en estado "Pendiente" o "Rechazado". Puede editar sus registros siempre que no estén "Pagados".
    *   **Flujo de Corrección:** Si su documento es "Rechazado", puede "Enviar Corrección" para devolverlo a "Pendiente".
    *   **Restricciones:** No puede autorizar, rechazar, subir comprobantes de pago, exportar datos ni gestionar proveedores.

## 🤝 Flujo de Trabajo Típico

1.  **Carga de Documentos:** Un **Proveedor** o **Admin/Supervisor** sube un documento (XML, Excel, texto, manual). El estado inicial es **Pendiente**.
2.  **Revisión y Autorización:** Un **Supervisor** revisa los documentos de sus subordinados.
    *   Si aprueba, el estado cambia a **Autorizado**.
    *   Si encuentra problemas, lo **Rechaza** (requiere un motivo).
3.  **Corrección por Proveedor:** Si un documento es **Rechazado**, el **Proveedor** puede corregirlo y **Enviar Corrección**, devolviéndolo a **Pendiente** para una nueva revisión.
4.  **Gestión de Pago:** Un **Administrador** (o un supervisor con permisos específicos para el campo `porcentaje_pago`) puede subir el **Comprobante de Pago**, marcando el documento como **Pagado**. También puede establecer la `fecha_estimada_pago`.
5.  **Reversiones:** Los **Administradores** y **Supervisores** pueden retroceder el estado de los documentos (ej. de Pagado a Autorizado, o de Autorizado a Pendiente) para correcciones.
6.  **Eliminación:** La eliminación está sujeta a las reglas de `permissions.py`. Por ejemplo, un Proveedor solo puede eliminar sus documentos Pendientes o Rechazados, mientras que un Admin puede eliminar cualquier documento en cualquier estado.

## 🛠️ Modificaciones Frecuentes y Pautas de Extensión

### 1. Añadir un Nuevo Campo a los Documentos o Proveedores

1.  **`models.py`:** Define la nueva columna en la clase `DBDocument` o `DBProvider` con su tipo y valor por defecto.
    ```python
    # Ejemplo en DBDocument
    class DBDocument(Base):
        # ...
        nuevo_campo_texto = Column(String, default="")
        nueva_fecha = Column(DateTime, default=None, nullable=True)
    ```
2.  **Actualizar DB:**
    *   **Desarrollo (SQLite):** Elimina `datahub.db` y reinicia la aplicación para recrear las tablas.
    *   **Producción (PostgreSQL):** Utiliza una herramienta de migraciones como Alembic para aplicar los cambios al esquema de forma segura (`alembic revision --autogenerate -m "Añadir nuevo_campo"`, luego `alembic upgrade head`).
3.  **Backend (`routers/uploads.py`, `routers/documents.py`, `routers/providers.py`):**
    *   Si el campo se extrae automáticamente (XML, Excel, correo): Modifica la función de procesamiento en `routers/uploads.py` (`procesar_xml`, `procesar_excel`, `procesar_texto`) para extraer y asignar el valor al nuevo campo del `DBDocument`.
    *   Si el campo es editable: Actualiza la función `editar_doc` en `routers/documents.py` o `update_provider` en `routers/providers.py` para recibir y guardar el nuevo valor.
    *   Si el campo se registra manualmente: Actualiza `procesar_manual` en `routers/uploads.py`.
4.  **Frontend (`templates/index.html`):**
    *   **Formularios:** Añade el `<input>` o `<select>` correspondiente en los modales de registro manual (`manual-modal`), edición de documento (`edit-modal`) o gestión de proveedores (`create-provider-modal`, `edit-provider-modal`).
    *   **Lógica JS:** En las funciones `saveManual()`, `saveEdit()`, `saveNewProvider()`, `saveEditedProvider()`, asegúrate de leer el valor del nuevo campo del DOM y enviarlo en el `body` de la petición al backend.
    *   **Visualización:** Actualiza la función `renderTable()` para mostrar el nuevo campo en la tabla principal. Si el campo es parte de la exportación a Excel, añade su checkbox en el modal `export-modal`.

### 2. Modificar un Rol Existente o Añadir uno Nuevo

1.  **`models.py`:** El campo `role` en `DBUser` es `String`. No se requiere cambiar el tipo, solo los valores posibles que puede tomar.
2.  **`main.py`:** Si el nuevo rol necesita usuarios de prueba al inicio, modifícalos en `startup_event`.
3.  **`permissions.py`:** Este es el archivo clave. Actualiza las funciones de `puede_...` (`puede_editar`, `puede_eliminar`, etc.) y `obtener_usuarios_permitidos` para incorporar la lógica del nuevo rol o modificar las reglas del existente. Considera la visibilidad y las acciones permitidas.
4.  **Frontend (`templates/index.html`):** Adapta la visibilidad de botones o secciones en la función `showDashboard()` (y otras funciones relevantes) si el nuevo rol tiene una experiencia de usuario diferente.

### 3. Ajustar Lógica de Extracción de Datos (XML, Excel, Texto/Correo)

*   **`routers/uploads.py` y `email_processor.py`:**
    *   **XML:** Si el esquema de tus XML cambia (nuevas etiquetas, diferentes rutas), modifica las funciones `procesar_xml` (en `uploads.py`) y `procesar_xml_adjunto` (en `email_processor.py`) para reflejar los nuevos paths o atributos.
    *   **Texto/Correo:** Las expresiones regulares (`re.search`) en `procesar_texto` (en `uploads.py`) y `parsear_cuerpo_correo` (en `email_processor.py`) deben ser actualizadas si el formato del texto de donde se extraen los datos cambia.
    *   **Excel:** Si el layout del Excel de importación masiva cambia, ajusta los nombres de las columnas en `row.get("NombreColumna")` dentro de `procesar_excel` (en `uploads.py`).

### 4. Personalizar el Flujo de Estados del Documento

*   **`routers/documents.py`:** Las funciones `avanzar_estado`, `retroceder_estado`, `rechazar_registro` y `enviar_correccion` controlan directamente las transiciones de estado. Modifica la lógica para añadir nuevos estados, cambiar las transiciones permitidas o agregar validaciones adicionales (ej. "solo se puede autorizar si el total es menor a X").
*   **`permissions.py`:** Asegúrate de que las funciones de permisos reflejen quién puede iniciar o permitir cada cambio de estado.

### 5. Modificaciones de UI/UX

*   **`templates/index.html`:** Este archivo es el centro de todas las modificaciones de la interfaz de usuario.
    *   **Estilos:** Ajusta o añade clases de Tailwind CSS en cualquier elemento HTML.
    *   **Interactividad:** Modifica o añade funciones JavaScript para nuevos botones, formularios o lógicas de visualización.
    *   **Componentes Preline:** Utiliza la documentación de Preline UI para integrar nuevos componentes o modificar los existentes (modales, tabs, etc.).
    *   **Internacionalización:** Si la aplicación necesita soportar múltiples idiomas, este archivo es el lugar para implementar la lógica de I18n en el frontend.

---

## ❓ Soporte y Contacto

Para cualquier duda, problema o sugerencia, consulta la documentación específica de cada módulo o contacta al administrador del sistema.

**Recursos de Desarrollo Útiles:**

*   [Documentación de FastAPI](https://fastapi.tiangolo.com/)
*   [Documentación de SQLAlchemy](https://www.sqlalchemy.org/)
*   [Documentación de Render](https://render.com/docs)
*   [Documentación de Tailwind CSS](https://tailwindcss.com/docs)
*   [Documentación de Preline UI](https://preline.co/)

---

**Última actualización:** 2024-07-30
**Versión del Documento:** 1.0