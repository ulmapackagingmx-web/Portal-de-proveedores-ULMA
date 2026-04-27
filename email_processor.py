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
