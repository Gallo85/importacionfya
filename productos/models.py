from django.db import models
from django.core.files.base import ContentFile
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from io import BytesIO
import qrcode
from PIL import Image
from django.core.exceptions import ValidationError

class ProductoBase(models.Model):
    modelo = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    estado = models.CharField(max_length=50, choices=[('Nuevo', 'Nuevo'), ('Usado', 'Usado')])
    fotos = models.ImageField(upload_to='productos/', blank=True, null=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Precio en dólares
    precio_pesos = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # ✅ Precio en pesos
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=1)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)  # ✅ Nuevo campo

    class Meta:
        abstract = True

    def generate_qr_code(self, data):
        """
        Genera un código QR basado en los datos proporcionados.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"{self.__class__.__name__.lower()}_{self.pk}_qr.png"
        return file_name, ContentFile(buffer.getvalue())

    def save(self, *args, **kwargs):
        if self.pk is None:  # Si es un nuevo producto
            self.stock = 1  # Stock inicial
        super().save(*args, **kwargs)

        # Generar el código QR después de guardar por primera vez
        if not self.qr_code:
            data = f"{self.__class__.__name__}: {self.modelo}, Precio: ${self.precio}, Estado: {self.estado}, Ubicación: {self.ubicacion or 'No asignada'}"
            file_name, qr_file = self.generate_qr_code(data)
            self.qr_code.save(file_name, qr_file, save=False)
            super().save(*args, **kwargs)

class Iphone(ProductoBase):
    imei = models.CharField(max_length=15, unique=True)  # IMEI debe ser único
    capacidad = models.CharField(max_length=50)
    version_ios = models.CharField(max_length=50)
    porcentaje_bateria = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Verificar si existe un iPhone con el mismo IMEI
        if Iphone.objects.filter(imei=self.imei).exists() and not self.pk:
            raise ValidationError(f"El iPhone con IMEI {self.imei} ya existe.")
        super().save(*args, **kwargs)

class Mac(ProductoBase):
    imei = models.CharField(max_length=15, unique=True)  # IMEI debe ser único
    capacidad = models.CharField(max_length=50)
    ram = models.CharField(max_length=50)
    pantalla = models.CharField(max_length=50)
    version_ios = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        # Verificar si existe una Mac con el mismo IMEI
        if Mac.objects.filter(imei=self.imei).exists() and not self.pk:
            raise ValidationError(f"La Mac con IMEI {self.imei} ya existe.")
        super().save(*args, **kwargs)

class Accesorio(ProductoBase):
    tipo = models.CharField(max_length=50, choices=[
        ('Funda', 'Funda'),
        ('Auricular', 'Auricular'),
        ('Cargador', 'Cargador'),
        ('Protec. Pantalla', 'Protec. Pantalla')
    ])

    def save(self, *args, **kwargs):
        # Verificar si existe un accesorio similar por ID
        if Accesorio.objects.filter(id=self.id).exists() and not self.pk:
            raise ValidationError(f"El accesorio con ID {self.id} ya existe.")
        super().save(*args, **kwargs)

class FotoProducto(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    producto = GenericForeignKey('content_type', 'object_id')
    foto = models.ImageField(upload_to='productos/fotos_extra/')
    es_principal = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.es_principal:
            FotoProducto.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                es_principal=True
            ).update(es_principal=False)
        super().save(*args, **kwargs)
