from django.urls import path
from . import views
from .views import eliminar_nota_credito, caja_diaria, imprimir_factura, enviar_factura_email_view


app_name = 'facturacion'

urlpatterns = [
    path('facturas/', views.listar_facturas, name='listar_facturas'),
    path('facturas/nueva/', views.crear_factura, name='crear_factura'),
    path('facturas/<int:factura_id>/', views.detalle_factura, name='detalle_factura'),
    path('facturas/<int:factura_id>/eliminar/', views.eliminar_factura, name='eliminar_factura'),
    path('total-ventas/', views.total_ventas, name='total_ventas'),
    path('caja-diaria/', caja_diaria, name='caja_diaria'),
    path('productos/buscar/', views.buscar_productos, name='buscar_productos'),
    path('notas-credito/nueva/<int:factura_id>/', views.crear_nota_credito, name='crear_nota_credito'),
    path('notas-credito/procesar/<int:nota_id>/', views.procesar_nota_credito, name='procesar_nota_credito'),  # Nueva ruta
    path('notas-credito/', views.listar_notas_credito, name='listar_notas_credito'),
    path('notas-credito/facturas/', views.listar_facturas_para_nota_credito, name='listar_facturas_para_nota_credito'),
    path('notas-credito/anular/<int:nota_id>/', views.anular_nota_credito, name='anular_nota_credito'),
    path('nota-credito/<int:nota_id>/', views.detalle_nota_credito, name='detalle_nota_credito'),
    path('nota_credito/eliminar/<int:nota_id>/', eliminar_nota_credito, name='eliminar_nota_credito'),
    path('factura/<int:factura_id>/imprimir/', imprimir_factura, name='imprimir_factura'),
    path('factura/<int:factura_id>/enviar-email/', enviar_factura_email_view, name='enviar_factura_email'),

    ]