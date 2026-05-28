# Arquitectura y Funcionamiento de Mi Web Service V9

Este documento explica de manera detallada y técnica cómo funciona el proyecto `mi-web-serviceV9`. Está diseñado para ayudar a desarrolladores a entender la arquitectura, el flujo de datos, los componentes y la lógica de negocio implementada.

## 1. Visión General del Proyecto

`mi-web-serviceV9` es un sistema backend robusto desarrollado en **Python** utilizando **FastAPI**. El propósito principal del sistema es la gestión de documentos fiscales (XMLs y PDFs), la administración de proveedores y la automatización de la captura de datos a través de procesamiento de correos electrónicos. 

### Tecnologías Principales
*   **FastAPI**: Framework web para la construcción de las APIs RESTful, elegido por su alto rendimiento y generación automática de documentación (Swagger/OpenAPI).
*   **SQLAlchemy**: ORM (Object-Relational Mapping) utilizado para interactuar con la base de datos de manera orientada a objetos.
*   **SQLite**: Base de datos ligera utilizada para almacenar la información de usuarios, documentos y proveedores (configurado en `datahub.db`).
*   **exchangelib**: Librería utilizada para la conexión y lectura de buzones de correo en servidores Microsoft Exchange (Office 365) para procesar archivos adjuntos automáticamente.
*   **bcrypt**: Para el hash seguro de contraseñas de usuarios.

## 2. Estructura de Datos (Modelos)

El sistema define la estructura de la base de datos en `models.py` utilizando `declarative_base` de SQLAlchemy.

### 2.1 Usuarios (`DBUser`)
Gestiona el acceso al sistema. Un usuario tiene los siguientes atributos:
*   `id`, `username`, `hashed_password`
*   `role`: Define el nivel de acceso. Puede ser `proveedor`, `supervisor`, o `admin`.
*   `subordinados`: Cadena de texto (separada por comas) que define qué usuarios están a cargo de un supervisor. Esto es clave para el sistema jerárquico de permisos.

### 2.2 Documentos (`DBDocument`)
Es el núcleo de los datos. Almacena toda la información extraída de los comprobantes fiscales y los metadatos asociados.
*   Datos básicos: `id`, `tipo`, `remitente_rfc`, `nombre`, `uuid_folio`, `total`, `fecha_emision`, `fecha_registro`, `subido_por`.
*   Gestión de costos: `centro_costo`, `subcatalogo_centro`, `porcentaje_centro`.
*   Gestión de pagos: `fecha_pago`, `estado_pago` (Pendiente, Autorizado, Pagado), `fecha_estimada_pago`.
*   Archivos: Rutas locales a archivos subidos como `comprobante_pdf`, `comprobante_pago_pdf`, `otros_documentos_pdf`.
*   Datos fiscales (XML): `regimen_fiscal_emisor`, `traslados`, `retenciones`, `uso_cfdi`, `forma_pago`, `metodo_pago`, `clave_sat`, `descripcion_concepto`, `moneda`.

### 2.3 Historial (`DBHistory`)
Permite mantener una traza de auditoría de los cambios de estado en un documento. Guarda `document_id`, la `accion` (Creado, Autorizado, Rechazado, Pagado, etc.), el `motivo`, el `usuario` que hizo el cambio y la `fecha`.

### 2.4 Proveedores (`DBProvider`)
Catálogo de proveedores que almacena información fiscal y bancaria.
*   Datos de identificación: `nombre_proveedor`, `rfc_proveedor` (único).
*   Datos bancarios: `banco`, `numero_cuenta_clabe`, `tipo_operacion`.
*   Estados de validación: `validacion_bancaria`, `validacion_expediente` (booleanos).
*   Datos extra: `expediente`, `campo_libre`, `email_contacto`.

## 3. Seguridad y Sistema de Permisos

El sistema implementa un modelo de control de acceso basado en roles (RBAC) jerárquico, implementado en `security.py` y `permissions.py`.

### Autenticación (`security.py`)
Utiliza `OAuth2PasswordBearer` de FastAPI. Actualmente, la validación del token es simplificada (utiliza el `username` como token para propósitos de demostración o MVP), pero la arquitectura está preparada para integrarse con JWT reales. La encriptación de contraseñas se hace con `bcrypt` (`verify_password`, `get_password_hash`).

### Autorización y Jerarquía (`permissions.py`)
La lógica de negocio define estrictas reglas basadas en el rol del usuario:

1.  **Proveedor (Nivel Base):**
    *   Solo puede ver, editar y eliminar sus *propios* documentos.
    *   No puede autorizar documentos ni ver el listado general de proveedores.
2.  **Supervisor (Nivel Medio):**
    *   Puede ver y editar sus documentos Y los de los usuarios listados en su campo `subordinados`.
    *   Puede autorizar o rechazar los documentos de sus subordinados (pero no los propios).
    *   Puede ver el catálogo de proveedores.
3.  **Admin (Nivel Superior):**
    *   Acceso irrestricto. Puede ver, editar, eliminar y autorizar cualquier documento.
    *   Es el único rol que puede subir comprobantes de pago.
    *   Puede gestionar por completo el catálogo de proveedores (crear, editar, eliminar).

## 4. Procesamiento Automático de Correos (`email_processor.py`)

Una de las funcionalidades más avanzadas es la ingesta de documentos vía correo electrónico.
1.  **Conexión Exchange:** Se conecta a un servidor de Microsoft Exchange utilizando `exchangelib` y las credenciales definidas en las variables de entorno (`.env`).
2.  **Filtro:** Busca correos no leídos que contengan la etiqueta `[DATAHUB]` en el asunto.
3.  **Extracción de Adjuntos:** Descarga los archivos `.xml` y `.pdf` adjuntos.
4.  **Parseo de XML:** Lee el archivo XML utilizando `xml.etree.ElementTree` y extrae la información fiscal del nodo del Emisor (RFC, Nombre), TimbreFiscalDigital (UUID), Receptor (Uso CFDI), y los Conceptos (Clave SAT, Descripción), así como el total, la moneda, forma y método de pago.
5.  **Parseo del Cuerpo del Correo (Expresiones Regulares):** Busca metadatos inyectados en el cuerpo del correo mediante `re` (Regex). Extrae información como la fecha de pago esperada y la distribución por Centros de Costo y Subcatálogos con sus respectivos porcentajes.
6.  **Persistencia:** Si todas las validaciones pasan (como que los porcentajes sumen 100%), se crea un nuevo registro `DBDocument` en la base de datos, se asocian los archivos físicos guardados en la carpeta `uploads/` y se marca el correo como leído.

## 5. Arquitectura de API (Routers)

La API está modularizada utilizando `APIRouter` de FastAPI. Los endpoints están distribuidos en la carpeta `routers/`:

*   **`uploads.py`**: Maneja la recepción manual de archivos y la lógica de subida desde el frontend web.
*   **`documents.py`**: Contiene los endpoints CRUD para la gestión, filtrado y modificación del estado de los documentos (`DBDocument`) y sus historiales (`DBHistory`).
*   **`providers.py`**: Endpoints para gestionar el catálogo de proveedores (`DBProvider`), aplicando estrictas reglas de validación de permisos.
*   **`webhook.py`**: Punto de entrada para posibles integraciones de terceros o eventos externos.

## 6. Inicialización y Middleware (`main.py`)

El punto de entrada de la aplicación (`main.py`) se encarga de:
1.  **Montaje de Rutas y Middleware:** Configura CORS para permitir peticiones del frontend y monta una ruta estática (`/uploads`) para servir los archivos PDF y XML almacenados localmente.
2.  **Base de Datos y Usuarios Iniciales:** Al arrancar (mediante `@app.on_event("startup")`), el sistema verifica si la base de datos está vacía. Si es así, crea automáticamente la jerarquía de roles inicial (Admin, Supervisores y Proveedores de prueba).
3.  **Frontend Básico:** Expone un endpoint raíz (`/`) que devuelve un archivo HTML (`templates/index.html`) que funciona como cliente ligero de la API.
4.  **Autenticación de Acceso:** Provee el endpoint `/token` para procesar inicios de sesión mediante el estándar `OAuth2PasswordRequestForm`.

---
*Fin del documento técnico.*