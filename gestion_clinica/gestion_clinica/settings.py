"""
Django settings for gestion_clinica project.
"""

from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
# En producción, SECRET_KEY debe estar en variables de entorno sin default
if DEBUG:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-28vh&5z1ku08x3e@gwocph(vtcc=k3shq(!6=4@-v1iuw+c)5t')
else:
    SECRET_KEY = config('SECRET_KEY')  # Sin default en producción - debe estar en .env

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# CSRF Trusted Origins - Agregar tu IP o dominio
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'citas',
    'personal',
    'pacientes',
    'historial_clinico',
    'inventario',
    'proveedores',
    'finanzas',
    'configuracion',
    # Apps de cliente_web unificadas
    'cuentas',
    'reservas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cuentas.middleware.ClienteActivoMiddleware',  # Verificar que el cliente esté activo
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_clinica.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'citas.context_processors.info_clinica',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_clinica.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DB_ENGINE = config('DB_ENGINE', default='sqlite')

if DB_ENGINE == 'postgresql':
    # Validar que las credenciales críticas estén presentes en producción
    if not DEBUG:
        db_password = config('DB_PASSWORD')
        if not db_password:
            raise ValueError("DB_PASSWORD debe estar configurado en producción")
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='clinica_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            # Pool de conexiones para mejor rendimiento
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),  # 10 minutos
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }
else:
    # SQLite por defecto (solo para desarrollo local)
    # NOTA: En producción siempre usar PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de WhiteNoise para servir archivos estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/trabajadores/login/'
LOGIN_REDIRECT_URL = '/trabajadores/dashboard/'
LOGOUT_REDIRECT_URL = '/trabajadores/login/'

# Autenticación - Backends personalizados para clientes
AUTHENTICATION_BACKENDS = [
    'cuentas.backends.ClienteBackend',  # Backend personalizado que verifica existencia en sistema de gestión
    'django.contrib.auth.backends.ModelBackend',  # Backend estándar como fallback
]

# Nota: Solo se usa correo electrónico para notificaciones. WhatsApp y SMS no están implementados.

# Información de la clínica para personalizar mensajes (opcional, se obtiene del modelo si no se define)
CLINIC_NAME = config('CLINIC_NAME', default='Clínica Dental San Felipe')
CLINIC_ADDRESS = config('CLINIC_ADDRESS', default='')
CLINIC_PHONE = config('CLINIC_PHONE', default='')
CLINIC_EMAIL = config('CLINIC_EMAIL', default='')
CLINIC_WEBSITE = config('CLINIC_WEBSITE', default='')
CLINIC_MAP_URL = config('CLINIC_MAP_URL', default='https://www.google.com/maps/place/Clinica+San+Felipe/@-38.2356192,-72.3361399,17z/data=!3m1!4b1!4m6!3m5!1s0x966b155a8306e093:0x46de06dfbc92e29d!8m2!3d-38.2356192!4d-72.333565!16s%2Fg%2F11sswz76yt?hl=es&entry=ttu')

# URL base del sitio para construir enlaces en mensajes
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Variables eliminadas - ya no se usan después de la unificación

# Configuración de Email
# Email de la clínica para enviar correos
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='miclinicacontacto@gmail.com')
# IMPORTANTE: En producción, EMAIL_HOST_PASSWORD debe estar en .env sin default
# Nunca hardcodear contraseñas en el código
if DEBUG:
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
else:
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Sin default en producción
# Email desde el cual se enviarán los correos (debe ser el mismo que EMAIL_HOST_USER para Gmail)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='miclinicacontacto@gmail.com')

# Configuración de Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,  # Mantener 5 archivos de backup
            'formatter': 'verbose',
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,  # Mantener 5 archivos de backup
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'citas': {
            'handlers': ['console', 'file', 'file_info'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'reservas': {
            'handlers': ['console', 'file', 'file_info'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'cuentas': {
            'handlers': ['console', 'file', 'file_info'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# ============================================
# CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN
# ============================================
if not DEBUG:
    # Detectar si estamos usando HTTPS o HTTP
    USE_HTTPS = config('USE_HTTPS', default=False, cast=bool)
    
    # HTTPS y seguridad (solo si usamos HTTPS)
    if USE_HTTPS:
        SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
        SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 año
        SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
        SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
        # Cookies seguras solo con HTTPS
        SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
        CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    else:
        # Si usamos HTTP, las cookies no deben ser seguras
        SECURE_SSL_REDIRECT = False
        SESSION_COOKIE_SECURE = False
        CSRF_COOKIE_SECURE = False
    
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Si está detrás de un proxy (Nginx, etc.)
    SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default=None)
    if SECURE_PROXY_SSL_HEADER:
        SECURE_PROXY_SSL_HEADER = tuple(SECURE_PROXY_SSL_HEADER.split(','))
    
    # X-Frame-Options
    X_FRAME_OPTIONS = 'DENY'
    
    # Content Security Policy (opcional, puede causar problemas con algunos templates)
    # SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_BROWSER_XSS_FILTER = True

# Handlers para páginas de error personalizadas
handler404 = 'citas.views.handler404'
handler500 = 'citas.views.handler500'
