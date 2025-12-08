"""
URL configuration for gestion_clinica project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from citas.views_health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoint para monitoreo
    path('health/', health_check, name='health_check'),
    
    # Página de inicio (público/clientes)
    path('', TemplateView.as_view(template_name="inicio.html"), name="inicio"),
    
    # Rutas para clientes
    path('cuentas/', include('cuentas.urls')),
    path('reservas/', include('reservas.urls')),
    
    # Rutas para trabajadores
    path('trabajadores/', include('citas.urls')),        # vistas trabajadores + auth
    
    # API REST (mantenemos por compatibilidad o acceso externo)
    path('api/', include('citas.api_urls'))
]

# Servir archivos multimedia en desarrollo
# En producción, estos archivos deben ser servidos por el servidor web (Nginx, Apache, etc.)
# o un servicio de almacenamiento (S3, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # En producción, servir media files también (para demostración)
    # NOTA: Para producción real a largo plazo, usar S3 o similar
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
