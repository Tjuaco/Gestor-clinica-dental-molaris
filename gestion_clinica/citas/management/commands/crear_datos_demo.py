"""
Comando para crear datos de demostración
Uso: python manage.py crear_datos_demo
"""
from django.core.management.base import BaseCommand
from personal.models import Perfil
from pacientes.models import Cliente
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea datos de demostración (admin, dentista, cliente)'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de demostración...')
        
        # Crear administrador
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@clinica.cl',
                password='admin123'
            )
            admin_perfil = Perfil.objects.create(
                user=admin_user,
                nombre_completo='Administrador Demo',
                rol='administrativo',
                activo=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Administrador creado (admin/admin123)'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Administrador ya existe'))
        
        # Crear dentista
        if not User.objects.filter(username='dentista').exists():
            dentista_user = User.objects.create_user(
                username='dentista',
                email='dentista@clinica.cl',
                password='dentista123'
            )
            dentista_perfil = Perfil.objects.create(
                user=dentista_user,
                nombre_completo='Dr. Juan Pérez',
                rol='dentista',
                activo=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Dentista creado (dentista/dentista123)'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Dentista ya existe'))
        
        # Crear cliente
        if not Cliente.objects.filter(email='paciente@demo.cl').exists():
            cliente = Cliente.objects.create(
                nombre_completo='Paciente Demo',
                email='paciente@demo.cl',
                telefono='+56912345678',
                activo=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Cliente creado (paciente@demo.cl)'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Cliente ya existe'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Datos de demostración creados exitosamente'))
        self.stdout.write('\nCredenciales:')
        self.stdout.write('  - Administrador: admin / admin123')
        self.stdout.write('  - Dentista: dentista / dentista123')
        self.stdout.write('  - Cliente: paciente@demo.cl (crear usuario web desde sistema)')


