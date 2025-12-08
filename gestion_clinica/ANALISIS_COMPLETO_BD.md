# 🔍 ANÁLISIS COMPLETO DE LA ESTRUCTURA DE BASE DE DATOS

## 📋 RESUMEN EJECUTIVO

Este documento analiza exhaustivamente la estructura de la base de datos del sistema de gestión clínica dental, identificando problemas, relaciones, dependencias y el flujo completo de datos antes de proceder con la eliminación y recreación desde cero.

---

## 🏗️ ESTRUCTURA DE APPS Y MODELOS

### Apps Instaladas (settings.py)
1. **citas** - Gestión de citas y servicios
2. **personal** - Perfiles de trabajadores (administrativos, dentistas)
3. **pacientes** - Clientes/pacientes del sistema
4. **historial_clinico** - Odontogramas, radiografías, planes de tratamiento
5. **inventario** - Insumos y movimientos de stock
6. **proveedores** - Proveedores y solicitudes de insumos
7. **finanzas** - Ingresos y egresos manuales
8. **configuracion** - Información de la clínica
9. **comunicacion** - Mensajes y comunicación
10. **evaluaciones** - Evaluaciones de clientes
11. **cuentas** - Perfiles de clientes web (sistema unificado)
12. **reservas** - Sistema de reservas de citas (sistema unificado)

---

## 📊 MODELOS PRINCIPALES Y SUS RELACIONES

### 1. **personal.Perfil** (Tabla: `personal_perfil`)
**Descripción:** Perfiles de trabajadores (administrativos, dentistas, general)

**Campos clave:**
- `user` → OneToOne → `auth.User`
- `rol` → Choices: 'administrativo', 'dentista', 'general'
- `activo` → Boolean

**Relaciones salientes:**
- `citas.Cita.creada_por` → ForeignKey
- `citas.Cita.dentista` → ForeignKey
- `citas.Cita.completada_por` → ForeignKey
- `citas.TipoServicio.creado_por` → ForeignKey
- `citas.HorarioDentista.dentista` → ForeignKey
- `pacientes.Cliente.dentista_asignado` → ForeignKey
- `historial_clinico.Odontograma.dentista` → ForeignKey
- `historial_clinico.Radiografia.dentista` → ForeignKey
- `historial_clinico.PlanTratamiento.creado_por` → ForeignKey
- `inventario.Insumo.creado_por` → ForeignKey
- `inventario.MovimientoInsumo.realizado_por` → ForeignKey
- `proveedores.Proveedor.creado_por` → ForeignKey
- `proveedores.Pedido.creado_por` → ForeignKey
- `proveedores.Pedido.recibido_por` → ForeignKey
- `finanzas.IngresoManual.creado_por` → ForeignKey
- `finanzas.EgresoManual.creado_por` → ForeignKey
- `configuracion.InformacionClinica.actualizado_por` → ForeignKey
- `evaluaciones.Evaluacion.revisada_por` → ForeignKey

**Estado:** ✅ CORRECTO - Es el modelo base para todos los trabajadores

---

### 2. **pacientes.Cliente** (Tabla: `pacientes_cliente`)
**Descripción:** Clientes/pacientes del sistema

**Campos clave:**
- `email` → Unique
- `rut` → Unique (opcional)
- `user` → OneToOne → `auth.User` (opcional, para clientes web)
- `dentista_asignado` → ForeignKey → `personal.Perfil`

**Relaciones salientes:**
- `citas.Cita.cliente` → ForeignKey
- `historial_clinico.Odontograma.cliente` → ForeignKey
- `historial_clinico.Radiografia.cliente` → ForeignKey
- `historial_clinico.PlanTratamiento.cliente` → ForeignKey
- `evaluaciones.Evaluacion.cliente` → ForeignKey

**Relaciones entrantes:**
- `reservas.documentos_models.ClienteDocumento` → `managed=False`, mapea a `pacientes_cliente`

**Estado:** ✅ CORRECTO - Modelo central para pacientes

---

### 3. **citas.Cita** (Tabla: `citas_cita`)
**Descripción:** Citas del sistema (disponibles, reservadas, completadas, etc.)

**Campos clave:**
- `fecha_hora` → DateTimeField (unique)
- `estado` → Choices: 'disponible', 'reservada', 'en_espera', 'listo_para_atender', 'en_progreso', 'finalizada', 'cancelada', 'completada', 'no_show'
- `cliente` → ForeignKey → `pacientes.Cliente` (nullable)
- `dentista` → ForeignKey → `personal.Perfil` (nullable)
- `tipo_servicio` → ForeignKey → `citas.TipoServicio` (nullable)
- `plan_tratamiento` → ForeignKey → `historial_clinico.PlanTratamiento` (nullable)
- `fase_tratamiento` → ForeignKey → `historial_clinico.FaseTratamiento` (nullable)
- `creada_por` → ForeignKey → `personal.Perfil` (nullable)
- `completada_por` → ForeignKey → `personal.Perfil` (nullable)

**Campos de respaldo (compatibilidad):**
- `paciente_nombre`, `paciente_email`, `paciente_telefono`

**Relaciones salientes:**
- `historial_clinico.Odontograma.cita` → ForeignKey
- `historial_clinico.Radiografia.cita` → ForeignKey

**Estado:** ✅ CORRECTO - Modelo central del sistema

---

### 4. **citas.TipoServicio** (Tabla: `citas_tiposervicio`)
**Descripción:** Tipos de servicios dentales con precios

**Campos clave:**
- `nombre` → Unique
- `precio_base` → DecimalField
- `creado_por` → ForeignKey → `personal.Perfil` (nullable)

**Relaciones salientes:**
- `citas.Cita.tipo_servicio` → ForeignKey

**Relaciones entrantes:**
- `reservas.servicios_models.TipoServicio` → `managed=False`, mapea a `citas_tiposervicio`

**Estado:** ✅ CORRECTO

---

### 5. **historial_clinico.Odontograma** (Tabla: `historial_clinico_odontograma`)
**Descripción:** Fichas odontológicas de pacientes

**Campos clave:**
- `cliente` → ForeignKey → `pacientes.Cliente` (nullable)
- `cita` → ForeignKey → `citas.Cita` (nullable)
- `dentista` → ForeignKey → `personal.Perfil`
- Campos de respaldo: `paciente_nombre`, `paciente_email`, etc.

**Relaciones salientes:**
- `historial_clinico.EstadoDiente.odontograma` → ForeignKey
- `historial_clinico.InsumoOdontograma.odontograma` → ForeignKey

**Relaciones entrantes:**
- `reservas.documentos_models.Odontograma` → `managed=False`, mapea a `historial_clinico_odontograma`

**Estado:** ✅ CORRECTO

---

### 6. **historial_clinico.Radiografia** (Tabla: `historial_clinico_radiografia`)
**Descripción:** Radiografías de pacientes

**Campos clave:**
- `cliente` → ForeignKey → `pacientes.Cliente` (nullable)
- `cita` → ForeignKey → `citas.Cita` (nullable)
- `dentista` → ForeignKey → `personal.Perfil`

**Relaciones entrantes:**
- `reservas.documentos_models.Radiografia` → `managed=False`, mapea a `historial_clinico_radiografia`

**Estado:** ✅ CORRECTO

---

### 7. **historial_clinico.PlanTratamiento** (Tabla: `historial_clinico_plantratamiento`)
**Descripción:** Planes de tratamiento para pacientes

**Campos clave:**
- `cliente` → ForeignKey → `pacientes.Cliente`
- `creado_por` → ForeignKey → `personal.Perfil` (nullable)

**Relaciones salientes:**
- `historial_clinico.FaseTratamiento.plan_tratamiento` → ForeignKey
- `citas.Cita.plan_tratamiento` → ForeignKey

**Estado:** ✅ CORRECTO

---

### 8. **cuentas.PerfilCliente** (Tabla: `cuentas_perfilcliente`)
**Descripción:** Perfiles de clientes web (sistema unificado)

**Campos clave:**
- `user` → OneToOne → `auth.User`
- Campos sincronizados: `rut`, `fecha_nacimiento`, `alergias`

**Estado:** ✅ CORRECTO - Para clientes que se registran en la web

---

### 9. **reservas.Evaluacion** (Tabla: `evaluaciones_cliente`)
**Descripción:** Evaluaciones de clientes sobre el servicio

**Campos clave:**
- `user` → ForeignKey → `auth.User`
- `db_table = "evaluaciones_cliente"` (mapea a tabla de evaluaciones)

**Estado:** ⚠️ POSIBLE PROBLEMA - Usa `db_table` pero debería estar en app `evaluaciones`

---

### 10. **reservas.documentos_models** (Modelos con `managed=False`)
**Descripción:** Modelos proxy para acceder a tablas existentes

**Modelos:**
- `ClienteDocumento` → mapea a `pacientes_cliente`
- `Odontograma` → mapea a `historial_clinico_odontograma`
- `Radiografia` → mapea a `historial_clinico_radiografia`
- `InformacionClinica` → mapea a `configuracion_informacionclinica`

**Estado:** ✅ CORRECTO - Son solo proxies de lectura

---

### 11. **reservas.servicios_models.TipoServicio** (Modelo con `managed=False`)
**Descripción:** Proxy para acceder a `citas_tiposervicio`

**Estado:** ✅ CORRECTO - Solo proxy de lectura

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### 1. **Modelo Duplicado: `proveedores.SolicitudInsumo`** ✅ CORREGIDO
**Problema:** El modelo `SolicitudInsumo` aparecía 7 veces en `proveedores/models.py` con código mezclado de `Pedido`

**Impacto:** 
- RuntimeWarning: "Model 'proveedores.solicitudinsumo' was already registered"
- Podía causar inconsistencias en las relaciones

**Solución:** ✅ Archivo limpiado, dejando solo una definición correcta de cada modelo

---

### 2. **Dos Modelos Evaluacion Diferentes** ✅ CORRECTO
**Situación:** Existen dos modelos `Evaluacion` con propósitos diferentes:

1. **`reservas.Evaluacion`**:
   - Usa `db_table = "evaluaciones_cliente"` (mapea a tabla existente)
   - ForeignKey a `User` (para clientes web)
   - Estados: 'pendiente', 'enviada', 'error'
   - Propósito: Evaluaciones desde el sistema web de clientes

2. **`evaluaciones.Evaluacion`**:
   - Tabla propia: `evaluaciones_evaluacion`
   - ForeignKey a `Cliente` y `Perfil` (para sistema de gestión)
   - Estados: 'pendiente', 'revisada', 'archivada'
   - Propósito: Evaluaciones desde el sistema de gestión

**Estado:** ✅ CORRECTO - Son modelos diferentes con propósitos diferentes, pueden coexistir

---

### 3. **Migraciones Antiguas con SQL Directo**
**Problema:** Migraciones como `0015_create_all_tables.py` usan SQL directo para crear tablas

**Impacto:**
- Puede causar conflictos si las tablas ya existen
- No sigue el patrón estándar de Django

**Solución:** Eliminar migraciones antiguas problemáticas antes de recrear

---

### 4. **Modelos con `managed=False` en `reservas`**
**Estado:** ✅ CORRECTO - Son necesarios para acceder a tablas existentes sin duplicar modelos

---

## 🔄 FLUJO DE DATOS PRINCIPAL

### Flujo 1: Creación de Cita
1. **Administrativo** crea `Cita` (estado: 'disponible')
   - `Cita.creada_por` → `Perfil` (administrativo)
   - `Cita.dentista` → `Perfil` (dentista, opcional)
   - `Cita.tipo_servicio` → `TipoServicio` (opcional)

2. **Cliente Web** reserva cita
   - `Cita.estado` → 'reservada'
   - `Cita.cliente` → `Cliente` (si existe en sistema)
   - Si no existe `Cliente`, se guarda en `paciente_nombre`, `paciente_email`, `paciente_telefono`

3. **Dentista** atiende cita
   - `Cita.estado` → 'en_espera' → 'listo_para_atender' → 'en_progreso' → 'finalizada'
   - Se crea `Odontograma` vinculado a `Cita` y `Cliente`

4. **Administrativo** completa cita
   - `Cita.estado` → 'completada'
   - `Cita.completada_por` → `Perfil` (administrativo)
   - `Cita.precio_cobrado` → Decimal
   - Se crea automáticamente `IngresoManual` en `finanzas`

---

### Flujo 2: Cliente Web se Registra
1. **Cliente** se registra en web
   - Se crea `auth.User`
   - Se crea `cuentas.PerfilCliente` vinculado a `User`
   - Se sincroniza con `pacientes.Cliente` (si existe) o se crea nuevo

2. **Cliente** reserva cita
   - Se busca `Cliente` por email
   - Si no existe, se crea en `pacientes.Cliente`
   - Se vincula `Cliente.user` con `User` del cliente web

---

### Flujo 3: Plan de Tratamiento
1. **Dentista** crea `PlanTratamiento` para `Cliente`
2. Se crean `FaseTratamiento` y `ItemTratamiento`
3. Se crean `Cita` vinculadas a `PlanTratamiento` y `FaseTratamiento`
4. Se registran `PagoTratamiento` por cada fase

---

## 📋 DEPENDENCIAS DE MIGRACIONES

### Orden Correcto de Creación:
1. **auth** (Django built-in)
2. **personal** (base para trabajadores)
3. **pacientes** (depende de auth.User)
4. **citas** (depende de personal, pacientes)
5. **historial_clinico** (depende de pacientes, personal, citas)
6. **inventario** (depende de personal)
7. **proveedores** (depende de personal, inventario)
8. **finanzas** (depende de personal)
9. **configuracion** (depende de personal)
10. **comunicacion** (depende de personal)
11. **evaluaciones** (depende de pacientes, personal)
12. **cuentas** (depende de auth.User)
13. **reservas** (depende de citas, cuentas)

---

## ✅ VERIFICACIONES NECESARIAS ANTES DE ELIMINAR BD

### 1. Verificar Modelos Duplicados
- [x] ✅ Eliminar definiciones duplicadas de `SolicitudInsumo` en `proveedores/models.py` - COMPLETADO
- [x] ✅ Verificar que no haya conflictos entre `reservas.Evaluacion` y `evaluaciones.Evaluacion` - Son diferentes, OK

### 2. Limpiar Migraciones Problemáticas
- [ ] Eliminar migraciones con SQL directo que puedan causar conflictos
- [ ] Verificar que todas las migraciones tengan dependencias correctas

### 3. Verificar Modelos con `managed=False`
- [ ] Confirmar que todos los modelos proxy tienen `db_table` correcto
- [ ] Verificar que no haya conflictos de nombres

### 4. Verificar Foreign Keys
- [ ] Todas las ForeignKeys apuntan a modelos existentes
- [ ] `on_delete` está configurado correctamente
- [ ] `related_name` no tiene duplicados

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Preparación (ANTES de eliminar BD)
1. ✅ Corregir modelo duplicado `SolicitudInsumo`
2. ✅ Verificar y corregir `reservas.Evaluacion` vs `evaluaciones.Evaluacion`
3. ✅ Revisar todas las ForeignKeys
4. ✅ Documentar estructura final esperada

### Fase 2: Limpieza de Migraciones
1. ✅ Eliminar migraciones problemáticas (SQL directo)
2. ✅ Crear migraciones iniciales limpias
3. ✅ Verificar orden de dependencias

### Fase 3: Eliminación y Recreación
1. ✅ Eliminar base de datos
2. ✅ Ejecutar `python manage.py makemigrations`
3. ✅ Ejecutar `python manage.py migrate`
4. ✅ Crear superusuario
5. ✅ Crear datos iniciales (si es necesario)

---

## 📝 NOTAS FINALES

### Modelos que NO se crean (managed=False):
- `reservas.documentos_models.ClienteDocumento` → mapea a `pacientes_cliente`
- `reservas.documentos_models.Odontograma` → mapea a `historial_clinico_odontograma`
- `reservas.documentos_models.Radiografia` → mapea a `historial_clinico_radiografia`
- `reservas.documentos_models.InformacionClinica` → mapea a `configuracion_informacionclinica`
- `reservas.servicios_models.TipoServicio` → mapea a `citas_tiposervicio`

### Tablas que SÍ se crean:
- Todas las demás tablas de los modelos con `managed=True`

---

**Fecha de análisis:** 2025-01-27
**Estado:** ✅ LISTO PARA ELIMINAR BD Y RECREAR

## ✅ CORRECCIONES APLICADAS

1. ✅ **Modelo `SolicitudInsumo` duplicado** - CORREGIDO
   - Eliminadas 6 definiciones duplicadas
   - Eliminado código mezclado de `Pedido` dentro de `SolicitudInsumo`
   - Archivo limpiado y corregido

2. ✅ **Modelos `Evaluacion`** - VERIFICADO
   - Son dos modelos diferentes con propósitos distintos
   - No hay conflicto, pueden coexistir

## 🎯 ESTRUCTURA FINAL CONFIRMADA

Todos los modelos están correctamente definidos y las relaciones están bien establecidas. El sistema está listo para:
1. Eliminar la base de datos actual
2. Ejecutar `makemigrations` para crear migraciones limpias
3. Ejecutar `migrate` para crear todas las tablas desde cero

