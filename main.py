import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Importaciones locales
from database import engine, get_db, SessionLocal
from models import Base, DBUser
from security import verify_password, get_password_hash

# Routers
from routers.uploads import router as uploads_router
from routers.documents import router as documents_router
from routers.webhook import router as webhook_router

# 1. Crear carpetas y base de datos
os.makedirs("uploads", exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataHub Ulma", version="4.4")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# 2. Conectar los routers
app.include_router(uploads_router)
app.include_router(documents_router)
app.include_router(webhook_router)

# 3. Crear usuarios iniciales al arrancar
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    
    # Verificar si ya existen usuarios
    usuarios_existentes = db.query(DBUser).count()
    
    if usuarios_existentes == 0:
        print("Creando usuarios iniciales del sistema...")
        
        # Usuarios de nivel más bajo (proveedores)
        usuarios_proveedores = [
            DBUser(username="usuarioA", hashed_password=get_password_hash("pass123"), role="proveedor", subordinados=""),
            DBUser(username="usuarioB", hashed_password=get_password_hash("pass123"), role="proveedor", subordinados=""),
            DBUser(username="usuarioC", hashed_password=get_password_hash("pass123"), role="proveedor", subordinados=""),
            DBUser(username="usuarioD", hashed_password=get_password_hash("pass123"), role="proveedor", subordinados=""),
        ]
        
        # Usuarios supervisores (tienen subordinados)
        usuarios_supervisores = [
            DBUser(username="usuario1", hashed_password=get_password_hash("super123"), role="supervisor", subordinados="usuarioA,usuarioB"),
            DBUser(username="usuario2", hashed_password=get_password_hash("super123"), role="supervisor", subordinados="usuarioC,usuarioD"),
        ]
        
        # Usuario administrador (tiene acceso a todo)
        usuario_admin = DBUser(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            subordinados="usuario1,usuario2,usuarioA,usuarioB,usuarioC,usuarioD"
        )
        
        # Agregar todos los usuarios
        for usuario in usuarios_proveedores:
            db.add(usuario)
        for usuario in usuarios_supervisores:
            db.add(usuario)
        db.add(usuario_admin)
        
        db.commit()
        
        print("✅ Usuarios creados:")
        print("   👑 admin (contraseña: admin123) - Acceso total")
        print("   👔 usuario1 (contraseña: super123) - Supervisor de usuarioA y usuarioB")
        print("   👔 usuario2 (contraseña: super123) - Supervisor de usuarioC y usuarioD")
        print("   👤 usuarioA, usuarioB, usuarioC, usuarioD (contraseña: pass123) - Proveedores")
    
    db.close()

@app.get("/", response_class=HTMLResponse)
def mostrar_portal(): 
    html_path = Path("templates/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from permissions import obtener_info_usuario
    
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    # Obtener información de permisos del usuario
    info_usuario = obtener_info_usuario(user.username, db)
    
    return {
        "access_token": user.username,
        "token_type": "bearer",
        "role": user.role,
        "permisos": info_usuario
    }
