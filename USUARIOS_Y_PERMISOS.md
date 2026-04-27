# 👥 Usuarios y Permisos - DataHub Ulma

## 📋 Lista de Usuarios Creados

### 👑 Administrador
- **Usuario:** `admin`
- **Contraseña:** `admin123`
- **Rol:** Administrador
- **Permisos:**
  - ✅ Ver todos los registros de todos los usuarios
  - ✅ Crear, editar y eliminar cualquier registro
  - ✅ Autorizar y revertir estados de pago
  - ✅ Subir facturas y comprobantes de pago
  - ✅ Exportar a Excel
  - ✅ Resetear base de datos
  - ✅ Acceso total al sistema

---

### 👔 Supervisores

#### Supervisor 1
- **Usuario:** `usuario1`
- **Contraseña:** `super123`
- **Rol:** Supervisor
- **Subordinados:** usuarioA, usuarioB
- **Permisos:**
  - ✅ Ver sus propios registros + registros de usuarioA y usuarioB
  - ✅ Crear, editar sus registros y los de sus subordinados
  - ✅ Eliminar registros de subordinados (solo si están en Pendiente)
  - ✅ Eliminar sus propios registros (solo si están en Pendiente)
  - ✅ Autorizar registros de subordinados (Pendiente → Autorizado)
  - ✅ Rechazar registros de subordinados (Pendiente → Rechazado)
  - ✅ Subir comprobantes de pago para subordinados (Autorizado → Pagado)
  - ✅ Revertir estados de subordinados (Pagado → Autorizado → Pendiente)
  - ✅ Exportar a Excel (sus registros + subordinados)
  - ❌ NO puede ver registros de otros supervisores ni sus subordinados

#### Supervisor 2
- **Usuario:** `usuario2`
- **Contraseña:** `super123`
- **Rol:** Supervisor
- **Subordinados:** usuarioC, usuarioD
- **Permisos:**
  - ✅ Ver sus propios registros + registros de usuarioC y usuarioD
  - ✅ Crear, editar sus registros y los de sus subordinados
  - ✅ Eliminar registros de subordinados (solo si están en Pendiente)
  - ✅ Eliminar sus propios registros (solo si están en Pendiente)
  - ✅ Autorizar registros de subordinados (Pendiente → Autorizado)
  - ✅ Rechazar registros de subordinados (Pendiente → Rechazado)
  - ✅ Subir comprobantes de pago para subordinados (Autorizado → Pagado)
  - ✅ Revertir estados de subordinados (Pagado → Autorizado → Pendiente)
  - ✅ Exportar a Excel (sus registros + subordinados)
  - ❌ NO puede ver registros de otros supervisores ni sus subordinados

---

### 👤 Proveedores (Usuarios Básicos)

#### Proveedor A
- **Usuario:** `usuarioA`
- **Contraseña:** `pass123`
- **Rol:** Proveedor
- **Supervisor:** usuario1
- **Permisos:**
  - ✅ Ver solo sus propios registros
  - ✅ Crear nuevos registros
  - ✅ Editar solo sus propios registros
  - ✅ Subir facturas PDF para sus registros
  - ✅ Eliminar sus registros (solo si están en estado "Rechazado")
  - ❌ NO puede autorizar/cambiar estados
  - ❌ NO puede subir comprobantes de pago
  - ❌ NO puede exportar a Excel

#### Proveedor B
- **Usuario:** `usuarioB`
- **Contraseña:** `pass123`
- **Rol:** Proveedor
- **Supervisor:** usuario1
- **Permisos:** (Iguales a usuarioA)

#### Proveedor C
- **Usuario:** `usuarioC`
- **Contraseña:** `pass123`
- **Rol:** Proveedor
- **Supervisor:** usuario2
- **Permisos:** (Iguales a usuarioA)

#### Proveedor D
- **Usuario:** `usuarioD`
- **Contraseña:** `pass123`
- **Rol:** Proveedor
- **Supervisor:** usuario2
- **Permisos:** (Iguales a usuarioA)

---

## 🔐 Jerarquía de Permisos

```
┌─────────────────────────────────────────┐
│           👑 ADMIN                      │
│   (Ve y controla TODO)                  │
│   - usuario1, usuario2                  │
│   - usuarioA, usuarioB, usuarioC, usuarioD │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│  👔 usuario1   │    │  👔 usuario2    │
│  (Supervisor)  │    │  (Supervisor)   │
│                │    │                 │
│  Subordinados: │    │  Subordinados:  │
│  - usuarioA    │    │  - usuarioC     │
│  - usuarioB    │    │  - usuarioD     │
└────────────────┘    └─────────────────┘
        │                       │
    ┌───┴───┐             ┌────┴────┐
    │       │             │         │
┌───▼──┐ ┌──▼───┐    ┌───▼──┐ ┌───▼──┐
│👤 A  │ │👤 B  │    │👤 C  │ │👤 D  │
│Prov. │ │Prov. │    │Prov. │ │Prov. │
└──────┘ └──────┘    └──────┘ └──────┘
```

---

## 📊 Matriz de Permisos

| Acción | Proveedor | Supervisor | Admin |
|--------|-----------|------------|-------|
| Ver propios registros | ✅ | ✅ | ✅ |
| Ver registros de subordinados | ❌ | ✅ | ✅ |
| Ver todos los registros | ❌ | ❌ | ✅ |
| Crear registros | ✅ | ✅ | ✅ |
| Editar propios registros | ✅ | ✅ | ✅ |
| Editar registros de subordinados | ❌ | ✅ | ✅ |
| Eliminar propios registros | ✅ (si Rechazado) | ✅ (si Pendiente) | ✅ (siempre) |
| Eliminar registros de subordinados | ❌ | ✅ (si Pendiente) | ✅ (siempre) |
| Autorizar/Rechazar estado | ❌ | ✅ (subordinados) | ✅ (todos) |
| Subir factura PDF | ✅ (propios) | ✅ (propios + subordinados) | ✅ (todos) |
| Subir comprobante de pago | ❌ | ✅ (subordinados) | ✅ (todos) |
| Exportar a Excel | ❌ | ✅ | ✅ |
| Reset BD | ❌ | ❌ | ✅ |

---

## 🎯 Casos de Uso

### Caso 1: Proveedor carga factura
1. `usuarioA` inicia sesión
2. Sube XML y PDF de su factura
3. El registro queda en estado "Pendiente"
4. Solo `usuarioA`, `usuario1` (su supervisor) y `admin` pueden ver este registro

### Caso 2: Supervisor autoriza
1. `usuario1` inicia sesión
2. Ve registros de `usuarioA` y `usuarioB`
3. Revisa factura de `usuarioA`
4. Click en "Autorizar" → Estado cambia a "Autorizado"
5. Puede subir comprobante de pago → Estado cambia a "Pagado"

### Caso 3: Admin supervisa todo
1. `admin` inicia sesión
2. Ve TODOS los registros de todos los usuarios
3. Puede editar, eliminar, autorizar cualquier registro
4. Puede exportar reporte completo en Excel
5. Puede revertir estados si es necesario

### Caso 4: Supervisor rechaza factura
1. `usuario1` revisa factura de `usuarioA`
2. Encuentra un error
3. Click en "Rechazar" → Estado cambia a "Rechazado"
4. `usuarioA` ve su registro rechazado
5. `usuarioA` puede eliminarlo y volver a cargarlo correctamente

### Caso 5: Proveedor intenta eliminar registro Pendiente
1. `usuarioA` intenta eliminar su registro en estado "Pendiente"
2. ❌ Sistema rechaza: "Solo puedes eliminar tus registros si están en estado 'Rechazado'"
3. Debe esperar a que supervisor lo rechace o lo autorice

---

## 🔄 Flujo de Trabajo Típico

```
1. PROVEEDOR carga factura
   └─> Estado: Pendiente
   
2. SUPERVISOR revisa:
   
   Opción A - APRUEBA:
   └─> Estado: Autorizado
       └─> Sube comprobante de pago
           └─> Estado: Pagado
   
   Opción B - RECHAZA:
   └─> Estado: Rechazado
       └─> Proveedor puede eliminar y volver a cargar
   
3. ADMIN puede revertir si hay error
   └─> Estado: Autorizado o Pendiente
```

---

## 🚦 Estados del Registro

| Estado | Color | Descripción | Quién puede cambiar |
|--------|-------|-------------|---------------------|
| **Pendiente** | 🔴 Rojo | Registro recién creado, esperando revisión | Automático al crear |
| **Rechazado** | ⚫ Negro | Supervisor rechazó el registro | Supervisor/Admin |
| **Autorizado** | 🟡 Amarillo | Supervisor aprobó, pendiente de pago | Supervisor/Admin |
| **Pagado** | 🟢 Verde | Pago realizado y comprobado | Supervisor/Admin (al subir comprobante) |

### Reglas de Eliminación por Estado:

- **Proveedor:** Solo puede eliminar si está en "Rechazado"
- **Supervisor:** Solo puede eliminar si está en "Pendiente" (propios o subordinados)
- **Admin:** Puede eliminar en cualquier estado

---

## 🚀 Cómo Iniciar Sesión

1. Ir a: http://localhost:8001
2. Ingresar usuario y contraseña
3. El sistema mostrará:
   - Icono según rol (👑 admin, 👔 supervisor, 👤 proveedor)
   - Solo los registros que tienes permiso de ver
   - Botones habilitados según tus permisos

---

## 🔧 Cambiar Contraseñas

Para cambiar contraseñas, el admin debe:

1. Conectarse a la base de datos
2. Usar el endpoint de reset (borra todo)
3. O modificar directamente en código `main.py` y reiniciar

**Recomendación:** Cambiar las contraseñas por defecto en producción.

---

## 📞 Soporte

Si necesitas:
- Crear más usuarios
- Cambiar jerarquías
- Modificar permisos

Contacta al administrador del sistema.

---

---

## 🆕 Últimas Actualizaciones (27/04/2026)

### ✅ Cambios Implementados:

1. **Sistema de Eliminación por Estado:**
   - Proveedores pueden eliminar sus registros solo si están "Rechazados"
   - Supervisores pueden eliminar registros solo si están "Pendientes"
   - Admin puede eliminar en cualquier estado

2. **Nueva Acción: Rechazar Registro**
   - Endpoint: `PUT /api/rechazar-registro/{doc_id}`
   - Supervisores pueden rechazar registros de subordinados
   - Solo se puede rechazar si está en estado "Pendiente"
   - Permite al proveedor corregir y volver a cargar

3. **Validación de Permisos Mejorada:**
   - Todos los endpoints validan permisos según rol y estado
   - Mensajes de error específicos según el contexto
   - Sistema jerárquico completamente funcional

### 📝 Archivos Modificados:
- `permissions.py` - Lógica de permisos por estado
- `routers/documents.py` - Endpoints con validación
- `models.py` - Campo subordinados agregado
- `main.py` - Creación automática de usuarios

---

**Última actualización:** 27/04/2026
