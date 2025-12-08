"""
Funciones helper para simplificar y unificar la lógica de vistas administrativas de citas
"""
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from citas.models import Cita
from historial_clinico.models import Odontograma
from personal.models import Perfil
from pacientes.models import Cliente
from citas.models import TipoServicio


def obtener_citas_filtradas(estado, search_query=None, fecha=None, exclude_canceladas=False):
    """
    Función centralizada para obtener citas filtradas.
    
    Args:
        estado: Estado o lista de estados a filtrar
        search_query: Texto de búsqueda (opcional)
        fecha: Fecha específica para filtrar (opcional)
        exclude_canceladas: Si True, excluye citas canceladas
    
    Returns:
        QuerySet de citas filtradas
    """
    # Construir filtro base
    if isinstance(estado, list):
        citas_list = Cita.objects.filter(estado__in=estado)
    else:
        citas_list = Cita.objects.filter(estado=estado)
    
    # Excluir canceladas si se solicita
    if exclude_canceladas:
        citas_list = citas_list.exclude(estado='cancelada')
    
    # Filtrar por fecha si se proporciona
    if fecha:
        citas_list = citas_list.filter(fecha_hora__date=fecha)
    
    # Optimizar con select_related
    citas_list = citas_list.select_related('tipo_servicio', 'dentista', 'cliente')
    
    # Aplicar filtro de búsqueda si existe
    if search_query:
        citas_list = citas_list.filter(
            Q(cliente__nombre_completo__icontains=search_query) |
            Q(cliente__email__icontains=search_query) |
            Q(cliente__telefono__icontains=search_query) |
            Q(paciente_nombre__icontains=search_query) |
            Q(paciente_email__icontains=search_query) |
            Q(tipo_servicio__nombre__icontains=search_query) |
            Q(tipo_consulta__icontains=search_query) |
            Q(dentista__nombre_completo__icontains=search_query) |
            Q(notas__icontains=search_query)
        )
    
    return citas_list


def agregar_info_fichas(citas_queryset):
    """
    Agrega información de fichas odontológicas a las citas de forma optimizada.
    
    Args:
        citas_queryset: QuerySet de citas
    
    Returns:
        Lista de citas con información de fichas agregada
    """
    citas_list = list(citas_queryset)
    
    if not citas_list:
        return citas_list
    
    # Obtener IDs de citas
    citas_ids = [cita.id for cita in citas_list]
    
    # Obtener odontogramas en una sola consulta
    odontogramas_dict = {
        od.cita_id: od for od in Odontograma.objects.filter(
            cita_id__in=citas_ids
        ).select_related('cita')
    }
    
    citas_con_ficha = set(odontogramas_dict.keys())
    
    # Agregar información de fichas a cada cita
    for cita in citas_list:
        cita.tiene_ficha = cita.id in citas_con_ficha
        if cita.tiene_ficha:
            cita.odontograma = odontogramas_dict.get(cita.id)
    
    return citas_list


def obtener_estadisticas_citas(fecha_hoy=None):
    """
    Obtiene estadísticas de citas de forma optimizada.
    
    Args:
        fecha_hoy: Fecha de hoy (opcional, por defecto usa timezone.now().date())
    
    Returns:
        Diccionario con estadísticas
    """
    if fecha_hoy is None:
        fecha_hoy = timezone.now().date()
    
    return {
        'citas_hoy': Cita.objects.filter(fecha_hora__date=fecha_hoy).exclude(estado='cancelada').count(),
        'disponibles': Cita.objects.filter(estado='disponible').count(),
        'realizadas': Cita.objects.filter(estado='completada').count(),
    }


def obtener_contexto_base_citas(perfil):
    """
    Obtiene el contexto base común para todas las vistas de citas administrativas.
    
    Args:
        perfil: Perfil del usuario
    
    Returns:
        Diccionario con contexto base
    """
    return {
        'dentistas': Perfil.objects.filter(rol='dentista', activo=True).select_related('user'),
        'servicios_activos': TipoServicio.objects.filter(activo=True).order_by('categoria', 'nombre'),
        'clientes': Cliente.objects.filter(activo=True).order_by('nombre_completo'),
        'es_admin': perfil.es_administrativo(),
    }


def paginar_citas(citas_list, page_number, per_page=6):
    """
    Pagina una lista de citas.
    
    Args:
        citas_list: Lista de citas
        page_number: Número de página
        per_page: Elementos por página
    
    Returns:
        Página paginada
    """
    paginator = Paginator(citas_list, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

