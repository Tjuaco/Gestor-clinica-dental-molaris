from rest_framework import serializers
from .models import Cita, TipoServicio
from pacientes.models import Cliente
from personal.models import Perfil
# Sistema de evaluaciones eliminado
# from evaluaciones.models import Evaluacion
from historial_clinico.models import Odontograma, Radiografia


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'rut', 'fecha_nacimiento', 'alergias', 'activo']


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre_completo', 'rol', 'especialidad']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServicio
        fields = ['id', 'nombre', 'descripcion', 'precio_base']


class CitaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    dentista = PerfilSerializer(read_only=True)
    tipo_servicio = TipoServicioSerializer(read_only=True)
    
    class Meta:
        model = Cita
        fields = '__all__'


class OdontogramaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Odontograma
        fields = '__all__'


class RadiografiaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Radiografia
        fields = '__all__'


# Sistema de evaluaciones eliminado - serializer comentado
# class EvaluacionSerializer(serializers.ModelSerializer):
#     ...

from pacientes.models import Cliente
from personal.models import Perfil
# Sistema de evaluaciones eliminado
# from evaluaciones.models import Evaluacion
from historial_clinico.models import Odontograma, Radiografia


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'rut', 'fecha_nacimiento', 'alergias', 'activo']


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre_completo', 'rol', 'especialidad']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServicio
        fields = ['id', 'nombre', 'descripcion', 'precio_base']


class CitaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    dentista = PerfilSerializer(read_only=True)
    tipo_servicio = TipoServicioSerializer(read_only=True)
    
    class Meta:
        model = Cita
        fields = '__all__'


class OdontogramaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Odontograma
        fields = '__all__'


class RadiografiaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Radiografia
        fields = '__all__'


# Sistema de evaluaciones eliminado - serializer comentado
# class EvaluacionSerializer(serializers.ModelSerializer):
#     ...

from pacientes.models import Cliente
from personal.models import Perfil
# Sistema de evaluaciones eliminado
# from evaluaciones.models import Evaluacion
from historial_clinico.models import Odontograma, Radiografia


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'rut', 'fecha_nacimiento', 'alergias', 'activo']


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre_completo', 'rol', 'especialidad']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServicio
        fields = ['id', 'nombre', 'descripcion', 'precio_base']


class CitaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    dentista = PerfilSerializer(read_only=True)
    tipo_servicio = TipoServicioSerializer(read_only=True)
    
    class Meta:
        model = Cita
        fields = '__all__'


class OdontogramaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Odontograma
        fields = '__all__'


class RadiografiaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Radiografia
        fields = '__all__'


# Sistema de evaluaciones eliminado - serializer comentado
# class EvaluacionSerializer(serializers.ModelSerializer):
#     ...

from pacientes.models import Cliente
from personal.models import Perfil
# Sistema de evaluaciones eliminado
# from evaluaciones.models import Evaluacion
from historial_clinico.models import Odontograma, Radiografia


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'rut', 'fecha_nacimiento', 'alergias', 'activo']


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre_completo', 'rol', 'especialidad']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServicio
        fields = ['id', 'nombre', 'descripcion', 'precio_base']


class CitaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    dentista = PerfilSerializer(read_only=True)
    tipo_servicio = TipoServicioSerializer(read_only=True)
    
    class Meta:
        model = Cita
        fields = '__all__'


class OdontogramaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Odontograma
        fields = '__all__'


class RadiografiaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Radiografia
        fields = '__all__'


# Sistema de evaluaciones eliminado - serializer comentado
# class EvaluacionSerializer(serializers.ModelSerializer):
#     ...

from pacientes.models import Cliente
from personal.models import Perfil
# Sistema de evaluaciones eliminado
# from evaluaciones.models import Evaluacion
from historial_clinico.models import Odontograma, Radiografia


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'email', 'telefono', 'rut', 'fecha_nacimiento', 'alergias', 'activo']


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre_completo', 'rol', 'especialidad']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServicio
        fields = ['id', 'nombre', 'descripcion', 'precio_base']


class CitaSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    dentista = PerfilSerializer(read_only=True)
    tipo_servicio = TipoServicioSerializer(read_only=True)
    
    class Meta:
        model = Cita
        fields = '__all__'


class OdontogramaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Odontograma
        fields = '__all__'


class RadiografiaSerializer(serializers.ModelSerializer):
    dentista = PerfilSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cita = CitaSerializer(read_only=True)
    
    class Meta:
        model = Radiografia
        fields = '__all__'


# Sistema de evaluaciones eliminado - serializer comentado
# class EvaluacionSerializer(serializers.ModelSerializer):
#     ...
