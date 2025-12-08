# 📋 COMANDOS PARA SUBIR A GITHUB

## ✅ Estás en la carpeta correcta: `gestion_clinica`

## PASO 1: Cambiar el repositorio remoto

```bash
git remote set-url origin https://github.com/Tjuaco/Gestor-clinica-dental-molaris.git
```

## PASO 2: Verificar que se cambió correctamente

```bash
git remote -v
```

Deberías ver:
```
origin  https://github.com/Tjuaco/Gestor-clinica-dental-molaris.git (fetch)
origin  https://github.com/Tjuaco/Gestor-clinica-dental-molaris.git (push)
```

## PASO 3: Agregar todos los archivos nuevos y cambios

```bash
git add .
```

## PASO 4: Hacer commit de todos los cambios

```bash
git commit -m "Sistema completo preparado para despliegue en Render"
```

## PASO 5: Subir al nuevo repositorio

```bash
git push -u origin main
```

Si te pide usuario y contraseña:
- **Usuario:** Tu usuario de GitHub (Tjuaco)
- **Contraseña:** Usa un Personal Access Token (ver abajo)

---

## 🔑 CREAR PERSONAL ACCESS TOKEN (Si te pide contraseña)

1. Ve a: https://github.com/settings/tokens
2. Click en "Generate new token" → "Generate new token (classic)"
3. Nombre: "Render Deployment"
4. Expiración: 90 días (o el que prefieras)
5. Marca la casilla **"repo"** (acceso completo a repositorios)
6. Click en "Generate token" (abajo)
7. **COPIA EL TOKEN** (solo se muestra una vez, algo como: `ghp_xxxxxxxxxxxxx`)
8. Úsalo como contraseña cuando Git te la pida

---

## ✅ VERIFICAR QUE SE SUBIÓ

1. Ve a: https://github.com/Tjuaco/Gestor-clinica-dental-molaris
2. Deberías ver todos tus archivos

---

## ⚠️ SI HAY ERRORES

**Error: "remote origin already exists"**
→ Ya lo cambiamos con `git remote set-url`, está bien

**Error: "authentication failed"**
→ Usa Personal Access Token en lugar de contraseña

**Error: "failed to push"**
→ Verifica que el repositorio esté vacío o que tengas permisos

