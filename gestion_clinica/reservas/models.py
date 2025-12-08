# reservas/models.py
"""
Modelos para la app reservas.
NOTA: El modelo Cita se eliminó porque ya existe en citas.models.Cita
y ambos estaban usando la misma tabla (citas_cita), causando conflictos.
Ahora reservas usa directamente citas.models.Cita.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# NOTA: No definimos Cita aquí porque ya existe en citas.models.Cita
# Usar: from citas.models import Cita


class Evaluacion(models.Model):
    """Modelo para almacenar evaluaciones de clientes del servicio de citas"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Envío'),
        ('enviada', 'Enviada'),
        ('error', 'Error al Enviar'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluaciones')
    email_cliente = models.EmailField()
    estrellas = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas"
    )
    comentario = models.TextField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Estado de envío al sistema de gestión
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    error_mensaje = models.TextField(blank=True, null=True)
    
    creada_el = models.DateTimeField(auto_now_add=True)
    actualizada_el = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "evaluaciones_cliente"
        ordering = ['-creada_el']
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        # Solo una evaluación por usuario
        unique_together = ['user']
    
    def __str__(self):
        return f"Evaluación de {self.email_cliente} - {self.estrellas} estrellas"