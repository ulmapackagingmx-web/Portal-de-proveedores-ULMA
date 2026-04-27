from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # proveedor, supervisor, admin
    subordinados = Column(String, default="")  # Lista de usuarios subordinados separados por coma

class DBDocument(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String) 
    remitente_rfc = Column(String, index=True)
    nombre = Column(String, default="DESCONOCIDO") 
    uuid_folio = Column(String, default="S/F") 
    total = Column(Float)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    subido_por = Column(String) 
    centro_costo = Column(String, default="Administración")
    subcatalogo_centro = Column(String, default="")  # Subcatálogo del centro de costo
    porcentaje_centro = Column(String, default="100%")
    fecha_pago = Column(String, default="POR DEFINIR") 
    comprobante_pdf = Column(String, default="") 
    estado_pago = Column(String, default="Pendiente")  # Pendiente, Autorizado, Pagado
    comprobante_pago_pdf = Column(String, default="")
    # Nuevos campos para XML
    uso_cfdi = Column(String, default="")
    forma_pago = Column(String, default="")
    metodo_pago = Column(String, default="")
    clave_sat = Column(String, default="")
    descripcion_sat = Column(String, default="")
    descripcion_concepto = Column(String, default="")  # Primera descripción del XML
    moneda = Column(String, default="MXN")
