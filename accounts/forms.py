from django import forms
from .models import Cliente
from .models import Usuario
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellido", "email", "telefono", "direccion", "notas", "vendedor"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Obtener usuario autenticado
        super(ClienteForm, self).__init__(*args, **kwargs)

        # 🔹 Filtrar solo vendedores en la lista desplegable
        self.fields["vendedor"].queryset = Usuario.objects.filter(role="Vendedor")

        # 🔹 Si el cliente YA EXISTE y el usuario NO es Gerente, deshabilitar el campo vendedor
        if self.instance.pk and user and user.role != "Gerente":
            self.fields["vendedor"].disabled = True  # Bloquear edición en la vista de edición


class RegistroUsuarioForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[('Vendedor', 'Vendedor'), ('Empleado', 'Empleado')],
        label="Rol del Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Usuario  # Si tienes un modelo personalizado basado en AbstractUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña',
            'role': 'Rol del Usuario'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True  # Activar el usuario por defecto
        if commit:
            user.save()
        return user


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario  # Usa el modelo de usuario personalizado
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'role': 'Rol del Usuario'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class EditarUsuarioForm(UserChangeForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para no cambiar'}),
        label="Nueva Contraseña (Opcional)"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'role': 'Rol del Usuario',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        if new_password:
            user.set_password(new_password)  # Cambia la contraseña si el usuario ingresa una nueva
        if commit:
            user.save()
        return user