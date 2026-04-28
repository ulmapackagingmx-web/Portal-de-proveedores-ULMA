import os
import io
import json
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, DBUser, DBDocument
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

def agregar_evento_historial(doc: DBDocument, evento: str, usuario: str, motivo: str = ""):
    """Agrega un evento al historial del documento."""
    try:
        historial = json.loads(doc.historial or "[]")
    except Exception:
        historial = []
    entrada = {
        "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "evento": evento,
        "usuario": usuario,
    }
    if motivo:
        entrada["motivo"] = motivo
    historial.append(entrada)
    doc.historial = json.dumps(historial, ensure_ascii=False)

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
            raise HTTPException(status_code=403, detail="Solo puedes eliminar tus registros si están en estado 'Rechazado'")
        elif current_user.role == "supervisor":
            raise HTTPException(status_code=403, detail="Solo puedes eliminar registros en estado 'Pendiente'")
        else:
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este registro")
    
    # Eliminar archivos asociados si existen
    if doc.comprobante_pdf and os.path.exists(doc.comprobante_pdf):
        os.remove(doc.comprobante_pdf)
    if doc.comprobante_pago_pdf and os.path.exists(doc.comprobante_pago_pdf):
        os.remove(doc.comprobante_pago_pdf)
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
    
    # Verificar permisos para editar
    if not puede_editar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este registro")
    
    doc.remitente_rfc = datos.get('rfc', doc.remitente_rfc)
    doc.nombre = datos.get('nombre', doc.nombre)
    doc.total = datos.get('total', doc.total)
    doc.uuid_folio = datos.get('folio', doc.uuid_folio)
    doc.centro_costo = datos.get('centro_costo', doc.centro_costo)
    doc.subcatalogo_centro = datos.get('subcatalogo', doc.subcatalogo_centro)
    doc.porcentaje_centro = datos.get('porcentaje_centro', doc.porcentaje_centro)
    doc.fecha_pago = datos.get('fecha_pago', doc.fecha_pago)
    doc.moneda = datos.get('moneda', doc.moneda)
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
        agregar_evento_historial(doc, "En proceso de autorización", current_user.username)
    elif doc.estado_pago == "Autorizado":
        doc.estado_pago = "Pagado"
        agregar_evento_historial(doc, "Pagado", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.put("/retroceder-estado/{doc_id}")
def retroceder_estado(doc_id: int, datos: dict = Body(default={}), current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar permisos para revertir estado
    if not puede_autorizar(current_user.username, doc.subido_por, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para revertir el estado de este registro")
    
    motivo = datos.get("motivo", "").strip()
    if not motivo:
        raise HTTPException(status_code=400, detail="Debes indicar el motivo de revocación")

    if doc.estado_pago == "Pagado":
        doc.estado_pago = "Autorizado"
        agregar_evento_historial(doc, "Pago revertido", current_user.username, motivo)
    elif doc.estado_pago == "Autorizado":
        doc.estado_pago = "Pendiente"
        agregar_evento_historial(doc, "Autorización revocada", current_user.username, motivo)
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
    
    motivo = datos.get("motivo", "").strip()
    if not motivo:
        raise HTTPException(status_code=400, detail="Debes indicar el motivo de rechazo")

    doc.estado_pago = "Rechazado"
    agregar_evento_historial(doc, "Rechazado", current_user.username, motivo)
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
    agregar_evento_historial(doc, "Pagado", current_user.username)
    db.commit()
    return {"status": "ok"}

@router.get("/descargar-comprobante-pago/{doc_id}")
def descargar_comprobante_pago(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if doc and doc.comprobante_pago_pdf and os.path.exists(doc.comprobante_pago_pdf):
        return FileResponse(doc.comprobante_pago_pdf, filename=os.path.basename(doc.comprobante_pago_pdf))
    raise HTTPException(status_code=404, detail="Comprobante no encontrado")

@router.get("/ver-datos")
def ver_datos(current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Obtener lista de usuarios cuyos registros puede ver
    usuarios_permitidos = obtener_usuarios_permitidos(current_user.username, db)
    
    # Filtrar registros según permisos
    registros = db.query(DBDocument).filter(
        DBDocument.subido_por.in_(usuarios_permitidos)
    ).order_by(DBDocument.id.desc()).all()
    
    return {"registros": registros, "role": current_user.role}

@router.get("/descargar-excel")
def descargar_excel(current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar permisos para exportar
    if not puede_exportar(current_user.username, db):
        raise HTTPException(status_code=403, detail="No tienes permisos para exportar")
    
    # Obtener registros según permisos
    usuarios_permitidos = obtener_usuarios_permitidos(current_user.username, db)
    docs = db.query(DBDocument).filter(
        DBDocument.subido_por.in_(usuarios_permitidos)
    ).order_by(DBDocument.id.desc()).all()
    
    data = [{"ID": d.id, "Origen": d.tipo, "RFC": d.remitente_rfc, "Nombre": d.nombre, "UUID/Folio": d.uuid_folio, "Total": d.total, "C. Costo": d.centro_costo, 
             "Fecha Pago": d.fecha_pago, "Estado": d.estado_pago, "Usuario": d.subido_por} for d in docs]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, headers={'Content-Disposition': 'attachment; filename="DataHub_Ulma_Reporte.xlsx"'})
