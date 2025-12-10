from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re
from personal.models import Perfil


def normalizar_telefono_trabajador(telefono):
    """
    Normaliza un número de teléfono chileno al formato +56912345678
    Acepta solo 8 dígitos (los últimos 8 del número celular) y los convierte a +56912345678
    """
    if not telefono:
        return None
    
    # Eliminar espacios, guiones, paréntesis y otros caracteres
    telefono_limpio = re.sub(r'[\s\-\(\)\.\+]', '', str(telefono).strip())
    
    # Si empieza con 0, eliminarlo (formato nacional antiguo)
    if telefono_limpio.startswith('0'):
        telefono_limpio = telefono_limpio[1:]
    
    # Validar que solo contenga dígitos
    if not telefono_limpio.isdigit():
        return None
    
    # CASO PREFERIDO: 8 dígitos (solo los últimos 8 del número celular)
    # Se agrega el 9 inicial y el código de país 56
    if len(telefono_limpio) == 8:
        return f"+569{telefono_limpio}"
    
    # Si no coincide con el formato válido, retornar None
    return None


class RegistroTrabajadorForm(UserCreationForm):
    # Campos del usuario
    first_name = forms.CharField(
        label="Nombre",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    # Campos del perfil
    nombre_completo = forms.CharField(
        label="Nombre Completo",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Ingresa tu nombre completo (máximo 150 caracteres)'
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=8,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'maxlength': '8',
            'pattern': '[0-9]{8}',
            'inputmode': 'numeric'
        }),
        help_text='Solo ingresa los 8 dígitos del número celular chileno (sin el 9 inicial ni el código de país +56)'
    )
    rol = forms.ChoiceField(
        choices=Perfil.ROLE_CHOICES,
        label="Rol",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campos específicos para dentistas
    especialidad = forms.CharField(
        label="Especialidad",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    numero_colegio = forms.CharField(
        label="Número de Colegio",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de ayuda
        self.fields['username'].help_text = 'Requerido. El nombre de usuario debe ser único.'
        self.fields['password1'].help_text = 'Requerido. Mínimo 8 caracteres. No debe ser similar a tu nombre de usuario ni ser una contraseña común.'
        self.fields['password2'].help_text = 'Ingresa la misma contraseña para verificación'
        
        # Los validadores de contraseña de Django están activos (configurados en settings.py)
        # AUTH_PASSWORD_VALIDATORS incluye: UserAttributeSimilarityValidator, MinimumLengthValidator,
        # CommonPasswordValidator, y NumericPasswordValidator
        
        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError('El nombre de usuario es requerido.')
        
        # Sanitizar username - solo strip
        username = username.strip()
        
        # Verificar si existe (única restricción necesaria)
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('El email es requerido.')
        
        # Sanitizar email - strip y lower primero
        email = email.strip().lower()
        
        # Validar formato de email más estricto
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise forms.ValidationError('Por favor, ingresa un email válido.')
        
        # Verificar longitud máxima
        if len(email) > 254:  # RFC 5321
            raise forms.ValidationError('El email es demasiado largo.')
        
        # Verificar si existe
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado.')
        
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono:
            raise forms.ValidationError('El teléfono es requerido.')
        
        # Sanitizar teléfono - solo números
        telefono_limpio = re.sub(r'\D', '', str(telefono).strip())
        
        # Validar que solo contenga dígitos
        if not telefono_limpio.isdigit():
            raise forms.ValidationError('El teléfono solo debe contener números.')
        
        # Validar que tenga exactamente 8 dígitos
        if len(telefono_limpio) != 8:
            raise forms.ValidationError('El teléfono debe tener exactamente 8 dígitos. Solo ingresa los 8 dígitos del número celular (sin el 9 inicial ni el código de país).')
        
        # Normalizar el teléfono (agregar +569 automáticamente)
        telefono_normalizado = normalizar_telefono_trabajador(telefono_limpio)
        if not telefono_normalizado:
            raise forms.ValidationError('El teléfono ingresado no es válido. Debe tener exactamente 8 dígitos.')
        
        # Retornar el teléfono normalizado para guardarlo en la BD
        return telefono_normalizado
    
    def clean_password1(self):
        """
        Valida la contraseña usando los validadores de Django configurados en settings.py
        """
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise forms.ValidationError('La contraseña es requerida.')
        
        # Ejecutar validadores de Django (mínimo 8 caracteres, no similar a username, etc.)
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        try:
            validate_password(password1, self.instance)
        except DjangoValidationError as e:
            raise forms.ValidationError(e.messages)
        
        return password1
    
    def clean_password2(self):
        """
        Valida que las contraseñas coincidan y ejecuta las validaciones de Django
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if not password2:
            raise forms.ValidationError('La confirmación de contraseña es requerida.')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        
        # Ejecutar validaciones de Django (similitud con username, contraseñas comunes, etc.)
        return super().clean_password2()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            
            # Crear el perfil con todos los campos
            perfil_data = {
                'user': user,
                'nombre_completo': self.cleaned_data['nombre_completo'],
                'telefono': self.cleaned_data['telefono'],  # Ya viene normalizado con +569
                'email': user.email,
                'rol': self.cleaned_data['rol'],
            }
            
            # Agregar campos específicos para dentistas
            if self.cleaned_data['rol'] == 'dentista':
                perfil_data['especialidad'] = self.cleaned_data.get('especialidad', '')
                perfil_data['numero_colegio'] = self.cleaned_data.get('numero_colegio', '')
            
            Perfil.objects.create(**perfil_data)
        
        return user


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre_completo', 'telefono', 'email', 'rol', 'especialidad', 'numero_colegio', 'activo']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_colegio': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos específicos de dentista opcionales para administrativos
        if self.instance.pk and self.instance.rol == 'administrativo':
            self.fields['especialidad'].required = False
            self.fields['numero_colegio'].required = False
