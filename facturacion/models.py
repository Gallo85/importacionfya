from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from accounts.models import Cliente
from productos.models import Iphone, Mac, Accesorio
from django.db.models import Sum
from django.core.exceptions import ValidationError

class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='facturas')
    fecha = models.DateTimeField(auto_now_add=True)
    dolar_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Dólar al momento de la venta
    pago_pesos = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Monto en pesos
    pago_dolares = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Monto en dólares
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('pesos', 'Pesos'),
            ('dolares', 'Dólares'),
            ('mixto', 'Mixto')
        ],
        default='pesos'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vuelto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)  # Nuevo campo agregado
    vuelto_entregado = models.BooleanField(default=False, verbose_name="¿Vuelto entregado?")  # ✅ Nuevo campo

    def __str__(self):
        return f"Factura {self.id} - Cliente: {self.cliente}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto_iphone = models.ForeignKey(Iphone, on_delete=models.SET_NULL, null=True, blank=True)
    producto_mac = models.ForeignKey(Mac, on_delete=models.SET_NULL, null=True, blank=True)
    producto_accesorio = models.ForeignKey(Accesorio, on_delete=models.SET_NULL, null=True, blank=True)

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def clean(self):
        productos = [self.producto_iphone, self.producto_mac, self.producto_accesorio]
        productos_seleccionados = sum(1 for p in productos if p is not None)
        if productos_seleccionados != 1:
            raise ValidationError("Debes seleccionar exactamente un producto para el detalle de la factura.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.factura.id:
            if self.producto_accesorio:
                if self.cantidad > self.producto_accesorio.cantidad:
                    raise ValidationError(f"No hay suficiente stock de {self.producto_accesorio.modelo}. Disponible: {self.producto_accesorio.cantidad}")
                self.producto_accesorio.cantidad -= self.cantidad
                self.producto_accesorio.save()
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.producto_accesorio:
            self.producto_accesorio.cantidad += self.cantidad
            self.producto_accesorio.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.obtener_nombre_producto()} - Cantidad: {self.cantidad} - Subtotal: {self.subtotal}"

    # ✅ MÉTODO NUEVO
    def nombre_con_imei(self):
        if self.producto_iphone:
            return f"iPhone – {self.producto_iphone.modelo} – IMEI: {self.producto_iphone.imei}"
        if self.producto_mac:
            return f"Mac – {self.producto_mac.modelo} – IMEI: {self.producto_mac.imei}"
        if self.producto_accesorio:
            return f"Accesorio – {self.producto_accesorio.modelo}"
        return "Producto sin especificar"



class NotaCredito(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, null=True, blank=True, related_name='notas_credito'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    MOTIVO_CHOICES = [
        ('devolucion', 'Devolución de producto'),
        ('error_facturacion', 'Error en la facturación'),
    ]
    motivo = models.CharField(max_length=255, choices=MOTIVO_CHOICES)
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=10,
        choices=[
            ('pendiente', 'Pendiente'),
            ('procesada', 'Procesada'),
            ('anulada', 'Anulada'),
        ],
        default='pendiente',
    )
    usuario_creador = models.CharField(max_length=255, null=True, blank=True)
    descripcion_adicional = models.TextField(null=True, blank=True)

    def procesar(self):
        """
        Procesa la nota de crédito, devolviendo los productos al inventario según los detalles asociados a la factura,
        y cambiando el estado de la nota a 'procesada'.
        """
        if self.estado != 'pendiente':
            raise ValueError("Solo se pueden procesar notas en estado 'pendiente'.")

        # Obtener los detalles de la factura asociada
        detalles_factura = self.factura.detalles.all()
        print(f"Procesando Nota de Crédito #{self.id} asociada a Factura #{self.factura.id}")

        for detalle in detalles_factura:
            # Determinar qué tipo de producto es
            producto = detalle.producto_iphone or detalle.producto_mac or detalle.producto_accesorio

            if producto:
                print(f"Producto encontrado: {producto.modelo}, Stock actual: {producto.stock}, Devolviendo: {detalle.cantidad}")
                producto.stock += detalle.cantidad
                producto.save()
                print(f"Nuevo stock de {producto.modelo}: {producto.stock}")
            else:
                print(f"Producto no encontrado en el detalle con ID: {detalle.id}")

        # Cambiar el estado de la nota de crédito
        self.estado = 'procesada'
        self.save()
        print(f"Nota de Crédito #{self.id} marcada como procesada.")

    def anular(self):
        """
        Anula la nota de crédito, cambiando su estado a 'anulada'.
        Si la nota ya fue procesada, se revertirá el impacto en el inventario.
        """
        if self.estado == 'anulada':
            raise ValueError("La nota de crédito ya está anulada.")

        if self.estado == 'procesada':
            # Obtener los detalles de la factura asociada
            detalles_factura = self.factura.detalles.all()
            print(f"Revirtiendo Nota de Crédito #{self.id} asociada a Factura #{self.factura.id}")

            for detalle in detalles_factura:
                # Determinar qué tipo de producto es
                producto = detalle.producto_iphone or detalle.producto_mac or detalle.producto_accesorio

                if producto:
                    print(f"Producto encontrado: {producto.modelo}, Stock actual: {producto.stock}, Eliminando: {detalle.cantidad}")
                    producto.stock -= detalle.cantidad
                    producto.save()
                    print(f"Nuevo stock de {producto.modelo}: {producto.stock}")
                else:
                    print(f"Producto no encontrado en el detalle con ID: {detalle.id}")

        # Cambiar el estado a 'anulada'
        self.estado = 'anulada'
        self.save()
        print(f"Nota de Crédito #{self.id} marcada como anulada.")

    def __str__(self):
        return f"Nota de Crédito #{self.id} - Factura {self.factura.id}"



