from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
import logging

from .models import Sala
from personal.models import Perfil
from .models_auditoria import registrar_auditoria

logger = logging.getLogger(__name__)


# ==========================================
# GESTIÓN DE SALAS
# ==========================================

@login_required
def gestor_salas(request):
    """Vista para gestionar salas de atención"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            messages.error(request, 'Solo los administrativos pueden gestionar salas.')
            return redirect('panel_trabajador')
    except Perfil.DoesNotExist:
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('login')
    
    # Filtros de búsqueda
    search = request.GET.get('search', '')
    estado = request.GET.get('estado', '')
    
    # Obtener salas
    salas = Sala.objects.all()
    
    # Aplicar filtros
    if search:
        salas = salas.filter(
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    if estado == 'activa':
        salas = salas.filter(activa=True)
    elif estado == 'inactiva':
        salas = salas.filter(activa=False)
    
    salas = salas.order_by('nombre')
    
    # Obtener dentistas con sus salas asignadas
    dentistas = Perfil.objects.filter(rol='dentista', activo=True).select_related('sala_asignada').order_by('nombre_completo')
    
    # Estadísticas
    total_salas = Sala.objects.count()
    salas_activas = Sala.objects.filter(activa=True).count()
    salas_inactivas = Sala.objects.filter(activa=False).count()
    dentistas_con_sala = Perfil.objects.filter(rol='dentista', activo=True, sala_asignada__isnull=False).count()
    dentistas_sin_sala = Perfil.objects.filter(rol='dentista', activo=True, sala_asignada__isnull=True).count()
    
    estadisticas = {
        'total_salas': total_salas,
        'salas_activas': salas_activas,
        'salas_inactivas': salas_inactivas,
        'dentistas_con_sala': dentistas_con_sala,
        'dentistas_sin_sala': dentistas_sin_sala,
    }
    
    # Obtener solo salas activas para el selector de asignación
    salas_activas = Sala.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'perfil': perfil,
        'salas': salas,
        'salas_activas': salas_activas,  # Para el selector de asignación
        'dentistas': dentistas,
        'estadisticas': estadisticas,
        'search': search,
        'estado': estado,
    }
    
    return render(request, 'citas/salas/gestor_salas.html', context)

@login_required
def crear_sala(request):
    """Vista para crear una nueva sala"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Solo los administrativos pueden crear salas.'}, status=403)
            messages.error(request, 'Solo los administrativos pueden crear salas.')
            return redirect('gestor_salas')
    except Perfil.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No tienes permisos para acceder a esta función.'}, status=403)
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            # El checkbox envía 'on' cuando está marcado, o no se envía si no está marcado
            activa = 'activa' in request.POST
            
            # Validaciones
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not nombre:
                error_msg = 'El nombre de la sala es obligatorio.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('gestor_salas')
            
            if len(nombre) < 2:
                error_msg = 'El nombre de la sala debe tener al menos 2 caracteres.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('gestor_salas')
            
            # Verificar si ya existe una sala con el mismo nombre
            if Sala.objects.filter(nombre__iexact=nombre).exists():
                error_msg = f'Ya existe una sala con el nombre "{nombre}".'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('gestor_salas')
            
            # Crear sala
            sala = Sala.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                activa=activa
            )
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=perfil,
                accion='crear',
                modulo='salas',
                descripcion=f'Sala "{sala.nombre}" creada',
                detalles=f'Nombre: {sala.nombre}'
            )
            
            success_msg = f'Sala "{sala.nombre}" creada exitosamente.'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('gestor_salas')
            
        except Exception as e:
            logger.error(f"Error al crear sala: {e}")
            error_msg = f'Error al crear la sala: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('gestor_salas')
    
    return redirect('gestor_salas')

@login_required
def editar_sala(request, sala_id):
    """Vista para editar una sala existente"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Solo los administrativos pueden editar salas.'}, status=403)
            messages.error(request, 'Solo los administrativos pueden editar salas.')
            return redirect('gestor_salas')
    except Perfil.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No tienes permisos para acceder a esta función.'}, status=403)
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('login')
    
    sala = get_object_or_404(Sala, id=sala_id)
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            # El checkbox envía 'on' cuando está marcado, o no se envía si no está marcado
            activa = 'activa' in request.POST
            
            # Validaciones
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not nombre:
                error_msg = 'El nombre de la sala es obligatorio.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('editar_sala', sala_id=sala_id)
            
            if len(nombre) < 2:
                error_msg = 'El nombre de la sala debe tener al menos 2 caracteres.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('editar_sala', sala_id=sala_id)
            
            # Verificar si ya existe otra sala con el mismo nombre
            if Sala.objects.filter(nombre__iexact=nombre).exclude(id=sala_id).exists():
                error_msg = f'Ya existe otra sala con el nombre "{nombre}".'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('editar_sala', sala_id=sala_id)
            
            # Guardar cambios
            nombre_anterior = sala.nombre
            sala.nombre = nombre
            sala.descripcion = descripcion
            sala.activa = activa
            sala.save()
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=perfil,
                accion='editar',
                modulo='salas',
                descripcion=f'Sala "{sala.nombre}" editada',
                detalles=f'Nombre anterior: {nombre_anterior}, Nombre nuevo: {sala.nombre}'
            )
            
            success_msg = f'Sala "{sala.nombre}" actualizada exitosamente.'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('gestor_salas')
            
        except Exception as e:
            logger.error(f"Error al editar sala: {e}")
            error_msg = f'Error al editar la sala: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('gestor_salas')
    
    context = {
        'perfil': perfil,
        'sala': sala,
    }
    return render(request, 'citas/salas/editar_sala.html', context)

@login_required
def eliminar_sala(request, sala_id):
    """Vista para eliminar una sala"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Solo los administrativos pueden eliminar salas.'}, status=403)
            messages.error(request, 'Solo los administrativos pueden eliminar salas.')
            return redirect('gestor_salas')
    except Perfil.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No tienes permisos para acceder a esta función.'}, status=403)
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('login')
    
    sala = get_object_or_404(Sala, id=sala_id)
    
    if request.method == 'POST':
        try:
            # Verificar si hay dentistas asignados a esta sala
            dentistas_asignados = Perfil.objects.filter(rol='dentista', sala_asignada=sala, activo=True).count()
            
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if dentistas_asignados > 0:
                error_msg = f'No se puede eliminar la sala "{sala.nombre}" porque tiene {dentistas_asignados} dentista(s) asignado(s). Primero debe reasignar los dentistas a otras salas.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect('gestor_salas')
            
            nombre_sala = sala.nombre
            sala.delete()
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=perfil,
                accion='eliminar',
                modulo='salas',
                descripcion=f'Sala "{nombre_sala}" eliminada',
                detalles=f'Nombre: {nombre_sala}'
            )
            
            success_msg = f'Sala "{nombre_sala}" eliminada exitosamente.'
            if is_ajax:
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            return redirect('gestor_salas')
            
        except Exception as e:
            logger.error(f"Error al eliminar sala: {e}")
            error_msg = f'Error al eliminar la sala: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('gestor_salas')
    
    return redirect('gestor_salas')

@login_required
def asignar_sala_dentista(request, dentista_id):
    """Vista AJAX para asignar/desasignar sala a un dentista"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            return JsonResponse({'success': False, 'message': 'Solo los administrativos pueden asignar salas.'}, status=403)
    except Perfil.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No tienes permisos para acceder a esta función.'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)
    
    try:
        dentista = get_object_or_404(Perfil, id=dentista_id, rol='dentista')
        sala_id = request.POST.get('sala_id', '')
        
        if sala_id == '' or sala_id == 'null':
            # Desasignar sala
            sala_anterior = dentista.sala_asignada
            dentista.sala_asignada = None
            dentista.save()
            
            if sala_anterior:
                registrar_auditoria(
                    usuario=perfil,
                    accion='editar',
                    modulo='salas',
                    descripcion=f'Sala desasignada del dentista {dentista.nombre_completo}',
                    detalles=f'Dentista: {dentista.nombre_completo}, Sala anterior: {sala_anterior.nombre}'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Sala desasignada del dentista {dentista.nombre_completo} exitosamente.'
            })
        else:
            # Asignar sala
            sala = get_object_or_404(Sala, id=sala_id, activa=True)
            sala_anterior = dentista.sala_asignada
            dentista.sala_asignada = sala
            dentista.save()
            
            registrar_auditoria(
                usuario=perfil,
                accion='editar',
                modulo='salas',
                descripcion=f'Sala asignada al dentista {dentista.nombre_completo}',
                detalles=f'Dentista: {dentista.nombre_completo}, Sala: {sala.nombre}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Sala "{sala.nombre}" asignada al dentista {dentista.nombre_completo} exitosamente.'
            })
            
    except Exception as e:
        logger.error(f"Error al asignar sala a dentista: {e}")
        return JsonResponse({'success': False, 'message': f'Error al asignar la sala: {str(e)}'}, status=500)

