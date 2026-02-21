from django.urls import path
from . import views
from .views import registrar_usuario, listado_usuarios, eliminar_usuario, editar_usuario, reactivar_usuario

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('clientes/', views.gestion_clientes, name='clientes'),  # Ruta para la gestión de clientes
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('registrar-usuario/', registrar_usuario, name='registrar_usuario'),
    path('usuarios/', listado_usuarios, name='listado_usuarios'),
    path('usuarios/editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/reactivar/<int:pk>/', reactivar_usuario, name='reactivar_usuario'),
]
    