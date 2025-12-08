# 🚀 GUÍA COMPLETA DE DESPLIEGUE PARA DEMOSTRACIÓN

## 📋 ANÁLISIS DEL SISTEMA

### Componentes Críticos Identificados:

1. **Base de Datos**: PostgreSQL (requerido en producción)
2. **Envío de Emails**: SMTP (Gmail configurado)
3. **Archivos Media**: Imágenes de radiografías, consentimientos, insumos, personal
4. **Archivos Estáticos**: CSS, JavaScript, imágenes del frontend
5. **3 Vistas Requeridas**:
   - Administrador (sistema de gestión)
   - Dentista (sistema de gestión)
   - Paciente (portal web)

### Archivos Media Identificados:

- **Radiografías**: `media/radiografias/%Y/%m/%d/`
- **Radiografías Anotadas**: `media/radiografias/anotadas/%Y/%m/%d/`
- **Consentimientos PDF**: `media/consentimientos/%Y/%m/%d/`
- **Consentimientos Firmados**: `media/consentimientos/firmados/%Y/%m/%d/`
- **Documentos**: `media/documentos/%Y/%m/%d/`
- **Insumos**: `media/insumos/imagenes/`
- **Personal**: `media/personal/`
- **Mensajes**: `media/mensajes/archivos/%Y/%m/`

---

## 🎯 OPCIONES DE DESPLIEGUE (Alternativas a Railway)

### ✅ OPCIÓN 1: RENDER.COM (RECOMENDADA) ⭐

**Ventajas:**
- ✅ Permite SMTP sin restricciones
- ✅ PostgreSQL gratuito incluido
- ✅ Servicio de archivos estáticos incluido
- ✅ Fácil configuración
- ✅ HTTPS automático
- ✅ Plan gratuito disponible (con limitaciones)

**Desventajas:**
- ⚠️ Plan gratuito se "duerme" después de 15 min de inactividad
- ⚠️ Para demostración en vivo, necesitas plan de pago ($7/mes)

**Configuración:**
- Base de datos PostgreSQL: Incluida
- Servir media files: Render puede servir archivos estáticos
- Emails: Sin restricciones

---

### ✅ OPCIÓN 2: PYTHONANYWHERE

**Ventajas:**
- ✅ Permite SMTP sin restricciones
- ✅ Plan gratuito disponible
- ✅ Fácil para principiantes
- ✅ Base de datos MySQL/PostgreSQL disponible

**Desventajas:**
- ⚠️ Plan gratuito tiene limitaciones (1 app, dominio .pythonanywhere.com)
- ⚠️ Requiere configuración manual de archivos estáticos
- ⚠️ Puede ser lento en plan gratuito

**Configuración:**
- Base de datos: MySQL incluido (o PostgreSQL con plan de pago)
- Servir media files: Configuración manual necesaria
- Emails: Sin restricciones

---

### ✅ OPCIÓN 3: DIGITALOCEAN APP PLATFORM

**Ventajas:**
- ✅ Permite SMTP
- ✅ PostgreSQL incluido
- ✅ Muy rápido y confiable
- ✅ Escalable

**Desventajas:**
- ⚠️ Plan mínimo: $5/mes
- ⚠️ Requiere tarjeta de crédito

**Configuración:**
- Base de datos: PostgreSQL incluido
- Servir media files: DigitalOcean Spaces (S3-compatible)
- Emails: Sin restricciones

---

### ✅ OPCIÓN 4: HEROKU

**Ventajas:**
- ✅ Permite SMTP
- ✅ PostgreSQL incluido
- ✅ Muy establecido y documentado

**Desventajas:**
- ⚠️ Ya no tiene plan gratuito
- ⚠️ Más caro que alternativas ($7-25/mes)
- ⚠️ Requiere tarjeta de crédito

---

### ✅ OPCIÓN 5: VPS PROPIO (Máxima Flexibilidad)

**Ventajas:**
- ✅ Control total
- ✅ Sin restricciones
- ✅ Puede ser más barato a largo plazo

**Desventajas:**
- ⚠️ Requiere conocimientos de servidor
- ⚠️ Configuración más compleja
- ⚠️ Necesitas mantener el servidor

**Proveedores VPS:**
- DigitalOcean Droplets ($4-6/mes)
- Linode ($5/mes)
- Vultr ($2.50/mes)
- Contabo (muy barato, desde €4.99/mes)

---

## 🏆 RECOMENDACIÓN PARA DEMOSTRACIÓN

### Para Demostración Presencial: **RENDER.COM** (Plan Starter $7/mes)

**Razones:**
1. ✅ No se "duerme" (plan de pago)
2. ✅ Emails funcionan perfectamente
3. ✅ Configuración sencilla
4. ✅ PostgreSQL incluido
5. ✅ HTTPS automático
6. ✅ Servir archivos media es posible

**Alternativa si no puedes pagar:** PythonAnywhere (gratis, pero puede ser lento)

---

## 📦 PREPARACIÓN PARA DESPLIEGUE

### 1. Archivos Necesarios para Crear

#### A. `Procfile` (para Render/Heroku)
```txt
web: gunicorn gestion_clinica.wsgi:application --bind 0.0.0.0:$PORT
```

#### B. `runtime.txt` (especificar versión de Python)
```txt
python-3.11.0
```

#### C. `requirements.txt` (ya existe, verificar que incluya)
```txt
gunicorn==21.2.0
whitenoise==6.6.0  # Para servir archivos estáticos
```

#### D. `.env.example` (template de variables de entorno)
```env
# Django
DEBUG=False
SECRET_KEY=tu-secret-key-super-segura-aqui
ALLOWED_HOSTS=tu-dominio.onrender.com,localhost,127.0.0.1

# Base de Datos
DB_ENGINE=postgresql
DB_NAME=clinica_db
DB_USER=clinica_user
DB_PASSWORD=tu-password-segura
DB_HOST=localhost
DB_PORT=5432

# Email (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-gmail
DEFAULT_FROM_EMAIL=tu-email@gmail.com

# URL del sitio
SITE_URL=https://tu-dominio.onrender.com

# Información de la clínica
CLINIC_NAME=Clínica San Felipe
CLINIC_ADDRESS=Tu dirección
CLINIC_PHONE=+56 9 XXXX XXXX
CLINIC_EMAIL=contacto@clinicasanfelipe.cl
```

---

## 🔧 CONFIGURACIÓN DE ARCHIVOS MEDIA

### Opción A: Servir desde el mismo servidor (Render/PythonAnywhere)

**Ventajas:**
- ✅ Simple
- ✅ Sin costos adicionales
- ✅ Funciona para demostración

**Desventajas:**
- ⚠️ Archivos se pierden si se reinicia el servidor (en algunos planes)
- ⚠️ No es ideal para producción a largo plazo

**Configuración en `settings.py`:**
```python
# Ya está configurado para servir en desarrollo
# En producción, Render/PythonAnywhere pueden servir archivos estáticos
```

**Configuración en `urls.py`:**
```python
# Ya está configurado para servir en DEBUG=True
# Para producción, el servidor web debe servir /media/
```

### Opción B: Almacenamiento en la nube (Recomendado para producción)

**Servicios recomendados:**
- **AWS S3** (más profesional)
- **Cloudinary** (más fácil, incluye transformaciones de imágenes)
- **DigitalOcean Spaces** (más barato, compatible con S3)

**Configuración con django-storages:**
```python
# Instalar: pip install django-storages boto3
INSTALLED_APPS = [
    # ...
    'storages',
]

# Para AWS S3
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
```

**Para demostración:** Opción A es suficiente. Opción B es para producción real.

---

## 📝 PASOS DETALLADOS PARA DESPLEGAR EN RENDER

### Paso 1: Preparar el Código

1. **Crear `Procfile`:**
```bash
cd gestion_clinica
echo "web: gunicorn gestion_clinica.wsgi:application --bind 0.0.0.0:\$PORT" > Procfile
```

2. **Crear `runtime.txt`:**
```bash
echo "python-3.11.0" > runtime.txt
```

3. **Actualizar `requirements.txt`:**
```bash
# Agregar al final de requirements.txt:
gunicorn==21.2.0
whitenoise==6.6.0
```

4. **Modificar `settings.py` para producción:**
```python
# Agregar al final de settings.py (después de la línea 293):
# Configuración para servir archivos estáticos con WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware de WhiteNoise (debe estar después de SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # AGREGAR ESTA LÍNEA
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... resto del middleware
]
```

5. **Modificar `urls.py` para servir media en producción:**
```python
# Reemplazar las líneas 44-49 con:
# Servir archivos multimedia en desarrollo y producción
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # En producción, servir media files también (para demostración)
    # En producción real, usar S3 o similar
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
```

### Paso 2: Subir a GitHub

```bash
git init
git add .
git commit -m "Preparado para despliegue"
git branch -M main
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main
```

### Paso 3: Crear Servicio en Render

1. Ir a https://render.com
2. Crear cuenta (con GitHub)
3. Click en "New" → "Web Service"
4. Conectar tu repositorio
5. Configurar:
   - **Name**: `clinica-dental` (o el que prefieras)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn gestion_clinica.wsgi:application`
   - **Plan**: Starter ($7/mes) o Free (se duerme)

### Paso 4: Crear Base de Datos PostgreSQL en Render

1. En Render Dashboard: "New" → "PostgreSQL"
2. Configurar:
   - **Name**: `clinica-db`
   - **Database**: `clinica_db`
   - **User**: `clinica_user`
   - **Region**: Más cercano a ti
   - **Plan**: Free (para demostración) o Starter ($7/mes)
3. Copiar las credenciales de conexión

### Paso 5: Configurar Variables de Entorno en Render

En el servicio web, ir a "Environment" y agregar:

```env
DEBUG=False
SECRET_KEY=generar-con-python-secret-key-generador
ALLOWED_HOSTS=tu-app.onrender.com
DB_ENGINE=postgresql
DB_NAME=clinica_db
DB_USER=clinica_user
DB_PASSWORD=password-de-la-bd
DB_HOST=dpg-xxxxx-a.oregon-postgres.render.com
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-gmail
DEFAULT_FROM_EMAIL=tu-email@gmail.com
SITE_URL=https://tu-app.onrender.com
CLINIC_NAME=Clínica San Felipe
```

**Generar SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Obtener App Password de Gmail:**
1. Ir a https://myaccount.google.com/apppasswords
2. Generar nueva contraseña de aplicación
3. Usar esa contraseña (no tu contraseña normal)

### Paso 6: Ejecutar Migraciones

En Render, ir a "Shell" y ejecutar:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Paso 7: Subir Archivos Media Existentes (Opcional)

Si tienes imágenes en `media/` localmente:
1. Usar `rsync` o subir manualmente
2. O usar el panel de Render para subir archivos
3. O simplemente crear nuevas imágenes en la demostración

---

## 🎬 PREPARACIÓN PARA DEMOSTRACIÓN

### 1. Crear Datos de Prueba

**Script para crear datos de demostración:**
```python
# management/commands/crear_datos_demo.py
from django.core.management.base import BaseCommand
from personal.models import Perfil
from pacientes.models import Cliente
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Crear administrador
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@clinica.cl',
            password='admin123'
        )
        admin_perfil = Perfil.objects.create(
            user=admin_user,
            nombre_completo='Administrador Demo',
            rol='administrativo',
            activo=True
        )
        
        # Crear dentista
        dentista_user = User.objects.create_user(
            username='dentista',
            email='dentista@clinica.cl',
            password='dentista123'
        )
        dentista_perfil = Perfil.objects.create(
            user=dentista_user,
            nombre_completo='Dr. Juan Pérez',
            rol='dentista',
            activo=True
        )
        
        # Crear cliente
        cliente = Cliente.objects.create(
            nombre_completo='Paciente Demo',
            email='paciente@demo.cl',
            telefono='+56912345678',
            activo=True
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de demostración creados'))
```

**Ejecutar:**
```bash
python manage.py crear_datos_demo
```

### 2. Credenciales para Demostración

**Administrador:**
- Usuario: `admin`
- Contraseña: `admin123`

**Dentista:**
- Usuario: `dentista`
- Contraseña: `dentista123`

**Paciente (Portal Web):**
- Email: `paciente@demo.cl`
- Contraseña: (crear desde el sistema de gestión)

### 3. Verificar Funcionalidades

- [ ] Login de administrador funciona
- [ ] Login de dentista funciona
- [ ] Login de paciente funciona
- [ ] Envío de emails funciona
- [ ] Subir imágenes funciona
- [ ] Ver imágenes funciona
- [ ] Crear citas funciona
- [ ] Reservar citas desde portal funciona

---

## 🚨 SOLUCIÓN DE PROBLEMAS COMUNES

### Error: "No such file or directory: 'media/'"
**Solución:** Crear directorio media en el servidor:
```bash
mkdir -p media/radiografias media/consentimientos media/insumos media/personal
```

### Error: "Static files not found"
**Solución:** Ejecutar `collectstatic`:
```bash
python manage.py collectstatic --noinput
```

### Error: "Email not sending"
**Solución:** 
1. Verificar que `EMAIL_HOST_PASSWORD` sea App Password de Gmail (no contraseña normal)
2. Verificar que Gmail permita "Acceso de aplicaciones menos seguras" (si es necesario)
3. Verificar firewall del servidor

### Error: "Database connection failed"
**Solución:**
1. Verificar variables de entorno `DB_*`
2. Verificar que la BD esté activa en Render
3. Verificar que el host permita conexiones externas

### Imágenes no se muestran
**Solución:**
1. Verificar que `MEDIA_ROOT` y `MEDIA_URL` estén configurados
2. Verificar que `urls.py` sirva archivos media
3. Verificar permisos de archivos
4. Verificar que las rutas sean correctas

---

## 📋 CHECKLIST PRE-DEMOSTRACIÓN

- [ ] Código subido a GitHub
- [ ] Servicio web creado en Render
- [ ] Base de datos PostgreSQL creada
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado
- [ ] Datos de demostración creados
- [ ] Emails funcionando (probar enviando uno)
- [ ] Imágenes se suben correctamente
- [ ] Imágenes se muestran correctamente
- [ ] Las 3 vistas funcionan (admin, dentista, paciente)
- [ ] HTTPS funciona (Render lo hace automático)
- [ ] Dominio personalizado configurado (opcional)

---

## 💡 CONSEJOS PARA LA DEMOSTRACIÓN

1. **Tener 3 pestañas abiertas:**
   - Pestaña 1: Administrador (sistema de gestión)
   - Pestaña 2: Dentista (sistema de gestión)
   - Pestaña 3: Paciente (portal web)

2. **Preparar flujo de demostración:**
   - Mostrar cómo el paciente se registra
   - Mostrar cómo el paciente reserva una cita
   - Mostrar cómo el administrador ve la cita
   - Mostrar cómo el dentista atiende la cita
   - Mostrar cómo se envían emails automáticos

3. **Tener datos de respaldo:**
   - Si algo falla, tener datos ya creados para mostrar

4. **Probar antes:**
   - Probar todo el flujo 1 día antes
   - Verificar que emails lleguen
   - Verificar que imágenes se muestren

---

## 🎯 RESUMEN RÁPIDO

**Para demostración rápida:**
1. Render.com (Plan Starter $7/mes)
2. PostgreSQL incluido en Render
3. WhiteNoise para archivos estáticos
4. Servir media files desde el mismo servidor
5. Gmail con App Password para emails

**Tiempo estimado de despliegue:** 1-2 horas

**Costo mensual:** $7 USD (Render Starter) + $0 (PostgreSQL Free)

---

¡Éxito con tu demostración! 🎓


