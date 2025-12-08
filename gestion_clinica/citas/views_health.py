"""
Vista de health check para monitoreo del sistema
"""
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Endpoint de health check para verificar el estado del sistema.
    Retorna 200 si todo está bien, 503 si hay problemas.
    """
    status = {
        'status': 'healthy',
        'checks': {}
    }
    overall_healthy = True
    
    # Verificar base de datos
    try:
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status['checks']['database'] = 'ok'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status['checks']['database'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Verificar cache (opcional, solo si está configurado)
    try:
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            status['checks']['cache'] = 'ok'
        else:
            status['checks']['cache'] = 'error: cache not working'
            overall_healthy = False
    except Exception as e:
        # Cache no es crítico, solo lo reportamos
        status['checks']['cache'] = f'warning: {str(e)}'
    
    # Determinar código de respuesta HTTP
    if overall_healthy:
        status['status'] = 'healthy'
        return JsonResponse(status, status=200)
    else:
        status['status'] = 'unhealthy'
        return JsonResponse(status, status=503)

