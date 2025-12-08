"""
Script para verificar que todo esté listo antes de desplegar
Ejecutar: python verificar_preparacion.py
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("🔍 Verificando preparación para despliegue...\n")

errores = []
advertencias = []

# 1. Verificar archivos necesarios
archivos_requeridos = [
    'Procfile',
    'runtime.txt',
    'requirements.txt',
    'manage.py',
    'gestion_clinica/settings.py',
    'gestion_clinica/urls.py',
]

print("📁 Verificando archivos necesarios...")
for archivo in archivos_requeridos:
    ruta = BASE_DIR / archivo
    if ruta.exists():
        print(f"  ✅ {archivo}")
    else:
        print(f"  ❌ {archivo} - NO ENCONTRADO")
        errores.append(f"Falta el archivo: {archivo}")

# 2. Verificar contenido de Procfile
print("\n📄 Verificando Procfile...")
procfile_path = BASE_DIR / 'Procfile'
if procfile_path.exists():
    contenido = procfile_path.read_text()
    if 'gunicorn' in contenido:
        print("  ✅ Procfile contiene gunicorn")
    else:
        print("  ❌ Procfile no contiene gunicorn")
        errores.append("Procfile debe contener gunicorn")
else:
    errores.append("Procfile no existe")

# 3. Verificar requirements.txt
print("\n📦 Verificando requirements.txt...")
requirements_path = BASE_DIR / 'requirements.txt'
if requirements_path.exists():
    contenido = requirements_path.read_text()
    if 'gunicorn' in contenido:
        print("  ✅ gunicorn en requirements.txt")
    else:
        print("  ⚠️  gunicorn NO está en requirements.txt")
        advertencias.append("Agregar gunicorn a requirements.txt")
    
    if 'whitenoise' in contenido:
        print("  ✅ whitenoise en requirements.txt")
    else:
        print("  ⚠️  whitenoise NO está en requirements.txt")
        advertencias.append("Agregar whitenoise a requirements.txt")
    
    if 'Django' in contenido:
        print("  ✅ Django en requirements.txt")
    else:
        print("  ❌ Django NO está en requirements.txt")
        errores.append("Django debe estar en requirements.txt")
else:
    errores.append("requirements.txt no existe")

# 4. Verificar settings.py
print("\n⚙️  Verificando settings.py...")
settings_path = BASE_DIR / 'gestion_clinica' / 'settings.py'
if settings_path.exists():
    contenido = settings_path.read_text()
    if 'whitenoise' in contenido.lower():
        print("  ✅ WhiteNoise configurado en settings.py")
    else:
        print("  ⚠️  WhiteNoise no encontrado en settings.py")
        advertencias.append("Verificar configuración de WhiteNoise en settings.py")
    
    if 'DB_ENGINE' in contenido:
        print("  ✅ Configuración de base de datos con variables de entorno")
    else:
        print("  ⚠️  No se encontró DB_ENGINE en settings.py")
        advertencias.append("Verificar configuración de base de datos")
else:
    errores.append("settings.py no existe")

# 5. Verificar urls.py
print("\n🔗 Verificando urls.py...")
urls_path = BASE_DIR / 'gestion_clinica' / 'urls.py'
if urls_path.exists():
    contenido = urls_path.read_text()
    if 'media' in contenido.lower():
        print("  ✅ Configuración de media files encontrada")
    else:
        print("  ⚠️  No se encontró configuración de media files")
        advertencias.append("Verificar configuración de media files en urls.py")
else:
    errores.append("urls.py no existe")

# 6. Verificar comando crear_datos_demo
print("\n📝 Verificando comando crear_datos_demo...")
comando_path = BASE_DIR / 'citas' / 'management' / 'commands' / 'crear_datos_demo.py'
if comando_path.exists():
    print("  ✅ Comando crear_datos_demo existe")
else:
    print("  ⚠️  Comando crear_datos_demo no existe")
    advertencias.append("El comando crear_datos_demo no existe (opcional)")

# Resumen
print("\n" + "="*50)
print("📊 RESUMEN")
print("="*50)

if errores:
    print(f"\n❌ ERRORES ENCONTRADOS: {len(errores)}")
    for error in errores:
        print(f"  • {error}")
    print("\n⚠️  DEBES CORREGIR ESTOS ERRORES ANTES DE DESPLEGAR")
else:
    print("\n✅ No se encontraron errores críticos")

if advertencias:
    print(f"\n⚠️  ADVERTENCIAS: {len(advertencias)}")
    for advertencia in advertencias:
        print(f"  • {advertencia}")
    print("\n💡 Revisa estas advertencias, pero no bloquean el despliegue")
else:
    print("\n✅ No se encontraron advertencias")

if not errores and not advertencias:
    print("\n🎉 ¡TODO LISTO PARA DESPLEGAR!")
    print("\nPróximos pasos:")
    print("  1. Subir código a GitHub")
    print("  2. Crear cuenta en Render.com")
    print("  3. Seguir la guía paso a paso")
elif not errores:
    print("\n✅ Puedes proceder con el despliegue, pero revisa las advertencias")
else:
    print("\n❌ NO procedas con el despliegue hasta corregir los errores")

print("\n" + "="*50)

