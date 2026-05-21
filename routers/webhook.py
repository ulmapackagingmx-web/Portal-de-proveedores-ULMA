import os
import base64
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional

from database import SessionLocal
from models import DBDocument

router = APIRouter(prefix="/api/webhook", tags=["Webhook Power Automate"])

@router.post("/procesar-correo")
async def procesar_correo_webhook(datos: dict = Body(...)):
    """
    Endpoint webhook para recibir correos desde Power Automate
    
    Estructura esperada del JSON:
    {
        "usuario": "admin",
        "xml_base64": "PD94bWwgdmVyc2lvbj0iMS4wIj8+...",
        "pdf_base64": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC...",  // Opcional
        "pdf_filename": "factura.pdf",  // Opcional
        "centro_costo": "Administración",
        "subcatalogo": "SERVICIOS ADMINISTRATIVOS",
        "porcentaje": "100%",  // O "Administración:50%,Comercial:50%"
        "fecha_pago": "2026-05-15",  // Opcional
        "moneda": "MXN"  // Opcional
    }
    """
    try:
        # Validar campos requeridos
        if 'usuario' not in datos or 'xml_base64' not in datos:
            raise HTTPException(status_code=400, detail="Faltan campos requeridos: usuario y xml_base64")
        
        usuario = datos.get('usuario', 'usuario')
        xml_base64 = datos.get('xml_base64')
        pdf_base64 = datos.get('pdf_base64')
        pdf_filename = datos.get('pdf_filename', 'factura.pdf')
        
        # Decodificar XML
        try:
            xml_content = base64.b64decode(xml_base64)
            root = ET.fromstring(xml_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al decodificar XML: {str(e)}")
        
        # Extraer datos del XML
        monto_total = float(root.attrib.get('Total', '0.0'))
        moneda_xml = root.attrib.get('Moneda', 'MXN')
        rfc_emisor = "DESCONOCIDO"
        nombre_emisor = "DESCONOCIDO"
        uuid_xml = "S/F"
        uso_cfdi = ""
        forma_pago = ""
        metodo_pago = ""
        clave_sat = ""
        descripcion_concepto = ""
        
        for elem in root.iter():
            if elem.tag.endswith('Emisor'):
                rfc_emisor = elem.attrib.get('Rfc', 'DESCONOCIDO')
                nombre_emisor = elem.attrib.get('Nombre', 'DESCONOCIDO')
            if elem.tag.endswith('TimbreFiscalDigital'):
                uuid_xml = elem.attrib.get('UUID', 'S/F')
            if elem.tag.endswith('Receptor'):
                uso_cfdi = elem.attrib.get('UsoCFDI', '')
            if elem.tag.endswith('Concepto'):
                if not clave_sat:  # Solo el primer concepto
                    clave_sat = elem.attrib.get('ClaveProdServ', '')
                    descripcion = elem.attrib.get('Descripcion', '')
                    descripcion_concepto = descripcion[:200] if descripcion else ''
        
        forma_pago = root.attrib.get('FormaPago', '')
        metodo_pago = root.attrib.get('MetodoPago', '')
        
        # Obtener datos logísticos del cuerpo
        centro_costo = datos.get('centro_costo', 'Administración')
        subcatalogo = datos.get('subcatalogo', '')
        porcentaje = datos.get('porcentaje', '100%')
        fecha_pago = datos.get('fecha_pago', 'POR DEFINIR')
        moneda = datos.get('moneda', moneda_xml)
        
        # Validar porcentajes
        if not validar_porcentajes(porcentaje):
            raise HTTPException(status_code=400, detail="Los porcentajes no suman 100%")
        
        # Crear registro en la base de datos
        db = SessionLocal()
        nuevo_doc = DBDocument(
            tipo="XML",
            remitente_rfc=rfc_emisor,
            nombre=nombre_emisor,
            total=monto_total,
            uuid_folio=uuid_xml,
            subido_por=usuario,
            centro_costo=centro_costo,
            subcatalogo_centro=subcatalogo,
            porcentaje_centro=porcentaje,
            fecha_pago=fecha_pago,
            uso_cfdi=uso_cfdi,
            forma_pago=forma_pago,
            metodo_pago=metodo_pago,
            clave_sat=clave_sat,
            descripcion_sat=descripcion_concepto,
            descripcion_concepto=descripcion_concepto,
            moneda=moneda,
            comentarios=""
        )
        
        db.add(nuevo_doc)
        db.commit()
        db.refresh(nuevo_doc)

        from routers.documents import registrar_historial
        registrar_historial(db, nuevo_doc.id, "Creado (Webhook/Correo)", usuario)
        
        # Si hay PDF, guardarlo
        if pdf_base64:
            try:
                pdf_content = base64.b64decode(pdf_base64)
                pdf_path = f"uploads/{nuevo_doc.id}_{pdf_filename}"
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_content)
                nuevo_doc.comprobante_pdf = pdf_path
                db.commit()
            except Exception as e:
                print(f"Error guardando PDF: {str(e)}")
        
        db.close()
        
        return {
            "status": "ok",
            "message": "Registro creado exitosamente",
            "id": nuevo_doc.id,
            "rfc": rfc_emisor,
            "nombre": nombre_emisor,
            "total": monto_total,
            "uuid": uuid_xml
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando correo: {str(e)}")

def validar_porcentajes(porcentaje_str: str) -> bool:
    """Valida que los porcentajes sumen 100%"""
    if not porcentaje_str or porcentaje_str == '100%':
        return True
    
    import re
    regex = r'(\d+(?:\.\d+)?)%'
    matches = re.findall(regex, porcentaje_str)
    if not matches:
        return False
    
    suma = sum(float(match) for match in matches)
    return abs(suma - 100) < 0.01
