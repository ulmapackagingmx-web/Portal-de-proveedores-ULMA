import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, DBUser, DBDocument, DBHistory, DBProvider
from security import get_current_user, get_password_hash
from permissions import (
    obtener_usuarios_permitidos,
    puede_editar,
    puede_eliminar,
    puede_autorizar,
    puede_subir_comprobante_pago,
    puede_exportar
)

# Creamos el router para documentos
router = APIRouter(prefix="/api", tags=["Documentos y Utilidades"])

def validate_porcentaje_pago(db: Session, uuid_folio: str, nuevo_porcentaje: float, doc_id_excluido: int = None):
    if not uuid_folio or uuid_folio == "S/F":
        return
    query = db.query(DBDocument).filter(DBDocument.uuid_folio == uuid_folio)
    if doc_id_excluido:
        query = query.filter(DBDocument.id != doc_id_excluido)
    
    total = sum([(d.porcentaje_pago if d.porcentaje_pago is not None else 0.0) for d in query.all()])
    if total + nuevo_porcentaje > 100.0:
        raise HTTPException(
            status_code=400, 
            detail=f"La factura o UUID {uuid_folio} ya fue subida y rebasa el 100% de pago."
        )

def registrar_historial(db: Session, doc_id: int, accion: str, usuario: str, motivo: str = ""):
    # Evitar duplicados exactos en el mismo segundo para el mismo doc
    from datetime import datetime, timedelta
    ahora = datetime.utcnow()
    existente = db.query(DBHistory).filter(
        DBHistory.document_id == doc_id,
        DBHistory.accion == accion,
        DBHistory.usuario == usuario,
        DBHistory.fecha >= ahora - timedelta(seconds=2)
    ).first()
    
    if not existente:
        historial = DBHistory(document_id=doc_id, accion=accion, usuario=usuario, motivo=motivo)
        db.add(historial)
    # No hacemos commit aquí para evitar duplicados en la sesión

@router.post("/reset-db")
def reset_database(current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin": raise HTTPException(status_code=403, detail="No autorizado")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db.add(DBUser(username="admin", hashed_password=get_password_hash("admin123"), role="admin"))
    db.add(DBUser(username="usuario", hashed_password=get_password_hash("usuario123"), role="usuario"))
    db.commit()
    return {"status": "ok"}

@router.delete("/documentos/{doc_id}")
def eliminar_doc(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para eliminar (ahora incluye validación por estado)
    if not puede_eliminar(current_user.username, doc.subido_por, doc.estado_pago, db):
        if current_user.role == "proveedor":
            raise HTTPException(status_code=403, detail="Solo puedes eliminar tus registros si están en estado \"Rechazado\"")
        elif current_user.role == "supervisor":
            raise HTTPException(status_code=403, detail="Solo puedes eliminar registros en estado \"Pendiente\"")
        else:
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este registro")
    
    # Eliminar archivos asociados si existen
    if doc.comprobante_pdf and os.path.exists(doc.comprobante_pdf):
        os.remove(doc.comprobante_pdf)
    if doc.comprobante_pago_pdf and os.path.exists(doc.comprobante_pago_pdf):
        os.remove(doc.comprobante_pago_pdf)
    
    # IMPORTANTE: Borrar historial asociado para evitar registros huérfanos
    db.query(DBHistory).filter(DBHistory.document_id == doc_id).delete()
    
    db.delete(doc)
    db.commit()
    return {"status": "ok"}

@router.delete("/eliminar-pdf/{doc_id}")
async def eliminar_pdf(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404)
    # Verificar permisos: admin puede eliminar cualquier PDF, usuario solo sus propios documentos
    if current_user.role != "admin" and doc.subido_por != current_user.username:
        raise HTTPException(status_code=403, detail="No autorizado")
    if doc.comprobante_pdf and os.path.exists(doc.comprobante_pdf):
        os.remove(doc.comprobante_pdf)
        doc.comprobante_pdf = ""
        db.commit()
    return {"status": "ok"}

@router.put("/documentos/{doc_id}")
def editar_doc(doc_id: int, datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
        
    uuid_folio = datos.get("folio_factura", doc.uuid_folio)
    if "porcentaje_pago" in datos and current_user.role in ["admin", "supervisor"]:
        nuevo_porcentaje = float(datos.get("porcentaje_pago"))
        validate_porcentaje_pago(db, uuid_folio, nuevo_porcentaje, doc_id_excluido=doc_id)
    
    # Verificar permisos para editar
    if not puede_editar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este registro")
    
    doc.tipo_tercero = datos.get("tipo_tercero", doc.tipo_tercero)
    doc.remitente_rfc = datos.get("rfc", doc.remitente_rfc)
    doc.nombre = datos.get("nombre", doc.nombre)
    doc.total = datos.get("total", doc.total)
    doc.uuid_folio = datos.get("folio_factura", doc.uuid_folio) # Ahora folio factura
    doc.referencia_pago = datos.get("referencia_pago", doc.referencia_pago) # Nuevo campo
    doc.centro_costo = datos.get("centro_costo", doc.centro_costo)
    doc.subcatalogo_centro = datos.get("subcatalogo", doc.subcatalogo_centro)
    doc.porcentaje_centro = datos.get("porcentaje_centro", doc.porcentaje_centro)
    if "porcentaje_pago" in datos:
        if current_user.role in ["admin", "supervisor"]:
            doc.porcentaje_pago = datos.get("porcentaje_pago")
    doc.fecha_pago = datos.get("fecha_pago", doc.fecha_pago)
    doc.fecha_estimada_pago = datos.get("fecha_estimada_pago", doc.fecha_estimada_pago)
    doc.moneda = datos.get("moneda", doc.moneda)
    doc.comentarios = datos.get("comentarios", doc.comentarios)
    
    # Nuevos campos para REFACCIONES
    doc.naturaleza = datos.get("naturaleza", doc.naturaleza)
    doc.numero_pedido = datos.get("numero_pedido", doc.numero_pedido) # Nuevo campo
    # doc.cliente = datos.get("cliente", doc.cliente) # Eliminado
    # doc.modelo_maquina = datos.get("modelo_maquina", doc.modelo_maquina) # Eliminado
    # doc.numero_serie = datos.get("numero_serie", doc.numero_serie) # Eliminado
    registrar_historial(db, doc.id, "Editado", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.post("/subir-pdf/{doc_id}")
async def subir_pdf(doc_id: int, file: UploadFile = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404)
    file_path = f"uploads/{doc_id}_{file.filename}"
    with open(file_path, "wb") as buffer: buffer.write(await file.read())
    doc.comprobante_pdf = file_path 
    db.commit()
    return {"status": "ok"}

@router.get("/descargar-pdf/{doc_id}")
def descargar_pdf(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if doc and doc.comprobante_pdf and os.path.exists(doc.comprobante_pdf):
        return FileResponse(doc.comprobante_pdf, filename=os.path.basename(doc.comprobante_pdf))
    raise HTTPException(status_code=404, detail="PDF no encontrado")

@router.put("/avanzar-estado/{doc_id}")
def avanzar_estado(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para autorizar
    if not puede_autorizar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para cambiar el estado de este registro")
    
    if doc.estado_pago == "Pendiente":
        doc.estado_pago = "Autorizado"
        registrar_historial(db, doc.id, "Autorizado", current_user.username)
    elif doc.estado_pago == "Autorizado":
        doc.estado_pago = "Pagado"
        registrar_historial(db, doc.id, "Pagado", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.put("/retroceder-estado/{doc_id}")
def retroceder_estado(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para revertir estado
    if not puede_autorizar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para revertir el estado de este registro")
    
    if doc.estado_pago == "Pagado":
        doc.estado_pago = "Autorizado"
        registrar_historial(db, doc.id, "Revertido a Autorizado", current_user.username)
    elif doc.estado_pago == "Autorizado":
        doc.estado_pago = "Pendiente"
        registrar_historial(db, doc.id, "Revertido a Pendiente", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.put("/rechazar-registro/{doc_id}")
def rechazar_registro(doc_id: int, datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para rechazar (solo supervisores y admin)
    if not puede_autorizar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para rechazar este registro")
    
    # Solo se puede rechazar si está en Pendiente
    if doc.estado_pago != "Pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden rechazar registros en estado Pendiente")
    
    motivo = datos.get("motivo", "Sin motivo")
    doc.estado_pago = "Rechazado"
    registrar_historial(db, doc.id, "Rechazado", current_user.username, motivo)
    db.commit()
    return {"status": "ok"}

@router.put("/enviar-correccion/{doc_id}")
def enviar_correccion(doc_id: int, current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Solo el dueño puede enviar corrección
    if doc.subido_por != current_user.username:
        raise HTTPException(status_code=403, detail="Solo el creador del registro puede enviar correcciones")
    
    if doc.estado_pago != "Rechazado":
        raise HTTPException(status_code=400, detail="Solo se pueden corregir registros rechazados")
    
    doc.estado_pago = "Pendiente"
    registrar_historial(db, doc.id, "Corrección Enviada", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.post("/subir-comprobante-pago/{doc_id}")
async def subir_comprobante_pago(doc_id: int, file: UploadFile = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para subir comprobante de pago
    if not puede_subir_comprobante_pago(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para subir comprobante de pago")
    
    file_path = f"uploads/{doc_id}_pago_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    doc.comprobante_pago_pdf = file_path
    doc.estado_pago = "Pagado"
    registrar_historial(db, doc.id, "Pagado (Comprobante)", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.get("/descargar-comprobante-pago/{doc_id}")
def descargar_comprobante_pago(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if doc and doc.comprobante_pago_pdf and os.path.exists(doc.comprobante_pago_pdf):
        return FileResponse(doc.comprobante_pago_pdf, filename=os.path.basename(doc.comprobante_pago_pdf))
    raise HTTPException(status_code=404, detail="Comprobante no encontrado")

@router.post("/subir-otros-documentos/{doc_id}")
async def subir_otros_documentos(doc_id: int, file: UploadFile = File(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if not puede_editar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para subir otros documentos")
    
    file_path = f"uploads/{doc_id}_otros_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    doc.otros_documentos_pdf = file_path
    registrar_historial(db, doc.id, "Subido 'Otro Documento'", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.get("/descargar-otros-documentos/{doc_id}")
def descargar_otros_documentos(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if doc and doc.otros_documentos_pdf and os.path.exists(doc.otros_documentos_pdf):
        return FileResponse(doc.otros_documentos_pdf, filename=os.path.basename(doc.otros_documentos_pdf))
    raise HTTPException(status_code=404, detail="'Otro Documento' no encontrado")

from typing import Optional

@router.get("/ver-datos")
def ver_datos(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    origen: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_, and_, func
    from datetime import datetime

    query = db.query(DBDocument)

    # Filtrar por rol
    if current_user.role == "proveedor":
        query = query.filter(DBDocument.subido_por == current_user.username)
    elif current_user.role == "supervisor":
        usuarios_subordinados = current_user.subordinados.split(",") if current_user.subordinados else []
        usuarios_subordinados = [u.strip() for u in usuarios_subordinados if u.strip()]
        usuarios_a_mostrar = [current_user.username] + usuarios_subordinados
        query = query.filter(DBDocument.subido_por.in_(usuarios_a_mostrar))

    # Filtros de búsqueda (texto)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DBDocument.nombre.ilike(search_term),
                DBDocument.remitente_rfc.ilike(search_term),
                DBDocument.uuid_folio.ilike(search_term),
                DBDocument.referencia_pago.ilike(search_term),
                DBDocument.centro_costo.ilike(search_term)
            )
        )
        
    # Filtro de origen
    if origen:
        query = query.filter(DBDocument.tipo == origen)

    # Filtros de fecha (sobre fecha_estimada_pago)
    if fecha_inicio:
        query = query.filter(DBDocument.fecha_estimada_pago >= fecha_inicio, DBDocument.fecha_estimada_pago != "POR DEFINIR")
    if fecha_fin:
        query = query.filter(DBDocument.fecha_estimada_pago <= fecha_fin, DBDocument.fecha_estimada_pago != "POR DEFINIR")

    # Calcular KPIs sobre los registros filtrados (antes del filtro de estado)
    all_kpi_records = query.with_entities(DBDocument.estado_pago, DBDocument.total, DBDocument.fecha_registro).all()

    # Filtro de estado
    if estado:
        if estado == "pagado_mes":
            query = query.filter(DBDocument.estado_pago == "Pagado")
            # Podríamos añadir un filtro por mes actual si fuera necesario
            from datetime import datetime
            hoy = datetime.utcnow()
            query = query.filter(func.extract('year', DBDocument.fecha_registro) == hoy.year)
            query = query.filter(func.extract('month', DBDocument.fecha_registro) == hoy.month)
        elif estado == "en_proceso":
            query = query.filter(DBDocument.estado_pago == "Autorizado")
        elif estado == "rechazado":
            query = query.filter(DBDocument.estado_pago == "Rechazado")
        elif estado == "pendiente":
            query = query.filter(DBDocument.estado_pago == "Pendiente")

    total_count = query.count()
    hoy = datetime.utcnow()
    total_pagado_mes = 0.0
    total_en_proceso = 0.0
    total_rechazado = 0.0
    total_pendiente = 0.0
    for st, tot, f_reg in all_kpi_records:
        t = tot if tot else 0.0
        if st == "Pagado" and f_reg and f_reg.year == hoy.year and f_reg.month == hoy.month:
            total_pagado_mes += t
        elif st == "Autorizado":
            total_en_proceso += t
        elif st == "Rechazado":
            total_rechazado += t
        elif st == "Pendiente":
            total_pendiente += t

    kpis = {
        "total_registros": total_count,
        "total_pagado_mes": total_pagado_mes,
        "total_en_proceso": total_en_proceso,
        "total_rechazado": total_rechazado,
        "total_pendiente": total_pendiente,
    }

    # Paginación
    registros = query.order_by(DBDocument.id.desc()).offset(skip).limit(limit).all()

    resultado = []
    for r in registros:
        historial = db.query(DBHistory).filter(DBHistory.document_id == r.id).order_by(DBHistory.fecha.asc()).all()
        r_dict = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        if current_user.role not in ["admin", "supervisor"]:
            r_dict.pop("porcentaje_pago", None)
        r_dict["historial"] = [{
            "accion": h.accion,
            "motivo": h.motivo,
            "usuario": h.usuario,
            "fecha": h.fecha.strftime("%Y-%m-%d %H:%M")
        } for h in historial]
        resultado.append(r_dict)

    return {
        "registros": resultado, 
        "role": current_user.role, 
        "kpis": kpis,
        "total_count": total_count,
        "skip": skip,
        "limit": limit
    }

@router.post("/descargar-excel")
def descargar_excel(datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar permisos para exportar
    if not puede_exportar(current_user.username, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para exportar")
    
    ids = datos.get("ids")
    campos = datos.get("campos", [])
    
    # Obtener registros según permisos
    usuarios_permitidos = obtener_usuarios_permitidos(current_user.username, db)
    query = db.query(DBDocument).filter(DBDocument.subido_por.in_(usuarios_permitidos))
    
    if ids:
        query = query.filter(DBDocument.id.in_(ids))
    
    docs = query.order_by(DBDocument.id.desc()).all()
    
    providers = db.query(DBProvider).all()
    provider_map = {p.rfc_proveedor.upper(): p for p in providers if p.rfc_proveedor}

    # Diccionario de todos los campos posibles
    all_data = []
    for d in docs:
        prov = provider_map.get((d.remitente_rfc or "").upper())
        # Parsear el expediente
        expediente_str = ""
        if prov and prov.expediente:
            import json
            try:
                exp_dict = json.loads(prov.expediente)
                expediente_str = ", ".join([f"{k}: {'Sí' if v else 'No'}" for k, v in exp_dict.items()])
            except:
                expediente_str = prov.expediente

        row = {
            "ID": d.id,
            "Origen": d.tipo,
            "RFC Emisor": d.remitente_rfc,
            "Nombre Emisor": d.nombre,
            "Tipo de Tercero": d.tipo_tercero,
            "FOLIO FACTURA": d.uuid_folio,
            "REFERENCIA DE PAGO": d.referencia_pago,
            "Total": d.total,
            "Moneda": d.moneda,
            "Fecha Emisión": d.fecha_emision,
            "Fecha Registro": d.fecha_registro.strftime("%Y-%m-%d %H:%M") if d.fecha_registro else "",
            "Usuario": d.subido_por,
            "Centro Costo": d.centro_costo,
            "Subcatálogo": d.subcatalogo_centro,
            "Porcentaje": d.porcentaje_centro,
            "Fecha Pago": d.fecha_pago,
            "Estado": d.estado_pago,
            "Fecha Estimada de Pago": d.fecha_estimada_pago,
            "Uso CFDI": d.uso_cfdi,
            "Forma Pago": d.forma_pago,
            "Método Pago": d.metodo_pago,
            "Clave SAT": d.clave_sat,
            "Descripción SAT": d.descripcion_sat,
            "Comentarios": d.comentarios,
            "Porcentaje Pago (Registro)": d.porcentaje_pago,
            "Proveedor Registrado": "Sí" if prov else "No",
            "Banco (Proveedor)": prov.banco if prov else "",
            "Cuenta/CLABE (Proveedor)": prov.numero_cuenta_clabe if prov else "",
            "Tipo Operación (Proveedor)": prov.tipo_operacion if prov else "",
            "Expediente (Proveedor)": expediente_str,
            "Validación Bancaria": "Sí" if prov and prov.validacion_bancaria else "No",
            "Validación Expediente": "Sí" if prov and prov.validacion_expediente else "No",
            "Email (Proveedor)": prov.email_contacto if prov else "",
            "Campo Libre (Proveedor)": prov.campo_libre if prov else "",
        }
        
        # Si se especificaron campos, filtrar, si no, enviar todos
        if campos:
            filtered_row = {k: v for k, v in row.items() if k in campos}
            all_data.append(filtered_row)
        else:
            all_data.append(row)

    df = pd.DataFrame(all_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, headers={"Content-Disposition": "attachment; filename=\"DataHub_Reporte.xlsx\""})

@router.post("/documentos/bulk-delete")
def bulk_eliminar_docs(datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = datos.get("ids", [])
    if not ids:
        return {"status": "ok", "deleted": 0}
    
    docs = db.query(DBDocument).filter(DBDocument.id.in_(ids)).all()
    deleted_count = 0
    
    for doc in docs:
        if puede_eliminar(current_user.username, doc.subido_por, doc.estado_pago, db):
            # Eliminar archivos asociados
            if doc.comprobante_pdf and os.path.exists(doc.comprobante_pdf):
                os.remove(doc.comprobante_pdf)
            if doc.comprobante_pago_pdf and os.path.exists(doc.comprobante_pago_pdf):
                os.remove(doc.comprobante_pago_pdf)
            db.query(DBHistory).filter(DBHistory.document_id == doc.id).delete()
            db.delete(doc)
            deleted_count += 1
            
    db.commit()
    return {"status": "ok", "deleted": deleted_count}


@router.post("/documentos/duplicate")
def duplicar_docs(datos: dict = Body(...), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Duplica (clona) los documentos seleccionados por id.
    Crea nuevos registros copiando los campos del documento original,
    reinicia el estado a 'Pendiente', los asigna al usuario actual y
    deja los comprobantes/PDF sin referencia (el duplicado es un registro nuevo).
    """
    ids = datos.get("ids", [])
    if not ids:
        return {"status": "ok", "duplicated": 0}

    docs = db.query(DBDocument).filter(DBDocument.id.in_(ids)).all()
    duplicated = 0

    for doc in docs:
        # Solo duplicar registros sobre los que el usuario puede editar
        if not puede_editar(current_user.username, doc.subido_por, db):
            continue

        nuevo = DBDocument(
            tipo=doc.tipo,
            tipo_tercero=doc.tipo_tercero,
            remitente_rfc=doc.remitente_rfc,
            nombre=doc.nombre,
            uuid_folio=doc.uuid_folio,
            referencia_pago=doc.referencia_pago,
            total=doc.total,
            fecha_emision=doc.fecha_emision,
            subido_por=current_user.username,
            centro_costo=doc.centro_costo,
            subcatalogo_centro=doc.subcatalogo_centro,
            porcentaje_centro=doc.porcentaje_centro,
            porcentaje_pago=doc.porcentaje_pago,
            fecha_pago=doc.fecha_pago,
            estado_pago="Pendiente",
            fecha_estimada_pago=doc.fecha_estimada_pago,
            regimen_fiscal_emisor=doc.regimen_fiscal_emisor,
            traslados=doc.traslados,
            retenciones=doc.retenciones,
            uso_cfdi=doc.uso_cfdi,
            forma_pago=doc.forma_pago,
            metodo_pago=doc.metodo_pago,
            clave_sat=doc.clave_sat,
            descripcion_sat=doc.descripcion_sat,
            descripcion_concepto=doc.descripcion_concepto,
            moneda=doc.moneda,
            comentarios=doc.comentarios,
            naturaleza=doc.naturaleza,
            numero_pedido=doc.numero_pedido,
            cliente=doc.cliente,
            modelo_maquina=doc.modelo_maquina,
            numero_serie=doc.numero_serie,
        )
        db.add(nuevo)
        db.flush()
        registrar_historial(db, nuevo.id, "Duplicado", current_user.username)
        duplicated += 1

    db.commit()
    return {"status": "ok", "duplicated": duplicated}


