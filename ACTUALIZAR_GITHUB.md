# 🔄 Actualizar Repositorio Existente en GitHub

## Tu Configuración Actual:

- **GitHub:** https://github.com/ulmapackagingmx-web/api-datahub
- **Render:** https://api-datahub.onrender.com

---

## 🚀 Pasos para Actualizar tu Repositorio

### Paso 1: Conectar tu proyecto local con GitHub

```bash
# Ir a tu proyecto
cd /Users/edbravo/Desktop/mi-web-service

# Inicializar Git (si no está inicializado)
git init

# Conectar con tu repositorio existente
git remote add origin https://github.com/ulmapackagingmx-web/api-datahub.git

# Verificar que se conectó correctamente
git remote -v
```

---

### Paso 2: Descargar el estado actual del repositorio

```bash
# Descargar el contenido actual de GitHub
git fetch origin

# Ver qué archivos hay en GitHub
git ls-tree -r origin/main --name-only
```

---

### Paso 3: OPCIÓN A - Reemplazar TODO (Recomendado)

**⚠️ ADVERTENCIA:** Esto eliminará todos los archivos actuales en GitHub y los reemplazará con tu código nuevo.

```bash
# Forzar que tu versión local sea la principal
git checkout -b main

# Agregar todos tus archivos
git add .

# Hacer commit
git commit -m "Actualización completa - Sistema de permisos jerárquico implementado"

# Forzar push (reemplaza todo en GitHub)
git push -f origin main
```

---

### Paso 3: OPCIÓN B - Fusionar con archivos existentes

Si quieres conservar algunos archivos de GitHub:

```bash
# Descargar rama main
git pull origin main --allow-unrelated-histories

# Resolver conflictos si los hay
# (Git te dirá qué archivos tienen conflictos)

# Agregar archivos resueltos
git add .

# Hacer commit
git commit -m "Merge con versión actualizada"

# Subir a GitHub
git push origin main
```

---

## 4️⃣ Verificar en GitHub

1. Ve a https://github.com/ulmapackagingmx-web/api-datahub
2. Verifica que veas tus archivos nuevos:
   - `main.py`
   - `models.py`
   - `permissions.py`
   - `routers/`
   - `templates/`
   - etc.

---

## 5️⃣ Render se Actualizará Automáticamente

Una vez que subas a GitHub:

1. Render detectará los cambios automáticamente
2. Comenzará a redesplegar (2-5 minutos)
3. Puedes ver el progreso en: https://dashboard.render.com
4. Ve a tu servicio → **"Events"** para ver el despliegue

---

## 6️⃣ Verificar el Despliegue en Render

1. Espera a que termine el despliegue
2. Ve a https://api-datahub.onrender.com
3. Deberías ver la pantalla de login
4. Prueba con: `admin` / `admin123`

---

## ⚠️ IMPORTANTE: Base de Datos en Render

**Problema:** Render Free tier borra la base de datos SQLite cada vez que se reinicia.

**Solución:** Usar PostgreSQL de Render (gratis)

### Crear PostgreSQL en Render:

1. En Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Nombre: `datahub-db`
3. Database: `datahub`
4. User: `datahub_user`
5. Region: Mismo que tu web service
6. Plan: **Free**
7. Click **"Create Database"**

### Conectar PostgreSQL a tu Web Service:

1. Copia la **Internal Database URL** de tu PostgreSQL
2. Ve a tu Web Service → **"Environment"**
3. Agrega variable:
   - Key: `DATABASE_URL`
   - Value: (pega la URL copiada)
4. Click **"Save Changes"**

### Actualizar database.py:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Usar PostgreSQL en producción, SQLite en desarrollo
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datahub.db")

# Render usa postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Actualizar requirements.txt:

Agregar al final:
```
psycopg2-binary
```

### Subir cambios:

```bash
git add database.py requirements.txt
git commit -m "Add PostgreSQL support for Render"
git push origin main
```

---

## 🔄 Flujo de Trabajo Continuo

Cada vez que hagas cambios:

```bash
# 1. Hacer cambios en tu código

# 2. Probar localmente
python3 -m uvicorn main:app --reload --port 8001

# 3. Si funciona, subir a GitHub
git add .
git commit -m "Descripción del cambio"
git push origin main

# 4. Render redesplegará automáticamente
# 5. Verifica en https://api-datahub.onrender.com
```

---

## 📝 Comandos Útiles

```bash
# Ver estado de Git
git status

# Ver archivos que se subirán
git diff

# Ver historial de commits
git log --oneline

# Deshacer último commit (mantiene cambios)
git reset --soft HEAD~1

# Ver archivos en GitHub
git ls-tree -r origin/main --name-only

# Forzar actualización desde GitHub
git fetch origin
git reset --hard origin/main
```

---

## 🎯 Resumen Rápido

```bash
# OPCIÓN RÁPIDA - Reemplazar todo en GitHub:

cd /Users/edbravo/Desktop/mi-web-service
git init
git remote add origin https://github.com/ulmapackagingmx-web/api-datahub.git
git add .
git commit -m "Sistema completo con permisos jerárquicos"
git push -f origin main

# Render redesplegará automáticamente
# Verifica en: https://api-datahub.onrender.com
```

---

## 🔐 Autenticación con GitHub

Si te pide usuario y contraseña:

1. **Usuario:** ulmapackagingmx-web
2. **Contraseña:** Usa un **Personal Access Token**
   - Ve a GitHub → Settings → Developer settings
   - Personal access tokens → Tokens (classic)
   - Generate new token
   - Marca "repo"
   - Copia el token
   - Úsalo como contraseña

---

## ✅ Checklist

- [ ] Conectar repositorio local con GitHub
- [ ] Subir código a GitHub (push)
- [ ] Verificar archivos en GitHub
- [ ] Esperar redespliegue en Render (2-5 min)
- [ ] Probar https://api-datahub.onrender.com
- [ ] (Recomendado) Configurar PostgreSQL
- [ ] Cambiar contraseñas por defecto

---

**Tu URL de producción:** https://api-datahub.onrender.com  
**Tu repositorio:** https://github.com/ulmapackagingmx-web/api-datahub

**Última actualización:** 27/04/2026
