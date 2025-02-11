from django.urls import path
from . import views
from .views import editar_perfil 

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/empleado/', views.dashboard_empleado, name='dashboard_empleado'),
    path('dashboard/vendedor/', views.dashboard_vendedor, name='dashboard_vendedor'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('inventario/vendedor/', views.inventario_vendedor, name='inventario_vendedor'),
    
]


