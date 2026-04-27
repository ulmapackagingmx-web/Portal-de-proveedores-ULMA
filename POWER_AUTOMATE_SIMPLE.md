# 🚀 Power Automate - Guía Simplificada (Paso a Paso)

## ⚠️ IMPORTANTE: Debes usar Power Automate CLOUD, no Desktop

**Power Automate Cloud:** https://make.powerautomate.com (navegador web)  
**Power Automate Desktop:** Solo para automatización local de Windows

---

## 📱 Guía Paso a Paso SIMPLIFICADA

### PASO 1: Acceder a Power Automate Cloud

1. Abre tu navegador
2. Ve a: **https://make.powerautomate.com**
3. Inicia sesión con tu cuenta de Microsoft/Office 365

---

### PASO 2: Crear Nuevo Flow

1. Click en **"+ Crear"** (esquina superior izquierda)
2. Selecciona **"Flujo de nube automatizado"**
3. Nombre: `DataHub Procesar Facturas`
4. Busca: **"Cuando llega un nuevo correo electrónico"**
5. Selecciona: **"Cuando llega un nuevo correo electrónico (V3)" - Outlook de Office 365**
6. Click **"Crear"**

---

### PASO 3: Configurar el Trigger (Desencadenador)

En la tarjeta que aparece:

1. **Carpeta:** Bandeja de entrada
2. **Incluir datos adjuntos:** SÍ ✅
3. Click en **"Mostrar opciones avanzadas"**
4. **Filtro de asunto:** `[DATAHUB]`
5. **Solo con datos adjuntos:** SÍ ✅

**NO agregues condición aquí** - Eso viene después

---

### PASO 4: Agregar Acción HTTP (¡AQUÍ ES DONDE ENVÍAS AL WEBHOOK!)

1. Click en **"+ Nuevo paso"** (debajo del trigger)
2. Busca: **"HTTP"**
3. Selecciona: **"HTTP"** (el conector premium)
4. Si no tienes premium, usa **"HTTP con Azure AD"** o **"Solicitud HTTP"**

**Configuración de la acción HTTP:**

- **Método:** `POST`
- **URI:** `http://TU_IP_SERVIDOR:8001/api/webhook/procesar-correo`
- **Encabezados:**
  ```
  Content-Type    application/json
  ```
- **Cuerpo:** (Click en el icono de rayo ⚡ para modo expresión)

**COPIA ESTE JSON EN EL CUERPO:**

```json
{
  "usuario": "admin",
  "xml_base64": "@{base64(first(triggerOutputs()?['body/attachments'])?['contentBytes'])}",
  "pdf_base64": "@{if(greater(length(triggerOutputs()?['body/attachments']), 1), base64(last(triggerOutputs()?['body/attachments'])?['contentBytes']), '')}",
  "pdf_filename": "@{if(greater(length(triggerOutputs()?['body/attachments']), 1), last(triggerOutputs()?['body/attachments'])?['name'], 'factura.pdf')}",
  "centro_costo": "Administración",
  "subcatalogo": "SERVICIOS ADMINISTRATIVOS",
  "porcentaje": "100%",
  "fecha_pago": "POR DEFINIR",
  "moneda": "MXN"
}
```

**NOTA:** Por ahora usa valores fijos. Después puedes extraer del cuerpo del correo.

---

### PASO 5: Marcar correo como leído

1. Click en **"+ Nuevo paso"**
2. Busca: **"Marcar como leído"**
3. Selecciona: **"Marcar como leído o no leído (V3)"**
4. **Id. de mensaje:** Selecciona del menú dinámico → **"Id. de mensaje"** (del trigger)
5. **Marcar como:** `Leído`

---

### PASO 6: Guardar y Probar

1. Click en **"Guardar"** (esquina superior derecha)
2. Click en **"Probar"** → **"Manualmente"**
3. Envía un correo de prueba a tu buzón con:
   - Asunto: `[DATAHUB] Prueba`
   - Adjunto: Un archivo XML válido
4. Verifica que el Flow se ejecute
5. Revisa tu dashboard en http://localhost:8001

---

## 🎯 VERSIÓN ULTRA SIMPLIFICADA (Sin extraer del cuerpo)

Si solo quieres que funcione rápido, usa este JSON más simple:

```json
{
  "usuario": "admin",
  "xml_base64": "@{base64(first(triggerOutputs()?['body/attachments'])?['contentBytes'])}",
  "centro_costo": "Administración",
  "porcentaje": "100%"
}
```

Esto procesará el XML con valores por defecto. Después puedes editar el registro en el dashboard.

---

## 🔧 Alternativa: Si no tienes conector HTTP Premium

### Opción A: Usar "Solicitud HTTP a SharePoint"
1. Guarda el XML en SharePoint
2. Usa webhook desde SharePoint

### Opción B: Usar Azure Logic Apps (Gratis)
1. Ve a https://portal.azure.com
2. Crea un Logic App (tiene HTTP gratis)
3. Misma configuración que Power Automate

### Opción C: Usar Power Automate Desktop + Python

Crear un flow en Desktop que:
1. Monitorea carpeta de Outlook
2. Extrae XML y PDF
3. Ejecuta script Python que hace POST al webhook

---

## 🐍 Script Python para Power Automate Desktop

Si usas Desktop, crea este script: `enviar_webhook.py`

```python
import sys
import json
import base64
import requests

# Argumentos: xml_path, pdf_path (opcional), centro, fecha, usuario
xml_path = sys.argv[1]
pdf_path = sys.argv[2] if len(sys.argv) > 2 else None
centro = sys.argv[3] if len(sys.argv) > 3 else "Administración"
fecha = sys.argv[4] if len(sys.argv) > 4 else "POR DEFINIR"
usuario = sys.argv[5] if len(sys.argv) > 5 else "admin"

# Leer y codificar XML
with open(xml_path, 'rb') as f:
    xml_base64 = base64.b64encode(f.read()).decode('utf-8')

# Leer y codificar PDF si existe
pdf_base64 = ""
pdf_filename = "factura.pdf"
if pdf_path:
    with open(pdf_path, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
        pdf_filename = pdf_path.split('/')[-1]

# Preparar datos
datos = {
    "usuario": usuario,
    "xml_base64": xml_base64,
    "pdf_base64": pdf_base64,
    "pdf_filename": pdf_filename,
    "centro_costo": centro,
    "porcentaje": "100%",
    "fecha_pago": fecha,
    "moneda": "MXN"
}

# Enviar al webhook
response = requests.post(
    'http://localhost:8001/api/webhook/procesar-correo',
    json=datos,
    headers={'Content-Type': 'application/json'}
)

print(response.json())
```

**Uso en Power Automate Desktop:**
```
Ejecutar script Python: python3 enviar_webhook.py "ruta/al/archivo.xml" "ruta/al/pdf.pdf" "Administración" "2026-05-15" "admin"
```

---

## 🎬 VIDEO TUTORIAL (Texto)

### Minuto 0:00 - Crear Flow
- Ir a make.powerautomate.com
- Click "Crear"
- "Flujo automatizado"

### Minuto 0:30 - Configurar Trigger
- Buscar "correo electrónico"
- Seleccionar "Cuando llega nuevo correo V3"
- Carpeta: Bandeja entrada
- Incluir adjuntos: SÍ
- Filtro asunto: [DATAHUB]

### Minuto 1:00 - Agregar HTTP
- Click "+ Nuevo paso"
- Buscar "HTTP"
- Método: POST
- URI: http://TU_IP:8001/api/webhook/procesar-correo
- Headers: Content-Type = application/json
- Body: Copiar JSON simplificado

### Minuto 1:30 - Marcar leído
- "+ Nuevo paso"
- "Marcar como leído"
- Id mensaje: del trigger

### Minuto 2:00 - Guardar y Probar
- Click "Guardar"
- Click "Probar"
- Enviar correo de prueba

---

## 📞 RESPUESTA A TUS PREGUNTAS:

### ❓ "¿Qué archivo necesito para meter mis credenciales?"

**RESPUESTA:** Con Power Automate **NO NECESITAS** meter credenciales en ningún archivo. Power Automate se conecta directamente a tu buzón de Outlook usando tu sesión de Office 365.

Si usaras el script Python directo (`email_processor.py`), ahí sí necesitarías crear un archivo `.env` con:
```
EXCHANGE_EMAIL=tu_correo@ulma.com.mx
EXCHANGE_PASSWORD=tu_contraseña
```

Pero con Power Automate esto NO es necesario. ✅

### ❓ "¿No será más fácil con webhook desde Power Automate?"

**RESPUESTA:** ¡SÍ! Es MUCHO más fácil. Por eso creé el webhook. Solo necesitas:

1. Configurar el Flow en Power Automate Cloud (3 pasos)
2. El Flow envía los datos al webhook
3. Tu web service los procesa automáticamente

**NO necesitas:**
- ❌ Credenciales de Exchange en el servidor
- ❌ Scripts complejos
- ❌ Configuración de seguridad adicional

---

## 🎯 RESUMEN: ¿Qué hacer ahora?

1. ✅ Tu servidor ya está listo (corriendo en puerto 8001)
2. ✅ El webhook ya está creado y funcionando
3. 📱 Solo falta configurar Power Automate Cloud:
   - Ve a https://make.powerautomate.com
   - Sigue los pasos 1-6 de arriba
   - Usa el JSON simplificado
4. 📧 Envía un correo de prueba
5. ✅ ¡Listo!

**Documentación completa:** `POWER_AUTOMATE_GUIA.md`
