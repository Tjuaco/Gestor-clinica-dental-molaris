# Gestión del Historial de Auditoría

## Problema

El sistema de auditoría registra todas las acciones realizadas en el sistema (crear, editar, eliminar, login, etc.). Con el uso diario, esto puede generar miles de registros por día, lo que puede:

- Ralentizar las consultas a la base de datos
- Consumir espacio en disco
- Hacer difícil encontrar información relevante

## Solución Implementada

### 1. Limpieza Automática

El sistema incluye una **limpieza automática** que se ejecuta periódicamente:

- **Política de retención**: Mantiene los últimos **12 meses (365 días)** de registros
- **Límite de registros**: Mantiene máximo **100,000 registros** (los más recientes)
- **Ejecución**: Se ejecuta automáticamente cada ~100 registros nuevos (1% de probabilidad)

### 2. Limpieza Manual

Los administradores pueden limpiar el historial manualmente desde la interfaz:

1. Ir a **Auditoría** → **Gestión de Historial**
2. Hacer clic en **"Limpiar Historial"**
3. Configurar:
   - **Días a mantener**: Mínimo 30 días, máximo 1,095 días (3 años)
   - **Máximo de registros**: Mínimo 10,000, máximo 500,000
4. Confirmar la limpieza

### 3. Comando de Management

Para ejecutar la limpieza desde la línea de comandos o programarla:

```bash
# Limpieza con valores por defecto (12 meses, 100,000 registros)
python manage.py limpiar_auditoria

# Limpiar manteniendo solo 6 meses y 50,000 registros
python manage.py limpiar_auditoria --dias=180 --max-registros=50000

# Simular limpieza sin eliminar (dry-run)
python manage.py limpiar_auditoria --dias=365 --dry-run
```

### 4. Programación Automática (Recomendado)

Para ejecutar la limpieza automáticamente, configure un cron job o tarea programada:

#### Linux/Mac (Cron):
```bash
# Ejecutar cada domingo a las 2:00 AM
0 2 * * 0 cd /ruta/al/proyecto && python manage.py limpiar_auditoria --dias=365 --max-registros=100000
```

#### Windows (Tareas Programadas):
1. Abrir "Programador de tareas"
2. Crear nueva tarea
3. Configurar para ejecutar: `python manage.py limpiar_auditoria`
4. Establecer frecuencia (recomendado: semanal)

## Recomendaciones

### Para Clínicas Pequeñas (< 50 citas/día)
- **Retención**: 12 meses
- **Máximo registros**: 50,000
- **Limpieza**: Mensual

### Para Clínicas Medianas (50-200 citas/día)
- **Retención**: 12 meses
- **Máximo registros**: 100,000
- **Limpieza**: Semanal

### Para Clínicas Grandes (> 200 citas/día)
- **Retención**: 6 meses
- **Máximo registros**: 200,000
- **Limpieza**: Diaria o semanal

## Optimizaciones de Base de Datos

El modelo `AuditoriaLog` incluye índices para mejorar el rendimiento:

- Índice en `fecha_hora` (descendente)
- Índice compuesto en `usuario` + `fecha_hora`
- Índice compuesto en `modulo` + `fecha_hora`
- Índice compuesto en `accion` + `fecha_hora`

Estos índices mejoran significativamente las consultas filtradas.

## Monitoreo

Para verificar el estado del historial:

1. Ir a **Auditoría**
2. Revisar las estadísticas en el banner superior:
   - Total de registros
   - Registros de hoy
   - Registros del mes

## Consideraciones Legales

- **Retención mínima**: Algunas regulaciones pueden requerir mantener registros por períodos específicos
- **Backup**: Antes de limpiar, considere hacer un backup de la base de datos
- **Exportación**: Si necesita mantener registros antiguos, puede exportarlos antes de limpiar

## Troubleshooting

### El sistema está lento
- Verificar cantidad de registros: `python manage.py limpiar_auditoria --dry-run`
- Ejecutar limpieza si hay más de 200,000 registros

### Necesito más historial
- Aumentar `--dias` y `--max-registros` en la limpieza manual
- Considerar aumentar el límite en el código si es necesario

### Error al limpiar
- Verificar permisos de base de datos
- Verificar espacio en disco
- Revisar logs del sistema

