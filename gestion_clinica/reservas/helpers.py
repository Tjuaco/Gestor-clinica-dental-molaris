"""
Funciones helper para simplificar y unificar la lógica de búsqueda de citas
"""
from django.db.models import Q
from django.db import connections
from citas.models import Cita
from pacientes.models import Cliente
from cuentas.models import PerfilCliente
import logging

logger = logging.getLogger(__name__)


def obtener_citas_cliente(user, estados=None, incluir_completadas=False):
    """
    Función centralizada para obtener citas de un cliente.
    
    Args:
        user: Usuario de Django
        estados: Lista de estados a filtrar (por defecto: ['reservada', 'confirmada'])
        incluir_completadas: Si True, incluye también citas completadas
    
    Returns:
        QuerySet de citas del cliente
    """
    # Obtener email del usuario
    try:
        perfil_usuario = PerfilCliente.objects.get(user=user)
        email_usuario = perfil_usuario.email or user.email
    except PerfilCliente.DoesNotExist:
        email_usuario = user.email
    
    # Estados por defecto
    if estados is None:
        estados = ['reservada', 'confirmada']
        if incluir_completadas:
            estados.append('completada')
    
    # Primero intentar buscar por cliente_id (más confiable)
    citas_ids = set()
    
    try:
        with connections['default'].cursor() as cursor:
            # Obtener cliente_id del usuario
            cursor.execute("""
                SELECT id FROM pacientes_cliente
                WHERE email = %s AND activo = TRUE
                LIMIT 1
            """, [email_usuario])
            cliente_row = cursor.fetchone()
            
            if cliente_row:
                cliente_id = cliente_row[0]
                # Buscar citas por cliente_id
                placeholders = ','.join(['%s'] * len(estados))
                cursor.execute(f"""
                    SELECT id FROM citas_cita
                    WHERE cliente_id = %s 
                    AND estado IN ({placeholders})
                """, [cliente_id] + estados)
                for row in cursor.fetchall():
                    citas_ids.add(row[0])
    except Exception as e:
        logger.warning(f"Error al buscar citas por cliente_id: {e}")
    
    # También buscar por email (fallback)
    citas_por_email = Cita.objects.filter(
        estado__in=estados
    ).filter(
        Q(paciente_email=email_usuario) |
        Q(paciente_email=user.email)
    )
    
    for cita in citas_por_email:
        citas_ids.add(cita.id)
    
    # Obtener todas las citas únicas con select_related para optimizar
    if citas_ids:
        citas = Cita.objects.filter(
            id__in=list(citas_ids)
        ).select_related('dentista', 'tipo_servicio', 'cliente').order_by('fecha_hora')
    else:
        citas = Cita.objects.none()
    
    return citas


def obtener_dentistas_activos():
    """
    Obtiene la lista de todos los dentistas activos usando ORM de Django.
    Reemplaza a obtener_todos_dentistas_activos() de dentist_service.py
    """
    from personal.models import Perfil
    
    dentistas = Perfil.objects.filter(
        rol='dentista',
        activo=True
    ).select_related('user').order_by('nombre_completo')
    
    return dentistas

