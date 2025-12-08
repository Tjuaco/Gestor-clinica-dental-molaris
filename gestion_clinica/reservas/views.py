# reservas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.utils import timezone
from django.db.models import Q
from django.db import connections
from datetime import datetime, timedelta
from functools import wraps
# Usar Cita de citas.models en lugar de reservas.models (evita conflicto de tablas)
from citas.models import Cita
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import requests
from urllib.parse import urljoin

# Solo se usa correo electrónico para notificaciones. WhatsApp y SMS no están implementados.
import logging

logger = logging.getLogger(__name__)
from cuentas.models import PerfilCliente
from .helpers import obtener_citas_cliente, obtener_dentistas_activos
from .documentos_models import Odontograma, Radiografia, ClienteDocumento
from .servicios_models import TipoServicio


def login_required_cliente(view_func):
    """
    Decorador personalizado para vistas de clientes que redirige al login de clientes
    en lugar del login de trabajadores.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Usuario no autenticado, redirigir al login de clientes
            messages.info(request, 'Por favor, inicia sesión para acceder a esta sección.')
            return redirect('login_cliente')
        
        # Usuario autenticado, verificar que tenga PerfilCliente (es cliente, no trabajador)
        try:
            PerfilCliente.objects.get(user=request.user)
            # Si tiene PerfilCliente, ejecutar la vista normalmente
            return view_func(request, *args, **kwargs)
        except PerfilCliente.DoesNotExist:
            # Si no tiene PerfilCliente, es un trabajador intentando acceder
            # Cerrar sesión y redirigir al login de clientes con mensaje
            from django.contrib.auth import logout
            logout(request)
            messages.warning(request, 'Esta sección es solo para clientes. Por favor, inicia sesión con tu cuenta de cliente.')
            return redirect('login_cliente')
    return wrapper

@login_required_cliente
def reservar_cita(request, cita_id):
    if request.method == 'POST':
        # Verificar que el usuario no tenga ya una cita reservada
        # Buscar por email y cliente_id (más confiable que username)
        try:
            perfil_temp = PerfilCliente.objects.get(user=request.user)
            email_temp = perfil_temp.email or request.user.email
        except PerfilCliente.DoesNotExist:
            email_temp = request.user.email
        
        # Buscar por email
        citas_existentes = Cita.objects.filter(
            paciente_email=email_temp,
            estado__in=['reservada', 'confirmada']
        ).count()
        
        # También buscar por cliente_id si existe
        if citas_existentes == 0:
            try:
                from django.db import connections
                with connections['default'].cursor() as cursor:
                    cursor.execute("""
                        SELECT id FROM pacientes_cliente
                        WHERE email = %s AND activo = TRUE
                        LIMIT 1
                    """, [email_temp])
                    cliente_row = cursor.fetchone()
                    if cliente_row:
                        cliente_id = cliente_row[0]
                        cursor.execute("""
                            SELECT COUNT(*) FROM citas_cita
                            WHERE cliente_id = %s 
                            AND estado IN ('reservada', 'confirmada')
                        """, [cliente_id])
                        count_row = cursor.fetchone()
                        if count_row:
                            citas_existentes = count_row[0]
            except Exception as e:
                logger.warning(f"Error al verificar citas existentes por cliente_id: {e}")
                # Continuar con la verificación por email
        
        if citas_existentes > 0:
            messages.error(request, '❌ Ya tienes una cita activa. Solo puedes reservar una cita a la vez.')
            return redirect('panel_cliente')
        
        cita = get_object_or_404(Cita.objects.select_related('dentista', 'tipo_servicio', 'cliente'), id=cita_id)
        if cita.estado == 'disponible':
            # Obtener datos de perfil del usuario para usar nombre completo
            try:
                perfil = PerfilCliente.objects.get(user=request.user)
                nombre_completo = perfil.nombre_completo
                email = perfil.email or request.user.email
                telefono = perfil.telefono
            except PerfilCliente.DoesNotExist:
                # Si no hay perfil, usar datos del User
                nombre_completo = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                email = request.user.email or ''
                telefono = ''
            
            # Buscar o crear el Cliente en el sistema de gestión usando SQL directo
            from django.db import connections
            cliente_id = None
            
            with connections['default'].cursor() as cursor:
                # Primero intentar buscar en pacientes_cliente (tabla correcta)
                cursor.execute("""
                    SELECT id, nombre_completo, telefono, activo
                    FROM pacientes_cliente
                    WHERE email = %s
                    LIMIT 1
                """, [email])
                
                cliente_existente = cursor.fetchone()
                
                # Si no existe en pacientes_cliente, crear nuevo cliente
                if not cliente_existente:
                    # Crear nuevo cliente en pacientes_cliente
                    telefono_cliente = telefono if telefono else '+56900000000'
                    cursor.execute("""
                        INSERT INTO pacientes_cliente (nombre_completo, email, telefono, activo, fecha_registro)
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING id
                    """, [nombre_completo, email, telefono_cliente, True])
                    
                    cliente_id = cursor.fetchone()[0]
                else:
                    # Cliente existe en pacientes_cliente, actualizar si es necesario
                    cliente_id, nombre_existente, telefono_existente, activo = cliente_existente
                    
                    # Actualizar información si es necesario
                    actualizar = False
                    nuevos_valores = {}
                    
                    if nombre_completo and nombre_completo != nombre_existente:
                        nuevos_valores['nombre_completo'] = nombre_completo
                        actualizar = True
                    
                    if telefono and telefono != telefono_existente:
                        nuevos_valores['telefono'] = telefono
                        actualizar = True
                    
                    # Asegurar que el cliente esté activo
                    if not activo:
                        nuevos_valores['activo'] = True
                        actualizar = True
                    
                    if actualizar:
                        # Construir SET clause de forma segura
                        set_parts = []
                        valores_update = []
                        for key, value in nuevos_valores.items():
                            set_parts.append(f"{key} = %s")
                            valores_update.append(value)
                        valores_update.append(cliente_id)
                        
                        cursor.execute(f"""
                            UPDATE pacientes_cliente
                            SET {', '.join(set_parts)}
                            WHERE id = %s
                        """, valores_update)
            
            # Actualizar la cita con el cliente_id y los datos del paciente
            # Guardar tanto el nombre completo como el username para facilitar búsquedas
            # El nombre completo se guarda en paciente_nombre, y el username se puede usar en notas o como respaldo
            cita.paciente_nombre = nombre_completo
            cita.paciente_email = email
            cita.paciente_telefono = telefono if telefono else None
            cita.estado = 'reservada'
            # Guardar el username en las notas para referencia (formato: "username: juanperez")
            notas_actuales = cita.notas or ''
            if f"username: {request.user.username}" not in notas_actuales:
                cita.notas = f"{notas_actuales}\nusername: {request.user.username}".strip() if notas_actuales else f"username: {request.user.username}"
            
            # Actualizar cliente_id usando SQL directo (ya que el modelo de cliente_web no tiene este campo)
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    UPDATE citas_cita
                    SET cliente_id = %s,
                        paciente_nombre = %s,
                        paciente_email = %s,
                        paciente_telefono = %s,
                        estado = %s,
                        notas = %s
                    WHERE id = %s
                """, [cliente_id, nombre_completo, email, telefono if telefono else None, 'reservada', cita.notas, cita.id])
            
            # Actualizar también el objeto en memoria para que refleje los cambios
            # No usar refresh_from_db() para evitar JOINs automáticos que puedan causar problemas
            # En su lugar, actualizar manualmente los campos
            cita.paciente_nombre = nombre_completo
            cita.paciente_email = email
            cita.paciente_telefono = telefono if telefono else None
            cita.estado = 'reservada'
            
            # IMPORTANTE: Asegurar que el objeto tenga cliente_id para que las relaciones funcionen
            if hasattr(cita, 'cliente_id'):
                cita.cliente_id = cliente_id

            # IMPORTANTE: Refrescar el objeto cita desde la BD para obtener todas las relaciones
            # (dentista, tipo_servicio, precio_cobrado, etc.) antes de enviar el correo
            try:
                cita.refresh_from_db()
            except Exception as e:
                logger.warning(f"No se pudo refrescar cita desde BD: {e}. Continuando con datos en memoria.")
                    
            # Enviar notificaciones por correo electrónico
            try:
                # Usar el servicio de mensajería de gestion_clinica (ahora está unificado)
                from citas.mensajeria_service import enviar_notificaciones_cita
                logger.info(f"[DEBUG] Enviando notificaciones por correo para cita {cita.id} desde página web cliente")
                resultado = enviar_notificaciones_cita(cita)
                
                if resultado.get('email', {}).get('enviado'):
                    messages.success(request, f"Cita reservada exitosamente para {cita.fecha_hora}. Se envió confirmación por correo electrónico.")
                else:
                    error_email = resultado.get('email', {}).get('error', 'Error desconocido')
                    logger.warning(f"No se pudo enviar correo de confirmación para cita {cita.id}: {error_email}")
                    messages.success(request, f"Cita reservada exitosamente para {cita.fecha_hora}.")
            except (ImportError, ModuleNotFoundError) as e:
                logger.warning(f"No se pudo usar servicio de mensajería de gestion_clinica: {e}")
                messages.success(request, f"Cita reservada exitosamente para {cita.fecha_hora}.")
            except Exception as e:
                logger.error(f"Error al enviar notificaciones para cita {cita.id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                messages.success(request, f"Cita reservada exitosamente para {cita.fecha_hora}. No se pudieron enviar las notificaciones automáticas.")
        else:
            messages.error(request, "Esta cita ya no está disponible")
        return redirect('panel_cliente')
    return redirect('panel_cliente')


@login_required_cliente
def panel_cliente(request):
    # Obtener parámetros de filtro
    tipo_consulta = request.GET.get('tipo_consulta', '')
    fecha_filtro = request.GET.get('fecha', '')
    dentista_id = request.GET.get('dentista_id', '')
    
    # Obtener citas disponibles con filtros
    citas_disponibles = Cita.objects.filter(estado='disponible')
    
    # Aplicar filtros si existen
    if tipo_consulta:
        # Si tipo_consulta es un ID numérico, filtrar por tipo_servicio
        # Si es texto, filtrar por tipo_consulta (compatibilidad con valores antiguos)
        try:
            tipo_servicio_id = int(tipo_consulta)
            citas_disponibles = citas_disponibles.filter(tipo_servicio_id=tipo_servicio_id)
        except ValueError:
            # Es texto, usar filtro por tipo_consulta
            citas_disponibles = citas_disponibles.filter(tipo_consulta=tipo_consulta)
    
    if fecha_filtro:
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            citas_disponibles = citas_disponibles.filter(fecha_hora__date=fecha_obj)
        except ValueError as e:
            logger.debug(f"Fecha de filtro inválida: {fecha_filtro}, error: {e}")
            # Si la fecha es inválida, ignorar el filtro
    
    citas_disponibles = citas_disponibles.order_by('fecha_hora')
    
    # Aplicar filtro de dentista si existe
    if dentista_id:
        try:
            dentista_id_int = int(dentista_id)
            # Filtrar citas que tienen este dentista asignado
            citas_disponibles = citas_disponibles.filter(dentista_id=dentista_id_int)
        except ValueError as e:
            logger.debug(f"ID de dentista inválido: {dentista_id}, error: {e}")
            # Si el ID es inválido, ignorar el filtro
    
    # Optimizar consulta con select_related (elimina necesidad de servicios innecesarios)
    citas_disponibles = citas_disponibles.select_related('dentista', 'tipo_servicio')
    
    # Preparar información adicional para cada cita
    citas_preparadas = []
    for cita in citas_disponibles:
        # Preparar información del servicio
        servicio_info = None
        if cita.tipo_servicio:
            precio = cita.precio_cobrado if cita.precio_cobrado else cita.tipo_servicio.precio_base
            servicio_info = {
                'nombre': cita.tipo_servicio.nombre,
                'precio': precio,
                'precio_formateado': f'${precio:,.0f}' if precio else None,
                'precio_cobrado_formateado': f'${cita.precio_cobrado:,.0f}' if cita.precio_cobrado else None,
                'duracion_estimada': cita.tipo_servicio.duracion_estimada if hasattr(cita.tipo_servicio, 'duracion_estimada') else None,
            }
        
        # Preparar información del dentista
        dentista_info = None
        if cita.dentista:
            dentista_info = {
                'nombre': cita.dentista.nombre_completo,
                'especialidad': getattr(cita.dentista, 'especialidad', 'Odontología General'),
                'foto': getattr(cita.dentista, 'foto', ''),
                'numero_colegio': getattr(cita.dentista, 'numero_colegio', 'N/A'),
            }
        
        # Agregar información a la cita (usando atributos dinámicos)
        cita.servicio_info = servicio_info
        cita.dentista_info = dentista_info
        citas_preparadas.append(cita)
    
    # Obtener citas reservadas usando función helper centralizada
    citas_reservadas = obtener_citas_cliente(request.user, estados=['reservada', 'confirmada'])
    
    # Obtener perfil del usuario
    try:
        perfil_usuario = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil_usuario = None
    

    # Obtener lista de dentistas disponibles para el filtro usando ORM
    dentistas_disponibles = obtener_dentistas_activos()
    
    # Obtener servicios activos del sistema de gestión
    from citas.models import TipoServicio
    servicios_activos = TipoServicio.objects.filter(activo=True).order_by('categoria', 'nombre')
    
    # Obtener información de la clínica desde settings
    telefono_clinica = getattr(settings, 'CLINIC_PHONE', '+56 9 1234 5678')
    clinic_map_url = getattr(settings, 'CLINIC_MAP_URL', '')
    clinic_address = getattr(settings, 'CLINIC_ADDRESS', 'Victoria, Región de la Araucanía')
    
    return render(request, "reservas/panel.html", {
        "citas": citas_preparadas,  # Citas con información preparada
        "citas_reservadas": citas_reservadas,
        "perfil_usuario": perfil_usuario,
        "dentistas_disponibles": dentistas_disponibles,
        "servicios_activos": servicios_activos,
        "telefono_clinica": telefono_clinica,
        "CLINIC_MAP_URL": clinic_map_url,
        "CLINIC_ADDRESS": clinic_address,
    })


def _cambiar_estado_cita(cita: Cita, nuevo_estado: str):
    cita.estado = nuevo_estado
    cita.save(update_fields=["estado"])


@csrf_exempt
def confirmar_cita(request, cita_id):
    """Endpoint público para confirmar sin login (desde enlace)."""
    cita = get_object_or_404(Cita, id=cita_id)
    if cita.estado in ("reservada", "confirmada"):
        _cambiar_estado_cita(cita, "confirmada")
        messages.success(request, f"Cita confirmada para {cita.fecha_hora}")
        return redirect('panel_cliente') if request.user.is_authenticated else JsonResponse({
            'ok': True,
            'cita_id': cita.id,
            'estado': cita.estado,
        })
    return JsonResponse({'ok': False, 'error': 'Cita no reservada'}, status=400)



@login_required_cliente
def obtener_citas_fecha(request):
    """Vista AJAX para obtener citas de una fecha específica"""
    if request.method == 'GET':
        fecha = request.GET.get('fecha')
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                citas = Cita.objects.filter(
                    fecha_hora__date=fecha_obj,
                    estado='disponible'
                ).order_by('fecha_hora')
                
                citas_data = []
                for cita in citas:
                    citas_data.append({
                        'id': cita.id,
                        'fecha_hora': cita.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                        'hora': cita.fecha_hora.strftime('%H:%M')
                    })
                
                return JsonResponse({'citas': citas_data})
            except ValueError:
                return JsonResponse({'error': 'Formato de fecha inválido'})
    
    return JsonResponse({'error': 'Método no permitido'})


# ============================================
# VISTAS DEL MENÚ LATERAL
# ============================================

@login_required_cliente
def mi_perfil(request):
    """Vista para ver y editar el perfil del usuario"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        # Si no existe perfil, crear uno automáticamente con los datos del usuario
        # Intentar obtener teléfono de alguna cita existente usando email (más confiable)
        telefono_desde_cita = None
        try:
            email_usuario = request.user.email
            if email_usuario:
                cita_existente = Cita.objects.filter(paciente_email=email_usuario).first()
                if cita_existente and cita_existente.paciente_telefono:
                    telefono_desde_cita = cita_existente.paciente_telefono
        except Exception:
            pass
        
        # Crear perfil con datos disponibles
        nombre_completo = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        email = request.user.email or ''
        
        perfil = PerfilCliente.objects.create(
            user=request.user,
            nombre_completo=nombre_completo,
            telefono=telefono_desde_cita or '',
            email=email,
            telefono_verificado=False
        )
    
    # Sincronizar información del perfil desde pacientes_cliente del sistema de gestión
    # Esto asegura que el email, teléfono y nombre estén actualizados
    cliente_doc = None
    
    # 1. Intentar buscar el cliente en pacientes_cliente por múltiples métodos
    try:
        # Primero intentar por nombre completo (más estable que el email)
        if perfil.nombre_completo:
            cliente_doc = ClienteDocumento.objects.filter(nombre_completo=perfil.nombre_completo).first()
        
        # Si no se encontró, intentar por el email del User de Django (puede estar más actualizado)
        if not cliente_doc and request.user.email:
            cliente_doc = ClienteDocumento.objects.filter(email=request.user.email).first()
        
        # Si no se encontró, intentar por el email del perfil actual
        if not cliente_doc and perfil.email:
            cliente_doc = ClienteDocumento.objects.filter(email=perfil.email).first()
        
        # Si aún no se encontró, intentar buscar desde las citas del usuario usando email
        # Las citas pueden tener el email actualizado
        if not cliente_doc:
            try:
                email_usuario = request.user.email or perfil.email
                if email_usuario:
                    cita_con_email = Cita.objects.filter(
                        paciente_email=email_usuario,
                        paciente_email__isnull=False
                    ).exclude(paciente_email='').first()
                    
                    if cita_con_email and cita_con_email.paciente_email:
                        cliente_doc = ClienteDocumento.objects.filter(email=cita_con_email.paciente_email).first()
            except Exception:
                pass
        
        # Si encontramos el cliente en pacientes_cliente, sincronizar todos los datos
        if cliente_doc:
            actualizado = False
            
            # Actualizar email si es diferente
            if cliente_doc.email and cliente_doc.email != perfil.email:
                perfil.email = cliente_doc.email
                actualizado = True
            
            # Actualizar teléfono si está vacío o es diferente
            if cliente_doc.telefono:
                if not perfil.telefono or perfil.telefono.strip() == '':
                    perfil.telefono = cliente_doc.telefono
                    actualizado = True
            
            # Actualizar nombre completo si está disponible y es diferente
            if cliente_doc.nombre_completo and cliente_doc.nombre_completo != perfil.nombre_completo:
                perfil.nombre_completo = cliente_doc.nombre_completo
                actualizado = True
            
            # Actualizar RUT si está disponible y es diferente
            if cliente_doc.rut and cliente_doc.rut != perfil.rut:
                perfil.rut = cliente_doc.rut
                actualizado = True
            
            # Actualizar fecha de nacimiento si está disponible y es diferente
            if cliente_doc.fecha_nacimiento and cliente_doc.fecha_nacimiento != perfil.fecha_nacimiento:
                perfil.fecha_nacimiento = cliente_doc.fecha_nacimiento
                actualizado = True
            
            # Actualizar alergias si está disponible y es diferente (MUY IMPORTANTE)
            if cliente_doc.alergias is not None:
                # Actualizar si el perfil no tiene alergias o si son diferentes
                if not perfil.alergias or perfil.alergias.strip() == '' or cliente_doc.alergias.strip() != perfil.alergias.strip():
                    perfil.alergias = cliente_doc.alergias
                    actualizado = True
            
            # Guardar los cambios si hubo actualizaciones
            if actualizado:
                perfil.save()
    except Exception:
        pass
    
    # Si no se encontró en pacientes_cliente y el teléfono está vacío, intentar desde las citas del usuario usando email
    if perfil and (not perfil.telefono or perfil.telefono.strip() == ''):
        telefono_encontrado = None
        try:
            email_usuario = request.user.email or perfil.email
            if email_usuario:
                cita_con_telefono = Cita.objects.filter(
                    paciente_email=email_usuario,
                    paciente_telefono__isnull=False
                ).exclude(paciente_telefono='').first()
                
                if cita_con_telefono and cita_con_telefono.paciente_telefono:
                    telefono_encontrado = cita_con_telefono.paciente_telefono
                    
                    # Actualizar el perfil si se encontró teléfono
                    if telefono_encontrado:
                        perfil.telefono = telefono_encontrado
                        perfil.save(update_fields=['telefono'])
        except Exception:
            pass
    
    # Obtener estadísticas del usuario usando la función helper (más confiable)
    citas_totales = obtener_citas_cliente(
        request.user, 
        estados=['reservada', 'confirmada', 'completada', 'cancelada'],
        incluir_completadas=True
    ).count()
    citas_reservadas = obtener_citas_cliente(
        request.user, 
        estados=['reservada', 'confirmada']
    ).count()
    citas_completadas = obtener_citas_cliente(
        request.user, 
        estados=['completada'],
        incluir_completadas=True
    ).count()
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'user': request.user,
        'citas_totales': citas_totales,
        'citas_reservadas': citas_reservadas,
        'citas_completadas': citas_completadas,
    }
    
    return render(request, 'reservas/mi_perfil.html', context)


@login_required_cliente
def mis_citas_activas(request):
    """Vista para ver solo la cita activa actual del usuario"""
    # Usar función helper centralizada
    citas_activas = obtener_citas_cliente(request.user, estados=['reservada', 'confirmada'])
    
    # Obtener perfil del usuario
    try:
        perfil_usuario_obj = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil_usuario_obj = None
    
    context = {
        'citas_activas': citas_activas,
        'perfil_usuario': perfil_usuario_obj,
        'total_citas_activas': citas_activas.count(),
        'citas_reservadas': citas_activas,  # Para el badge del sidebar
    }
    
    return render(request, 'reservas/mis_citas_activas.html', context)


@login_required_cliente
def historial_citas(request):
    """Vista para ver el historial completo de citas del usuario"""
    # Usar función helper centralizada con todos los estados
    citas_historial = obtener_citas_cliente(
        request.user, 
        estados=['reservada', 'confirmada', 'completada', 'cancelada'],
        incluir_completadas=True
    ).order_by('-fecha_hora')
    
    context = {
        'citas_historial': citas_historial,
    }
    
    return render(request, 'reservas/historial_citas.html', context)


@login_required_cliente
def ayuda(request):
    """Vista para el centro de ayuda"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil = None
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
    }
    
    return render(request, 'reservas/ayuda.html', context)


# ============================================
# VISTAS DE DOCUMENTOS (FICHAS Y RADIOGRAFÍAS)
# ============================================

@login_required_cliente
def ver_odontogramas(request):
    """Vista para ver todas las fichas odontológicas del usuario"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener cliente desde la tabla pacientes_cliente si existe
    cliente_doc = None
    try:
        cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
    except Exception:
        pass
    
    # Obtener odontogramas por email del paciente (optimizado)
    odontogramas = Odontograma.objects.filter(paciente_email=email_usuario)
    
    # Si tenemos cliente_id, también buscar por ese ID
    if cliente_doc:
        odontogramas_cliente = Odontograma.objects.filter(cliente_id=cliente_doc.id)
        odontogramas = (odontogramas | odontogramas_cliente).distinct()
    
    # Ordenar
    odontogramas = odontogramas.order_by('-fecha_creacion')
    
    # Obtener perfil del usuario para el template base
    try:
        perfil_usuario = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil_usuario = None
    
    context = {
        'odontogramas': odontogramas,
        'total': odontogramas.count(),
        'perfil': perfil if 'perfil' in locals() else None,
        'perfil_usuario': perfil_usuario,
    }
    
    return render(request, 'reservas/ver_odontogramas.html', context)


@login_required_cliente
def ver_odontograma(request, odontograma_id):
    """Vista para ver un odontograma específico"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener el odontograma solo si pertenece al usuario
    try:
        odontograma = Odontograma.objects.get(
            id=odontograma_id,
            paciente_email=email_usuario
        )
    except Odontograma.DoesNotExist:
        # Intentar buscar por cliente_id también
        try:
            cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
            if cliente_doc:
                odontograma = Odontograma.objects.get(
                    id=odontograma_id,
                    cliente_id=cliente_doc.id
                )
            else:
                messages.error(request, 'No tienes acceso a este documento.')
                return redirect('ver_odontogramas')
        except Odontograma.DoesNotExist:
            messages.error(request, 'No tienes acceso a este documento.')
            return redirect('ver_odontogramas')
    
    # Obtener perfil del usuario para el template base
    try:
        perfil_usuario = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil_usuario = None
    
    context = {
        'odontograma': odontograma,
        'perfil_usuario': perfil_usuario,
    }
    
    return render(request, 'reservas/ver_odontograma.html', context)


@login_required_cliente
def descargar_odontograma(request, odontograma_id):
    """Vista para ver resumen de odontograma - Redirige a la vista de detalle"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Verificar que el odontograma pertenece al usuario (optimizado)
    try:
        odontograma = Odontograma.objects.get(
            id=odontograma_id,
            paciente_email=email_usuario
        )
    except Odontograma.DoesNotExist:
        try:
            cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
            if cliente_doc:
                odontograma = Odontograma.objects.get(
                    id=odontograma_id,
                    cliente_id=cliente_doc.id
                )
            else:
                messages.error(request, 'No tienes acceso a este documento.')
                return redirect('ver_odontogramas')
        except Odontograma.DoesNotExist:
            messages.error(request, 'No tienes acceso a este documento.')
            return redirect('ver_odontogramas')
    
    # Redirigir a la vista de detalle que mostrará el resumen
    return redirect('ver_odontograma', odontograma_id=odontograma_id)


@login_required_cliente
def ver_pdf_odontograma(request, odontograma_id):
    """Vista proxy para servir PDF de odontograma (evita problemas de CORS)"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener el odontograma solo si pertenece al usuario (optimizado)
    try:
        odontograma = Odontograma.objects.get(
            id=odontograma_id,
            paciente_email=email_usuario
        )
    except Odontograma.DoesNotExist:
        try:
            cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
            if cliente_doc:
                odontograma = Odontograma.objects.get(
                    id=odontograma_id,
                    cliente_id=cliente_doc.id
                )
            else:
                return HttpResponse('Acceso denegado', status=403)
        except Odontograma.DoesNotExist:
            return HttpResponse('Acceso denegado', status=403)
    
    # Ya no necesitamos URL externa, todo está unificado
    # Usar la URL base del sitio actual
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    
    # Intentar primero desde API endpoints (si existen)
    api_endpoints = [
        f"{base_url}/api/odontogramas/{odontograma_id}/pdf/",
        f"{base_url}/api/fichas/{odontograma_id}/pdf/",
        f"{base_url}/trabajadores/odontogramas/{odontograma_id}/exportar-pdf/",
        f"{base_url}/odontogramas/{odontograma_id}/pdf/",
        f"{base_url}/fichas/{odontograma_id}/pdf/",
    ]
    
    for api_url in api_endpoints:
        try:
            response = requests.get(api_url, timeout=10, stream=True, allow_redirects=True)
            if response.status_code == 200:
                content = response.content
                # Verificar que sea PDF válido
                if content and (content[:4] == b'%PDF' or 'pdf' in response.headers.get('Content-Type', '').lower()):
                    http_response = HttpResponse(content, content_type='application/pdf')
                    http_response['Content-Disposition'] = 'inline; filename="odontograma.pdf"'
                    http_response['Cache-Control'] = 'public, max-age=3600'
                    return http_response
        except Exception as e:
            continue
    
    # Si no funciona API, probar rutas de archivos estáticos/media
    from datetime import datetime
    fecha_creacion = odontograma.fecha_creacion
    if fecha_creacion:
        year = fecha_creacion.year
        month = fecha_creacion.month
        day = fecha_creacion.day
    else:
        fecha_actual = datetime.now()
        year = fecha_actual.year
        month = fecha_actual.month
        day = fecha_actual.day
    
    possible_paths = [
        f"media/odontogramas/{year}/{month:02d}/{day:02d}/odontograma_{odontograma_id}.pdf",
        f"media/odontogramas/{year}/{month:02d}/{day:02d}/ficha_{odontograma_id}.pdf",
        f"media/fichas/{year}/{month:02d}/{day:02d}/odontograma_{odontograma_id}.pdf",
        f"media/fichas/{year}/{month:02d}/{day:02d}/ficha_{odontograma_id}.pdf",
        f"media/odontogramas/{odontograma_id}.pdf",
        f"media/odontogramas/odontograma_{odontograma_id}.pdf",
        f"media/fichas/{odontograma_id}.pdf",
        f"media/fichas/ficha_{odontograma_id}.pdf",
        f"media/pdf/odontograma_{odontograma_id}.pdf",
        f"media/pdf/ficha_{odontograma_id}.pdf",
        f"odontogramas/{year}/{month:02d}/{day:02d}/odontograma_{odontograma_id}.pdf",
        f"odontogramas/{odontograma_id}.pdf",
        f"fichas/{odontograma_id}.pdf",
        f"fichas/ficha_{odontograma_id}.pdf",
    ]
    
    # Intentar cada ruta posible
    for pdf_path in possible_paths:
        pdf_url = urljoin(base_url + '/', pdf_path)
        try:
            response = requests.get(pdf_url, timeout=10, stream=True, allow_redirects=True)
            if response.status_code == 200:
                content = response.content
                # Verificar que sea PDF válido (magic bytes %PDF o tamaño razonable)
                if content and (content[:4] == b'%PDF' or len(content) > 1000):
                    http_response = HttpResponse(content, content_type='application/pdf')
                    http_response['Content-Disposition'] = 'inline; filename="odontograma.pdf"'
                    http_response['Cache-Control'] = 'public, max-age=3600'
                    return http_response
        except Exception as e:
            continue
    
    # Si no se encuentra el PDF, retornar 404
    return HttpResponse('PDF no disponible', status=404)


@login_required_cliente
def ver_radiografias(request):
    """Vista para ver todas las radiografías del usuario"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener cliente desde la tabla pacientes_cliente si existe
    cliente_doc = None
    try:
        cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
    except Exception:
        pass
    
    # Obtener radiografías por email del paciente (optimizado)
    radiografias = Radiografia.objects.filter(paciente_email=email_usuario)    
    # Si tenemos cliente_id, también buscar por ese ID
    if cliente_doc:
        radiografias_cliente = Radiografia.objects.filter(cliente_id=cliente_doc.id)
        radiografias = (radiografias | radiografias_cliente).distinct()
    
    # Ordenar
    radiografias = radiografias.order_by('-fecha_carga')
    
    # Agrupar por tipo
    radiografias_por_tipo = {}
    for radio in radiografias:
        tipo = radio.get_tipo_display_value()
        if tipo not in radiografias_por_tipo:
            radiografias_por_tipo[tipo] = []
        radiografias_por_tipo[tipo].append(radio)
    
    # Obtener perfil del usuario para el template base
    try:
        perfil_usuario = PerfilCliente.objects.get(user=request.user)
    except PerfilCliente.DoesNotExist:
        perfil_usuario = None
    
    context = {
        'radiografias': radiografias,
        'radiografias_por_tipo': radiografias_por_tipo,
        'total': radiografias.count(),
        'perfil': perfil if 'perfil' in locals() else None,
        'perfil_usuario': perfil_usuario,
    }
    
    return render(request, 'reservas/ver_radiografias.html', context)


@login_required_cliente
def descargar_radiografia(request, radiografia_id):
    """Vista para descargar imagen de radiografía"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener la radiografía solo si pertenece al usuario (optimizado)
    try:
        radiografia = Radiografia.objects.get(
            id=radiografia_id,
            paciente_email=email_usuario
        )
    except Radiografia.DoesNotExist:
        try:
            cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
            if cliente_doc:
                radiografia = Radiografia.objects.get(
                    id=radiografia_id,
                    cliente_id=cliente_doc.id
                )
            else:
                messages.error(request, 'No tienes acceso a esta radiografía.')
                return redirect('ver_radiografias')
        except Radiografia.DoesNotExist:
            messages.error(request, 'No tienes acceso a esta radiografía.')
            return redirect('ver_radiografias')
    
    if not radiografia.imagen:
        messages.error(request, 'Esta radiografía no tiene imagen disponible.')
        return redirect('ver_radiografias')
    
    # Ya no necesitamos URL externa, todo está unificado
    # Usar la URL base del sitio actual
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    
    # Determinar la ruta correcta según el formato
    if radiografia.imagen.startswith('http://') or radiografia.imagen.startswith('https://'):
        # URL completa
        image_url = radiografia.imagen
    elif radiografia.imagen.startswith('media/'):
        # Ya incluye media/
        image_url = urljoin(base_url + '/', radiografia.imagen)
    else:
        # Formato esperado: radiografias/2025/11/02/radiografia_1.png
        # Agregar media/ al inicio
        image_url = urljoin(base_url + '/', f"media/{radiografia.imagen}")
    
    try:
        response = requests.get(image_url, timeout=10, stream=True)
        if response.status_code == 200:
            # Determinar tipo de contenido
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            extension = '.jpg'
            if 'png' in content_type.lower():
                extension = '.png'
            elif 'pdf' in content_type.lower():
                extension = '.pdf'
            
            filename = f"radiografia_{radiografia_id}_{radiografia.get_tipo_display_value().replace(' ', '_')}{extension}"
            response_http = HttpResponse(response.content, content_type=content_type)
            response_http['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response_http
    except Exception as e:
        pass
    
    # Si no se puede descargar, redirigir a ver la imagen
    messages.info(request, 'No se pudo descargar la imagen. Puedes verla en la galería.')
    return redirect('ver_radiografias')


# ============================================================================
# GESTIÓN DE CONSENTIMIENTOS INFORMADOS (CLIENTE WEB)
# ============================================================================

@login_required_cliente
def ver_consentimientos(request):
    """Vista para listar los consentimientos informados del cliente"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener consentimientos del cliente desde el sistema de gestión
    # Usar conexión directa a la base de datos del sistema de gestión
    from django.db import connections
    consentimientos = []
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar TODOS los clientes activos con ese email (por si hay duplicados)
            cursor.execute("""
                SELECT id, nombre_completo FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
                ORDER BY id DESC
            """, [email_usuario])
            
            clientes_rows = cursor.fetchall()
            
            if clientes_rows:
                # Obtener IDs de todos los clientes con ese email
                cliente_ids = [row[0] for row in clientes_rows]
                
                # Si hay múltiples clientes, usar el más reciente (mayor ID) como principal
                cliente_id_principal = cliente_ids[0]
                
                # Obtener consentimientos de TODOS los clientes con ese email
                # pero también verificar el email en el JOIN para mayor seguridad
                placeholders = ','.join(['%s'] * len(cliente_ids))
                cursor.execute(f"""
                    SELECT DISTINCT
                        ci.id, ci.titulo, ci.tipo_procedimiento, ci.estado,
                        ci.fecha_creacion, ci.fecha_firma, ci.fecha_vencimiento,
                        ci.token_firma, ci.cliente_id
                    FROM historial_clinico_consentimientoinformado ci
                    INNER JOIN pacientes_cliente c ON ci.cliente_id = c.id
                    WHERE ci.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    ORDER BY ci.fecha_creacion DESC
                """, cliente_ids + [email_usuario])
                
                # Usar un set para evitar duplicados por ID de consentimiento
                consentimientos_ids_vistos = set()
                for row in cursor.fetchall():
                    cons_id = row[0]
                    # Evitar duplicados - solo agregar si no lo hemos visto antes
                    if cons_id not in consentimientos_ids_vistos:
                        consentimientos_ids_vistos.add(cons_id)
                        consentimientos.append({
                            'id': cons_id,
                            'titulo': row[1],
                            'tipo_procedimiento': row[2],
                            'estado': row[3],
                            'fecha_creacion': row[4],
                            'fecha_firma': row[5],
                            'fecha_vencimiento': row[6],
                            'token_firma': row[7],
                        })
    except Exception as e:
        logger.error(f"Error al obtener consentimientos: {str(e)}")
        messages.error(request, 'Error al cargar los consentimientos.')
    
    # Mapear estados a nombres legibles
    ESTADO_CHOICES = {
        'pendiente': 'Pendiente de Firma',
        'firmado': 'Firmado',
        'rechazado': 'Rechazado',
        'vencido': 'Vencido',
    }
    
    TIPO_CHOICES = {
        'endodoncia': 'Endodoncia',
        'extraccion': 'Extracción',
        'implante': 'Implante',
        'ortodoncia': 'Ortodoncia',
        'limpieza': 'Limpieza',
        'blanqueamiento': 'Blanqueamiento',
        'otro': 'Otro',
    }
    
    for cons in consentimientos:
        cons['estado_display'] = ESTADO_CHOICES.get(cons['estado'], cons['estado'])
        cons['tipo_display'] = TIPO_CHOICES.get(cons['tipo_procedimiento'], cons['tipo_procedimiento'])
    
    # Calcular estadísticas
    total = len(consentimientos)
    pendientes = sum(1 for cons in consentimientos if cons['estado'] == 'pendiente')
    firmados = sum(1 for cons in consentimientos if cons['estado'] == 'firmado')
    
    context = {
        'consentimientos': consentimientos,
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'total': total,
        'pendientes': pendientes,
        'firmados': firmados,
    }
    
    return render(request, 'reservas/consentimientos.html', context)


@login_required_cliente
def ver_consentimiento(request, consentimiento_id):
    """Vista para ver el detalle de un consentimiento"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener consentimiento desde el sistema de gestión
    from django.db import connections
    consentimiento = None
    
    try:
        with connections['default'].cursor() as cursor:
            # Primero obtener todos los IDs de clientes con ese email
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
            """, [email_usuario])
            
            cliente_ids = [row[0] for row in cursor.fetchall()]
            
            if not cliente_ids:
                messages.error(request, 'Cliente no encontrado.')
                return redirect('ver_consentimientos')
            
            # Verificar que el consentimiento pertenece a alguno de esos clientes
            placeholders = ','.join(['%s'] * len(cliente_ids))
            cursor.execute(f"""
                SELECT 
                    ci.id, ci.titulo, ci.tipo_procedimiento, ci.estado,
                    ci.fecha_creacion, ci.fecha_firma, ci.fecha_vencimiento,
                    ci.diagnostico, ci.contenido, ci.riesgos, ci.beneficios,
                    ci.alternativas, ci.pronostico, ci.cuidados_postoperatorios,
                    ci.naturaleza_procedimiento, ci.objetivos_tratamiento,
                    ci.cliente_id
                FROM historial_clinico_consentimientoinformado ci
                INNER JOIN pacientes_cliente c ON ci.cliente_id = c.id
                WHERE ci.id = %s 
                AND ci.cliente_id IN ({placeholders})
                AND c.email = %s 
                AND c.activo = TRUE
            """, [consentimiento_id] + cliente_ids + [email_usuario])
            
            row = cursor.fetchone()
            if row:
                consentimiento = {
                    'id': row[0],
                    'titulo': row[1],
                    'tipo_procedimiento': row[2],
                    'estado': row[3],
                    'fecha_creacion': row[4],
                    'fecha_firma': row[5],
                    'fecha_vencimiento': row[6],
                    'diagnostico': row[7],
                    'contenido': row[8],
                    'riesgos': row[9],
                    'beneficios': row[10],
                    'alternativas': row[11],
                    'pronostico': row[12],
                    'cuidados_postoperatorios': row[13],
                    'naturaleza_procedimiento': row[14],
                    'objetivos_tratamiento': row[15],
                    'cliente_id': row[16],
                }
    except Exception as e:
        logger.error(f"Error al obtener consentimiento: {str(e)}")
        messages.error(request, 'Error al cargar el consentimiento.')
        return redirect('ver_consentimientos')
    
    if not consentimiento:
        messages.error(request, 'Consentimiento no encontrado o no tienes permisos para verlo.')
        return redirect('ver_consentimientos')
    
    ESTADO_CHOICES = {
        'pendiente': 'Pendiente de Firma',
        'firmado': 'Firmado',
        'rechazado': 'Rechazado',
        'vencido': 'Vencido',
    }
    
    TIPO_CHOICES = {
        'endodoncia': 'Endodoncia',
        'extraccion': 'Extracción',
        'implante': 'Implante',
        'ortodoncia': 'Ortodoncia',
        'limpieza': 'Limpieza',
        'blanqueamiento': 'Blanqueamiento',
        'otro': 'Otro',
    }
    
    consentimiento['estado_display'] = ESTADO_CHOICES.get(consentimiento['estado'], consentimiento['estado'])
    consentimiento['tipo_display'] = TIPO_CHOICES.get(consentimiento['tipo_procedimiento'], consentimiento['tipo_procedimiento'])
    
    context = {
        'consentimiento': consentimiento,
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'puede_firmar': consentimiento['estado'] == 'pendiente',
    }
    
    return render(request, 'reservas/ver_consentimiento.html', context)


@login_required_cliente
def firmar_consentimiento_cliente(request, consentimiento_id):
    """Vista para que el cliente firme un consentimiento desde el sistema web"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        return JsonResponse({'error': 'No se encontró tu perfil.'}, status=403)
    
    # Verificar que el consentimiento pertenece al cliente y está pendiente
    from django.db import connections
    from django.utils import timezone
    
    try:
        with connections['default'].cursor() as cursor:
            # Primero obtener todos los IDs de clientes con ese email
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
            """, [email_usuario])
            
            cliente_ids = [row[0] for row in cursor.fetchall()]
            
            if not cliente_ids:
                return JsonResponse({'error': 'Cliente no encontrado.'}, status=404)
            
            # Verificar que el consentimiento pertenece a alguno de esos clientes
            placeholders = ','.join(['%s'] * len(cliente_ids))
            cursor.execute(f"""
                SELECT ci.id, ci.estado, ci.cliente_id
                FROM historial_clinico_consentimientoinformado ci
                INNER JOIN pacientes_cliente c ON ci.cliente_id = c.id
                WHERE ci.id = %s 
                AND ci.cliente_id IN ({placeholders})
                AND c.email = %s 
                AND c.activo = TRUE
            """, [consentimiento_id] + cliente_ids + [email_usuario])
            
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'error': 'Consentimiento no encontrado o no tienes permisos.'}, status=404)
            
            if row[1] != 'pendiente':
                return JsonResponse({'error': 'Este consentimiento ya ha sido firmado o no está disponible.'}, status=400)
            
            # Obtener datos del formulario
            firma_paciente = request.POST.get('firma_paciente', '')
            nombre_firmante = request.POST.get('nombre_firmante', perfil.nombre_completo)
            rut_firmante = request.POST.get('rut_firmante', perfil.rut or '')
            nombre_testigo = request.POST.get('nombre_testigo', '')
            rut_testigo = request.POST.get('rut_testigo', '')
            firma_testigo = request.POST.get('firma_testigo', '')
            declaracion_comprension = request.POST.get('declaracion_comprension') == 'on'
            derecho_revocacion = request.POST.get('derecho_revocacion') == 'on'
            
            if not firma_paciente:
                return JsonResponse({'error': 'La firma del paciente es obligatoria.'}, status=400)
            
            if not declaracion_comprension:
                return JsonResponse({'error': 'Debe confirmar la declaración de comprensión.'}, status=400)
            
            if not derecho_revocacion:
                return JsonResponse({'error': 'Debe confirmar que conoce su derecho de revocación.'}, status=400)
            
            # Actualizar consentimiento
            cursor.execute("""
                UPDATE historial_clinico_consentimientoinformado
                SET 
                    firma_paciente = %s,
                    nombre_firmante = %s,
                    rut_firmante = %s,
                    nombre_testigo = %s,
                    rut_testigo = %s,
                    firma_testigo = %s,
                    declaracion_comprension = %s,
                    derecho_revocacion = %s,
                    estado = 'firmado',
                    fecha_firma = %s
                WHERE id = %s
            """, [
                firma_paciente,
                nombre_firmante,
                rut_firmante,
                nombre_testigo if nombre_testigo else None,
                rut_testigo if rut_testigo else None,
                firma_testigo if firma_testigo else None,
                declaracion_comprension,
                derecho_revocacion,
                timezone.now(),
                consentimiento_id
            ])
            
            return JsonResponse({
                'success': True,
                'message': 'Consentimiento firmado exitosamente.'
            })
            
    except Exception as e:
        logger.error(f"Error al firmar consentimiento desde cliente_web: {str(e)}")
        return JsonResponse({'error': f'Error al firmar el consentimiento: {str(e)}'}, status=500)


@login_required_cliente
def ver_presupuestos(request):
    """Vista para listar los presupuestos pendientes de aceptación del cliente"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener presupuestos pendientes del cliente desde el sistema de gestión
    # Estrategia: Buscar desde los consentimientos del cliente (que ya funcionan)
    # y luego obtener los planes de tratamiento asociados
    presupuestos = []
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar TODOS los clientes activos con ese email
            cursor.execute("""
                SELECT id, nombre_completo, email FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
                ORDER BY id DESC
            """, [email_usuario])
            
            clientes_rows = cursor.fetchall()
            logger.info(f"Buscando presupuestos para email: {email_usuario}, clientes encontrados: {len(clientes_rows)}")
            
            if clientes_rows:
                cliente_ids = [row[0] for row in clientes_rows]
                logger.info(f"IDs de clientes: {cliente_ids}")
                
                # Estrategia 1: Buscar planes de tratamiento directamente por cliente_id
                placeholders = ','.join(['%s'] * len(cliente_ids))
                cursor.execute(f"""
                    SELECT DISTINCT
                        pt.id, pt.nombre, pt.descripcion, pt.estado,
                        pt.creado_el, pt.presupuesto_aceptado, 
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_plantratamiento pt
                    INNER JOIN pacientes_cliente c ON pt.cliente_id = c.id
                    WHERE pt.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    AND pt.presupuesto_aceptado = FALSE
                    AND pt.estado NOT IN ('cancelado', 'rechazado', 'completado')
                    ORDER BY pt.creado_el DESC
                """, cliente_ids + [email_usuario])
                
                rows_directos = cursor.fetchall()
                logger.info(f"Presupuestos encontrados directamente por cliente: {len(rows_directos)}")
                
                # Estrategia 2: Buscar planes de tratamiento desde consentimientos del cliente
                cursor.execute(f"""
                    SELECT DISTINCT
                        pt.id, pt.nombre, pt.descripcion, pt.estado,
                        pt.creado_el, pt.presupuesto_aceptado, 
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_consentimientoinformado ci
                    INNER JOIN historial_clinico_plantratamiento pt ON ci.plan_tratamiento_id = pt.id
                    INNER JOIN pacientes_cliente c ON ci.cliente_id = c.id
                    WHERE ci.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    AND pt.presupuesto_aceptado = FALSE
                    AND pt.estado NOT IN ('cancelado', 'rechazado', 'completado')
                    ORDER BY pt.creado_el DESC
                """, cliente_ids + [email_usuario])
                
                rows_desde_consentimientos = cursor.fetchall()
                logger.info(f"Presupuestos encontrados desde consentimientos: {len(rows_desde_consentimientos)}")
                
                # Combinar ambos resultados (usar set para evitar duplicados)
                presupuestos_ids_vistos = set()
                all_rows = list(rows_directos) + list(rows_desde_consentimientos)
                
                for row in all_rows:
                    presupuesto_id = row[0]
                    if presupuesto_id not in presupuestos_ids_vistos:
                        presupuestos_ids_vistos.add(presupuesto_id)
                        presupuestos.append({
                            'id': row[0],
                            'nombre': row[1],
                            'descripcion': row[2],
                            'estado': row[3],
                            'fecha_creacion': row[4],
                            'presupuesto_aceptado': row[5],
                            'fecha_aceptacion_presupuesto': row[6],
                            'presupuesto_total': row[7],
                            'descuento': row[8],
                            'precio_final': row[9],
                            'cliente_id': row[10],
                            'cliente_nombre': row[11],
                        })
                        logger.info(f"Presupuesto agregado: ID={row[0]}, Nombre={row[1]}, Estado={row[3]}, Aceptado={row[5]}")
            else:
                logger.warning(f"No se encontraron clientes con email: {email_usuario}")
    
    except Exception as e:
        logger.error(f"Error al obtener presupuestos desde cliente_web: {str(e)}", exc_info=True)
        messages.error(request, f'Error al cargar los presupuestos: {str(e)}')
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'presupuestos': presupuestos,
    }
    
    return render(request, 'reservas/ver_presupuestos.html', context)


@login_required_cliente
def ver_presupuesto(request, presupuesto_id):
    """Vista para ver el detalle de un presupuesto y aceptarlo"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener el presupuesto desde el sistema de gestión
    from django.db import connections
    presupuesto = None
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar clientes con ese email
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
            """, [email_usuario])
            
            cliente_ids = [row[0] for row in cursor.fetchall()]
            
            if cliente_ids:
                placeholders = ','.join(['%s'] * len(cliente_ids))
                cursor.execute(f"""
                    SELECT 
                        pt.id, pt.nombre, pt.descripcion, pt.diagnostico, pt.objetivo,
                        pt.estado, pt.creado_el, pt.presupuesto_aceptado,
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_plantratamiento pt
                    INNER JOIN pacientes_cliente c ON pt.cliente_id = c.id
                    WHERE pt.id = %s
                    AND pt.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    AND pt.presupuesto_aceptado = FALSE
                    AND pt.estado NOT IN ('cancelado', 'rechazado', 'completado')
                """, [presupuesto_id] + cliente_ids + [email_usuario])
                
                row = cursor.fetchone()
                if row:
                    presupuesto = {
                        'id': row[0],
                        'nombre': row[1],
                        'descripcion': row[2],
                        'diagnostico': row[3],
                        'objetivo': row[4],
                        'estado': row[5],
                        'fecha_creacion': row[6],  # Mantener el nombre en el dict para compatibilidad con el template
                        'presupuesto_aceptado': row[7],
                        'fecha_aceptacion_presupuesto': row[8],
                        'presupuesto_total': row[9],
                        'descuento': row[10],
                        'precio_final': row[11],
                        'cliente_id': row[12],
                        'cliente_nombre': row[13],
                    }
    
    except Exception as e:
        logger.error(f"Error al obtener presupuesto desde cliente_web: {str(e)}")
        messages.error(request, 'Error al cargar el presupuesto.')
        return redirect('ver_presupuestos')
    
    if not presupuesto:
        messages.error(request, 'Presupuesto no encontrado o no tienes permisos para verlo.')
        return redirect('ver_presupuestos')
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'presupuesto': presupuesto,
        'puede_aceptar': not presupuesto['presupuesto_aceptado'] and presupuesto['estado'] in ['borrador', 'pendiente_aprobacion'],
    }
    
    return render(request, 'reservas/ver_presupuesto.html', context)


@login_required_cliente
def ver_tratamientos(request):
    """Vista para listar los tratamientos activos del cliente (solo con presupuesto aceptado)"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener tratamientos ACTIVOS del cliente (solo con presupuesto aceptado)
    # Estrategia: Buscar desde los consentimientos del cliente y también directamente
    tratamientos = []
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar TODOS los clientes activos con ese email
            cursor.execute("""
                SELECT id, nombre_completo, email FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
                ORDER BY id DESC
            """, [email_usuario])
            
            clientes_rows = cursor.fetchall()
            logger.info(f"Buscando tratamientos para email: {email_usuario}, clientes encontrados: {len(clientes_rows)}")
            
            if clientes_rows:
                cliente_ids = [row[0] for row in clientes_rows]
                logger.info(f"IDs de clientes: {cliente_ids}")
                
                placeholders = ','.join(['%s'] * len(cliente_ids))
                
                # Estrategia 1: Buscar tratamientos directamente por cliente_id
                cursor.execute(f"""
                    SELECT DISTINCT
                        pt.id, pt.nombre, pt.descripcion, pt.estado,
                        pt.creado_el, pt.presupuesto_aceptado, 
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_plantratamiento pt
                    INNER JOIN pacientes_cliente c ON pt.cliente_id = c.id
                    WHERE pt.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    AND pt.presupuesto_aceptado = TRUE
                    ORDER BY pt.fecha_aceptacion_presupuesto DESC
                """, cliente_ids + [email_usuario])
                
                rows_directos = cursor.fetchall()
                logger.info(f"Tratamientos encontrados directamente por cliente: {len(rows_directos)}")
                
                # Estrategia 2: Buscar tratamientos desde consentimientos del cliente
                cursor.execute(f"""
                    SELECT DISTINCT
                        pt.id, pt.nombre, pt.descripcion, pt.estado,
                        pt.creado_el, pt.presupuesto_aceptado, 
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_consentimientoinformado ci
                    INNER JOIN historial_clinico_plantratamiento pt ON ci.plan_tratamiento_id = pt.id
                    INNER JOIN pacientes_cliente c ON ci.cliente_id = c.id
                    WHERE ci.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                    AND pt.presupuesto_aceptado = TRUE
                    ORDER BY pt.fecha_aceptacion_presupuesto DESC
                """, cliente_ids + [email_usuario])
                
                rows_desde_consentimientos = cursor.fetchall()
                logger.info(f"Tratamientos encontrados desde consentimientos: {len(rows_desde_consentimientos)}")
                
                # Combinar ambos resultados (usar set para evitar duplicados)
                tratamientos_ids_vistos = set()
                all_rows = list(rows_directos) + list(rows_desde_consentimientos)
                
                for row in all_rows:
                    tratamiento_id = row[0]
                    if tratamiento_id not in tratamientos_ids_vistos:
                        tratamientos_ids_vistos.add(tratamiento_id)
                        tratamientos.append({
                            'id': row[0],
                            'nombre': row[1],
                            'descripcion': row[2],
                            'estado': row[3],
                            'fecha_creacion': row[4],
                            'presupuesto_aceptado': row[5],
                            'fecha_aceptacion_presupuesto': row[6],
                            'presupuesto_total': row[7],
                            'descuento': row[8],
                            'precio_final': row[9],
                            'cliente_id': row[10],
                            'cliente_nombre': row[11],
                        })
                        logger.info(f"Tratamiento agregado: ID={row[0]}, Nombre={row[1]}, Estado={row[3]}, Aceptado={row[5]}")
            else:
                logger.warning(f"No se encontraron clientes con email: {email_usuario}")
    
    except Exception as e:
        logger.error(f"Error al obtener tratamientos desde cliente_web: {str(e)}", exc_info=True)
        messages.error(request, f'Error al cargar los tratamientos: {str(e)}')
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'tratamientos': tratamientos,
    }
    
    return render(request, 'reservas/ver_tratamientos.html', context)


@login_required_cliente
def ver_tratamiento(request, tratamiento_id):
    """Vista para ver el detalle de un tratamiento activo"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil.')
        return redirect('panel_cliente')
    
    # Obtener el tratamiento desde el sistema de gestión
    from django.db import connections
    tratamiento = None
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar clientes con ese email
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
            """, [email_usuario])
            
            cliente_ids = [row[0] for row in cursor.fetchall()]
            
            if cliente_ids:
                placeholders = ','.join(['%s'] * len(cliente_ids))
                cursor.execute(f"""
                    SELECT 
                        pt.id, pt.nombre, pt.descripcion, pt.diagnostico, pt.objetivo,
                        pt.estado, pt.creado_el, pt.presupuesto_aceptado,
                        pt.fecha_aceptacion_presupuesto, pt.presupuesto_total,
                        pt.descuento, pt.precio_final, pt.cliente_id,
                        c.nombre_completo as cliente_nombre
                    FROM historial_clinico_plantratamiento pt
                    INNER JOIN pacientes_cliente c ON pt.cliente_id = c.id
                    WHERE pt.id = %s
                    AND pt.cliente_id IN ({placeholders})
                    AND c.email = %s
                    AND c.activo = TRUE
                """, [tratamiento_id] + cliente_ids + [email_usuario])
                
                row = cursor.fetchone()
                if row:
                    tratamiento = {
                        'id': row[0],
                        'nombre': row[1],
                        'descripcion': row[2],
                        'diagnostico': row[3],
                        'objetivo': row[4],
                        'estado': row[5],
                        'fecha_creacion': row[6],  # Mantener el nombre en el dict para compatibilidad con el template
                        'presupuesto_aceptado': row[7],
                        'fecha_aceptacion_presupuesto': row[8],
                        'presupuesto_total': row[9],
                        'descuento': row[10],
                        'precio_final': row[11],
                        'cliente_id': row[12],
                        'cliente_nombre': row[13],
                    }
    
    except Exception as e:
        logger.error(f"Error al obtener tratamiento desde cliente_web: {str(e)}")
        messages.error(request, 'Error al cargar el tratamiento.')
        return redirect('ver_tratamientos')
    
    if not tratamiento:
        messages.error(request, 'Tratamiento no encontrado o no tienes permisos para verlo.')
        return redirect('ver_tratamientos')
    
    # Solo mostrar tratamientos con presupuesto aceptado
    if not tratamiento['presupuesto_aceptado']:
        messages.warning(request, 'Este tratamiento aún no tiene el presupuesto aceptado. Por favor, acepta el presupuesto primero.')
        return redirect('ver_presupuestos')
    
    context = {
        'perfil': perfil,
        'perfil_usuario': perfil,  # Para el template base
        'tratamiento': tratamiento,
    }
    
    return render(request, 'reservas/ver_tratamiento.html', context)


@login_required_cliente
def aceptar_presupuesto_cliente(request, presupuesto_id):
    """Vista para que el cliente acepte un presupuesto de tratamiento"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No se encontró tu perfil.'}, status=403)
    
    # Verificar que el presupuesto pertenece al cliente y puede ser aceptado
    from django.db import connections
    from django.utils import timezone
    
    try:
        with connections['default'].cursor() as cursor:
            # Buscar clientes con ese email
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
            """, [email_usuario])
            
            cliente_ids = [row[0] for row in cursor.fetchall()]
            
            if not cliente_ids:
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado.'}, status=404)
            
            # Verificar que el presupuesto pertenece al cliente
            placeholders = ','.join(['%s'] * len(cliente_ids))
            cursor.execute(f"""
                SELECT pt.id, pt.presupuesto_aceptado, pt.estado
                FROM historial_clinico_plantratamiento pt
                INNER JOIN pacientes_cliente c ON pt.cliente_id = c.id
                WHERE pt.id = %s
                AND pt.cliente_id IN ({placeholders})
                AND c.email = %s
                AND c.activo = TRUE
            """, [presupuesto_id] + cliente_ids + [email_usuario])
            
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'success': False, 'error': 'Presupuesto no encontrado o no tienes permisos.'}, status=404)
            
            if row[1]:  # presupuesto_aceptado
                return JsonResponse({'success': False, 'error': 'Este presupuesto ya ha sido aceptado.'}, status=400)
            
            if row[2] in ['cancelado', 'rechazado', 'completado']:  # estado
                return JsonResponse({'success': False, 'error': 'Este presupuesto no puede ser aceptado en su estado actual.'}, status=400)
            
            # Marcar presupuesto como aceptado
            cursor.execute("""
                UPDATE historial_clinico_plantratamiento
                SET 
                    presupuesto_aceptado = TRUE,
                    fecha_aceptacion_presupuesto = %s
                WHERE id = %s
            """, [timezone.now(), presupuesto_id])
            
            return JsonResponse({
                'success': True,
                'message': 'Presupuesto aceptado exitosamente. Por favor, acércate a la clínica o ponte en contacto con nosotros para continuar con tu tratamiento.'
            })
            
    except Exception as e:
        logger.error(f"Error al aceptar presupuesto desde cliente_web: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error al aceptar el presupuesto: {str(e)}'}, status=500)


@login_required_cliente
def ver_imagen_radiografia(request, radiografia_id):
    """Vista proxy para servir imágenes de radiografías (evita problemas de CORS)"""
    try:
        perfil = PerfilCliente.objects.get(user=request.user)
        email_usuario = perfil.email
    except PerfilCliente.DoesNotExist:
        email_usuario = request.user.email
    
    # Obtener la radiografía solo si pertenece al usuario (optimizado)
    try:
        radiografia = Radiografia.objects.get(
            id=radiografia_id,
            paciente_email=email_usuario
        )
    except Radiografia.DoesNotExist:
        try:
            cliente_doc = ClienteDocumento.objects.filter(email=email_usuario).first()
            if cliente_doc:
                radiografia = Radiografia.objects.get(
                    id=radiografia_id,
                    cliente_id=cliente_doc.id
                )
            else:
                return HttpResponse('Acceso denegado', status=403)
        except Radiografia.DoesNotExist:
            return HttpResponse('Acceso denegado', status=403)
    
    if not radiografia.imagen:
        return HttpResponse('Imagen no disponible', status=404)
    
    # Ya no necesitamos URL externa, todo está unificado
    # Usar la URL base del sitio actual
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    
    # Construir URL de la imagen - probar múltiples formatos
    image_path = radiografia.imagen.strip()
    
    # Rutas posibles para probar
    possible_urls = []
    
    if image_path.startswith('http://') or image_path.startswith('https://'):
        possible_urls.append(image_path)
    elif image_path.startswith('media/'):
        possible_urls.append(urljoin(base_url + '/', image_path))
    else:
        # Formato esperado: radiografias/2025/11/02/radiografia_1.png
        # Agregar media/ al inicio
        possible_urls.append(urljoin(base_url + '/', f"media/{image_path}"))
        # También probar sin media/
        possible_urls.append(urljoin(base_url + '/', image_path))
    
    # Intentar cada URL posible
    last_error = None
    for image_url in possible_urls:
        try:
            response = requests.get(image_url, timeout=10, stream=True, allow_redirects=True)
            if response.status_code == 200:
                content = response.content
                # Verificar que tenga contenido válido
                if content and len(content) > 100:  # Mínimo 100 bytes para ser una imagen válida
                    # Determinar tipo de contenido
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Si no tiene content-type, intentar detectarlo por extensión o magic bytes
                    if not content_type or 'text' in content_type.lower():
                        # Detectar por extensión
                        if image_path.lower().endswith('.png') or content[:8] == b'\x89PNG\r\n\x1a\n':
                            content_type = 'image/png'
                        elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') or content[:2] == b'\xff\xd8':
                            content_type = 'image/jpeg'
                        elif image_path.lower().endswith('.gif') or content[:6] == b'GIF89a':
                            content_type = 'image/gif'
                        else:
                            content_type = 'image/jpeg'  # Default
                    
                    http_response = HttpResponse(content, content_type=content_type)
                    http_response['Cache-Control'] = 'public, max-age=3600'
                    return http_response
                else:
                    last_error = f"Contenido vacío o muy pequeño ({len(content) if content else 0} bytes)"
            else:
                last_error = f"Status code: {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            last_error = f"No se pudo conectar: {str(e)}"
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout: {str(e)}"
        except Exception as e:
            last_error = f"Error: {str(e)}"
            continue
    
    # Si ninguna URL funciona, log el error y retornar 404 con mensaje descriptivo
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"No se pudo cargar imagen radiografia_id={radiografia_id}, imagen={image_path}, URLs probadas={possible_urls}, último error={last_error}")
    
    # Si el sistema de gestión no está corriendo, mostrar mensaje más claro
    if last_error and 'Connection' in last_error:
        error_msg = f'El sistema de gestión no está disponible en {base_url}. Por favor, inicia el sistema de gestión para poder ver las imágenes.'
    else:
        error_msg = f'No se pudo cargar la imagen. {last_error or "Error desconocido"}'
    
    return HttpResponse(error_msg, status=404)
