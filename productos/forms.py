from django import forms
from .models import Iphone, Mac, Accesorio, FotoProducto

class BaseForm(forms.ModelForm):
    """
    Clase base que aplica el mismo diseño a todos los formularios derivados.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control form-control-sm',  # Diseño uniforme para todos los campos
            })
            if isinstance(field, forms.fields.DecimalField):
                # Formato específico para campos decimales
                field.widget.attrs.update({'placeholder': '0,00'})  # Ejemplo específico para precio


class IphoneForm(BaseForm):
    class Meta:
        model = Iphone
        fields = ['imei', 'modelo', 'color', 'estado', 'capacidad', 'version_ios', 'porcentaje_bateria', 'ubicacion', 'precio', 'observaciones']
        widgets = {
            'precio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0,00'}),
        }

    def clean_imei(self):
        imei = self.cleaned_data.get('imei')
        # Excluir el objeto actual al verificar la unicidad del IMEI
        if Iphone.objects.filter(imei=imei).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("El IMEI ya se encuentra registrado.")
        return imei

    def save(self, commit=True):
        # Inicializar stock en 1 al guardar un nuevo iPhone
        instance = super().save(commit=False)
        if not instance.pk:  # Si es un nuevo objeto
            instance.stock = 1
        if commit:
            instance.save()
        return instance


class MacForm(BaseForm):
    class Meta:
        model = Mac
        fields = ['imei', 'modelo', 'color', 'estado', 'capacidad', 'ram', 'pantalla', 'version_ios', 'ubicacion', 'precio', 'observaciones']
        widgets = {
            'precio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0,00'}),
        }

    def clean_imei(self):
        imei = self.cleaned_data.get('imei')
        # Excluir el objeto actual al verificar la unicidad del IMEI
        if Mac.objects.filter(imei=imei).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("El IMEI ya se encuentra registrado.")
        return imei

    def save(self, commit=True):
        # Inicializar stock en 1 al guardar una nueva Mac
        instance = super().save(commit=False)
        if not instance.pk:  # Si es un nuevo objeto
            instance.stock = 1
        if commit:
            instance.save()
        return instance


class AccesorioForm(BaseForm):
    class Meta:
        model = Accesorio
        fields = ['tipo', 'modelo', 'color', 'estado', 'ubicacion', 'precio', 'observaciones']
        widgets = {
            'precio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0,00'}),
        }

    def save(self, commit=True):
        # Inicializar stock en 1 al guardar un nuevo accesorio
        instance = super().save(commit=False)
        if not instance.pk:  # Si es un nuevo objeto
            instance.stock = 1
        if commit:
            instance.save()
        return instance


class FotoProductoForm(BaseForm):
    class Meta:
        model = FotoProducto
        fields = ['foto']


