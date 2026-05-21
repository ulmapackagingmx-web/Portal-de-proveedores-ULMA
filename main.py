import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
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
    
    # Verificar si ya existen usuarios
    usuarios_existentes = db.query(DBUser).count()
    
    if usuarios_existentes == 0:
        print("Creando usuarios iniciales del sistema...")
        
        # Asegurarse de que no existen para evitar duplicados
        db.query(DBUser).filter(DBUser.username == "admin").delete()
        db.query(DBUser).filter(DBUser.username == "usuario1").delete()
        db.query(DBUser).filter(DBUser.username == "usuario2").delete()
        db.query(DBUser).filter(DBUser.username == "usuarioA").delete()
        db.query(DBUser).filter(DBUser.username == "usuarioB").delete()
        db.query(DBUser).filter(DBUser.username == "usuarioC").delete()
        db.query(DBUser).filter(DBUser.username == "usuarioD").delete()
        db.commit()

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

