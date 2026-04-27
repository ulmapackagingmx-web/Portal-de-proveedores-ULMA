import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from database import get_db
from models import DBDocument, DBUser
from security import get_current_user

# Creamos el router principal para las subidas
router = APIRouter(prefix="/api", tags=["Subidas"])

@router.post("/subir-xml")
async def procesar_xml(files: List[UploadFile] = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        for file in files:
            contenido = await file.read()
            root = ET.fromstring(contenido)
            monto_total = float(root.attrib.get('Total', '0.0'))
            moneda_xml = root.attrib.get('Moneda', 'MXN')
            rfc_emisor = "DESCONOCIDO"
            nombre_emisor = "DESCONOCIDO"
            uuid_xml = "S/F"
            uso_cfdi = ""
            forma_pago = ""
            metodo_pago = ""
            clave_sat = ""
            descripcion_sat = ""
            
            for elem in root.iter():
                if elem.tag.endswith('Emisor'): 
                    rfc_emisor = elem.attrib.get('Rfc', 'DESCONOCIDO')
                    nombre_emisor = elem.attrib.get('Nombre', 'DESCONOCIDO')
                if elem.tag.endswith('TimbreFiscalDigital'):
                    uuid_xml = elem.attrib.get('UUID', 'S/F')
                if elem.tag.endswith('Receptor'):
                    uso_cfdi = elem.attrib.get('UsoCFDI', '')
                if elem.tag.endswith('Concepto'):
                    if not clave_sat:  # Solo tomar el primer concepto
                        clave_sat = elem.attrib.get('ClaveProdServ', '')
                        descripcion_sat = elem.attrib.get('Descripcion', '')
                        descripcion_sat = descripcion_sat[:200] if descripcion_sat else ''  # Limitar longitud
            
            # Obtener forma y método de pago del nodo raíz
            forma_pago = root.attrib.get('FormaPago', '')
            metodo_pago = root.attrib.get('MetodoPago', '')
            
            nuevo_doc = DBDocument(
                tipo="XML", 
                remitente_rfc=rfc_emisor, 
                nombre=nombre_emisor, 
                total=monto_total, 
                uuid_folio=uuid_xml, 
                subido_por=current_user.username,
                uso_cfdi=uso_cfdi,
                forma_pago=forma_pago,
                metodo_pago=metodo_pago,
                clave_sat=clave_sat,
                descripcion_sat=descripcion_sat,
                descripcion_concepto=descripcion_sat,  # Guardar la descripción del concepto
                moneda=moneda_xml
            )
            db.add(nuevo_doc)
        db.commit()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/subir-texto")
def procesar_texto(texto_correo: str = Form(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    texto = texto_correo.upper()
    rfc_match = re.search(r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}', texto)
    rfc = rfc_match.group(0) if rfc_match else "S/R"
    monto_match = re.search(r'(?:CANTIDAD DE|\$)\s*([\d,]+(?:\.\d{2})?)', texto)
    if not monto_match: monto_match = re.search(r'([\d,]+(?:\.\d{2})?)\s*PESOS', texto)
    monto = float(monto_match.group(1).replace(',', '')) if monto_match else 0.0
    nombre_match = re.search(r'PAGAR\s+(.*?)\s+(?:CON RFC|LA CANTIDAD)', texto)
    nombre = nombre_match.group(1).strip() if nombre_match else "EXTRAÍDO DE CORREO"
    fecha_match = re.search(r'(\d{1,2}\s+DE\s+[A-Z]+\s+DE\s+\d{4})', texto)
    fecha = fecha_match.group(1) if fecha_match else "POR DEFINIR"
    centro_match = re.search(r'CENTRO\s+(\w+)', texto)
    centro = centro_match.group(1) if centro_match else "Administración"
    folio_match = re.search(r'FOLIO\s*:?\s*([A-Z0-9\-]+)', texto)
    folio = folio_match.group(1) if folio_match else "S/F"
    moneda_match = re.search(r'MONEDA\s+([A-Z]{3})', texto)
    moneda = moneda_match.group(1) if moneda_match else "MXN"
    nuevo_doc = DBDocument(tipo="CORREO", remitente_rfc=rfc, nombre=nombre, total=monto, uuid_folio=folio, centro_costo=centro, fecha_pago=fecha, subido_por=current_user.username, moneda=moneda)
    db.add(nuevo_doc)
    db.commit()
    return {"status": "ok"}

@router.post("/subir-excel")
async def procesar_excel(file: UploadFile = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        for index, row in df.iterrows():
            rfc = str(row.get('RFC', 'S/R'))
            nombre = str(row.get('Nombre', 'DESCONOCIDO'))
            total = float(row.get('Total', 0.0))
            centro = str(row.get('Centro', 'Administración'))
            folio = str(row.get('Folio', 'S/F')) 
            moneda = str(row.get('Moneda', 'MXN'))
            fecha_val = row.get('Fecha Pago', 'POR DEFINIR')
            if isinstance(fecha_val, datetime): fecha = fecha_val.strftime('%Y-%m-%d')
            else: fecha = str(fecha_val)
            doc = DBDocument(tipo="EXCEL", remitente_rfc=rfc, nombre=nombre, total=total, uuid_folio=folio, centro_costo=centro, fecha_pago=fecha, subido_por=current_user.username, moneda=moneda)
            db.add(doc)
        db.commit()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/subir-manual")
def procesar_manual(datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = DBDocument(
        tipo="MANUAL", 
        remitente_rfc=datos.get("rfc"), 
        nombre=datos.get("nombre"), 
        total=datos.get("total"), 
        uuid_folio=datos.get("folio", "S/F"), 
        centro_costo=datos.get("centro"), 
        subcatalogo_centro=datos.get("subcatalogo", ""),
        porcentaje_centro=datos.get("porcentaje", "100%"),
        fecha_pago=datos.get("fecha"), 
        subido_por=current_user.username,
        moneda=datos.get("moneda", "MXN")
    )
    db.add(doc)
    db.commit()
    return {"status": "ok"}
