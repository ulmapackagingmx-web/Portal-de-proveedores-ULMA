from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import DBProvider, DBUser
from security import get_current_user
from permissions import puede_ver_proveedores, puede_editar_proveedor, puede_eliminar_proveedor

router = APIRouter(prefix="/api/providers", tags=["Proveedores"])

@router.post("/", response_model=dict)
def create_provider(
    nombre_proveedor: str = Body(...),
    rfc_proveedor: str = Body(...),
    banco: Optional[str] = Body(None),
    numero_cuenta_clabe: Optional[str] = Body(None),
    tipo_operacion: Optional[str] = Body(None), # Nuevo campo
    referencia_bancaria: Optional[str] = Body(None), # Nuevo campo
    expediente: Optional[str] = Body(None),
    campo_libre: Optional[str] = Body(None),
    email_contacto: Optional[str] = Body(None), # Nuevo campo
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.role in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No autorizado para crear proveedores")

    # Verificar si el RFC ya existe
    existing_provider = db.query(DBProvider).filter(DBProvider.rfc_proveedor == rfc_proveedor).first()
    if existing_provider:
        raise HTTPException(status_code=400, detail="Ya existe un proveedor con este RFC")

    import json
    from datetime import datetime

    historial_inicial = [{
        "accion": "Creado",
        "usuario": current_user.username,
        "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }]

    new_provider = DBProvider(
        nombre_proveedor=nombre_proveedor,
        rfc_proveedor=rfc_proveedor,
        banco=banco or "",
        numero_cuenta_clabe=numero_cuenta_clabe or "",
        tipo_operacion=tipo_operacion or "", # Nuevo campo
        referencia_bancaria=referencia_bancaria or "", # Nuevo campo
        expediente=expediente or "",
        campo_libre=campo_libre or "",
        email_contacto=email_contacto or "",
        historial=json.dumps(historial_inicial)
    )
    db.add(new_provider)
    db.commit()
    db.refresh(new_provider)
    return {"status": "ok", "provider_id": new_provider.id}

@router.get("/", response_model=List[dict])
def get_all_providers(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Aquí puedes implementar una lógica de permisos más granular si es necesario
    # Por ahora, solo admin y supervisor pueden ver la lista completa
    if not puede_ver_proveedores(current_user.username, db):
        raise HTTPException(status_code=403, detail="No autorizado para ver la lista de proveedores")

    providers = db.query(DBProvider).all()
    result = []
    import json
    for p in providers:
        try:
            historial = json.loads(p.historial) if p.historial else []
        except:
            historial = []

        provider_data = {
            "id": p.id,
            "nombre_proveedor": p.nombre_proveedor,
            "rfc_proveedor": p.rfc_proveedor,
            "banco": p.banco,
            "numero_cuenta_clabe": p.numero_cuenta_clabe,
            "tipo_operacion": p.tipo_operacion, # Nuevo campo
            "referencia_bancaria": p.referencia_bancaria, # Nuevo campo
            "expediente": p.expediente,
            "validacion_bancaria": p.validacion_bancaria,
            "validacion_expediente": p.validacion_expediente,
            "campo_libre": p.campo_libre,
            "email_contacto": p.email_contacto,
            "historial": historial
        }
        result.append(provider_data)
    return result
@router.put("/{provider_id}", response_model=dict)
def update_provider(
    provider_id: int,
    nombre_proveedor: Optional[str] = Body(None),
    banco: Optional[str] = Body(None),
    numero_cuenta_clabe: Optional[str] = Body(None),
    tipo_operacion: Optional[str] = Body(None), # Nuevo campo
    referencia_bancaria: Optional[str] = Body(None), # Nuevo campo
    expediente: Optional[str] = Body(None),
    campo_libre: Optional[str] = Body(None),
    email_contacto: Optional[str] = Body(None), # Nuevo campo
    validacion_bancaria: Optional[bool] = Body(None),
    validacion_expediente: Optional[bool] = Body(None),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    provider = db.query(DBProvider).filter(DBProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    if not puede_editar_proveedor(current_user.username, provider.nombre_proveedor, db):
        raise HTTPException(status_code=403, detail="No autorizado para editar este proveedor")

    import json
    from datetime import datetime
    try:
        historial = json.loads(provider.historial) if provider.historial else []
    except:
        historial = []

    cambios = []

    if nombre_proveedor is not None and provider.nombre_proveedor != nombre_proveedor:
        cambios.append("Nombre")
        provider.nombre_proveedor = nombre_proveedor
    if banco is not None and provider.banco != banco:
        cambios.append("Banco")
        provider.banco = banco
    if numero_cuenta_clabe is not None and provider.numero_cuenta_clabe != numero_cuenta_clabe:
        cambios.append("Cuenta/CLABE")
        provider.numero_cuenta_clabe = numero_cuenta_clabe
    if tipo_operacion is not None and provider.tipo_operacion != tipo_operacion:
        cambios.append("Tipo Operación")
        provider.tipo_operacion = tipo_operacion # Nuevo campo
    if referencia_bancaria is not None and provider.referencia_bancaria != referencia_bancaria:
        cambios.append("Ref. Bancaria")
        provider.referencia_bancaria = referencia_bancaria # Nuevo campo
    if expediente is not None and provider.expediente != expediente:
        cambios.append("Expediente")
        provider.expediente = expediente
    if campo_libre is not None and provider.campo_libre != campo_libre:
        cambios.append("Campo Libre")
        provider.campo_libre = campo_libre
    if email_contacto is not None and provider.email_contacto != email_contacto:
        cambios.append("Email")
        provider.email_contacto = email_contacto # Nuevo campo

    # Solo admin/supervisor pueden cambiar el estado de validación
    if current_user.role in ["admin", "supervisor"]:
        if validacion_bancaria is not None and provider.validacion_bancaria != validacion_bancaria:
            cambios.append("Val. Bancaria")
            provider.validacion_bancaria = validacion_bancaria
        if validacion_expediente is not None and provider.validacion_expediente != validacion_expediente:
            cambios.append("Val. Expediente")
            provider.validacion_expediente = validacion_expediente
    else:
        # Asegurarse de que otros roles no puedan cambiar las validaciones
        if validacion_bancaria is not None or validacion_expediente is not None:
            raise HTTPException(status_code=403, detail="No autorizado para modificar estados de validación")

    if cambios:
        historial.insert(0, {
            "accion": f"Editó: {', '.join(cambios)}",
            "usuario": current_user.username,
            "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        provider.historial = json.dumps(historial)

    db.commit()
    db.refresh(provider)
    return {"status": "ok", "provider_id": provider.id}

@router.delete("/{provider_id}", response_model=dict)
def delete_provider(
    provider_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    provider = db.query(DBProvider).filter(DBProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    if not puede_eliminar_proveedor(current_user.username, provider.nombre_proveedor, db):
        raise HTTPException(status_code=403, detail="No autorizado para eliminar este proveedor")

    db.delete(provider)
    db.commit()
    return {"status": "ok"}

import os
import shutil
from fastapi import UploadFile, File

@router.post("/{provider_id}/upload-document")
def upload_provider_document(
    provider_id: int,
    document_type: str = Body(...),
    file: UploadFile = File(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    provider = db.query(DBProvider).filter(DBProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    upload_dir = f"uploads/providers/{provider_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    safe_doc_type = document_type.replace(" ", "_").replace("/", "_")
    file_path = f"{upload_dir}/{safe_doc_type}{file_extension}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    import json
    try:
        expediente_data = json.loads(provider.expediente) if provider.expediente else {}
    except:
        expediente_data = {}
        
    expediente_data[document_type] = file_path
    provider.expediente = json.dumps(expediente_data)

    try:
        historial = json.loads(provider.historial) if provider.historial else []
    except:
        historial = []

    historial.insert(0, {
        "accion": f"Subió documento: {document_type}",
        "usuario": current_user.username,
        "fecha": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    provider.historial = json.dumps(historial)

    db.commit()
    return {"status": "ok", "file_path": file_path}

@router.get("/by-rfc/{rfc}", response_model=dict)
def get_provider_by_rfc(
    rfc: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not puede_ver_proveedores(current_user.username, db):
        raise HTTPException(status_code=403, detail="No autorizado para ver detalles de proveedores")

    provider = db.query(DBProvider).filter(DBProvider.rfc_proveedor == rfc).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
    provider_data = {
        "id": provider.id,
        "nombre_proveedor": provider.nombre_proveedor,
        "rfc_proveedor": provider.rfc_proveedor,
        "banco": provider.banco,
        "numero_cuenta_clabe": provider.numero_cuenta_clabe,
        "tipo_operacion": provider.tipo_operacion, # Nuevo campo
        "referencia_bancaria": provider.referencia_bancaria, # Nuevo campo
        "expediente": provider.expediente,
        "validacion_bancaria": provider.validacion_bancaria,
        "validacion_expediente": provider.validacion_expediente,
        "campo_libre": provider.campo_libre,
        "email_contacto": provider.email_contacto
    }
    return provider_data
