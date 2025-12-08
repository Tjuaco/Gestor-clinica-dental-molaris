from django.contrib import admin
# NOTA: Cita ya está registrado en citas.admin, no lo registramos aquí para evitar duplicados
from .models import Evaluacion


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ['email_cliente', 'estrellas', 'estado', 'creada_el', 'get_usuario']
    list_filter = ['estado', 'estrellas', 'creada_el']
    search_fields = ['email_cliente', 'comentario', 'user__username']
    readonly_fields = ['creada_el', 'actualizada_el', 'ip_address']
    date_hierarchy = 'creada_el'
    
    fieldsets = (
        ('Información de la Evaluación', {
            'fields': ('user', 'email_cliente', 'estrellas', 'comentario')
        }),
        ('Estado de Envío', {
            'fields': ('estado', 'error_mensaje')
        }),
        ('Información Técnica', {
            'fields': ('ip_address', 'creada_el', 'actualizada_el'),
            'classes': ('collapse',)
        }),
    )
    
    def get_usuario(self, obj):
        return obj.user.username
    get_usuario.short_description = 'Usuario'
    get_usuario.admin_order_field = 'user__username'
    
    actions = ['marcar_como_enviada', 'reintentar_envio']
    
    def marcar_como_enviada(self, request, queryset):
        count = queryset.update(estado='enviada', error_mensaje=None)
        self.message_user(request, f'{count} evaluaciones marcadas como enviadas.')
    marcar_como_enviada.short_description = 'Marcar como enviada'
    
    def reintentar_envio(self, request, queryset):
        # Función desactivada - sistema de evaluaciones eliminado
        self.message_user(request, 'El sistema de evaluaciones ha sido desactivado.')
    reintentar_envio.short_description = 'Reintentar envío al sistema de gestión (desactivado)'
