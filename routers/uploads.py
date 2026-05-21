import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from database import get_db
from models import DBDocument, DBUser, DBProvider
from security import get_current_user
from routers.documents import registrar_historial # Moved to top for consistency

# Creamos el router principal para las subidas
router = APIRouter(prefix="/api", tags=["Subidas"])

async def get_or_create_provider(db: Session, rfc: str, nombre: str):
    provider = db.query(DBProvider).filter(DBProvider.rfc_proveedor == rfc).first()
    if not provider:
        provider = DBProvider(rfc_proveedor=rfc, nombre_proveedor=nombre)
        db.add(provider)
        db.flush() # Para obtener el ID del nuevo proveedor si es necesario
    return provider

@router.post("/subir-xml")
async def procesar_xml(files: List[UploadFile] = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        for file in files:
            contenido = await file.read()
            root = ET.fromstring(contenido)
            monto_total = float(root.attrib.get("Total", "0.0"))
            moneda_xml = root.attrib.get("Moneda", "MXN")
            rfc_emisor = "DESCONOCIDO"
            nombre_emisor = "DESCONOCIDO"
            uuid_xml = "S/F"
            uso_cfdi = ""
            forma_pago = root.attrib.get("FormaPago", "")
            metodo_pago = root.attrib.get("MetodoPago", "")
            clave_sat = ""
            descripcion_sat = ""
            regimen_fiscal_emisor = ""
            traslados_info = []
            retenciones_info = []
            
            for elem in root.iter():
                # Obtener el nombre de la etiqueta sin el namespace (lo que va después de })
                tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                # Verificar si es una etiqueta oficial del SAT (CFDI)
                is_cfdi = "http://www.sat.gob.mx/cfd/" in elem.tag
                is_tfd = "http://www.sat.gob.mx/TimbreFiscalDigital" in elem.tag

                if is_cfdi and tag_local == "Emisor":
                    rfc_emisor = elem.attrib.get("Rfc", rfc_emisor)
                    nombre_emisor = elem.attrib.get("Nombre", nombre_emisor)
                    regimen_fiscal_emisor = elem.attrib.get("RegimenFiscal", regimen_fiscal_emisor)
                elif is_tfd and tag_local == "TimbreFiscalDigital":
                    uuid_xml = elem.attrib.get("UUID", uuid_xml)
                elif is_cfdi and tag_local == "Receptor":
                    uso_cfdi = elem.attrib.get("UsoCFDI", uso_cfdi)
                elif is_cfdi and tag_local == "Concepto":
                    if not clave_sat:
                        clave_sat = elem.attrib.get("ClaveProdServ", "").strip() if elem.attrib.get("ClaveProdServ") else ""
                        descripcion_sat = elem.attrib.get("Descripcion", "").strip() if elem.attrib.get("Descripcion") else ""
                        descripcion_sat = descripcion_sat[:200] # Limitar a 200 caracteres para evitar errores en DB
                    # Buscar impuestos dentro de cada concepto
                    impuestos_elem = elem.find(".//{http://www.sat.gob.mx/cfd/3}Impuestos")
                    if impuestos_elem is not None:
                        # Traslados
                        for traslado in impuestos_elem.findall(".//{http://www.sat.gob.mx/cfd/3}Traslado"):
                            tasa = traslado.attrib.get("TasaOCuota")
                            tipo = traslado.attrib.get("Impuesto")
                            if tasa and tipo:
                                traslados_info.append(f"Traslado {tipo}: {float(tasa)*100}%")
                        # Retenciones
                        for retencion in impuestos_elem.findall(".//{http://www.sat.gob.mx/cfd/3}Retencion"):
                            tasa = retencion.attrib.get("TasaOCuota")
                            tipo = retencion.attrib.get("Impuesto")
                            if tasa and tipo:
                                retenciones_info.append(f"Retención {tipo}: {float(tasa)*100}%")

            # --- Lógica de Autoregistro de Proveedores (XML) ---
            await get_or_create_provider(db, rfc_emisor, nombre_emisor)
            # ---------------------------------------------------

            fecha_xml = root.attrib.get("Fecha", "POR DEFINIR")
            if 'T' in fecha_xml: fecha_xml = fecha_xml.split('T')[0]
            
            nuevo_doc = DBDocument(
                tipo="XML",
                remitente_rfc=rfc_emisor, 
                nombre=nombre_emisor, 
                total=monto_total, 
                uuid_folio=uuid_xml, 
                subido_por=current_user.username,
                regimen_fiscal_emisor=regimen_fiscal_emisor,
                traslados=', '.join(list(set(traslados_info))),
                retenciones=', '.join(list(set(retenciones_info))),
                uso_cfdi=uso_cfdi,
                forma_pago=forma_pago,
                metodo_pago=metodo_pago,
                clave_sat=clave_sat,
                descripcion_sat=descripcion_sat,
                descripcion_concepto=descripcion_sat,  # Guardar la descripción del concepto
                moneda=moneda_xml,
                comentarios="",
                fecha_emision=fecha_xml
            )
            db.add(nuevo_doc)
            db.flush() # Obtener ID sin cerrar transaccion
            registrar_historial(db, nuevo_doc.id, "Creado (XML)", current_user.username)
        db.commit()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/subir-texto")
async def procesar_texto(texto_correo: str = Form(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    texto = texto_correo.upper()
    rfc_match = re.search(r'[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}', texto)
    rfc = rfc_match.group(0) if rfc_match else "S/R"
    monto_match = re.search(r'(?:CANTIDAD DE|\$)\s*([\d,]+(?:\.\d{2})?)', texto)
    if not monto_match: monto_match = re.search(r'(?:CANTIDAD DE|\$)\s*([\d,]+(?:\.\d{2})?)', texto)
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

    # --- Lógica de Autoregistro de Proveedores (Texto/Correo) ---
    await get_or_create_provider(db, rfc, nombre)
    # -----------------------------------------------------------

    nuevo_doc = DBDocument(tipo="CORREO", remitente_rfc=rfc, nombre=nombre, total=monto, uuid_folio=folio, centro_costo=centro, fecha_pago=fecha, subido_por=current_user.username, moneda=moneda, comentarios="")
    db.add(nuevo_doc)
    db.flush()
    registrar_historial(db, nuevo_doc.id, "Creado (Texto/Correo)", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.post("/subir-excel")
async def procesar_excel(file: UploadFile = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        for index, row in df.iterrows():
            rfc = str(row.get("RFC", "S/R"))
            nombre = str(row.get("Nombre", "DESCONOCIDO"))
            total = float(row.get("Total", 0.0))
            centro = str(row.get("Centro", "Administración"))
            folio = str(row.get("Folio", "S/F")) 
            moneda = str(row.get("Moneda", "MXN"))
            fecha_val = row.get("Fecha Pago", "POR DEFINIR")
            if isinstance(fecha_val, datetime): fecha = fecha_val.strftime("%Y-%m-%d")
            else: fecha = str(fecha_val)

            # --- Lógica de Autoregistro de Proveedores (Excel) ---
            await get_or_create_provider(db, rfc, nombre)
            # ---------------------------------------------------

            doc = DBDocument(tipo="EXCEL", remitente_rfc=rfc, nombre=nombre, total=total, uuid_folio=folio, centro_costo=centro, fecha_pago=fecha, subido_por=current_user.username, moneda=moneda, comentarios="")
            db.add(doc)
            db.flush()
            registrar_historial(db, doc.id, "Creado (Excel)", current_user.username)
        db.commit()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/subir-manual")
async def procesar_manual(datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
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
        moneda=datos.get("moneda", "MXN"),
        comentarios=datos.get("comentarios", ""),
        naturaleza=datos.get("naturaleza", ""),
        cliente=datos.get("cliente", ""),
        modelo_maquina=datos.get("modelo_maquina", ""),
        numero_serie=datos.get("numero_serie", "")
    )

    # --- Lógica de Autoregistro de Proveedores (Manual) ---
    if doc.remitente_rfc and doc.nombre:
        await get_or_create_provider(db, doc.remitente_rfc, doc.nombre)
    # ---------------------------------------------------

    db.add(doc)
    db.flush()
    registrar_historial(db, doc.id, "Creado (Manual)", current_user.username)
    db.commit()
    return {"status": "ok"}
