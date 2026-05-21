"""
Sistema de permisos jerárquico para DataHub Ulma

Roles:
- proveedor: Solo puede ver/editar sus propios registros, no puede eliminar ni autorizar
- supervisor: Puede ver/editar/eliminar/autorizar registros de sus subordinados
- admin: Puede hacer todo con todos los registros
"""

from sqlalchemy.orm import Session
from models import DBUser

def obtener_usuarios_permitidos(username: str, db: Session) -> list:
    """
    Retorna la lista de usuarios cuyos registros puede ver el usuario actual.
    
    - proveedor: solo él mismo
    - supervisor: él mismo + sus subordinados
    - admin: todos los usuarios
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return [username]
    
    if usuario.role == "admin":
        # Admin puede ver todos los registros
        todos_usuarios = db.query(DBUser).all()
        return [u.username for u in todos_usuarios]
    
    elif usuario.role == "supervisor":
        # Supervisor puede ver sus registros + los de sus subordinados
        subordinados = usuario.subordinados.split(",") if usuario.subordinados else []
        return [username] + [s.strip() for s in subordinados if s.strip()]
    
    else:  # proveedor
        # Proveedor solo puede ver sus propios registros
        return [username]

def puede_editar(username: str, registro_usuario: str, db: Session) -> bool:
    """
    Verifica si el usuario puede editar un registro.
    
    - proveedor: solo sus propios registros
    - supervisor: sus registros + los de sus subordinados
    - admin: cualquier registro
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return False
    
    if usuario.role == "admin":
        return True
    
    if usuario.role == "supervisor":
        subordinados = usuario.subordinados.split(",") if usuario.subordinados else []
        subordinados = [s.strip() for s in subordinados if s.strip()]
        return registro_usuario == username or registro_usuario in subordinados
    
    # proveedor
    return registro_usuario == username

def puede_eliminar(username: str, registro_usuario: str, estado_pago: str, db: Session) -> bool:
    """
    Verifica si el usuario puede eliminar un registro.
    
    - Admin: Siempre puede borrar.
    - Usuario (Subordinado/Supervisor): Puede borrar sus propios registros SOLO si están "Pendiente" o "Rechazado".
    - Supervisor: Puede borrar registros de subordinados si están en "Pendiente".
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    if not usuario: return False
    
    # El Admin puede borrar cualquier cosa en cualquier estado
    if usuario.role == "admin": return True
    
    # REGLA SOLICITADA: Dueño puede borrar si está Pendiente o Rechazado
    if registro_usuario == username:
        return estado_pago in ["Pendiente", "Rechazado"]
    
    # El supervisor puede borrar los de sus subordinados si aún están en Pendiente
    if usuario.role == "supervisor":
        subordinados = usuario.subordinados.split(",") if usuario.subordinados else []
        subordinados = [s.strip() for s in subordinados if s.strip()]
        return registro_usuario in subordinados and estado_pago == "Pendiente"
    
    return False

def puede_autorizar(username: str, registro_usuario: str, db: Session) -> bool:
    """
    Verifica si el usuario puede cambiar el estado de pago (autorizar/revertir).
    
    - proveedor: NO puede autorizar
    - supervisor: puede autorizar registros de sus subordinados Y NO los suyos
    - admin: puede autorizar cualquier registro
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return False
    
    if usuario.role == "admin":
        return True
    
    if usuario.role == "supervisor":
        subordinados = usuario.subordinados.split(",") if usuario.subordinados else []
        subordinados = [s.strip() for s in subordinados if s.strip()]
        # Solo puede autorizar si el registro es de un subordinado Y NO es el suyo propio
        return registro_usuario in subordinados and registro_usuario != username
    
    # proveedor no puede autorizar
    return False

def puede_subir_comprobante_pago(username: str, registro_usuario: str, db: Session) -> bool:
    """
    Verifica si el usuario puede subir comprobante de pago.
    
    - proveedor: NO puede subir comprobante de pago
    - supervisor: NO puede subir comprobante de pago
    - admin: puede subir comprobante de pago para cualquiera
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return False
    
    # Solo admin puede subir comprobante de pago
    return usuario.role == "admin"

def puede_exportar(username: str, db: Session) -> bool:
    """
    Verifica si el usuario puede exportar a Excel.
    
    - proveedor: NO puede exportar
    - supervisor: puede exportar
    - admin: puede exportar
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return False
    
    return usuario.role in ["admin", "supervisor"]

def obtener_info_usuario(username: str, db: Session) -> dict:
    """
    Retorna información del usuario para el frontend.
    """
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    
    if not usuario:
        return {
            "username": username,
            "role": "proveedor",
            "subordinados": [],
            "puede_eliminar": False,
            "puede_autorizar": False,
            "puede_exportar": False,
            "puede_subir_pago": False
        }
    
    subordinados = usuario.subordinados.split(",") if usuario.subordinados else []
    subordinados = [s.strip() for s in subordinados if s.strip()]
    
    return {
        "username": usuario.username,
        "role": usuario.role,
        "subordinados": subordinados,
        "puede_eliminar": usuario.role in ["admin", "supervisor"],
        "puede_autorizar": usuario.role in ["admin", "supervisor"],
        "puede_exportar": usuario.role in ["admin", "supervisor"],
        "puede_subir_pago": usuario.role in ["admin", "supervisor"]
    }

# =========================================================
# Nuevas funciones de Permisos para Proveedores
# =========================================================

def puede_ver_proveedores(username: str, db: Session) -> bool:
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    if not usuario: return False
    return usuario.role in ["admin", "supervisor"] # Solo admin y supervisor pueden ver la lista

def puede_editar_proveedor(username: str, proveedor_creador: str, db: Session) -> bool:
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    if not usuario: return False
    # Admin puede editar cualquiera
    if usuario.role == "admin": return True
    # Supervisor puede editar cualquiera (se asume que los supervisores gestionan proveedores)
    if usuario.role == "supervisor": return True
    return False # Proveedor no puede editar proveedores


def puede_eliminar_proveedor(username: str, proveedor_creador: str, db: Session) -> bool:
    usuario = db.query(DBUser).filter(DBUser.username == username).first()
    if not usuario: return False
    # Solo el admin puede eliminar proveedores por ahora
    return usuario.role == "admin"

