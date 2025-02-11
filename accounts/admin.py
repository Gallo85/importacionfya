from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from .models import Usuario

# 🔹 Registrar el modelo Usuario en el administrador
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role',)

# 🔹 Restricción de acceso al admin: Solo Gerentes y Superusuarios pueden ingresar
def has_admin_permission(request):
    """Solo los Gerentes y Superusuarios pueden ver el admin"""
    if request.user.is_superuser or request.user.role == "Gerente":
        return True
    raise PermissionDenied  # Bloquea el acceso si no es Gerente o Superusuario

# 🔹 Aplicar la restricción sin eliminar `admin.site`
admin.site.has_permission = has_admin_permission



