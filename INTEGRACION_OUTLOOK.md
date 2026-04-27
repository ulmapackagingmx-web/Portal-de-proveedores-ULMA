# Integración con Outlook Exchange - DataHub Ulma

## 📧 Objetivo
Permitir que los usuarios envíen correos electrónicos a un buzón de Outlook Exchange con archivos XML y PDF adjuntos, y que el sistema automáticamente procese estos correos y cree registros en el DataHub.

---

## 🔧 Requisitos Técnicos

### 1. Dependencias Python Necesarias
```bash
pip install exchangelib
pip install python-dotenv
```

Actualizar `requirements.txt`:
```
fastapi
uvicorn
sqlalchemy
python-multipart
pandas
openpyxl
xlsxwriter
passlib
python-jose
exchangelib
python-dotenv
```

### 2. Configuración de Credenciales
Crear archivo `.env` en la raíz del proyecto:
```env
# Configuración de Outlook Exchange
EXCHANGE_EMAIL=datahub@ulma.com.mx
EXCHANGE_PASSWORD=tu_password_seguro
EXCHANGE_SERVER=outlook.office365.com
EXCHANGE_DOMAIN=ulma.com.mx

# Mapeo de usuarios (email del remitente -> usuario del sistema)
USER_MAPPING={"usuario1@ulma.com.mx":"admin","usuario2@ulma.com.mx":"usuario"}
```

---

## 📨 Formato del Correo Electrónico

### Estructura Requerida

**Para:** datahub@ulma.com.mx  
**Asunto:** [DATAHUB] Nuevo Registro - [Nombre del Proveedor]  
**Adjuntos:** 
- `factura.xml` (obligatorio)
- `factura.pdf` (opcional)

**Cuerpo del correo (formato lista):**
```
Centro de Costo: Administración
Subcatálogo: SERVICIOS ADMINISTRATIVOS
Porcentaje: 100%
Fecha de Pago: 2026-05-15
Moneda: MXN

--- O para múltiples centros ---

Centro de Costo 1: Administración
Subcatálogo 1: SERVICIOS ADMINISTRATIVOS
Porcentaje 1: 50%

Centro de Costo 2: Comercial
Subcatálogo 2: SERVICIOS Y FERIAS
Porcentaje 2: 50%

Fecha de Pago: 2026-05-15
Moneda: MXN
```

### Campos Opcionales en el Cuerpo
- Si no se especifica `Fecha de Pago`, se asigna "POR DEFINIR"
- Si no se especifica `Moneda`, se asigna "MXN"
- Si no se especifica `Centro de Costo`, se asigna "Administración" al 100%

---

## 🔄 Flujo de Procesamiento

1. **Script de Monitoreo** se ejecuta cada X minutos (configurable)
2. **Lee correos no leídos** del buzón de Exchange
3. **Valida el asunto** (debe contener [DATAHUB])
4. **Extrae adjuntos** (XML y PDF)
5. **Procesa el XML** para obtener datos fiscales
6. **Parsea el cuerpo** del correo para obtener datos logísticos
7. **Valida porcentajes** (deben sumar 100%)
8. **Crea el registro** en la base de datos
9. **Adjunta el PDF** si existe
10. **Marca el correo como leído** y archivado

---

## 📝 Script de Integración

Crear archivo: `email_processor.py`

```python
import os
import re
import time
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from exchangelib import Credentials, Account, Configuration, DELEGATE, FileAttachment
from sqlalchemy.orm import Session

from database import SessionLocal
from models import DBDocument

# Cargar variables de entorno
load_dotenv()

# Configuración de Exchange
EXCHANGE_EMAIL = os.getenv('EXCHANGE_EMAIL')
EXCHANGE_PASSWORD = os.getenv('EXCHANGE_PASSWORD')
EXCHANGE_SERVER = os.getenv('EXCHANGE_SERVER', 'outlook.office365.com')
USER_MAPPING = json.loads(os.getenv('USER_MAPPING', '{}'))

def conectar_exchange():
    """Conecta con el servidor de Exchange"""
    credentials = Credentials(EXCHANGE_EMAIL, EXCHANGE_PASSWORD)
    config = Configuration(server=EXCHANGE_SERVER, credentials=credentials)
    account = Account(
        primary_smtp_address=EXCHANGE_EMAIL,
        config=config,
        autodiscover=False,
        access_type=DELEGATE
    )
    return account

def parsear_cuerpo_correo(body_text):
    """Extrae datos del cuerpo del correo"""
    datos = {
        'centros': [],
        'fecha_pago': 'POR DEFINIR',
        'moneda': 'MXN'
    }
    
    # Buscar fecha de pago
    fecha_match = re.search(r'Fecha de Pago:\s*(\d{4}-\d{2}-\d{2})', body_text, re.IGNORECASE)
    if fecha_match:
        datos['fecha_pago'] = fecha_match.group(1)
    
    # Buscar moneda
    moneda_match = re.search(r'Moneda:\s*([A-Z]{3})', body_text, re.IGNORECASE)
    if moneda_match:
        datos['moneda'] = moneda_match.group(1)
    
    # Buscar centros de costo (formato simple)
    centro_match = re.search(r'Centro de Costo:\s*([^\n]+)', body_text, re.IGNORECASE)
    subcatalogo_match = re.search(r'Subcatálogo:\s*([^\n]+)', body_text, re.IGNORECASE)
    porcentaje_match = re.search(r'Porcentaje:\s*(\d+(?:\.\d+)?)%?', body_text, re.IGNORECASE)
    
    if centro_match:
        datos['centros'].append({
            'centro': centro_match.group(1).strip(),
            'subcatalogo': subcatalogo_match.group(1).strip() if subcatalogo_match else '',
            'porcentaje': float(porcentaje_match.group(1)) if porcentaje_match else 100.0
        })
    
    # Buscar múltiples centros (formato numerado)
    for i in range(1, 10):
        centro_match = re.search(rf'Centro de Costo {i}:\s*([^\n]+)', body_text, re.IGNORECASE)
        subcatalogo_match = re.search(rf'Subcatálogo {i}:\s*([^\n]+)', body_text, re.IGNORECASE)
        porcentaje_match = re.search(rf'Porcentaje {i}:\s*(\d+(?:\.\d+)?)%?', body_text, re.IGNORECASE)
        
        if centro_match:
            datos['centros'].append({
                'centro': centro_match.group(1).strip(),
                'subcatalogo': subcatalogo_match.group(1).strip() if subcatalogo_match else '',
                'porcentaje': float(porcentaje_match.group(1)) if porcentaje_match else 0.0
            })
    
    # Si no se encontraron centros, usar Administración por defecto
    if not datos['centros']:
        datos['centros'].append({
            'centro': 'Administración',
            'subcatalogo': '',
            'porcentaje': 100.0
        })
    
    return datos

def procesar_xml_adjunto(xml_content):
    """Procesa el contenido del XML y extrae datos fiscales"""
    root = ET.fromstring(xml_content)
    
    datos = {
        'total': float(root.attrib.get('Total', '0.0')),
        'moneda': root.attrib.get('Moneda', 'MXN'),
        'rfc_emisor': 'DESCONOCIDO',
        'nombre_emisor': 'DESCONOCIDO',
        'uuid': 'S/F',
        'uso_cfdi': '',
        'forma_pago': '',
        'metodo_pago': '',
        'clave_sat': '',
        'descripcion_concepto': ''
    }
    
    for elem in root.iter():
        if elem.tag.endswith('Emisor'):
            datos['rfc_emisor'] = elem.attrib.get('Rfc', 'DESCONOCIDO')
            datos['nombre_emisor'] = elem.attrib.get('Nombre', 'DESCONOCIDO')
        if elem.tag.endswith('TimbreFiscalDigital'):
            datos['uuid'] = elem.attrib.get('UUID', 'S/F')
        if elem.tag.endswith('Receptor'):
            datos['uso_cfdi'] = elem.attrib.get('UsoCFDI', '')
        if elem.tag.endswith('Concepto'):
            if not datos['clave_sat']:  # Solo el primer concepto
                datos['clave_sat'] = elem.attrib.get('ClaveProdServ', '')
                descripcion = elem.attrib.get('Descripcion', '')
                datos['descripcion_concepto'] = descripcion[:200] if descripcion else ''
    
    datos['forma_pago'] = root.attrib.get('FormaPago', '')
    datos['metodo_pago'] = root.attrib.get('MetodoPago', '')
    
    return datos

def procesar_correos():
    """Función principal que procesa correos no leídos"""
    print(f"[{datetime.now()}] Iniciando procesamiento de correos...")
    
    try:
        account = conectar_exchange()
        inbox = account.inbox
        
        # Filtrar correos no leídos con [DATAHUB] en el asunto
        correos = inbox.filter(is_read=False).order_by('-datetime_received')[:10]
        
        for correo in correos:
            try:
                # Validar asunto
                if '[DATAHUB]' not in correo.subject.upper():
                    continue
                
                print(f"Procesando correo de: {correo.sender.email_address}")
                
                # Obtener usuario del sistema
                remitente_email = correo.sender.email_address.lower()
                usuario_sistema = USER_MAPPING.get(remitente_email, 'usuario')
                
                # Buscar adjuntos
                xml_content = None
                pdf_path = None
                
                for attachment in correo.attachments:
                    if isinstance(attachment, FileAttachment):
                        filename = attachment.name.lower()
                        
                        if filename.endswith('.xml'):
                            xml_content = attachment.content
                            print(f"  ✓ XML encontrado: {attachment.name}")
                        
                        elif filename.endswith('.pdf'):
                            # Guardar PDF temporalmente
                            temp_pdf = f"uploads/temp_{attachment.name}"
                            with open(temp_pdf, 'wb') as f:
                                f.write(attachment.content)
                            pdf_path = temp_pdf
                            print(f"  ✓ PDF encontrado: {attachment.name}")
                
                if not xml_content:
                    print(f"  ✗ No se encontró XML en el correo")
                    continue
                
                # Procesar XML
                datos_xml = procesar_xml_adjunto(xml_content)
                
                # Procesar cuerpo del correo
                body_text = correo.body if correo.body else correo.text_body
                datos_correo = parsear_cuerpo_correo(body_text)
                
                # Validar porcentajes
                total_porcentaje = sum(c['porcentaje'] for c in datos_correo['centros'])
                if abs(total_porcentaje - 100) > 0.01:
                    print(f"  ✗ ERROR: Porcentajes no suman 100% ({total_porcentaje}%)")
                    continue
                
                # Construir string de porcentajes
                if len(datos_correo['centros']) == 1 and datos_correo['centros'][0]['porcentaje'] == 100:
                    porcentaje_str = '100%'
                else:
                    porcentaje_str = ','.join([f"{c['centro']}:{c['porcentaje']}%" for c in datos_correo['centros']])
                
                # Crear registro en la base de datos
                db = SessionLocal()
                nuevo_doc = DBDocument(
                    tipo="XML",
                    remitente_rfc=datos_xml['rfc_emisor'],
                    nombre=datos_xml['nombre_emisor'],
                    total=datos_xml['total'],
                    uuid_folio=datos_xml['uuid'],
                    subido_por=usuario_sistema,
                    centro_costo=datos_correo['centros'][0]['centro'],
                    subcatalogo_centro=datos_correo['centros'][0]['subcatalogo'],
                    porcentaje_centro=porcentaje_str,
                    fecha_pago=datos_correo['fecha_pago'],
                    uso_cfdi=datos_xml['uso_cfdi'],
                    forma_pago=datos_xml['forma_pago'],
                    metodo_pago=datos_xml['metodo_pago'],
                    clave_sat=datos_xml['clave_sat'],
                    descripcion_sat=datos_xml['descripcion_concepto'],
                    descripcion_concepto=datos_xml['descripcion_concepto'],
                    moneda=datos_correo['moneda']
                )
                
                db.add(nuevo_doc)
                db.commit()
                db.refresh(nuevo_doc)
                
                # Si hay PDF, adjuntarlo al registro
                if pdf_path:
                    final_pdf_path = f"uploads/{nuevo_doc.id}_{Path(pdf_path).name.replace('temp_', '')}"
                    os.rename(pdf_path, final_pdf_path)
                    nuevo_doc.comprobante_pdf = final_pdf_path
                    db.commit()
                    print(f"  ✓ PDF adjuntado al registro #{nuevo_doc.id}")
                
                db.close()
                
                print(f"  ✓ Registro #{nuevo_doc.id} creado exitosamente")
                
                # Marcar correo como leído
                correo.is_read = True
                correo.save()
                
            except Exception as e:
                print(f"  ✗ Error procesando correo: {str(e)}")
                continue
        
        print(f"[{datetime.now()}] Procesamiento completado\n")
        
    except Exception as e:
        print(f"ERROR conectando con Exchange: {str(e)}")

if __name__ == "__main__":
    # Ejecutar una vez
    procesar_correos()
    
    # O ejecutar en loop cada 5 minutos
    # while True:
    #     procesar_correos()
    #     time.sleep(300)  # 5 minutos
```

---

## 🚀 Implementación

### Opción 1: Ejecución Manual
```bash
python3 email_processor.py
```

### Opción 2: Cron Job (Automático cada 5 minutos)
```bash
# Editar crontab
crontab -e

# Agregar línea:
*/5 * * * * cd /Users/edbravo/Desktop/mi-web-service && /usr/local/bin/python3 email_processor.py >> logs/email_processor.log 2>&1
```

### Opción 3: Servicio Systemd (Linux)
Crear `/etc/systemd/system/datahub-email.service`:
```ini
[Unit]
Description=DataHub Email Processor
After=network.target

[Service]
Type=simple
User=edbravo
WorkingDirectory=/Users/edbravo/Desktop/mi-web-service
ExecStart=/usr/local/bin/python3 email_processor.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

### Opción 4: Integración en FastAPI (Background Task)
Agregar a `main.py`:
```python
from fastapi import BackgroundTasks
import asyncio

async def procesar_correos_background():
    while True:
        try:
            # Importar y ejecutar el procesador
            from email_processor import procesar_correos
            procesar_correos()
        except Exception as e:
            print(f"Error en background task: {e}")
        await asyncio.sleep(300)  # 5 minutos

@app.on_event("startup")
async def startup_event():
    # ... código existente ...
    asyncio.create_task(procesar_correos_background())
```

---

## 📋 Ejemplos de Correos Válidos

### Ejemplo 1: Centro Único
```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Factura CFE Enero 2026
Adjuntos: CFE_Enero.xml, CFE_Enero.pdf

Cuerpo:
Centro de Costo: Administración
Subcatálogo: SERVICIOS ADMINISTRATIVOS
Porcentaje: 100%
Fecha de Pago: 2026-05-15
Moneda: MXN
```

### Ejemplo 2: Múltiples Centros
```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Factura Compartida Servicios
Adjuntos: factura_compartida.xml

Cuerpo:
Centro de Costo 1: Administración
Subcatálogo 1: SERVICIOS ADMINISTRATIVOS
Porcentaje 1: 60%

Centro de Costo 2: Comercial
Subcatálogo 2: SERVICIOS Y FERIAS
Porcentaje 2: 40%

Fecha de Pago: 2026-06-01
Moneda: MXN
```

### Ejemplo 3: Mínimo (solo XML)
```
Para: datahub@ulma.com.mx
Asunto: [DATAHUB] Nueva Factura
Adjuntos: factura.xml

Cuerpo:
(vacío o cualquier texto - se usarán valores por defecto)
```

---

## 🔐 Seguridad

1. **Autenticación**: Solo correos de usuarios mapeados en `USER_MAPPING` serán procesados
2. **Validación**: El asunto debe contener `[DATAHUB]`
3. **Archivos**: Solo se procesan archivos .xml y .pdf
4. **Porcentajes**: Se valida que sumen exactamente 100%
5. **Credenciales**: Almacenadas en `.env` (no en código)

---

## 📊 Logs y Monitoreo

Crear carpeta de logs:
```bash
mkdir -p logs
```

El script generará logs con:
- Timestamp de ejecución
- Correos procesados
- Errores encontrados
- Registros creados

---

## ⚠️ Consideraciones

1. **Permisos Exchange**: La cuenta debe tener permisos de lectura en el buzón
2. **Firewall**: Permitir conexión al servidor Exchange (puerto 443)
3. **Autenticación Moderna**: Si Outlook usa OAuth2, se requiere configuración adicional
4. **Límites**: Exchange tiene límites de API (throttling)
5. **Zona Horaria**: Ajustar según la ubicación del servidor

---

## 🧪 Pruebas

1. Enviar correo de prueba con XML válido
2. Verificar que el script lo procese
3. Confirmar que el registro aparezca en el dashboard
4. Validar que el PDF se adjunte correctamente
5. Probar con múltiples centros de costo

---

## 📞 Soporte

Para problemas con Exchange:
- Verificar credenciales en `.env`
- Revisar logs en `logs/email_processor.log`
- Confirmar que el buzón sea accesible vía IMAP/EWS
- Validar formato del correo según ejemplos

---

**Última actualización:** 27/04/2026
