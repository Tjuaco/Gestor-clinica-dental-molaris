# reservas/api_service.py
"""
Servicio para acceder directamente a los modelos del sistema de gestión.
Ya no se usa HTTP porque todo está unificado en un solo proyecto.
"""
import logging
from django.db.models import Q
from typing import Optional, Dict, Tuple

# Importar modelos directamente
from pacientes.models import Cliente
from citas.models import Cita
from historial_clinico.models import Odontograma, Radiografia
from evaluaciones.models import Evaluacion

logger = logging.getLogger(__name__)


def verificar_cliente_existe(email: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verifica si un cliente existe en el sistema de gestión.
    
    Args:
        email: Email del cliente
        
    Returns:
        tuple: (existe: bool, datos_cliente: dict or None)
    """
    try:
        cliente = Cliente.objects.get(email=email, activo=True)
        return True, {
            "id": cliente.id,
            "nombre_completo": cliente.nombre_completo,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "rut": getattr(cliente, 'rut', None),
            "fecha_nacimiento": cliente.fecha_nacimiento.isoformat() if hasattr(cliente, 'fecha_nacimiento') and cliente.fecha_nacimiento else None,
            "alergias": getattr(cliente, 'alergias', None),
            "dentista_asignado": cliente.dentista_asignado.nombre_completo if hasattr(cliente, 'dentista_asignado') and cliente.dentista_asignado else None,
        }
    except Cliente.DoesNotExist:
        return False, None
    except Exception as e:
        logger.error(f"Error al verificar cliente: {str(e)}", exc_info=True)
        return False, None


def obtener_historial_citas(email: str) -> Tuple[bool, list, Optional[str]]:
    """
    Obtiene el historial de citas de un cliente.
    
    Args:
        email: Email del cliente
        
    Returns:
        tuple: (success: bool, citas: list, error_message: str or None)
    """
    try:
        cliente = Cliente.objects.get(email=email, activo=True)
    except Cliente.DoesNotExist:
        return False, [], "Cliente no encontrado."
    except Exception as e:
        logger.error(f"Error al obtener historial de citas: {str(e)}", exc_info=True)
        return False, [], f"Error al obtener historial: {str(e)}"
    
    # Obtener todas las citas del cliente (incluyendo por email por compatibilidad)
    citas = Cita.objects.filter(
        Q(cliente=cliente) | Q(paciente_email=email)
    ).order_by('-fecha_hora')
    
    # Serializar las citas
    citas_data = []
    for cita in citas:
        citas_data.append({
            "id": cita.id,
            "fecha_hora": cita.fecha_hora.isoformat() if cita.fecha_hora else None,
            "estado": cita.estado,
            "paciente_nombre": getattr(cita, 'paciente_nombre', None),
            "paciente_email": getattr(cita, 'paciente_email', None),
            "paciente_telefono": getattr(cita, 'paciente_telefono', None),
            "motivo": getattr(cita, 'motivo', None),
            "notas": getattr(cita, 'notas', None),
            "dentista": cita.dentista.nombre_completo if hasattr(cita, 'dentista') and cita.dentista else None,
        })
    
    return True, citas_data, None


def obtener_odontogramas_cliente(email: str) -> Tuple[bool, list, Optional[str]]:
    """
    Obtiene los odontogramas de un cliente.
    
    Args:
        email: Email del cliente
        
    Returns:
        tuple: (success: bool, odontogramas: list, error_message: str or None)
    """
    try:
        cliente = Cliente.objects.get(email=email, activo=True)
    except Cliente.DoesNotExist:
        return False, [], "Cliente no encontrado."
    except Exception as e:
        logger.error(f"Error al obtener odontogramas: {str(e)}", exc_info=True)
        return False, [], f"Error al obtener odontogramas: {str(e)}"
    
    # Obtener odontogramas del cliente (incluyendo por email por compatibilidad)
    odontogramas = Odontograma.objects.filter(
        Q(cliente=cliente) | Q(paciente_email=email)
    ).order_by('-fecha_creacion')
    
    odontogramas_data = []
    for odontograma in odontogramas:
        odontogramas_data.append({
            "id": odontograma.id,
            "paciente_nombre": getattr(odontograma, 'paciente_nombre', None),
            "paciente_email": getattr(odontograma, 'paciente_email', None),
            "dentista": odontograma.dentista.nombre_completo if hasattr(odontograma, 'dentista') and odontograma.dentista else None,
            "fecha_creacion": odontograma.fecha_creacion.isoformat() if hasattr(odontograma, 'fecha_creacion') else None,
            "fecha_actualizacion": odontograma.fecha_actualizacion.isoformat() if hasattr(odontograma, 'fecha_actualizacion') else None,
            "motivo_consulta": getattr(odontograma, 'motivo_consulta', None),
            "estado_general": getattr(odontograma, 'estado_general', None),
            "higiene_oral": getattr(odontograma, 'higiene_oral', None),
            "plan_tratamiento": getattr(odontograma, 'plan_tratamiento', None),
            "total_dientes": odontograma.dientes.count() if hasattr(odontograma, 'dientes') else 0,
        })
    
    return True, odontogramas_data, None


def obtener_radiografias_cliente(email: str) -> Tuple[bool, list, Optional[str]]:
    """
    Obtiene las radiografías de un cliente.
    
    Args:
        email: Email del cliente
        
    Returns:
        tuple: (success: bool, radiografias: list, error_message: str or None)
    """
    try:
        cliente = Cliente.objects.get(email=email, activo=True)
    except Cliente.DoesNotExist:
        return False, [], "Cliente no encontrado."
    except Exception as e:
        logger.error(f"Error al obtener radiografías: {str(e)}", exc_info=True)
        return False, [], f"Error al obtener radiografías: {str(e)}"
    
    # Obtener radiografías del cliente (incluyendo por email por compatibilidad)
    radiografias = Radiografia.objects.filter(
        Q(cliente=cliente) | Q(paciente_email=email)
    ).order_by('-fecha_carga')
    
    radiografias_data = []
    for radiografia in radiografias:
        radiografias_data.append({
            "id": radiografia.id,
            "paciente_nombre": getattr(radiografia, 'paciente_nombre', None),
            "paciente_email": getattr(radiografia, 'paciente_email', None),
            "tipo": getattr(radiografia, 'tipo', None),
            "tipo_display": radiografia.get_tipo_display() if hasattr(radiografia, 'get_tipo_display') else None,
            "dentista": radiografia.dentista.nombre_completo if hasattr(radiografia, 'dentista') and radiografia.dentista else None,
            "fecha_carga": radiografia.fecha_carga.isoformat() if hasattr(radiografia, 'fecha_carga') else None,
            "fecha_tomada": radiografia.fecha_tomada.isoformat() if hasattr(radiografia, 'fecha_tomada') and radiografia.fecha_tomada else None,
            "descripcion": getattr(radiografia, 'descripcion', None),
            "imagen_url": radiografia.imagen.url if hasattr(radiografia, 'imagen') and radiografia.imagen else None,
            "imagen_anotada_url": radiografia.imagen_anotada.url if hasattr(radiografia, 'imagen_anotada') and radiografia.imagen_anotada else None,
        })
    
    return True, radiografias_data, None


# Funciones de evaluaciones eliminadas - sistema de evaluaciones desactivado
