from django.urls import path
from .api_views import (
    api_citas_disponibles, 
    api_reservar_cita,
    api_verificar_cliente,
    api_historial_citas,
    api_odontogramas_cliente,
    api_radiografias_cliente,
)

urlpatterns = [
    # Endpoints de citas
    path('citas_disponibles/', api_citas_disponibles, name='api_citas_disponibles'),
    path('reservar/', api_reservar_cita, name='api_reservar_cita'),
    path('citas/historial/', api_historial_citas, name='api_historial_citas'),
    
    # Endpoints de clientes
    path('clientes/verificar/', api_verificar_cliente, name='api_verificar_cliente'),
    
    # Endpoints de documentos
    path('documentos/odontogramas/', api_odontogramas_cliente, name='api_odontogramas_cliente'),
    path('documentos/radiografias/', api_radiografias_cliente, name='api_radiografias_cliente'),
]
