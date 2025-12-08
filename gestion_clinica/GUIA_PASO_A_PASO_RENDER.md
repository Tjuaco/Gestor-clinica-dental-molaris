# 🚀 GUÍA PASO A PASO: DESPLEGAR EN RENDER.COM

## 📋 ÍNDICE
1. [Preparación Local](#1-preparación-local)
2. [Crear Cuenta en Render](#2-crear-cuenta-en-render)
3. [Subir Código a GitHub](#3-subir-código-a-github)
4. [Crear Base de Datos PostgreSQL](#4-crear-base-de-datos-postgresql)
5. [Crear Servicio Web](#5-crear-servicio-web)
6. [Configurar Variables de Entorno](#6-configurar-variables-de-entorno)
7. [Ejecutar Migraciones](#7-ejecutar-migraciones)
8. [Crear Datos de Demostración](#8-crear-datos-de-demostración)
9. [Probar el Sistema](#9-probar-el-sistema)
10. [Solución de Problemas](#10-solución-de-problemas)

---

## 1. PREPARACIÓN LOCAL

### Paso 1.1: Verificar que tienes los archivos necesarios

Abre tu carpeta del proyecto y verifica que tengas estos archivos en la raíz de `gestion_clinica/`:

- ✅ `Procfile` (debe existir)
- ✅ `runtime.txt` (debe existir)
- ✅ `requirements.txt` (debe tener gunicorn y whitenoise)
- ✅ `manage.py`
- ✅ Carpeta `gestion_clinica/` (con settings.py)

### Paso 1.2: Generar SECRET_KEY

Abre PowerShell o Terminal en la carpeta `gestion_clinica/` y ejecuta:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**IMPORTANTE:** Copia el resultado (será algo como: `django-insecure-abc123xyz...`). Lo necesitarás más adelante.

### Paso 1.3: Preparar App Password de Gmail

1. Ve a: https://myaccount.google.com/apppasswords
2. Si te pide verificar tu identidad, hazlo
3. En "Seleccionar app", elige "Correo"
4. En "Seleccionar dispositivo", elige "Otro (nombre personalizado)" y escribe "Render"
5. Click en "Generar"
6. **IMPORTANTE:** Copia la contraseña de 16 caracteres que aparece (ejemplo: `abcd efgh ijkl mnop`). La necesitarás sin espacios.

---

## 2. CREAR CUENTA EN RENDER

### Paso 2.1: Ir a Render.com

1. Abre tu navegador y ve a: https://render.com
2. Click en "Get Started for Free" o "Sign Up"

### Paso 2.2: Registrarse con GitHub

1. Click en "Sign up with GitHub"
2. Autoriza a Render a acceder a tu cuenta de GitHub
3. Completa tu perfil si te lo pide

**Si no tienes cuenta de GitHub:**
1. Ve a: https://github.com
2. Crea una cuenta gratuita
3. Luego vuelve a Render y regístrate con GitHub

---

## 3. SUBIR CÓDIGO A GITHUB

### Paso 3.1: Inicializar Git (si no lo has hecho)

Abre PowerShell o Terminal en la carpeta `gestion_clinica/` y ejecuta:

```bash
# Verificar si ya es un repositorio git
git status
```

**Si dice "not a git repository":**

```bash
# Inicializar git
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Preparado para despliegue en Render"
```

### Paso 3.2: Crear Repositorio en GitHub

1. Ve a: https://github.com
2. Click en el botón "+" (arriba a la derecha) → "New repository"
3. Nombre del repositorio: `clinica-dental` (o el que prefieras)
4. Descripción: "Sistema de gestión clínica dental"
5. **IMPORTANTE:** Deja "Public" o "Private" (como prefieras)
6. **NO marques** "Add a README file" (ya tienes archivos)
7. Click en "Create repository"

### Paso 3.3: Subir Código a GitHub

GitHub te mostrará comandos. Ejecuta estos en PowerShell/Terminal (reemplaza `TU_USUARIO` con tu usuario de GitHub):

```bash
# Conectar con GitHub (reemplaza TU_USUARIO con tu usuario)
git remote add origin https://github.com/TU_USUARIO/clinica-dental.git

# Cambiar a rama main
git branch -M main

# Subir código
git push -u origin main
```

**Si te pide usuario y contraseña:**
- Usuario: Tu usuario de GitHub
- Contraseña: Usa un "Personal Access Token" (ver abajo)

**Para crear Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. Nombre: "Render Deployment"
4. Marca "repo" (acceso completo a repositorios)
5. Click "Generate token"
6. **Copia el token** (solo se muestra una vez)
7. Úsalo como contraseña al hacer `git push`

---

## 4. CREAR BASE DE DATOS POSTGRESQL

### Paso 4.1: Ir al Dashboard de Render

1. En Render.com, ve a tu Dashboard
2. Click en el botón azul "New +" (arriba a la derecha)

### Paso 4.2: Seleccionar PostgreSQL

1. En el menú desplegable, click en "PostgreSQL"

### Paso 4.3: Configurar Base de Datos

Completa el formulario:

- **Name:** `clinica-db` (o el nombre que prefieras)
- **Database:** `clinica_db` (nombre de la base de datos)
- **User:** `clinica_user` (usuario de la base de datos)
- **Region:** Elige la región más cercana a ti (ej: "Oregon (US West)")
- **PostgreSQL Version:** Deja la última versión (14 o 15)
- **Plan:** 
  - Para demostración: "Free" (gratis, pero se duerme después de 90 días de inactividad)
  - Para producción: "Starter" ($7/mes, no se duerme)

### Paso 4.4: Crear Base de Datos

1. Click en el botón azul "Create Database"
2. Espera 1-2 minutos mientras Render crea la base de datos
3. Cuando esté listo, verás un panel verde con "Available"

### Paso 4.5: Copiar Credenciales de Conexión

1. En el panel de la base de datos, busca la sección "Connections"
2. Verás algo como:
   ```
   Internal Database URL
   postgresql://clinica_user:XXXXX@dpg-xxxxx-a.oregon-postgres.render.com/clinica_db
   ```
3. **IMPORTANTE:** Copia esta URL completa. La necesitarás más adelante.

**También copia estos valores individuales:**
- **Host:** `dpg-xxxxx-a.oregon-postgres.render.com` (ejemplo)
- **Port:** `5432` (generalmente)
- **Database:** `clinica_db`
- **User:** `clinica_user`
- **Password:** Está en la URL (después de `:` y antes de `@`)

---

## 5. CREAR SERVICIO WEB

### Paso 5.1: Crear Nuevo Servicio Web

1. En Render Dashboard, click en "New +" → "Web Service"

### Paso 5.2: Conectar Repositorio

1. Si es la primera vez, click en "Connect account" junto a GitHub
2. Autoriza a Render a acceder a tus repositorios
3. Selecciona el repositorio `clinica-dental` (o el que creaste)
4. Click en "Connect"

### Paso 5.3: Configurar Servicio Web

Completa el formulario:

**Basic Settings:**
- **Name:** `clinica-dental` (o el nombre que prefieras)
- **Region:** La misma que elegiste para la base de datos
- **Branch:** `main` (o `master` si usas esa rama)
- **Root Directory:** Deja vacío (o pon `gestion_clinica` si tu `manage.py` está en una subcarpeta)
- **Runtime:** `Python 3`
- **Build Command:** 
  ```
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command:**
  ```
  gunicorn gestion_clinica.wsgi:application
  ```

**Plan:**
- Para demostración: "Starter" ($7/mes) - **RECOMENDADO** (no se duerme)
- Alternativa gratis: "Free" (se duerme después de 15 min de inactividad)

### Paso 5.4: Crear Servicio

1. **NO hagas click en "Create Web Service" todavía**
2. Primero necesitas configurar las variables de entorno (siguiente sección)

---

## 6. CONFIGURAR VARIABLES DE ENTORNO

### Paso 6.1: Agregar Variables de Entorno

Antes de crear el servicio, en la sección "Environment Variables", agrega estas variables una por una:

**1. DEBUG**
- Key: `DEBUG`
- Value: `False`

**2. SECRET_KEY**
- Key: `SECRET_KEY`
- Value: (Pega el SECRET_KEY que generaste en el Paso 1.2)

**3. ALLOWED_HOSTS**
- Key: `ALLOWED_HOSTS`
- Value: `tu-app.onrender.com,localhost,127.0.0.1`
- **NOTA:** Reemplaza `tu-app` con el nombre que pusiste en "Name" (ej: si pusiste `clinica-dental`, será `clinica-dental.onrender.com`)

**4. DB_ENGINE**
- Key: `DB_ENGINE`
- Value: `postgresql`

**5. DB_NAME**
- Key: `DB_NAME`
- Value: `clinica_db` (el nombre de la base de datos que pusiste)

**6. DB_USER**
- Key: `DB_USER`
- Value: `clinica_user` (el usuario que pusiste)

**7. DB_PASSWORD**
- Key: `DB_PASSWORD`
- Value: (La contraseña que copiaste de la URL de conexión en Paso 4.5)

**8. DB_HOST**
- Key: `DB_HOST`
- Value: (El host que copiaste, ej: `dpg-xxxxx-a.oregon-postgres.render.com`)

**9. DB_PORT**
- Key: `DB_PORT`
- Value: `5432`

**10. EMAIL_BACKEND**
- Key: `EMAIL_BACKEND`
- Value: `django.core.mail.backends.smtp.EmailBackend`

**11. EMAIL_HOST**
- Key: `EMAIL_HOST`
- Value: `smtp.gmail.com`

**12. EMAIL_PORT**
- Key: `EMAIL_PORT`
- Value: `587`

**13. EMAIL_USE_TLS**
- Key: `EMAIL_USE_TLS`
- Value: `True`

**14. EMAIL_HOST_USER**
- Key: `EMAIL_HOST_USER`
- Value: (Tu email de Gmail, ej: `miclinicacontacto@gmail.com`)

**15. EMAIL_HOST_PASSWORD**
- Key: `EMAIL_HOST_PASSWORD`
- Value: (La App Password de Gmail que generaste en Paso 1.3, sin espacios)

**16. DEFAULT_FROM_EMAIL**
- Key: `DEFAULT_FROM_EMAIL`
- Value: (El mismo email que pusiste en EMAIL_HOST_USER)

**17. SITE_URL**
- Key: `SITE_URL`
- Value: `https://tu-app.onrender.com` (reemplaza `tu-app` con el nombre de tu servicio)

**18. CLINIC_NAME**
- Key: `CLINIC_NAME`
- Value: `Clínica San Felipe`

### Paso 6.2: Crear el Servicio

1. Una vez que hayas agregado todas las variables de entorno
2. Click en el botón azul "Create Web Service"
3. Render comenzará a construir y desplegar tu aplicación
4. Esto tomará 5-10 minutos

### Paso 6.3: Esperar el Despliegue

1. Verás un log en tiempo real del proceso
2. Busca mensajes como:
   - "Building..."
   - "Installing dependencies..."
   - "Collecting static files..."
   - "Starting service..."

**Si hay errores:**
- Revisa el log para ver qué falló
- Verifica que todas las variables de entorno estén correctas
- Verifica que el código esté en GitHub

**Cuando termine exitosamente:**
- Verás "Your service is live at https://tu-app.onrender.com"
- Pero **NO funcionará todavía** porque falta ejecutar las migraciones

---

## 7. EJECUTAR MIGRACIONES

### Paso 7.1: Abrir Shell en Render

1. En el panel de tu servicio web en Render
2. Ve a la pestaña "Shell" (en el menú superior)
3. Click en "Open Shell"

### Paso 7.2: Ejecutar Migraciones

En la terminal que se abre, ejecuta:

```bash
python manage.py migrate
```

**Esto creará todas las tablas en la base de datos.**

Deberías ver mensajes como:
```
Running migrations:
  Applying citas.0001_initial... OK
  Applying personal.0001_initial... OK
  ...
```

### Paso 7.3: Crear Superusuario

En la misma terminal, ejecuta:

```bash
python manage.py createsuperuser
```

Te pedirá:
- **Username:** `admin` (o el que prefieras)
- **Email address:** `admin@clinica.cl` (o el que prefieras)
- **Password:** (escribe una contraseña segura, no la verás mientras escribes)
- **Password (again):** (escribe la misma contraseña)

**IMPORTANTE:** Guarda estas credenciales, las necesitarás para acceder al admin.

---

## 8. CREAR DATOS DE DEMOSTRACIÓN

### Paso 8.1: Ejecutar Comando de Datos Demo

En la misma terminal del Shell de Render, ejecuta:

```bash
python manage.py crear_datos_demo
```

Deberías ver:
```
Creando datos de demostración...
✅ Administrador creado (admin/admin123)
✅ Dentista creado (dentista/dentista123)
✅ Cliente creado (paciente@demo.cl)
```

### Paso 8.2: Verificar Credenciales

Ahora tienes estas credenciales listas:

**Sistema de Gestión (Administrador):**
- URL: `https://tu-app.onrender.com/trabajadores/login/`
- Usuario: `admin`
- Contraseña: `admin123`

**Sistema de Gestión (Dentista):**
- URL: `https://tu-app.onrender.com/trabajadores/login/`
- Usuario: `dentista`
- Contraseña: `dentista123`

**Portal Web (Paciente):**
- URL: `https://tu-app.onrender.com/`
- Email: `paciente@demo.cl`
- Contraseña: (debes crear el usuario desde el sistema de gestión primero)

---

## 9. PROBAR EL SISTEMA

### Paso 9.1: Probar Login de Administrador

1. Ve a: `https://tu-app.onrender.com/trabajadores/login/`
2. Usuario: `admin`
3. Contraseña: `admin123`
4. Deberías entrar al dashboard

### Paso 9.2: Crear Usuario Web para Paciente

1. Dentro del sistema de gestión (como admin)
2. Ve a "Gestor de Clientes"
3. Busca el cliente "Paciente Demo"
4. Click en "Enviar Credenciales" o "Crear Usuario Web"
5. Esto enviará un email al paciente con sus credenciales

### Paso 9.3: Probar Envío de Emails

1. En el sistema de gestión, intenta enviar credenciales a un cliente
2. Verifica que el email llegue
3. Si no llega, revisa:
   - Que `EMAIL_HOST_PASSWORD` sea la App Password (no la contraseña normal)
   - Que el email de Gmail tenga "Acceso de aplicaciones menos seguras" habilitado (si es necesario)

### Paso 9.4: Probar Subir Imágenes

1. Como dentista o admin, intenta subir una radiografía
2. Verifica que se suba correctamente
3. Verifica que se muestre correctamente

### Paso 9.5: Probar las 3 Vistas

Abre 3 pestañas:

**Pestaña 1 - Administrador:**
- URL: `https://tu-app.onrender.com/trabajadores/login/`
- Login: `admin` / `admin123`

**Pestaña 2 - Dentista:**
- URL: `https://tu-app.onrender.com/trabajadores/login/`
- Login: `dentista` / `dentista123`

**Pestaña 3 - Paciente:**
- URL: `https://tu-app.onrender.com/`
- Login: (crear desde sistema de gestión)

---

## 10. SOLUCIÓN DE PROBLEMAS

### Problema: "Application Error" al abrir la URL

**Causas posibles:**
1. Las migraciones no se ejecutaron
2. Variables de entorno incorrectas
3. Error en el código

**Solución:**
1. Ve a "Logs" en Render
2. Revisa los errores
3. Verifica que las variables de entorno estén correctas
4. Ejecuta las migraciones en el Shell

### Problema: "Database connection failed"

**Causas posibles:**
1. Variables de entorno de base de datos incorrectas
2. La base de datos está dormida (plan Free)

**Solución:**
1. Verifica `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
2. Si usas plan Free, espera 1-2 minutos después de hacer una petición (se despierta automáticamente)

### Problema: "Static files not found"

**Causas posibles:**
1. No se ejecutó `collectstatic`

**Solución:**
1. En el Shell de Render, ejecuta:
   ```bash
   python manage.py collectstatic --noinput
   ```
2. Reinicia el servicio (en Render, click en "Manual Deploy" → "Clear build cache & deploy")

### Problema: "Emails no se envían"

**Causas posibles:**
1. `EMAIL_HOST_PASSWORD` no es App Password
2. Gmail bloquea el acceso

**Solución:**
1. Verifica que `EMAIL_HOST_PASSWORD` sea la App Password de 16 caracteres (sin espacios)
2. Ve a https://myaccount.google.com/lesssecureapps y habilita "Acceso de aplicaciones menos seguras" (si está disponible)
3. Verifica que el email de Gmail tenga 2FA habilitado (requerido para App Passwords)

### Problema: "Imágenes no se muestran"

**Causas posibles:**
1. Directorio `media/` no existe
2. Permisos incorrectos

**Solución:**
1. En el Shell de Render, ejecuta:
   ```bash
   mkdir -p media/radiografias media/consentimientos media/insumos media/personal
   ```
2. Reinicia el servicio

### Problema: "Service is sleeping" (Plan Free)

**Causa:**
- El plan Free se duerme después de 15 minutos de inactividad

**Solución:**
- Actualiza a plan Starter ($7/mes) para que no se duerma
- O espera 30-60 segundos después de hacer una petición (se despierta automáticamente)

---

## ✅ CHECKLIST FINAL

Antes de tu demostración, verifica:

- [ ] El servicio está "Live" en Render
- [ ] Puedes hacer login como administrador
- [ ] Puedes hacer login como dentista
- [ ] Puedes hacer login como paciente (portal web)
- [ ] Los emails se envían correctamente
- [ ] Puedes subir imágenes
- [ ] Las imágenes se muestran correctamente
- [ ] Las 3 pestañas funcionan simultáneamente
- [ ] El flujo completo funciona (registro → cita → atención)

---

## 🎯 RESUMEN DE URLS Y CREDENCIALES

**URLs:**
- Portal Web: `https://tu-app.onrender.com/`
- Sistema Gestión: `https://tu-app.onrender.com/trabajadores/login/`
- Admin Django: `https://tu-app.onrender.com/admin/`

**Credenciales Demo:**
- Admin: `admin` / `admin123`
- Dentista: `dentista` / `dentista123`
- Paciente: (crear desde sistema de gestión)

---

## 💡 CONSEJOS FINALES

1. **Prueba todo 1 día antes** de la demostración
2. **Ten un plan B** (puedes correr localmente si Render falla)
3. **Guarda las credenciales** en un lugar seguro
4. **Ten datos de respaldo** creados por si algo falla
5. **Prueba el flujo completo** antes de la demostración

---

¡Éxito con tu despliegue! 🚀

Si tienes algún problema, revisa los logs en Render o consulta la sección de solución de problemas.

