# ⚡ RESUMEN RÁPIDO DE DESPLIEGUE

## 🎯 PASOS ESENCIALES (Versión Corta)

### 1️⃣ PREPARACIÓN (5 minutos)
```bash
# Generar SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Verificar preparación
python verificar_preparacion.py
```

### 2️⃣ GITHUB (10 minutos)
```bash
git init
git add .
git commit -m "Preparado para despliegue"
git remote add origin https://github.com/TU_USUARIO/clinica-dental.git
git push -u origin main
```

### 3️⃣ RENDER - BASE DE DATOS (5 minutos)
1. Render.com → "New +" → "PostgreSQL"
2. Name: `clinica-db`
3. Database: `clinica_db`
4. User: `clinica_user`
5. Plan: Starter ($7/mes) o Free
6. **Copiar credenciales de conexión**

### 4️⃣ RENDER - SERVICIO WEB (15 minutos)
1. Render.com → "New +" → "Web Service"
2. Conectar repositorio de GitHub
3. Configurar:
   - **Name:** `clinica-dental`
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn gestion_clinica.wsgi:application`
   - **Plan:** Starter ($7/mes)

### 5️⃣ VARIABLES DE ENTORNO (10 minutos)
Agregar en Render (Environment Variables):

```
DEBUG=False
SECRET_KEY=(el que generaste)
ALLOWED_HOSTS=clinica-dental.onrender.com,localhost
DB_ENGINE=postgresql
DB_NAME=clinica_db
DB_USER=clinica_user
DB_PASSWORD=(de la BD)
DB_HOST=(de la BD)
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=(App Password de Gmail)
DEFAULT_FROM_EMAIL=tu-email@gmail.com
SITE_URL=https://clinica-dental.onrender.com
CLINIC_NAME=Clínica San Felipe
```

### 6️⃣ MIGRACIONES (5 minutos)
En Render → Shell:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_datos_demo
```

### 7️⃣ PROBAR (5 minutos)
- Admin: `https://tu-app.onrender.com/trabajadores/login/` (admin/admin123)
- Dentista: `https://tu-app.onrender.com/trabajadores/login/` (dentista/dentista123)
- Portal: `https://tu-app.onrender.com/`

---

## 📋 CHECKLIST RÁPIDO

- [ ] SECRET_KEY generado
- [ ] App Password de Gmail creada
- [ ] Código subido a GitHub
- [ ] Base de datos PostgreSQL creada en Render
- [ ] Servicio web creado en Render
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado
- [ ] Datos demo creados
- [ ] Login funciona
- [ ] Emails funcionan

---

## 🔑 CREDENCIALES DEMO

**Administrador:**
- Usuario: `admin`
- Contraseña: `admin123`

**Dentista:**
- Usuario: `dentista`
- Contraseña: `dentista123`

**Paciente:**
- Email: `paciente@demo.cl`
- Contraseña: (crear desde sistema de gestión)

---

## ⚠️ PROBLEMAS COMUNES

**"Application Error"**
→ Revisar logs en Render → Verificar variables de entorno

**"Database connection failed"**
→ Verificar DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

**"Emails no se envían"**
→ Verificar que EMAIL_HOST_PASSWORD sea App Password (no contraseña normal)

**"Static files not found"**
→ Ejecutar: `python manage.py collectstatic --noinput` en Shell

---

## 📚 DOCUMENTACIÓN COMPLETA

Para pasos detallados, ver: `GUIA_PASO_A_PASO_RENDER.md`

---

¡Éxito! 🚀

