# 🚀 Guía de Despliegue - GitHub + Render

## 📋 Pasos para Subir a GitHub y Desplegar en Render

---

## 1️⃣ Preparar el Proyecto para GitHub

### Paso 1.1: Crear archivo .gitignore

```bash
cd /Users/edbravo/Desktop/mi-web-service
```

Crear archivo `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Base de datos local
*.db
datahub.db

# Archivos subidos
uploads/
*.pdf
*.xml

# Configuración local
.env
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log
```

### Paso 1.2: Inicializar Git

```bash
# Inicializar repositorio
git init

# Agregar todos los archivos
git add .

# Hacer el primer commit
git commit -m "Initial commit - DataHub Ulma con sistema de permisos jerárquico"
```

---

## 2️⃣ Crear Repositorio en GitHub

### Paso 2.1: Crear repositorio en GitHub.com

1. Ve a https://github.com
2. Click en el botón **"+"** → **"New repository"**
3. Nombre del repositorio: `datahub-ulma` (o el que prefieras)
4. Descripción: "Sistema de gestión de facturas con permisos jerárquicos"
5. **NO** marques "Initialize with README" (ya tienes archivos)
6. Click **"Create repository"**

### Paso 2.2: Conectar repositorio local con GitHub

```bash
# Agregar el repositorio remoto (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/datahub-ulma.git

# Cambiar a rama main
git branch -M main

# Subir código a GitHub
git push -u origin main
```

Si te pide credenciales:
- Usuario: tu usuario de GitHub
- Contraseña: usa un **Personal Access Token** (no tu contraseña)
  - Ve a GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  - Marca "repo" y genera el token
  - Usa ese token como contraseña

---

## 3️⃣ Preparar para Render

### Paso 3.1: Verificar requirements.txt

Asegúrate que `requirements.txt` tenga todas las dependencias:

```
fastapi
uvicorn
sqlalchemy
passlib[bcrypt]
python-multipart
pandas
xlsxwriter
openpyxl
exchangelib
python-dotenv
```

### Paso 3.2: Crear archivo de configuración para Render

Crear archivo `render.yaml` (opcional pero recomendado):

```yaml
services:
  - type: web
    name: datahub-ulma
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
```

### Paso 3.3: Subir cambios a GitHub

```bash
git add .
git commit -m "Add Render configuration"
git push origin main
```

---

## 4️⃣ Desplegar en Render

### Paso 4.1: Crear cuenta en Render

1. Ve a https://render.com
2. Click **"Get Started"**
3. Regístrate con tu cuenta de GitHub (recomendado)

### Paso 4.2: Crear nuevo Web Service

1. En el dashboard de Render, click **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Selecciona el repositorio `datahub-ulma`
4. Configuración:
   - **Name:** `datahub-ulma`
   - **Region:** Oregon (US West) o el más cercano
   - **Branch:** `main`
   - **Root Directory:** (dejar vacío)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free` (para empezar)

### Paso 4.3: Variables de Entorno (Opcional)

Si usas el procesador de correos, agrega estas variables:

- `EXCHANGE_EMAIL`: tu_correo@ulma.com.mx
- `EXCHANGE_PASSWORD`: tu_contraseña
- `EXCHANGE_SERVER`: outlook.office365.com
- `USER_MAPPING`: {"usuario@ulma.com":"admin"}

### Paso 4.4: Desplegar

1. Click **"Create Web Service"**
2. Render comenzará a construir y desplegar tu aplicación
3. Espera 2-5 minutos
4. Una vez completado, verás la URL de tu aplicación: `https://datahub-ulma.onrender.com`

---

## 5️⃣ Verificar el Despliegue

### Paso 5.1: Probar la aplicación

1. Abre la URL de Render en tu navegador
2. Deberías ver la pantalla de login
3. Prueba con: `admin` / `admin123`

### Paso 5.2: Revisar logs

En Render:
- Ve a tu servicio
- Click en **"Logs"**
- Verifica que no haya errores

---

## 6️⃣ Actualizar el Código

Cada vez que hagas cambios:

```bash
# 1. Hacer cambios en tu código local

# 2. Agregar cambios a Git
git add .

# 3. Hacer commit
git commit -m "Descripción de los cambios"

# 4. Subir a GitHub
git push origin main

# 5. Render detectará los cambios y redesplegará automáticamente
```

---

## 🔧 Configuración Adicional

### Dominio Personalizado

1. En Render, ve a tu servicio
2. Click en **"Settings"** → **"Custom Domain"**
3. Agrega tu dominio (ej: `datahub.ulma.com.mx`)
4. Configura los DNS según las instrucciones de Render

### Base de Datos Persistente

**IMPORTANTE:** Render Free tier reinicia cada 15 minutos de inactividad y borra la base de datos SQLite.

**Solución:** Usar PostgreSQL de Render (gratis):

1. En Render, click **"New +"** → **"PostgreSQL"**
2. Nombre: `datahub-db`
3. Plan: **Free**
4. Click **"Create Database"**
5. Copia la **Internal Database URL**
6. En tu Web Service, agrega variable de entorno:
   - `DATABASE_URL`: (pega la URL copiada)

7. Actualiza `database.py`:

```python
import os
from sqlalchemy import create_engine

# Usar PostgreSQL en producción, SQLite en desarrollo
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datahub.db")

# Render usa postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
```

8. Actualiza `requirements.txt`:

```
fastapi
uvicorn
sqlalchemy
passlib[bcrypt]
python-multipart
pandas
xlsxwriter
openpyxl
exchangelib
python-dotenv
psycopg2-binary  # <-- Agregar esto para PostgreSQL
```

---

## 🐛 Solución de Problemas

### Error: "Application failed to start"

**Solución:**
- Revisa los logs en Render
- Verifica que `requirements.txt` esté completo
- Asegúrate que el comando de inicio sea correcto

### Error: "Module not found"

**Solución:**
```bash
# Actualiza requirements.txt
pip freeze > requirements.txt

# Sube cambios
git add requirements.txt
git commit -m "Update requirements"
git push origin main
```

### La base de datos se borra

**Solución:**
- Usa PostgreSQL de Render (ver sección anterior)
- O usa un servicio externo como Supabase, PlanetScale, etc.

### Archivos subidos se pierden

**Solución:**
- Usa almacenamiento externo como:
  - AWS S3
  - Cloudinary
  - Render Disks (de pago)

---

## 📊 Monitoreo

### Ver estadísticas en Render

1. Dashboard → Tu servicio
2. **Metrics:** CPU, memoria, requests
3. **Logs:** Errores y actividad
4. **Events:** Despliegues y cambios

### Configurar alertas

1. Settings → Notifications
2. Agrega tu email
3. Recibirás alertas si el servicio falla

---

## 💰 Costos

### Plan Free de Render:

- ✅ 750 horas/mes gratis
- ✅ Despliegues ilimitados
- ✅ SSL automático
- ⚠️ Se duerme después de 15 min de inactividad
- ⚠️ Tarda ~30 seg en despertar
- ⚠️ 512 MB RAM

### Plan Starter ($7/mes):

- ✅ Siempre activo
- ✅ 512 MB RAM
- ✅ Sin tiempo de espera

---

## 🔐 Seguridad

### Cambiar contraseñas por defecto

Antes de producción, cambia las contraseñas en `main.py`:

```python
DBUser(username="admin", hashed_password=get_password_hash("TU_CONTRASEÑA_SEGURA"), ...)
```

### Usar variables de entorno

No pongas contraseñas en el código. Usa variables de entorno en Render.

### HTTPS

Render proporciona HTTPS automáticamente. ✅

---

## 📝 Checklist de Despliegue

- [ ] Crear `.gitignore`
- [ ] Inicializar Git
- [ ] Crear repositorio en GitHub
- [ ] Subir código a GitHub
- [ ] Verificar `requirements.txt`
- [ ] Crear cuenta en Render
- [ ] Crear Web Service en Render
- [ ] Configurar variables de entorno
- [ ] Verificar que la app funcione
- [ ] (Opcional) Configurar PostgreSQL
- [ ] (Opcional) Configurar dominio personalizado
- [ ] Cambiar contraseñas por defecto
- [ ] Probar todos los roles de usuario

---

## 🎯 Comandos Rápidos

```bash
# Ver estado de Git
git status

# Ver cambios
git diff

# Agregar todos los cambios
git add .

# Hacer commit
git commit -m "Mensaje descriptivo"

# Subir a GitHub
git push origin main

# Ver historial
git log --oneline

# Crear nueva rama
git checkout -b nueva-funcionalidad

# Volver a main
git checkout main
```

---

## 📞 Soporte

**GitHub:** https://docs.github.com  
**Render:** https://render.com/docs  
**FastAPI:** https://fastapi.tiangolo.com

---

**Última actualización:** 27/04/2026
