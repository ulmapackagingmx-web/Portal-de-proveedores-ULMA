from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
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
    fecha_emision = Column(String, default="POR DEFINIR")  # Fecha del XML/Factura
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    subido_por = Column(String) 
    centro_costo = Column(String, default="Administración")
    subcatalogo_centro = Column(String, default="")  # Subcatálogo del centro de costo
    porcentaje_centro = Column(String, default="100%")
    fecha_pago = Column(String, default="POR DEFINIR") 
    porcentaje_pago = Column(Float, default=100.0)
    comprobante_pdf = Column(String, default="") 
    estado_pago = Column(String, default="Pendiente")  # Pendiente, Autorizado, Pagado
    fecha_estimada_pago = Column(String, default="")
    comprobante_pago_pdf = Column(String, default="")
    otros_documentos_pdf = Column(String, default="")
    # Nuevos campos para XML
    regimen_fiscal_emisor = Column(String, default="")
    traslados = Column(String, default="")  # Almacenará un resumen de los traslados
    retenciones = Column(String, default="") # Almacenará un resumen de las retenciones
    uso_cfdi = Column(String, default="")
    forma_pago = Column(String, default="")
    metodo_pago = Column(String, default="")
    clave_sat = Column(String, default="")
    descripcion_sat = Column(String, default="")
    descripcion_concepto = Column(String, default="")  # Primera descripción del XML
    moneda = Column(String, default="MXN")
    comentarios = Column(String, default="")

    # Nuevos campos para "REFACCIONES"
    naturaleza = Column(String, default="")  # Venta, Costo de venta, Garantía
    numero_pedido = Column(String, default="") # Nuevo campo para número de pedido
    # cliente = Column(String, default="") # Eliminado
    # modelo_maquina = Column(String, default="") # Eliminado
    # numero_serie = Column(String, default="") # Eliminado

class DBHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    accion = Column(String)  # Creado, Autorizado, Rechazado, Pagado, etc.
    motivo = Column(String, default="")
    usuario = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

class DBProvider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    nombre_proveedor = Column(String, index=True)
    rfc_proveedor = Column(String, unique=True, index=True)
    banco = Column(String, default="")
    numero_cuenta_clabe = Column(String, default="")
    tipo_operacion = Column(String, default="") # Convenio CIE, Interbancario, Mismo Banco
    expediente = Column(String, default="")
    validacion_bancaria = Column(Boolean, default=False)
    validacion_expediente = Column(Boolean, default=False)
    campo_libre = Column(String, default="")
    email_contacto = Column(String, default="")

