# 🚀 Integración con Power Automate - DataHub Ulma

## ✅ SOLUCIÓN RECOMENDADA (Mucho más simple que Exchange directo)

Esta guía te muestra cómo configurar Power Automate para procesar correos automáticamente y enviarlos a tu web service.

---

## 📋 Ventajas de usar Power Automate

✅ **No necesitas credenciales en el servidor** - Power Automate maneja la autenticación  
✅ **Interfaz visual** - Fácil de configurar sin código  
✅ **Más seguro** - No expones credenciales de Exchange  
✅ **Más confiable** - Microsoft maneja la conexión  
✅ **Fácil de mantener** - Cambios desde la interfaz web  

---

## 🔗 Endpoint Webhook Creado

**URL:** `http://TU_SERVIDOR:8001/api/webhook/procesar-correo`  
**Método:** POST  
**Content-Type:** application/json

### Estructura del JSON:

```json
{
  "usuario": "admin",
  "xml_base64": "PD94bWwgdmVyc2lvbj0iMS4wIj8+...",
  "pdf_base64": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC...",
  "pdf_filename": "factura.pdf",
  "centro_costo": "Administración",
  "subcatalogo": "SERVICIOS ADMINISTRATIVOS",
  "porcentaje": "100%",
  "fecha_pago": "2026-05-15",
  "moneda": "MXN"
}
```

### Campos Requeridos:
- ✅ `usuario` - Usuario del sistema (admin, usuario, etc.)
- ✅ `xml_base64` - Archivo XML codificado en Base64

### Campos Opcionales:
- `pdf_base64` - Archivo PDF codificado en Base64
- `pdf_filename` - Nombre del archivo PDF
- `centro_costo` - Default: "Administración"
- `subcatalogo` - Default: ""
- `porcentaje` - Default: "100%"
- `fecha_pago` - Default: "POR DEFINIR"
- `moneda` - Default: "MXN"

---

## 🎯 Configuración en Power Automate

### Paso 1: Crear un nuevo Flow

1. Ve a https://make.powerautomate.com
2. Click en **"+ Crear"**
3. Selecciona **"Flujo de nube automatizado"**
4. Nombre: **"DataHub - Procesar Facturas XML"**

### Paso 2: Configurar el Trigger

**Trigger:** "Cuando llega un nuevo correo electrónico (V3)"

**Configuración:**
- **Carpeta:** Bandeja de entrada
- **Incluir adjuntos:** Sí
- **Filtro de asunto:** `[DATAHUB]`
- **Importancia:** Cualquiera

### Paso 3: Agregar Condición para XML

**Acción:** "Condición"

**Condición:**
```
Nombre de archivo de datos adjuntos    contiene    .xml
```

### Paso 4: Procesar Adjuntos (Rama SI)

#### 4.1 Aplicar a cada adjunto XML

**Acción:** "Aplicar a cada uno"
- **Seleccionar salida:** Datos adjuntos

**Dentro del bucle:**

##### 4.1.1 Condición: Es XML
```
Nombre de datos adjuntos    termina con    .xml
```

##### 4.1.2 Convertir XML a Base64 (Rama SI)
**Acción:** "Redactar"
- **Entradas:** `base64(items('Apply_to_each')?['contentBytes'])`
- **Guardar como:** `xml_base64`

##### 4.1.3 Buscar PDF adjunto
**Acción:** "Aplicar a cada uno" (segundo bucle)
- **Seleccionar salida:** Datos adjuntos

**Condición dentro:**
```
Nombre de datos adjuntos    termina con    .pdf
```

**Si es PDF:**
- **Acción:** "Redactar"
- **Entradas:** `base64(items('Apply_to_each_2')?['contentBytes'])`
- **Guardar como:** `pdf_base64`
- **Nombre archivo:** `items('Apply_to_each_2')?['name']`

### Paso 5: Extraer datos del cuerpo del correo

**Acción:** "Inicializar variable" (para cada campo)

Variables a crear:
- `centro_costo` - Tipo: String - Valor: `Administración`
- `subcatalogo` - Tipo: String - Valor: (vacío)
- `porcentaje` - Tipo: String - Valor: `100%`
- `fecha_pago` - Tipo: String - Valor: `POR DEFINIR`
- `moneda` - Tipo: String - Valor: `MXN`
- `usuario_sistema` - Tipo: String - Valor: `admin`

**Acción:** "Redactar" (para extraer del cuerpo)

Usar expresiones para extraer del cuerpo del correo:
```
Centro de Costo: @{first(split(last(split(triggerBody()?['body'], 'Centro de Costo:')), char(10)))}
```

### Paso 6: Enviar al Webhook

**Acción:** "HTTP"

**Configuración:**
- **Método:** POST
- **URI:** `http://TU_SERVIDOR_IP:8001/api/webhook/procesar-correo`
- **Encabezados:**
  ```
  Content-Type: application/json
  ```
- **Cuerpo:**
  ```json
  {
    "usuario": "@{variables('usuario_sistema')}",
    "xml_base64": "@{outputs('Compose_XML_Base64')}",
    "pdf_base64": "@{outputs('Compose_PDF_Base64')}",
    "pdf_filename": "@{variables('pdf_filename')}",
    "centro_costo": "@{variables('centro_costo')}",
    "subcatalogo": "@{variables('subcatalogo')}",
    "porcentaje": "@{variables('porcentaje')}",
    "fecha_pago": "@{variables('fecha_pago')}",
    "moneda": "@{variables('moneda')}"
  }
  ```

### Paso 7: Marcar correo como leído

**Acción:** "Marcar como leído o no leído (V3)"
- **Id. de mensaje:** Id. de mensaje (del trigger)
- **Marcar como:** Leído

---

## 📧 Formato del Correo que deben enviar los usuarios

### Ejemplo Simple (1 Centro de Costo):

```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Factura CFE Marzo 2026
Adjuntos: factura_cfe.xml, factura_cfe.pdf

Cuerpo:
Centro de Costo: Administración
Subcatálogo: SERVICIOS ADMINISTRATIVOS
Porcentaje: 100%
Fecha de Pago: 2026-05-15
Moneda: MXN
Usuario: admin
```

### Ejemplo Múltiples Centros:

```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Factura Compartida
Adjuntos: factura.xml

Cuerpo:
Porcentaje: Administración:60%,Comercial:40%
Centro de Costo: Administración
Subcatálogo: SERVICIOS ADMINISTRATIVOS
Fecha de Pago: 2026-06-01
Moneda: MXN
Usuario: admin
```

---

## 🔧 Configuración Simplificada con Power Automate

### Plantilla JSON para Power Automate (Copiar y Pegar):

```json
{
  "usuario": "@{coalesce(first(split(last(split(triggerBody()?['body'], 'Usuario:')), char(10))), 'admin')}",
  "xml_base64": "@{base64(first(triggerOutputs()?['body/attachments'])?['contentBytes'])}",
  "pdf_base64": "@{if(greater(length(triggerOutputs()?['body/attachments']), 1), base64(last(triggerOutputs()?['body/attachments'])?['contentBytes']), '')}",
  "pdf_filename": "@{if(greater(length(triggerOutputs()?['body/attachments']), 1), last(triggerOutputs()?['body/attachments'])?['name'], 'factura.pdf')}",
  "centro_costo": "@{coalesce(trim(first(split(last(split(triggerBody()?['body'], 'Centro de Costo:')), char(10)))), 'Administración')}",
  "subcatalogo": "@{coalesce(trim(first(split(last(split(triggerBody()?['body'], 'Subcatálogo:')), char(10)))), '')}",
  "porcentaje": "@{coalesce(trim(first(split(last(split(triggerBody()?['body'], 'Porcentaje:')), char(10)))), '100%')}",
  "fecha_pago": "@{coalesce(trim(first(split(last(split(triggerBody()?['body'], 'Fecha de Pago:')), char(10)))), 'POR DEFINIR')}",
  "moneda": "@{coalesce(trim(first(split(last(split(triggerBody()?['body'], 'Moneda:')), char(10)))), 'MXN')}"
}
```

---

## 🎬 Video Tutorial Paso a Paso

### 1. Crear Flow en Power Automate

1. **Nuevo Flow Automatizado**
   - Nombre: "DataHub Procesar Facturas"
   - Trigger: "Cuando llega un nuevo correo"

2. **Configurar Trigger**
   - Buzón: datahub@ulma.com.mx
   - Carpeta: Bandeja de entrada
   - Filtro asunto: [DATAHUB]
   - ✅ Incluir adjuntos

3. **Agregar Acción HTTP**
   - Método: POST
   - URI: `http://TU_IP:8001/api/webhook/procesar-correo`
   - Headers: `Content-Type: application/json`
   - Body: (Copiar JSON de arriba)

4. **Marcar como leído**
   - Acción: "Marcar como leído"
   - Mensaje: Id. de mensaje (del trigger)

5. **Guardar y Activar**

---

## 🧪 Prueba del Webhook

### Opción 1: Desde Power Automate
1. Envía un correo de prueba con XML adjunto
2. Verifica que el Flow se ejecute
3. Revisa el dashboard para ver el nuevo registro

### Opción 2: Prueba Manual con cURL

```bash
# Primero, codifica tu XML en base64
base64 -i factura.xml -o xml_base64.txt

# Luego envía el POST
curl -X POST http://localhost:8001/api/webhook/procesar-correo \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "admin",
    "xml_base64": "PEGAR_AQUI_EL_BASE64_DEL_XML",
    "centro_costo": "Administración",
    "porcentaje": "100%",
    "fecha_pago": "2026-05-15",
    "moneda": "MXN"
  }'
```

### Opción 3: Prueba con Postman

1. Método: POST
2. URL: `http://localhost:8001/api/webhook/procesar-correo`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "usuario": "admin",
  "xml_base64": "TU_XML_EN_BASE64",
  "centro_costo": "Administración",
  "porcentaje": "100%"
}
```

---

## 🔐 Seguridad del Webhook

### Opción 1: Sin autenticación (Red interna)
- Usar solo en red privada/VPN
- Firewall que solo permita IPs de Microsoft

### Opción 2: Con API Key (Recomendado)

Modificar `routers/webhook.py`:

```python
from fastapi import Header

API_KEY = "tu_clave_secreta_aqui_12345"

@router.post("/procesar-correo")
async def procesar_correo_webhook(
    datos: dict = Body(...),
    x_api_key: str = Header(...)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    # ... resto del código
```

En Power Automate agregar header:
```
X-API-Key: tu_clave_secreta_aqui_12345
```

---

## 📊 Mapeo de Usuarios

### Opción 1: Por correo del remitente

En Power Automate, agregar lógica:
```
Si De (correo) contiene "usuario1@ulma.com" → usuario = "admin"
Si De (correo) contiene "usuario2@ulma.com" → usuario = "usuario"
```

### Opción 2: En el cuerpo del correo

Los usuarios incluyen en el correo:
```
Usuario: admin
```

Y Power Automate lo extrae automáticamente.

---

## 🎨 Plantilla de Correo para Usuarios

Crea una plantilla que los usuarios puedan copiar:

```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Descripción de la factura

Adjuntos: 
- factura.xml (OBLIGATORIO)
- factura.pdf (OPCIONAL)

--- COPIAR DESDE AQUÍ ---
Centro de Costo: Administración
Subcatálogo: SERVICIOS ADMINISTRATIVOS
Porcentaje: 100%
Fecha de Pago: 2026-05-15
Moneda: MXN
Usuario: admin
--- HASTA AQUÍ ---

Notas adicionales: (opcional)
```

---

## 🔄 Flujo Completo en Power Automate

```
┌─────────────────────────────────────┐
│ 1. Trigger: Nuevo correo            │
│    - Buzón: datahub@ulma.com.mx     │
│    - Filtro: [DATAHUB]              │
│    - Con adjuntos                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Condición: ¿Tiene XML?           │
│    - Adjuntos contiene .xml         │
└──────────────┬──────────────────────┘
               │ SI
               ▼
┌─────────────────────────────────────┐
│ 3. Convertir XML a Base64           │
│    - base64(adjunto.contentBytes)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Convertir PDF a Base64 (si hay)  │
│    - base64(adjunto.contentBytes)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Extraer datos del cuerpo         │
│    - Centro, Subcatálogo, etc.      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. HTTP POST al webhook             │
│    - URL: /api/webhook/procesar-... │
│    - Body: JSON con todos los datos │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 7. Marcar correo como leído         │
└─────────────────────────────────────┘
```

---

## 📱 Notificaciones (Opcional)

Agregar al final del Flow:

**Si el webhook responde OK:**
- Enviar correo de confirmación al remitente
- Enviar notificación Teams
- Registrar en SharePoint

**Si el webhook falla:**
- Enviar alerta al admin
- Mover correo a carpeta "Errores"

---

## 🌐 Exponer tu servidor a Internet

### Opción 1: ngrok (Para pruebas)
```bash
# Instalar ngrok
brew install ngrok

# Exponer puerto 8001
ngrok http 8001

# Usar la URL que te da ngrok en Power Automate
# Ejemplo: https://abc123.ngrok.io/api/webhook/procesar-correo
```

### Opción 2: IP Pública + Puerto Forwarding
1. Configurar router para port forwarding (8001 → servidor)
2. Usar IP pública en Power Automate
3. Configurar firewall para permitir solo IPs de Microsoft

### Opción 3: Azure/AWS (Producción)
1. Desplegar el servicio en la nube
2. Usar dominio público
3. Certificado SSL (HTTPS)

---

## 📝 Expresiones Útiles de Power Automate

### Extraer texto después de una etiqueta:
```
trim(first(split(last(split(triggerBody()?['body'], 'Centro de Costo:')), char(10))))
```

### Convertir adjunto a Base64:
```
base64(items('Apply_to_each')?['contentBytes'])
```

### Obtener nombre de adjunto:
```
items('Apply_to_each')?['name']
```

### Validar si existe adjunto PDF:
```
if(greater(length(triggerOutputs()?['body/attachments']), 1), 'SI', 'NO')
```

---

## ✅ Checklist de Implementación

- [ ] Crear Flow en Power Automate
- [ ] Configurar trigger de correo
- [ ] Agregar conversión Base64 para XML
- [ ] Agregar conversión Base64 para PDF (opcional)
- [ ] Extraer datos del cuerpo del correo
- [ ] Configurar HTTP POST al webhook
- [ ] Probar con correo de prueba
- [ ] Configurar notificaciones (opcional)
- [ ] Documentar para usuarios finales
- [ ] Activar Flow en producción

---

## 🎓 Capacitación para Usuarios

### Instrucciones Simples:

1. **Redacta un correo** a: datahub@ulma.com.mx
2. **Asunto debe incluir:** [DATAHUB]
3. **Adjunta el XML** (obligatorio)
4. **Adjunta el PDF** (opcional)
5. **En el cuerpo, copia y pega:**
   ```
   Centro de Costo: Administración
   Subcatálogo: SERVICIOS ADMINISTRATIVOS
   Porcentaje: 100%
   Fecha de Pago: 2026-05-15
   Moneda: MXN
   Usuario: tu_usuario
   ```
6. **Envía el correo**
7. **Espera 1-2 minutos** y revisa el dashboard

---

## 🐛 Troubleshooting

### El Flow no se ejecuta
- ✅ Verifica que el asunto contenga [DATAHUB]
- ✅ Confirma que el correo llegó al buzón correcto
- ✅ Revisa el historial de ejecuciones en Power Automate

### El webhook retorna error
- ✅ Verifica que el servidor esté corriendo
- ✅ Revisa los logs del servidor
- ✅ Confirma que el XML sea válido
- ✅ Valida que los porcentajes sumen 100%

### El registro no aparece en el dashboard
- ✅ Click en "Actualizar" en el dashboard
- ✅ Verifica que el usuario sea correcto
- ✅ Revisa la base de datos directamente

---

## 📞 Contacto y Soporte

**Webhook URL:** `http://TU_SERVIDOR:8001/api/webhook/procesar-correo`  
**Documentación API:** `http://TU_SERVIDOR:8001/docs`  
**Archivo configuración:** `.env` (crear desde `.env.example`)

---

**Última actualización:** 27/04/2026  
**Versión:** 1.0
