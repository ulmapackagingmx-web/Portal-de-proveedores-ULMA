# 📁 Estructura del Proyecto - DataHub Ulma

## 🎯 Descripción General

Sistema web de gestión de facturas y documentos con sistema de permisos jerárquico (Admin → Supervisor → Proveedor). Permite cargar facturas XML, procesarlas automáticamente, gestionar estados de pago y exportar reportes.

---

## 📂 Estructura de Archivos

```
mi-web-service/
├── 📄 main.py                          # Archivo principal de la aplicación
├── 📄 models.py                        # Modelos de base de datos
├── 📄 database.py                      # Configuración de base de datos
├── 📄 security.py                      # Funciones de seguridad y autenticación
├── 📄 permissions.py                   # Sistema de permisos jerárquico
├── 📄 email_processor.py               # Procesador de correos de Outlook
├── 📄 requirements.txt                 # Dependencias de Python
├── 📄 .env.example                     # Ejemplo de variables de entorno
├── 📄 .gitignore                       # Archivos ignorados por Git
├── 📄 render.yaml                      # Configuración para Render
├── 📄 datahub.db                       # Base de datos SQLite (generada automáticamente)
│
├── 📁 routers/                         # Endpoints de la API
│   ├── 📄 uploads.py                   # Endpoints de carga de archivos
│   ├── 📄 documents.py                 # Endpoints de gestión de documentos
│   └── 📄 webhook.py                   # Webhook para Power Automate
│
├── 📁 templates/                       # Plantillas HTML
│   └── 📄 index.html                   # Interfaz web principal
│
├── 📁 uploads/                         # Archivos subidos (PDFs, XMLs)
│   └── (archivos generados dinámicamente)
│
└── 📁 Documentación/
    ├── 📄 USUARIOS_Y_PERMISOS.md       # Guía de usuarios y permisos
    ├── 📄 DEPLOY_GITHUB_RENDER.md      # Guía de despliegue
    ├── 📄 ACTUALIZAR_GITHUB.md         # Guía para actualizar GitHub
    ├── 📄 INTEGRACION_OUTLOOK.md       # Integración con Outlook
    ├── 📄 POWER_AUTOMATE_GUIA.md       # Guía de Power Automate
    ├── 📄 POWER_AUTOMATE_SIMPLE.md     # Versión simplificada
    ├── 📄 CAMBIOS_NUEVOS.md            # Registro de cambios
    └── 📄 ESTRUCTURA_PROYECTO.md       # Este archivo
```

---

## 📄 Descripción Detallada de Archivos

### 🔷 Archivos Principales

#### `main.py`
**Función:** Archivo principal que inicia la aplicación FastAPI.

**Qué hace:**
- Inicializa la aplicación FastAPI
- Configura CORS para permitir peticiones desde cualquier origen
- Crea la base de datos y tablas al iniciar
- Crea usuarios iniciales (admin, supervisores, proveedores)
- Conecta los routers (uploads, documents, webhook)
- Define el endpoint de login (`/token`)
- Sirve la interfaz web en la ruta raíz (`/`)

**Qué puedes modificar:**
```python
# Cambiar usuarios iniciales
DBUser(username="admin", hashed_password=get_password_hash("TU_CONTRASEÑA"), ...)

# Cambiar puerto de ejecución
# En terminal: uvicorn main:app --port 8000

# Agregar nuevos routers
from routers.nuevo_router import router as nuevo_router
app.include_router(nuevo_router)

# Cambiar configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-dominio.com"],  # Especificar dominios
    ...
)
```

---

#### `models.py`
**Función:** Define la estructura de las tablas de la base de datos.

**Qué hace:**
- Define el modelo `DBUser` (usuarios del sistema)
- Define el modelo `DBDocument` (facturas/documentos)
- Establece los campos y tipos de datos
- Configura relaciones entre tablas

**Qué puedes modificar:**
```python
# Agregar nuevos campos a DBDocument
class DBDocument(Base):
    __tablename__ = "documentos"
    # ... campos existentes ...
    nuevo_campo = Column(String, default="")  # Agregar nuevo campo
    
# Agregar nuevos campos a DBUser
class DBUser(Base):
    __tablename__ = "usuarios"
    # ... campos existentes ...
    departamento = Column(String, default="")  # Agregar departamento
    
# Crear nueva tabla
class DBCategoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
```

**⚠️ Importante:** Si modificas los modelos, debes:
1. Borrar `datahub.db`
2. Reiniciar la aplicación para recrear las tablas

---

#### `database.py`
**Función:** Configura la conexión a la base de datos.

**Qué hace:**
- Crea el motor de SQLAlchemy
- Define la sesión de base de datos
- Proporciona la función `get_db()` para obtener sesiones

**Qué puedes modificar:**
```python
# Cambiar a PostgreSQL (para producción)
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datahub.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# Cambiar nombre de archivo SQLite
engine = create_engine("sqlite:///./mi_base_datos.db")

# Habilitar logs de SQL
engine = create_engine(
    "sqlite:///./datahub.db",
    echo=True  # Muestra todas las queries SQL
)
```

---

#### `security.py`
**Función:** Maneja autenticación y seguridad.

**Qué hace:**
- Hashea contraseñas con bcrypt
- Verifica contraseñas
- Valida tokens de autenticación
- Obtiene el usuario actual desde el token

**Qué puedes modificar:**
```python
# Cambiar algoritmo de hash
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Agregar expiración de tokens (requiere JWT)
from datetime import datetime, timedelta
import jwt

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
```

---

#### `permissions.py`
**Función:** Sistema de permisos jerárquico.

**Qué hace:**
- Define quién puede ver qué registros
- Valida permisos de edición
- Valida permisos de eliminación (por estado)
- Valida permisos de autorización
- Valida permisos de pago

**Qué puedes modificar:**
```python
# Agregar nuevo rol
def puede_hacer_algo(username: str, db: Session) -> bool:
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if usuario.role == "gerente":  # Nuevo rol
        return True
    
    return False

# Cambiar lógica de permisos
def puede_eliminar(username: str, registro_usuario: str, estado_pago: str, db: Session) -> bool:
    # Permitir que supervisores eliminen en cualquier estado
    if usuario.role == "supervisor":
        return True  # Sin validar estado
    
    # ... resto de la lógica
```

---

### 🔷 Routers (Endpoints de la API)

#### `routers/uploads.py`
**Función:** Maneja la carga de archivos (XML, Excel, texto).

**Qué hace:**
- Procesa archivos XML de facturas (extrae datos del CFDI)
- Procesa archivos Excel masivos
- Procesa texto/correos para extraer datos
- Crea registros manuales

**Qué puedes modificar:**
```python
# Cambiar campos extraídos del XML
def extraer_datos_xml(xml_content):
    # Agregar nuevos campos
    uso_cfdi = root.find('.//{http://www.sat.gob.mx/cfd/4}Receptor').get('UsoCFDI', '')
    
    return {
        # ... campos existentes ...
        'uso_cfdi': uso_cfdi,  # Nuevo campo
    }

# Cambiar validación de Excel
required_columns = ['RFC', 'Nombre', 'Total', 'MiNuevoCampo']

# Cambiar expresiones regulares para texto
rfc_match = re.search(r'RFC:\s*([A-Z0-9]{12,13})', texto)
```

---

#### `routers/documents.py`
**Función:** Gestiona documentos (editar, eliminar, cambiar estado).

**Qué hace:**
- Edita documentos existentes
- Elimina documentos (con validación de permisos)
- Cambia estados (Pendiente → Autorizado → Pagado)
- Rechaza registros
- Sube PDFs de facturas y comprobantes de pago
- Exporta a Excel
- Resetea la base de datos (solo admin)

**Qué puedes modificar:**
```python
# Agregar nuevo estado
@router.put("/marcar-urgente/{doc_id}")
def marcar_urgente(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    doc.urgente = True  # Nuevo campo
    db.commit()
    return {"status": "ok"}

# Cambiar campos en edición
@router.put("/documentos/{doc_id}")
def editar_doc(doc_id: int, datos: dict = Body(...), ...):
    doc.nuevo_campo = datos.get('nuevo_campo', doc.nuevo_campo)
    
# Agregar validaciones
if doc.total > 100000:
    raise HTTPException(status_code=400, detail="Monto muy alto")
```

---

#### `routers/webhook.py`
**Función:** Recibe datos desde Power Automate.

**Qué hace:**
- Endpoint POST que recibe JSON desde Power Automate
- Procesa datos de correos de Outlook
- Crea registros automáticamente

**Qué puedes modificar:**
```python
# Cambiar estructura de datos esperada
@router.post("/webhook/outlook")
async def recibir_correo(datos: dict = Body(...)):
    # Agregar nuevos campos
    categoria = datos.get('categoria', 'General')
    
    # Cambiar validaciones
    if not datos.get('asunto'):
        raise HTTPException(status_code=400, detail="Falta asunto")
```

---

### 🔷 Frontend

#### `templates/index.html`
**Función:** Interfaz web completa del sistema.

**Qué hace:**
- Pantalla de login
- Dashboard con tabla de registros
- Formularios de carga (XML, Excel, texto, manual)
- Modales de edición
- Filtros y búsqueda
- Visualización de estados (semáforo)
- Botones de acción según permisos

**Qué puedes modificar:**
```javascript
// Cambiar colores
.ulma-red { background-color: #TU_COLOR; }

// Agregar nuevos filtros
<select id="filtro-estado">
    <option value="">Todos los Estados</option>
    <option value="Pendiente">Pendiente</option>
    <option value="Autorizado">Autorizado</option>
</select>

// Cambiar subcatálogos
const subcatalogos = {
    'Administración': ['SERVICIOS', 'CAPACITACION', 'TU_NUEVO_SUBCATALOGO'],
    'TuNuevoCentro': ['SUBCATALOGO1', 'SUBCATALOGO2']
};

// Agregar nuevas columnas a la tabla
<th>Tu Nueva Columna</th>
// ...
<td>${row.tu_nuevo_campo}</td>

// Cambiar validación de porcentajes
if (Math.abs(totalPorcentaje - 100) > 0.01) {
    // Cambiar a permitir menos del 100%
    if (totalPorcentaje > 100) {
        alert('No puede superar 100%');
    }
}
```

---

### 🔷 Archivos de Configuración

#### `requirements.txt`
**Función:** Lista de dependencias de Python.

**Qué hace:**
- Define las librerías necesarias
- Especifica versiones (opcional)

**Qué puedes modificar:**
```txt
# Agregar nuevas dependencias
fastapi
uvicorn
sqlalchemy
requests  # Nueva librería
pillow    # Para procesar imágenes
```

Después de modificar:
```bash
pip install -r requirements.txt
```

---

#### `.env.example`
**Función:** Ejemplo de variables de entorno.

**Qué hace:**
- Muestra qué variables de entorno se necesitan
- No contiene valores reales (es solo ejemplo)

**Qué puedes modificar:**
```env
# Agregar nuevas variables
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=tu_clave_secreta_aqui
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Para usar:
1. Copia `.env.example` a `.env`
2. Llena con valores reales
3. Carga en tu código:
```python
import os
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")
```

---

#### `.gitignore`
**Función:** Archivos que Git debe ignorar.

**Qué hace:**
- Evita subir archivos sensibles a GitHub
- Evita subir archivos generados

**Qué puedes modificar:**
```gitignore
# Agregar más patrones
*.db
*.log
.env
mi_carpeta_secreta/
*.backup
```

---

#### `render.yaml`
**Función:** Configuración para despliegue en Render.

**Qué hace:**
- Define cómo construir la aplicación
- Define cómo iniciar la aplicación
- Define variables de entorno

**Qué puedes modificar:**
```yaml
services:
  - type: web
    name: mi-app
    env: python
    buildCommand: pip install -r requirements.txt && python setup.py
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0  # Cambiar versión de Python
      - key: DATABASE_URL
        sync: false
```

---

## 🔧 Modificaciones Comunes

### 1. Agregar un Nuevo Campo a Documentos

**Paso 1:** Modificar `models.py`
```python
class DBDocument(Base):
    # ... campos existentes ...
    prioridad = Column(String, default="Normal")
```

**Paso 2:** Borrar `datahub.db` y reiniciar

**Paso 3:** Modificar `routers/uploads.py` para capturar el campo
```python
nuevo_doc = DBDocument(
    # ... campos existentes ...
    prioridad=datos.get('prioridad', 'Normal')
)
```

**Paso 4:** Modificar `templates/index.html` para mostrar el campo
```html
<td>${row.prioridad}</td>
```

---

### 2. Agregar un Nuevo Rol

**Paso 1:** Modificar `models.py`
```python
# No requiere cambios, el campo 'role' es String
```

**Paso 2:** Modificar `main.py` para crear usuarios con el nuevo rol
```python
DBUser(username="gerente1", hashed_password=get_password_hash("pass"), role="gerente")
```

**Paso 3:** Modificar `permissions.py` para definir permisos
```python
def puede_hacer_algo(username: str, db: Session) -> bool:
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    return usuario.role in ["admin", "gerente"]
```

**Paso 4:** Modificar `templates/index.html` para mostrar icono
```javascript
document.getElementById("user-greeting").innerText = 
    (userRole === 'admin' ? "👑 " : 
     userRole === 'gerente' ? "💼 " :
     userRole === 'supervisor' ? "👔 " : "👤 ") + username;
```

---

### 3. Cambiar Centros de Costo

**Modificar `templates/index.html`:**
```javascript
const subcatalogos = {
    'Producción': ['MAQUINARIA', 'MANTENIMIENTO'],
    'Ventas': ['COMISIONES', 'PUBLICIDAD'],
    'TuNuevoCentro': ['SUBCATALOGO1', 'SUBCATALOGO2']
};
```

---

### 4. Agregar Validación de Monto

**Modificar `routers/uploads.py`:**
```python
@router.post("/subir-manual")
async def subir_manual(datos: dict = Body(...), ...):
    total = datos.get('total', 0)
    
    # Validar monto máximo
    if total > 50000:
        raise HTTPException(
            status_code=400,
            detail="El monto no puede superar $50,000"
        )
    
    # ... resto del código
```

---

### 5. Cambiar Estados Disponibles

**Modificar `routers/documents.py`:**
```python
@router.put("/avanzar-estado/{doc_id}")
def avanzar_estado(doc_id: int, ...):
    if doc.estado_pago == "Pendiente":
        doc.estado_pago = "En Revisión"  # Nuevo estado
    elif doc.estado_pago == "En Revisión":
        doc.estado_pago = "Autorizado"
    # ... etc
```

**Modificar `templates/index.html`:**
```javascript
if (row.estado_pago === 'En Revisión') {
    semaforoHTML = `
        <div class="w-5 h-5 rounded-full bg-orange-500"></div>
        <span>En Revisión</span>
    `;
}
```

---

## 🚀 Comandos Útiles

### Desarrollo Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python3 -m uvicorn main:app --reload --port 8001

# Ver logs en tiempo real
python3 -m uvicorn main:app --reload --port 8001 --log-level debug

# Borrar base de datos
rm datahub.db
```

### Git
```bash
# Inicializar repositorio
git init

# Ver cambios
git status
git diff

# Agregar cambios
git add .
git commit -m "Descripción del cambio"

# Subir a GitHub
git push origin main
```

### Base de Datos
```bash
# Conectar a SQLite
sqlite3 datahub.db

# Ver tablas
.tables

# Ver estructura de tabla
.schema documentos

# Ver datos
SELECT * FROM documentos;

# Salir
.quit
```

---

## 📊 Flujo de Datos

```
1. Usuario carga XML
   └─> routers/uploads.py
       └─> Extrae datos del XML
           └─> Crea DBDocument en database
               └─> Retorna success
                   └─> Frontend actualiza tabla

2. Usuario edita registro
   └─> templates/index.html (modal de edición)
       └─> routers/documents.py (PUT /documentos/{id})
           └─> permissions.py (valida permisos)
               └─> Actualiza DBDocument
                   └─> Retorna success

3. Supervisor autoriza
   └─> templates/index.html (botón Autorizar)
       └─> routers/documents.py (PUT /avanzar-estado/{id})
           └─> permissions.py (valida que sea supervisor)
               └─> Cambia estado_pago a "Autorizado"
                   └─> Frontend actualiza semáforo
```

---

## 🔐 Seguridad

### Contraseñas
- Se hashean con bcrypt antes de guardar
- Nunca se almacenan en texto plano
- Se validan con `verify_password()`

### Autenticación
- Token Bearer en header `Authorization`
- Se valida en cada endpoint con `Depends(get_current_user)`
- Si el token es inválido, retorna 401 Unauthorized

### Permisos
- Se validan en cada acción
- Sistema jerárquico: Admin > Supervisor > Proveedor
- Validación por estado para eliminación

---

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "Table already exists"
```bash
rm datahub.db
# Reiniciar aplicación
```

### Error: "Permission denied"
```bash
# Verificar que el usuario tenga permisos
# Revisar permissions.py
# Revisar que el token sea correcto
```

### Frontend no actualiza
```bash
# Limpiar caché del navegador
# Ctrl + Shift + R (forzar recarga)
# Verificar consola del navegador (F12)
```

---

## 📞 Soporte

Para modificaciones avanzadas o problemas:
1. Revisa los logs del servidor
2. Revisa la consola del navegador (F12)
3. Verifica la documentación de FastAPI: https://fastapi.tiangolo.com
4. Verifica la documentación de SQLAlchemy: https://www.sqlalchemy.org

---

**Última actualización:** 27/04/2026
**Versión:** 4.4
