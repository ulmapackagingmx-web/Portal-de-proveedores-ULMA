import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Importaciones locales
from database import engine, get_db, SessionLocal
from models import Base, DBUser
from security import verify_password, get_password_hash, get_current_user

# Routers
from routers.uploads import router as uploads_router
from routers.documents import router as documents_router
from routers.webhook import router as webhook_router
from routers.providers import router as providers_router

# 1. Crear carpetas y base de datos
os.makedirs("uploads", exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataHub Ulma", version="4.4")

# Montar la carpeta de uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# 2. Conectar los routers
app.include_router(uploads_router)
app.include_router(documents_router)
app.include_router(webhook_router)
app.include_router(providers_router)

# 3. Crear usuarios iniciales al arrancar
@app.on_event("startup")
def startup_event():
    db = SessionLocal()

    from sqlalchemy import text
    try:
        db.execute(text("ALTER TABLE documents ADD COLUMN naturaleza VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE documents ADD COLUMN cliente VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE documents ADD COLUMN modelo_maquina VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE documents ADD COLUMN numero_serie VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE documents ADD COLUMN numero_pedido VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE providers ADD COLUMN tipo_operacion VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE providers ADD COLUMN referencia_bancaria VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE providers ADD COLUMN email_contacto VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE providers ADD COLUMN historial VARCHAR DEFAULT '[]'"))
        db.commit()
    except Exception:
        db.rollback()

    print("Creando/Verificando usuarios iniciales del sistema...")
    
    # Lista de usuarios solicitados basada en el Excel proporcionado
    default_users = [
        {"username": "gvelazquez", "email": "gvelazquez@ulmapackaging.com.mx", "role": "admin", "subordinados": ""},
        {"username": "edbravo", "email": "edbravo@ulmapackaging.com.mx", "role": "admin", "subordinados": ""},
        {"username": "hdominguez", "email": "hdominguez@ulmapackaging.com.mx", "role": "admin", "subordinados": ""},
        {"username": "janett.barrera", "email": "janett.barrera@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "ajcontreras", "email": "ajcontreras@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "rosario.estrada", "email": "rosario.estrada@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "holopez", "email": "holopez@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "jprrendon", "email": "jprrendon@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "dflores", "email": "dflores@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "diego.beato", "email": "diego.beato@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "patricia.delacruz", "email": "patricia.delacruz@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "daniel.munoz", "email": "daniel.munoz@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "cdvelazquez", "email": "cdvelazquez@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "yazmin.pedraza", "email": "yazmin.pedraza@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "jdiaz", "email": "jdiaz@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "jcarrasco", "email": "jcarrasco@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "rmhernandez", "email": "rmhernandez@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        {"username": "paola.servin", "email": "paola.servin@ulmapackaging.com.mx", "role": "supervisor", "subordinados": ""},
        # Usuario de sistemas: único con acceso a las secciones "Expedientes" y "Datos Bancarios"
        {"username": "sistemas", "email": "sistemas@ulmapackaging.com.mx", "role": "admin", "subordinados": "", "password": "sistemas123"}
    ]

    usuarios_creados = False
    for u in default_users:
        existing = db.query(DBUser).filter(DBUser.username == u["username"]).first()
        if not existing:
            # Cada usuario usa una contraseña específica si se define, si no la temporal por defecto
            contrasena = u.get("password", "Ulma2026*")
            new_user = DBUser(
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(contrasena),
                role=u["role"],
                subordinados=u["subordinados"]
            )
            db.add(new_user)
            usuarios_creados = True
    
    if usuarios_creados:
        db.commit()
        print("✅ Nuevos usuarios creados con la contraseña temporal: Ulma2026*")
    else:
        print("✅ Los usuarios ya existen en la base de datos.")
    
    db.close()

@app.get("/", response_class=HTMLResponse)
def mostrar_portal(): 
    html_path = Path("templates/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from permissions import obtener_info_usuario
    
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user:
        print(f"--- DEBUG: Intento de inicio de sesión fallido para usuario: {form_data.username} (Usuario no encontrado) ---")
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    if not verify_password(form_data.password, user.hashed_password):
        print(f"--- DEBUG: Intento de inicio de sesión fallido para usuario: {form_data.username} (Contraseña incorrecta) ---")
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    # Obtener información de permisos del usuario
    info_usuario = obtener_info_usuario(user.username, db);
    print(f"--- DEBUG: Inicio de sesión exitoso para usuario: {user.username} con rol: {user.role} ---")
    
    return {
        "access_token": user.username,
        "token_type": "bearer",
        "role": user.role,
        "permisos": info_usuario
    }

@app.post("/api/cambiar-password")
def cambiar_password(
    password_actual: str = Body(...),
    nuevo_password: str = Body(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_actual, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    current_user.hashed_password = get_password_hash(nuevo_password)
    db.commit()
    return {"status": "ok"}

