🤖 INSTRUCCIONES DE SISTEMA Y ARQUITECTURA (SYSTEM PROMPT)

Proyecto: SaaS DataHub Ulma - V9+

Última Actualización: 25/05/2026
Audiencia Objetivo: Agente de IA Autónomo (Cline / Gemini) y Desarrolladores Full-Stack.

🎯 0. DIRECTRICES FUNDAMENTALES PARA EL AGENTE IA (CLINE)

ALTO AHÍ, AGENTE IA: Antes de modificar, crear o refactorizar cualquier archivo en este entorno de trabajo, DEBES leer y asimilar completamente este documento. Este archivo es tu "Fuente Única de la Verdad" (Single Source of Truth).

Cero Alucinaciones: No asumas estructuras de base de datos ni clases CSS que no estén definidas aquí.

Idioma: Todo el código, comentarios, respuestas de API, y alertas del frontend deben estar estrictamente en Español.

Manejo de Errores: Todos los endpoints de FastAPI deben incluir bloques try/except y devolver HTTPException con códigos de estado semánticamente correctos (400, 401, 403, 404, 500).

Acoplamiento: Mantén el frontend en index.html (o archivos modulares si la arquitectura lo dicta) separado de la lógica de enrutamiento del backend.

🛠️ 1. STACK TECNOLÓGICO Y ESTÁNDARES DE CÓDIGO

1.1 Backend (Python 3.10+)

Framework: FastAPI. Todos los endpoints deben estar bajo el prefijo /api/v1/.

ORM: SQLAlchemy 2.0+ usando declarative_base.

Base de Datos: PostgreSQL (Migración final desde SQLite).

Seguridad: Passwords hasheados con bcrypt. Autenticación con OAuth2PasswordBearer (Tokens JWT).

1.2 Frontend (UI/UX)

Estructura Base: HTML5 semántico.

Framework CSS: Tailwind CSS (v3+).

Biblioteca de Componentes: Preline UI (OBLIGATORIO).

Directiva: Cline, no intentes crear modales o dropdowns desde cero. Debes usar los atributos de datos de Preline como data-hs-overlay, data-hs-tab, hs-dropdown.

Branding Ulma: * Fondo de pantallas y paneles: Colores claros corporativos (ej. bg-slate-50).

Botones principales: Azules corporativos (bg-blue-600 hover:bg-blue-700 text-white).

Logotipo: Utilizar ÚNICAMENTE el snippet SVG oficial de Ulma proporcionado en la cabecera/navbar. Prohibido usar etiquetas <img> a URLs externas.

Interactividad: JavaScript Vanilla moderno (ES6+) con fetch() API para consumos asíncronos. Uso intensivo de manipulación del DOM guiada por variables guardadas en localStorage.

1.3 Automatización y Notificaciones Externa

Regla de Oro: El backend en Python/FastAPI TIENE PROHIBIDO ejecutar rutinas SMTP directas para notificar a proveedores (por historial de bloqueos y políticas de TI).

Solución: Cualquier cambio de estado (ej. "Rechazado" a "Pagado") debe limitarse a actualizar la BD. Las notificaciones reales hacia el exterior las gestionará Power Automate leyendo los cambios en la BD o recibiendo un Webhook ligero disparado desde FastAPI.

🗄️ 2. ESQUEMAS DE BASE DE DATOS (SQLAlchemy Models)

Cline, cuando modifiques models.py, debes adherirte a esta estructura exacta. Presta atención a los nuevos campos y reglas empresariales.

2.1 Usuarios (DBUser)

Gestiona roles estrictos y control jerárquico.

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # Ej: admin, usuario 1, usuario a
    hashed_password = Column(String)
    role = Column(String) # Valores ESTRICTOS: "admin", "supervisor", "proveedor"
    subordinados = Column(String, default="") # IDs separados por coma (ej. "2,4,5")


2.2 Documentos (DBDocument)

Corazón del sistema. Incorpora los nuevos campos requeridos.

class DBDocument(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String) # Factura, Nota de Crédito, etc.
    remitente_rfc = Column(String, index=True)
    nombre = Column(String)
    uuid_folio = Column(String, unique=True, index=True)
    total = Column(Float)
    fecha_emision = Column(Date)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    subido_por = Column(Integer, ForeignKey("users.id"))
    
    # Costos y Pagos
    centro_costo = Column(String)
    subcatalogo_centro = Column(String)
    porcentaje_centro = Column(Float)
    porcentaje_pago = Column(Float, nullable=True) # NUEVO: Campo obligatorio en edición
    fecha_pago = Column(Date, nullable=True)
    estado_pago = Column(String, default="Pendiente") # Pendiente, Autorizado, Pagado, Rechazado
    fecha_estimada_pago = Column(Date, nullable=True) # RESTRINGIDO: Solo Admin puede editar/ver
    
    # Archivos
    comprobante_pdf = Column(String, nullable=True)
    comprobante_pago_pdf = Column(String, nullable=True)
    otros_documentos_pdf = Column(String, nullable=True)


2.3 Proveedores (DBProvider)

Implementa las nuevas lógicas de expediente (Checklist).

class DBProvider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    nombre_proveedor = Column(String)
    rfc_proveedor = Column(String, unique=True, index=True)
    creado_por = Column(Integer, ForeignKey("users.id")) # CRÍTICO para filtros de Supervisor
    
    # Bancarios
    banco = Column(String)
    numero_cuenta_clabe = Column(String)
    tipo_operacion = Column(String)
    validacion_bancaria = Column(Boolean, default=False)
    
    # Expediente (Checklist)
    has_comprobante_domicilio = Column(Boolean, default=False) # NUEVO
    has_opinion_cumplimiento = Column(Boolean, default=False) # NUEVO
    
    # Extra
    email_contacto = Column(String)
    campo_libre = Column(String, nullable=True)


🔒 3. MATRIZ DE PERMISOS, RUTEO Y REGLAS DE NEGOCIO (RBAC)

El archivo permissions.py y los routers correspondientes DEBEN forzar estas reglas. En el frontend, el DOM debe adaptarse leyendo el rol del localStorage.

3.1 Nivel 1: Administrador (role == "admin")

Visibilidad: Ve todos los registros y todos los proveedores.

Acciones BD: Crea, lee, actualiza y elimina sin restricciones.

Regla de UI Especial 1 (Fecha Estimada): Es el ÚNICO rol que puede ver e interactuar con el input <input type="date" id="fecha_estimada_pago" ...> en el modal de edición de documentos de Preline UI.

Proveedores: Tiene acceso total a la pestaña "Proveedores".

3.2 Nivel 2: Supervisor (role == "supervisor")

Visibilidad de Documentos: Ve documentos donde subido_por == su_propio_id O subido_por IN (sus_subordinados).

Acciones Documentos: Puede editar, pero NO autoriza sus propios documentos, solo los de sus subordinados.

Regla de UI Especial 1 (Fecha Estimada): El campo fecha_estimada_pago DEBE estar oculto (display: none o hidden en Tailwind) o en estado disabled al abrir el modal de edición. El backend rechazará silenciosamente cualquier intento de un supervisor de actualizar este campo.

Regla de UI Especial 2 (Proveedores): Acceso parcial. El endpoint /api/providers DEBE filtrar la respuesta y retornar únicamente aquellos donde creado_por == supervisor.id.

3.3 Nivel 3: Proveedor / Usuario Base (role == "proveedor" o general como "usuario 1")

Visibilidad de Documentos: Ve SOLAMENTE donde subido_por == su_propio_id.

Acciones Documentos: Solo puede editar y borrar si el estado es "Pendiente". No puede autorizar.

Regla de UI Especial 1 (Fecha Estimada): Igual que supervisor. El input fecha_estimada_pago es INVISIBLE o de solo lectura estricta. Un "usuario a" jamás llena cuándo se le va a pagar.

Regla de UI Especial 2 (Proveedores): BLOQUEO TOTAL. La pestaña / menú de navegación hacia "Proveedores" no se renderiza en el HTML para este rol. Si intentan forzar la URL al endpoint, el servidor devolverá 403 Forbidden.

🖥️ 4. INSTRUCCIONES ESPECÍFICAS DE IMPLEMENTACIÓN FRONTEND (index.html y JS)

Cline, estas son las instrucciones paso a paso para construir la UI requerida usando Tailwind y Preline:

4.1 Implementación del Campo: "Porcentaje de Pago"

Modal de Edición (Preline UI): Dentro del <div id="edit-modal" class="hs-overlay ...">, localiza el formulario de edición.

HTML a inyectar:

<div class="mb-4">
  <label for="edit_porcentaje_pago" class="block text-sm font-medium text-gray-700 mb-2">Porcentaje de Pago (%) <span class="text-red-500">*</span></label>
  <input type="number" step="0.01" min="0" max="100" id="edit_porcentaje_pago" name="edit_porcentaje_pago" class="py-3 px-4 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none" required placeholder="Ej: 50.00">
</div>


JavaScript: En la función saveEdit(), asegúrate de capturar document.getElementById('edit_porcentaje_pago').value y enviarlo en el payload JSON hacia /api/v1/documents/{id}.

4.2 Implementación Restringida: "Fecha Estimada de Pago"

HTML a inyectar (en modal de edición):

<div id="container_fecha_estimada" class="mb-4 hidden"> <!-- Oculto por defecto -->
  <label for="edit_fecha_estimada_pago" class="block text-sm font-medium text-gray-700 mb-2">Fecha Estimada de Pago (Solo Admin)</label>
  <input type="date" id="edit_fecha_estimada_pago" class="py-3 px-4 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500">
</div>


JavaScript de Control: Al momento de llamar a la función openEditModal(docId) o al cargar el DOM principal:

const userRole = localStorage.getItem('role');
const containerFecha = document.getElementById('container_fecha_estimada');

if (userRole === 'admin') {
    containerFecha.classList.remove('hidden');
} else {
    containerFecha.classList.add('hidden');
    // Asegurarse de que el valor se limpie para no enviar basura en el PUT
    document.getElementById('edit_fecha_estimada_pago').value = ''; 
}


4.3 Implementación Visual: Checklist de Expediente de Proveedores

Vista de Tabla de Proveedores: Al crear la tabla de Listado de Proveedores, la columna "Expediente" no debe ser texto plano. Debe usar componentes visuales (Badges de Preline).

Lógica de Renderizado en JS (renderProvidersTable()):

function createChecklistBadge(hasDocument, label) {
    if(hasDocument) {
        // Palomita Verde (Preline / Tailwind)
        return `<span class="inline-flex items-center gap-x-1.5 py-1.5 px-3 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
                  <svg class="flex-shrink-0 size-3" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  ${label}
                </span>`;
    } else {
        // Faltante / Rojo
        return `<span class="inline-flex items-center gap-x-1.5 py-1.5 px-3 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  <svg class="flex-shrink-0 size-3" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  Falta: ${label}
                </span>`;
    }
}

// Al iterar sobre el array de proveedores desde el backend:
const htmlExpediente = `
    <div class="flex flex-col gap-2">
        ${createChecklistBadge(proveedor.has_comprobante_domicilio, "Comprobante Domicilio")}
        ${createChecklistBadge(proveedor.has_opinion_cumplimiento, "Opinión Cumplimiento")}
    </div>
`;
// ... inyectar en el <td> correspondiente


📡 5. REGLAS DE ENRUTAMIENTO Y BACKEND (FastAPI Routers)

5.1 Endpoint de Edición (PUT /api/v1/documents/{id})

Cline, debes implementar validación defensiva en el endpoint.

Validación de porcentaje_pago: Si el payload incluye este campo, valida que sea un float entre 0 y 100.

Protección de fecha_estimada_pago: ```python
@router.put("/{doc_id}")
def update_document(doc_id: int, payload: DocumentUpdateSchema, current_user: DBUser = Depends(get_current_user)):
# ... buscar doc ...
if payload.fecha_estimada_pago is not None:
if current_user.role != "admin":
# Ignorar silenciosamente o levantar error, pero NUNCA guardar si no es admin
delattr(payload, 'fecha_estimada_pago')
# ... proceder con guardado




5.2 Endpoints de Proveedores (GET /api/v1/providers)

Cline, aplica la lógica de filtrado jerárquico.

Si current_user.role == "admin" -> return db.query(DBProvider).all()

Si current_user.role == "supervisor" -> return db.query(DBProvider).filter(DBProvider.creado_por == current_user.id).all()

Si current_user.role == "proveedor" -> raise HTTPException(status_code=403, detail="Acceso denegado a directorio de proveedores")

🔄 6. FLUJO DE PROCESAMIENTO AUTOMÁTICO (email_processor.py)

El script en background usa exchangelib.

Filtra buzón INBOX buscando [DATAHUB].

Extrae el XML, parsea nodos de CFDI (TimbreFiscalDigital, UUID, Emisor, Receptor).

Realiza Regex en el cuerpo del correo buscando variables inyectadas (Centros de costo, subcatálogos, distribución de porcentajes).

Aplica lógica de que los centros de costo sumen 100%.

Acción Final: Guarda el registro en la BD en estado Pendiente. Mueve el correo procesado a una subcarpeta para evitar bucles.

🤖 7. INSTRUCCIÓN FINAL PARA CLINE (EJECUCIÓN INMEDIATA)

Has leído la documentación. Tu conocimiento sobre el comportamiento esperado de este SaaS es total.
A partir de este momento, cada vez que el usuario te solicite un cambio o la construcción de una característica:

Valida mentalmente contra las reglas RBAC de este documento.

Utiliza estrictamente clases y modales de Preline UI para la interfaz.

Asegura que los campos como porcentaje_pago no se te olviden en los esquemas Pydantic y en los formularios HTML.

Recuerda que un usuario ordinario no sabe, ni debe saber, la fecha estimada de su pago, ni tiene acceso a la agenda de proveedores.

¡Fin del Documento de Arquitectura! Prepárate para codificar.