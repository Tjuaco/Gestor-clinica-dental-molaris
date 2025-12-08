"""
Comando de management para limpiar registros antiguos de auditoría.

Uso:
    python manage.py limpiar_auditoria [--dias=365] [--max-registros=100000] [--dry-run]

Este comando se puede ejecutar manualmente o configurarse para ejecutarse
periódicamente mediante un cron job o tarea programada.

Ejemplos:
    # Limpiar registros anteriores a 6 meses, manteniendo máximo 50,000 registros
    python manage.py limpiar_auditoria --dias=180 --max-registros=50000

    # Simular limpieza sin eliminar (dry-run)
    python manage.py limpiar_auditoria --dias=365 --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from citas.models_auditoria import AuditoriaLog


class Command(BaseCommand):
    help = 'Limpia registros antiguos de auditoría según los parámetros especificados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=365,
            help='Mantener registros de los últimos N días (por defecto: 365)'
        )
        parser.add_argument(
            '--max-registros',
            type=int,
            default=100000,
            help='Mantener máximo N registros (por defecto: 100000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular limpieza sin eliminar registros'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        max_registros = options['max_registros']
        dry_run = options['dry_run']

        # Validar parámetros
        if dias < 30:
            self.stdout.write(self.style.ERROR('Error: Debe mantener al menos 30 días de historial.'))
            return

        if max_registros < 10000:
            self.stdout.write(self.style.ERROR('Error: Debe mantener al menos 10,000 registros.'))
            return

        # Calcular fecha límite
        fecha_limite = timezone.now() - timedelta(days=dias)

        # Contar registros antes de limpiar
        total_antes = AuditoriaLog.objects.count()
        self.stdout.write(f'Total de registros antes de limpiar: {total_antes:,}')

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se eliminarán registros'))

        # Si hay más de max_registros, mantener solo los más recientes
        cantidad_eliminada_por_cantidad = 0
        if total_antes > max_registros:
            registros_ordenados = AuditoriaLog.objects.order_by('-fecha_hora')[:max_registros]
            if registros_ordenados:
                fecha_limite_cantidad = registros_ordenados[max_registros - 1].fecha_hora
                registros_a_eliminar_cantidad = AuditoriaLog.objects.filter(fecha_hora__lt=fecha_limite_cantidad)
                cantidad_eliminada_por_cantidad = registros_a_eliminar_cantidad.count()
                
                if not dry_run:
                    registros_a_eliminar_cantidad.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Eliminados {cantidad_eliminada_por_cantidad:,} registros (más de {max_registros:,} registros)'
                        )
                    )
                else:
                    self.stdout.write(
                        f'[DRY-RUN] Se eliminarían {cantidad_eliminada_por_cantidad:,} registros (más de {max_registros:,} registros)'
                    )

        # Eliminar registros antiguos por fecha
        registros_antiguos = AuditoriaLog.objects.filter(fecha_hora__lt=fecha_limite)
        cantidad_eliminada_por_fecha = registros_antiguos.count()
        
        if cantidad_eliminada_por_fecha > 0:
            if not dry_run:
                registros_antiguos.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Eliminados {cantidad_eliminada_por_fecha:,} registros anteriores a {dias} días'
                    )
                )
            else:
                self.stdout.write(
                    f'[DRY-RUN] Se eliminarían {cantidad_eliminada_por_fecha:,} registros anteriores a {dias} días'
                )

        # Contar registros después de limpiar
        if not dry_run:
            total_despues = AuditoriaLog.objects.count()
            total_eliminados = total_antes - total_despues
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS(f'Limpieza completada exitosamente'))
            self.stdout.write(self.style.SUCCESS(f'Registros antes: {total_antes:,}'))
            self.stdout.write(self.style.SUCCESS(f'Registros después: {total_despues:,}'))
            self.stdout.write(self.style.SUCCESS(f'Total eliminados: {total_eliminados:,}'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
        else:
            total_eliminados = cantidad_eliminada_por_cantidad + cantidad_eliminada_por_fecha
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('SIMULACIÓN COMPLETADA (DRY-RUN)'))
            self.stdout.write(f'Registros actuales: {total_antes:,}')
            self.stdout.write(f'Registros que se eliminarían: {total_eliminados:,}')
            self.stdout.write(f'Registros que quedarían: {total_antes - total_eliminados:,}')
            self.stdout.write(self.style.WARNING('=' * 60))

