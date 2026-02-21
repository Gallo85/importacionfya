from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.utils import role_required
from .models import Cliente, Usuario
from .forms import ClienteForm, UsuarioForm
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from .forms import RegistroUsuarioForm, EditarUsuarioForm


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if hasattr(user, 'role'):
                if user.role == 'Gerente':
                    return redirect('dashboard_gerente')
                elif user.role == 'Empleado':
                    return redirect('dashboard_empleado')
                elif user.role == 'Vendedor':
                    return redirect('dashboard_vendedor')
                else:
                    messages.error(request, 'Rol desconocido, contacta al administrador.')
                    print("MENSAJE ERROR: Rol desconocido")  # Debug
                    return redirect('login')
            else:
                messages.error(request, 'El usuario no tiene un rol asignado.')
                print("MENSAJE ERROR: Usuario sin rol")  # Debug
                return redirect('login')
        else:
            messages.error(request, 'Credenciales incorrectas.')
            print("MENSAJE ERROR: Credenciales incorrectas")  # Debug
            return redirect('login')

    return render(request, 'login.html')

def user_logout(request):
    messages.get_messages(request).used = True  # Elimina mensajes antes de cerrar sesión
    logout(request)
    return redirect('login')  # Redirige sin mensajes antiguos


@login_required
@role_required(['Gerente', 'Empleado'])
def gestion_clientes(request):
    nombre = request.GET.get('nombre', '')
    apellido = request.GET.get('apellido', '')
    email = request.GET.get('email', '')
    page_number = request.GET.get('page', 1)  # Página actual, por defecto 1

    # Filtrar clientes por nombre, apellido o email si hay búsqueda
    clientes_query = Cliente.objects.all()
    if nombre:
        clientes_query = clientes_query.filter(nombre__icontains=nombre)
    if apellido:
        clientes_query = clientes_query.filter(apellido__icontains=apellido)
    if email:
        clientes_query = clientes_query.filter(email__icontains=email)

    # Paginación: 10 clientes por página
    paginator = Paginator(clientes_query, 10)
    clientes_paginados = paginator.get_page(page_number)

    return render(request, 'accounts/clientes.html', {
        'clientes': clientes_paginados,  # 🔹 Enviamos clientes paginados
        'nombre': nombre,
        'apellido': apellido,
        'email': email
    })


def listar_clientes(request):
    clientes_list = Cliente.objects.all()

    paginator = Paginator(clientes_list, 15)  # Mostrar 10 clientes por página
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    # Verificar si el usuario tiene un rol asignado y si es Gerente o Superusuario
    es_gerente = request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == "Gerente")

    return render(request, 'accounts/clientes.html', {
        'clientes': clientes,
        'es_gerente': es_gerente
    })




@login_required
@role_required(['Gerente', 'Empleado'])
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, user=request.user)  # Pasar usuario
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('clientes')
    else:
        form = ClienteForm(user=request.user)  # Pasar usuario

    return render(request, 'clientes/crear_cliente.html', {'form': form})


@login_required
@role_required(['Gerente', 'Empleado'])
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente, user=request.user)  # Pasar usuario
        if form.is_valid():
            form.save()
            return redirect('clientes')
    else:
        form = ClienteForm(instance=cliente, user=request.user)  # Pasar usuario

    return render(request, 'clientes/editar_cliente.html', {'form': form, 'cliente': cliente})

@login_required
@role_required(['Gerente'])
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('clientes')  # Cambiado a 'clientes'
    return render(request, 'clientes/eliminar_cliente.html', {'cliente': cliente})


@login_required
@role_required(['Gerente'])
def registrar_usuario(request):
    if request.user.role != 'Gerente':  # 🔹 Solo Gerentes pueden registrar
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('dashboard_gerente')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado con éxito.")
            return redirect('dashboard_gerente')
        else:
            messages.error(request, "Hubo un error en el formulario.")
    else:
        form = RegistroUsuarioForm()

    return render(request, 'accounts/registrar_usuario.html', {'form': form})

User = get_user_model()

@login_required
@role_required(['Gerente'])
def listado_usuarios(request):
    usuarios = User.objects.all()  # Obtiene todos los usuarios registrados
    return render(request, 'accounts/listado_usuarios.html', {'usuarios': usuarios})

@login_required
@role_required(['Gerente'])
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    usuario.is_active = False
    usuario.save()
    messages.success(request, f'Usuario "{usuario.username}" desactivado correctamente. Sus datos se conservaron.')
    return redirect('listado_usuarios')

@login_required
@role_required(['Gerente'])
def reactivar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    usuario.is_active = True
    usuario.save()
    messages.success(request, f'Usuario "{usuario.username}" reactivado correctamente.')
    return redirect('listado_usuarios')

@login_required
@role_required(['Gerente'])
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('listado_usuarios')  # Redirige correctamente
        else:
            messages.error(request, "Error al actualizar el usuario. Revisa los campos.")
    else:
        form = EditarUsuarioForm(instance=usuario)

    return render(request, 'accounts/editar_usuario.html', {'form': form, 'usuario': usuario})