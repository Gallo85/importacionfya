from django.contrib.auth.models import AbstractUser, Permission, BaseUserManager
from django.db import models
from django.utils.timezone import now

# Permisos definidos por rol
GERENTE_PERMISOS = Permission.objects.all()
EMPLEADO_PERMISOS = Permission.objects.filter(
    codename__in=[
        'view_producto', 'change_producto',  # Productos
        'view_factura', 'add_factura',      # Facturación
        'view_cliente', 'change_cliente', 'add_cliente'  # Clientes
    ]
)
VENDEDOR_PERMISOS = Permission.objects.filter(
    codename__in=['view_producto']  # Solo ver productos
)

### **UserManager personalizado**
class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='Empleado', **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 'Gerente')  # Asegura que sea Gerente
        return self.create_user(username, email, password, **extra_fields)

### **Nuevo modelo de usuario**
class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('Gerente', 'Gerente'),
        ('Empleado', 'Empleado'),
        ('Vendedor', 'Vendedor'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Empleado')

    objects = UsuarioManager()  # Asigna el UserManager personalizado

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Asignar permisos según el rol
        if self.role == 'Gerente':
            self.is_superuser = True
            self.is_staff = True
            self.user_permissions.set(GERENTE_PERMISOS)
        elif self.role == 'Empleado':
            self.is_superuser = False
            self.is_staff = True
            self.user_permissions.set(EMPLEADO_PERMISOS)
        elif self.role == 'Vendedor':
            self.is_superuser = False
            self.is_staff = False
            self.user_permissions.set(VENDEDOR_PERMISOS)

        if not is_new:
            super().save(*args, **kwargs)


class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(default=now)
    vendedor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'Vendedor'})

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
