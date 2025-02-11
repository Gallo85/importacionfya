from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventario, name='productos_home'),  # Redirige al inventario
    path('inventario/', views.inventario, name='inventario'),
    path('crear/<str:tipo>/', views.crear_producto, name='crear_producto'),
    path('crear/', views.seleccionar_tipo_producto, name='seleccionar_tipo_producto'),
    path('editar/<str:tipo>/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<str:tipo>/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('ver/<str:tipo>/<int:pk>/', views.ver_producto, name='ver_producto'),
    path('imprimir_qr/<str:tipo>/<int:pk>/', views.imprimir_qr, name='imprimir_qr'),
    path('imprimir_descripcion/<str:tipo>/<int:pk>/', views.imprimir_descripcion, name='imprimir_descripcion'),
]
