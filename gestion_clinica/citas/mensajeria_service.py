"""
Servicio unificado de mensajería para gestion_clinica
Envía notificaciones por correo electrónico cuando se agendan citas
"""
import logging

logger = logging.getLogger(__name__)


def enviar_notificaciones_cita(cita, telefono_override: str | None = None):
    """
    Envía notificaciones de confirmación de cita por correo electrónico.
    
    Args:
        cita: Objeto Cita del modelo
        telefono_override: Teléfono alternativo (opcional, no se usa actualmente)
    
    Returns:
        dict: Resultado del envío con estado del correo
        {
            'email': {'enviado': bool, 'error': str|None}
        }
    """
    resultado = {
        'email': {'enviado': False, 'error': None}
    }
    
    # INTENTAR ENVIAR POR CORREO ELECTRÓNICO
    # Obtener email del paciente de forma segura
    email_paciente = None
    try:
        # Intentar usar la propiedad email_paciente (puede fallar si el modelo no está completamente cargado)
        email_paciente = cita.email_paciente
    except (AttributeError, TypeError):
        # Si falla, intentar desde el cliente directamente
        try:
            if cita.cliente:
                email_paciente = getattr(cita.cliente, 'email', None)
            else:
                # Usar el campo de respaldo
                email_paciente = getattr(cita, 'paciente_email', None)
        except (AttributeError, TypeError):
            email_paciente = None
    if email_paciente:
        try:
            from citas.email_service import enviar_email_confirmacion_cita
            email_result = enviar_email_confirmacion_cita(cita)
            if email_result:
                resultado['email']['enviado'] = True
                logger.info(f"Correo de confirmación enviado exitosamente para cita {cita.id} a {email_paciente}")
            else:
                resultado['email']['error'] = "No se pudo enviar correo"
        except ImportError:
            resultado['email']['error'] = "Servicio de correo no disponible"
        except Exception as e:
            resultado['email']['error'] = str(e)
            logger.error(f"Error al enviar correo de confirmación para cita {cita.id}: {e}")
    else:
        resultado['email']['error'] = "No hay email del paciente"
        logger.warning(f"No hay email del paciente para enviar correo de confirmación (Cita ID: {cita.id})")
    
    # Log del resultado final
    if resultado['email']['enviado']:
        logger.info(f"Correo de confirmación enviado exitosamente para cita {cita.id}")
    else:
        logger.warning(f"No se pudo enviar correo de confirmación para cita {cita.id}: {resultado['email']['error']}")
    
    return resultado


def enviar_notificaciones_cancelacion_cita(cita, telefono_override: str | None = None):
    """
    Envía notificaciones de cancelación de cita por correo electrónico.
    
    Args:
        cita: Objeto Cita del modelo
        telefono_override: Teléfono alternativo (opcional, no se usa actualmente)
    
    Returns:
        dict: Resultado del envío con estado del correo
    """
    resultado = {
        'email': {'enviado': False, 'error': None}
    }
    
    email_paciente = cita.email_paciente or (cita.cliente.email if cita.cliente else None)
    
    # INTENTAR ENVIAR POR CORREO ELECTRÓNICO
    if email_paciente:
        try:
            from citas.email_service import enviar_email_cancelacion_cita
            email_result = enviar_email_cancelacion_cita(cita)
            if email_result:
                resultado['email']['enviado'] = True
                logger.info(f"Correo de cancelación enviado exitosamente para cita {cita.id} a {email_paciente}")
            else:
                resultado['email']['error'] = "No se pudo enviar correo"
        except ImportError:
            resultado['email']['error'] = "Servicio de correo no disponible"
        except Exception as e:
            resultado['email']['error'] = str(e)
            logger.error(f"Error al enviar correo de cancelación para cita {cita.id}: {e}")
    else:
        resultado['email']['error'] = "No hay email del paciente"
        logger.warning(f"No hay email del paciente para enviar correo de cancelación (Cita ID: {cita.id})")
    
    # Log del resultado final
    if resultado['email']['enviado']:
        logger.info(f"Correo de cancelación enviado exitosamente para cita {cita.id}")
    else:
        logger.warning(f"No se pudo enviar correo de cancelación para cita {cita.id}: {resultado['email']['error']}")
    
    return resultado

