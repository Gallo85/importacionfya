import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone


BACKUP_DIR = '/home/importacionfya1/importacionfya/backups'


class Command(BaseCommand):
    help = 'Genera un backup de todas las tablas en formato CSV'

    def handle(self, *args, **kwargs):
        # Importar modelos aquí para evitar problemas de arranque
        from accounts.models import Usuario, Cliente
        from productos.models import Iphone, Mac, Accesorio
        from facturacion.models import Factura, DetalleFactura, NotaCredito

        # Crear carpeta si no existe
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Timestamp con formato DD-MM-YYYY_HH-MM
        ahora = timezone.localtime(timezone.now())
        timestamp = ahora.strftime('%d-%m-%Y_%H-%M')

        tablas = [
            ('usuarios',        Usuario.objects.all(),          self._exportar_usuario),
            ('clientes',        Cliente.objects.all(),          self._exportar_cliente),
            ('iphones',         Iphone.objects.all(),           self._exportar_iphone),
            ('macs',            Mac.objects.all(),              self._exportar_mac),
            ('accesorios',      Accesorio.objects.all(),        self._exportar_accesorio),
            ('facturas',        Factura.objects.all(),          self._exportar_factura),
            ('detalle_facturas',DetalleFactura.objects.all(),   self._exportar_detalle_factura),
            ('notas_credito',   NotaCredito.objects.all(),      self._exportar_nota_credito),
        ]

        for nombre_tabla, queryset, exportar_fn in tablas:
            nombre_archivo = f'backup_{timestamp}_{nombre_tabla}.csv'
            ruta = os.path.join(BACKUP_DIR, nombre_archivo)
            exportar_fn(queryset, ruta)
            self.stdout.write(self.style.SUCCESS(f'  ✓ {nombre_archivo}'))

        self.stdout.write(self.style.SUCCESS(f'\nBackup completado en: {BACKUP_DIR}'))

    # ── Exportadores por tabla ──────────────────────────────────────────────

    def _exportar_usuario(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined'])
            for u in qs:
                writer.writerow([u.id, u.username, u.email, u.first_name, u.last_name, u.role, u.is_active, u.date_joined])

    def _exportar_cliente(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nombre', 'apellido', 'email', 'telefono', 'direccion', 'notas', 'fecha_registro', 'vendedor_id', 'vendedor_username'])
            for c in qs:
                vendedor_id = c.vendedor_id or ''
                vendedor_username = c.vendedor.username if c.vendedor else ''
                writer.writerow([c.id, c.nombre, c.apellido, c.email, c.telefono, c.direccion, c.notas, c.fecha_registro, vendedor_id, vendedor_username])

    def _exportar_iphone(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'modelo', 'color', 'estado', 'imei', 'capacidad', 'version_ios', 'porcentaje_bateria', 'precio', 'precio_pesos', 'stock', 'ubicacion', 'proveedor', 'costo', 'numero_orden', 'observaciones'])
            for p in qs:
                writer.writerow([p.id, p.modelo, p.color, p.estado, p.imei, p.capacidad, p.version_ios, p.porcentaje_bateria, p.precio, p.precio_pesos, p.stock, p.ubicacion, p.proveedor, p.costo, p.numero_orden, p.observaciones])

    def _exportar_mac(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'modelo', 'color', 'estado', 'imei', 'capacidad', 'ram', 'pantalla', 'version_ios', 'precio', 'precio_pesos', 'stock', 'ubicacion', 'proveedor', 'costo', 'numero_orden', 'observaciones'])
            for p in qs:
                writer.writerow([p.id, p.modelo, p.color, p.estado, p.imei, p.capacidad, p.ram, p.pantalla, p.version_ios, p.precio, p.precio_pesos, p.stock, p.ubicacion, p.proveedor, p.costo, p.numero_orden, p.observaciones])

    def _exportar_accesorio(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'modelo', 'color', 'estado', 'tipo', 'cantidad', 'precio', 'precio_pesos', 'stock', 'ubicacion', 'proveedor', 'costo', 'numero_orden', 'observaciones'])
            for p in qs:
                writer.writerow([p.id, p.modelo, p.color, p.estado, p.tipo, p.cantidad, p.precio, p.precio_pesos, p.stock, p.ubicacion, p.proveedor, p.costo, p.numero_orden, p.observaciones])

    def _exportar_factura(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'cliente_id', 'cliente_nombre', 'fecha', 'metodo_pago', 'dolar_venta', 'pago_pesos', 'pago_dolares', 'total', 'vuelto', 'vuelto_entregado', 'observaciones'])
            for fac in qs:
                writer.writerow([fac.id, fac.cliente_id, str(fac.cliente), fac.fecha, fac.metodo_pago, fac.dolar_venta, fac.pago_pesos, fac.pago_dolares, fac.total, fac.vuelto, fac.vuelto_entregado, fac.observaciones])

    def _exportar_detalle_factura(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'factura_id', 'producto_iphone_id', 'producto_mac_id', 'producto_accesorio_id', 'precio_unitario', 'cantidad', 'subtotal'])
            for d in qs:
                writer.writerow([d.id, d.factura_id, d.producto_iphone_id, d.producto_mac_id, d.producto_accesorio_id, d.precio_unitario, d.cantidad, d.subtotal])

    def _exportar_nota_credito(self, qs, ruta):
        with open(ruta, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'factura_id', 'cliente_id', 'monto', 'motivo', 'fecha', 'estado', 'usuario_creador', 'descripcion_adicional'])
            for n in qs:
                writer.writerow([n.id, n.factura_id, n.cliente_id, n.monto, n.motivo, n.fecha, n.estado, n.usuario_creador, n.descripcion_adicional])
