from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta
from personal.models import Perfil
from .models_auditoria import AuditoriaLog, limpiar_auditoria_antigua_automatica


@login_required
def gestor_auditoria(request):
    """Vista para gestionar el historial de auditoría del sistema"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            messages.error(request, 'Solo los administrativos pueden acceder a la auditoría.')
            return redirect('panel_trabajador')
    except Perfil.DoesNotExist:
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('login')
    
    # Obtener parámetros de filtro
    modulo_filtro = request.GET.get('modulo', '')
    accion_filtro = request.GET.get('accion', '')
    usuario_filtro = request.GET.get('usuario', '')
    buscar = request.GET.get('buscar', '')
    
    # Obtener todos los registros de auditoría (incluyendo dentistas y administrativos)
    # No filtramos por rol, mostramos todos los registros
    registros = AuditoriaLog.objects.all().select_related('usuario').order_by('-fecha_hora')
    
    # Aplicar filtros
    if modulo_filtro:
        registros = registros.filter(modulo=modulo_filtro)
    
    if accion_filtro:
        registros = registros.filter(accion=accion_filtro)
    
    if usuario_filtro:
        registros = registros.filter(usuario_id=usuario_filtro)
    
    if buscar:
        registros = registros.filter(
            Q(descripcion__icontains=buscar) |
            Q(detalles__icontains=buscar) |
            Q(tipo_objeto__icontains=buscar)
        )
    
    # Estadísticas
    total_registros = AuditoriaLog.objects.count()
    registros_hoy = AuditoriaLog.objects.filter(fecha_hora__date=timezone.now().date()).count()
    registros_semana = AuditoriaLog.objects.filter(
        fecha_hora__date__gte=timezone.now().date().replace(day=1)
    ).count()
    
    # Contar por módulo
    registros_por_modulo = {}
    for modulo_val, modulo_nombre in AuditoriaLog.MODULO_CHOICES:
        registros_por_modulo[modulo_val] = AuditoriaLog.objects.filter(modulo=modulo_val).count()
    
    # Contar por acción
    registros_por_accion = {}
    for accion_val, accion_nombre in AuditoriaLog.ACCION_CHOICES:
        registros_por_accion[accion_val] = AuditoriaLog.objects.filter(accion=accion_val).count()
    
    # Paginación
    paginator = Paginator(registros, 50)
    page = request.GET.get('page', 1)
    try:
        registros_pag = paginator.page(page)
    except PageNotAnInteger:
        registros_pag = paginator.page(1)
    except EmptyPage:
        registros_pag = paginator.page(paginator.num_pages)
    
    # Obtener usuarios para el filtro
    usuarios = Perfil.objects.filter(
        user__is_active=True
    ).order_by('nombre_completo')[:100]
    
    # Filtrar módulos para excluir: configuracion, sistema, otro, auditoria
    modulos_excluidos = ['configuracion', 'sistema', 'otro', 'auditoria']
    modulos_filtrados = [
        (modulo_val, modulo_nombre) for modulo_val, modulo_nombre in AuditoriaLog.MODULO_CHOICES
        if modulo_val not in modulos_excluidos
    ]
    
    # Filtrar acciones para excluir: logout, acceso_denegado, importar, otro
    acciones_excluidas = ['logout', 'acceso_denegado', 'importar', 'otro']
    acciones_filtradas = [
        (accion_val, accion_nombre) for accion_val, accion_nombre in AuditoriaLog.ACCION_CHOICES
        if accion_val not in acciones_excluidas
    ]
    
    context = {
        'perfil': perfil,
        'registros': registros_pag,
        'modulos': modulos_filtrados,
        'acciones': acciones_filtradas,
        'usuarios': usuarios,
        'modulo_filtro': modulo_filtro,
        'accion_filtro': accion_filtro,
        'usuario_filtro': usuario_filtro,
        'buscar': buscar,
        'total_registros': total_registros,
        'registros_hoy': registros_hoy,
        'registros_semana': registros_semana,
        'registros_por_modulo': registros_por_modulo,
        'registros_por_accion': registros_por_accion,
    }
    
    return render(request, 'citas/auditoria/auditoria.html', context)


@login_required
def limpiar_auditoria(request):
    """Vista para eliminar todos los registros de auditoría (solo administradores)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            return JsonResponse({'success': False, 'error': 'Solo los administrativos pueden limpiar auditoría.'}, status=403)
    except Perfil.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    try:
        # Verificar que se haya confirmado
        confirmar = request.POST.get('confirmar')
        eliminar_todo = request.POST.get('eliminar_todo')
        
        if not confirmar or not eliminar_todo:
            return JsonResponse({'success': False, 'error': 'Debe confirmar la eliminación marcando el checkbox.'}, status=400)
        
        # Contar registros antes de eliminar
        total_antes = AuditoriaLog.objects.count()
        
        if total_antes == 0:
            return JsonResponse({
                'success': True,
                'message': 'No hay registros de auditoría para eliminar.',
                'total_antes': 0,
                'total_despues': 0,
                'eliminados': 0
            })
        
        # Eliminar TODOS los registros
        AuditoriaLog.objects.all().delete()
        
        # Registrar esta acción en auditoría (aunque se acaba de limpiar, esto quedará como el primer registro)
        from .models_auditoria import registrar_auditoria
        registrar_auditoria(
            usuario=perfil,
            accion='eliminar',
            modulo='auditoria',
            descripcion=f'Se eliminaron todos los registros de auditoría ({total_antes:,} registros eliminados)',
            detalles=f'Limpieza completa del historial de auditoría realizada por {perfil.nombre_completo}',
            request=request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Se eliminaron todos los registros de auditoría ({total_antes:,} registros eliminados).',
            'total_antes': total_antes,
            'total_despues': 0,
            'eliminados': total_antes
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al eliminar auditoría: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error al eliminar auditoría: {str(e)}'}, status=500)


@login_required
def estadisticas_auditoria(request):
    """Vista para obtener estadísticas de auditoría (solo administradores)"""
    try:
        perfil = Perfil.objects.get(user=request.user)
        if not perfil.es_administrativo():
            return JsonResponse({'success': False, 'error': 'Solo los administrativos pueden ver estadísticas.'}, status=403)
    except Perfil.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    try:
        total_registros = AuditoriaLog.objects.count()
        registros_hoy = AuditoriaLog.objects.filter(fecha_hora__date=timezone.now().date()).count()
        registros_ultimos_7_dias = AuditoriaLog.objects.filter(
            fecha_hora__date__gte=timezone.now().date() - timedelta(days=7)
        ).count()
        registros_ultimos_30_dias = AuditoriaLog.objects.filter(
            fecha_hora__date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # Registro más antiguo
        registro_mas_antiguo = AuditoriaLog.objects.order_by('fecha_hora').first()
        fecha_mas_antigua = registro_mas_antiguo.fecha_hora if registro_mas_antiguo else None
        
        # Registro más reciente
        registro_mas_reciente = AuditoriaLog.objects.order_by('-fecha_hora').first()
        fecha_mas_reciente = registro_mas_reciente.fecha_hora if registro_mas_reciente else None
        
        # Tamaño estimado de la tabla (aproximado)
        # Cada registro tiene aproximadamente 500-1000 bytes
        tamaño_estimado_mb = (total_registros * 750) / (1024 * 1024)  # 750 bytes promedio por registro
        
        return JsonResponse({
            'success': True,
            'total_registros': total_registros,
            'registros_hoy': registros_hoy,
            'registros_ultimos_7_dias': registros_ultimos_7_dias,
            'registros_ultimos_30_dias': registros_ultimos_30_dias,
            'fecha_mas_antigua': fecha_mas_antigua.isoformat() if fecha_mas_antigua else None,
            'fecha_mas_reciente': fecha_mas_reciente.isoformat() if fecha_mas_reciente else None,
            'tamaño_estimado_mb': round(tamaño_estimado_mb, 2)
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al obtener estadísticas de auditoría: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error al obtener estadísticas: {str(e)}'}, status=500)

