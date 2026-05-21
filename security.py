import bcrypt
from fastapi import Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import DBUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"--- DEBUG: Token recibido por el backend: '{token}' ---")
    # En un sistema de producción, se validaría un JWT real aquí
    # Por ahora, simplemente buscamos al usuario por el username que actúa como token
    user = db.query(DBUser).filter(DBUser.username == token).first()
    if not user:
        print(f"--- DEBUG: Usuario no encontrado para el token: \'{token}\' ---")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    print(f"--- DEBUG: Usuario \'{user.username}\' autenticado con rol \'{user.role}\' ---")
    return user
