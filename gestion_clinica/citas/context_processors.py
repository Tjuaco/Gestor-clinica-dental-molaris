from personal.models import Perfil

def perfil_context(request):
    """Context processor para incluir información del perfil en todos los templates"""
    if request.user.is_authenticated:
        try:
            perfil = Perfil.objects.get(user=request.user)
            
            return {
                'perfil': perfil,
                'es_admin': perfil.es_administrativo(),
                'es_dentista': perfil.es_dentista(),
            }
        except Perfil.DoesNotExist:
            return {
                'perfil': None,
                'es_admin': False,
                'es_dentista': False,
            }
    return {
        'perfil': None,
        'es_admin': False,
        'es_dentista': False,
    }


def info_clinica(request):
    """Context processor para incluir información de la clínica en todos los templates"""
    try:
        from configuracion.models import InformacionClinica
        info = InformacionClinica.obtener()
        return {
            'info_clinica': info,
            'nombre_clinica': info.nombre_clinica or 'Clínica Dental San Felipe',
            'direccion_clinica': info.direccion or '',
            'telefono_clinica': info.telefono or '',
            'email_clinica': info.email or '',
        }
    except Exception:
        # Si hay algún error, retornar valores por defecto
        return {
            'info_clinica': None,
            'nombre_clinica': 'Clínica Dental San Felipe',
            'direccion_clinica': '',
            'telefono_clinica': '',
            'email_clinica': '',
        }



































