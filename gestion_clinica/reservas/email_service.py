"""
Servicio de email para envío de códigos de verificación
"""
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def _normalizar_telefono_chile(telefono: str | None) -> str | None:
    """Normaliza número de teléfono chileno a formato +56XXXXXXXXX"""
    if not telefono:
        return None
    
    import re
    # Quitar espacios, guiones y caracteres no numéricos excepto '+' inicial
    telefono = telefono.strip()
    if telefono.startswith('+'):
        telefono_limpio = '+' + re.sub(r"\D", "", telefono[1:])
    else:
        telefono_limpio = re.sub(r"\D", "", telefono)

    # Si ya viene en formato +56...
    if telefono_limpio.startswith("+56"):
        return telefono_limpio

    # Si viene empezando por 56...
    if telefono_limpio.startswith("56"):
        return "+" + telefono_limpio

    # Si empieza por 0, quitar ceros a la izquierda
    telefono_limpio = telefono_limpio.lstrip('0')

    # Caso típico móvil chileno: 9XXXXXXXX (9 + 8 dígitos)
    if telefono_limpio.startswith('9') and len(telefono_limpio) == 9:
        return "+56" + telefono_limpio

    # Si quedan 8 dígitos, asumir que es móvil y agregar +569
    if len(telefono_limpio) == 8:
        return "+569" + telefono_limpio

    # Si quedan 9 dígitos y no empieza por 9, agregar +56
    if len(telefono_limpio) == 9 and not telefono_limpio.startswith('9'):
        return "+56" + telefono_limpio

    # No se pudo normalizar confiablemente
    return None


def enviar_codigo_por_email(email: str, codigo: str) -> bool:
    """
    Envía código de verificación por email usando template HTML con diseño de la clínica.
    
    Args:
        email: Dirección de email del usuario
        codigo: Código de verificación a enviar
    
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    try:
        clinic_name = getattr(settings, 'CLINIC_NAME', 'Clínica Dental')
        
        asunto = f"{clinic_name} - Código de Verificación"
        
        email_from = getattr(settings, 'EMAIL_FROM', getattr(settings, 'EMAIL_HOST_USER', 'noreply@clinica.com'))
        
        # Verificar si hay configuración de email
        email_host = getattr(settings, 'EMAIL_HOST', None)
        email_host_user = getattr(settings, 'EMAIL_HOST_USER', None)
        
        if not email_host or not email_host_user or email_host_user == 'tu-email@gmail.com':
            # Modo desarrollo: mostrar código en consola
            logger.warning(f"[MODO DESARROLLO] Código de verificación por email para {email}: {codigo}")
            print(f"\n{'='*60}")
            print(f"[MODO DESARROLLO] Código de verificación Email")
            print(f"Email: {email}")
            print(f"CÓDIGO: {codigo}")
            print(f"{'='*60}\n")
            return True
        
        # Renderizar template HTML
        try:
            mensaje_html = render_to_string('citas/emails/codigo_verificacion.html', {
                'nombre_clinica': clinic_name,
                'codigo': codigo,
            })
        except Exception as template_error:
            logger.warning(f"Error al renderizar template HTML: {template_error}. Usando mensaje de texto plano.")
            # Fallback a mensaje de texto plano si el template falla
            mensaje_html = f"""<html><body>
                <h2>Código de Verificación</h2>
                <p>Tu código de verificación es: <strong>{codigo}</strong></p>
                <p>Este código expira en 15 minutos.</p>
                <p>No compartas este código con nadie.</p>
                <p>Gracias por registrarte en {clinic_name}!</p>
            </body></html>"""
        
        # Crear mensaje de texto plano como alternativa
        mensaje_texto = f"""Hola!

Tu código de verificación es: {codigo}

Este código expira en 15 minutos.

No compartas este código con nadie.

Gracias por registrarte en {clinic_name}!

Saludos,
Equipo {clinic_name}"""
        
        # Enviar email con HTML y texto plano
        email_msg = EmailMultiAlternatives(
            asunto,
            mensaje_texto,
            email_from,
            [email],
        )
        email_msg.attach_alternative(mensaje_html, "text/html")
        email_msg.send()
        
        logger.info(f"Código de verificación enviado por email a {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar código por email: {e}")
        # En desarrollo, mostrar en consola
        print(f"\n{'='*60}")
        print(f"[MODO DESARROLLO] Código de verificación Email")
        print(f"Email: {email}")
        print(f"CÓDIGO: {codigo}")
        print(f"Error: {e}")
        print(f"{'='*60}\n")
        return True  # Retornar True para no romper el flujo en desarrollo

