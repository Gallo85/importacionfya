from django import forms
from .models import Factura, NotaCredito, DetalleFactura, Cliente


class FacturaForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Seleccione un cliente",
        empty_label="-- Seleccione un cliente --"
    )
    pago_pesos = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Pago en Pesos",
        min_value=0
    )
    pago_dolares = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Pago en Dólares",
        min_value=0
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Observaciones",
        required=False
    )
    vuelto_entregado = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="¿Vuelto entregado?"
    )

    class Meta:
        model = Factura
        fields = ['cliente', 'pago_pesos', 'pago_dolares', 'observaciones', 'vuelto_entregado']

    def clean(self):
        """
        Validaciones personalizadas para los pagos en pesos y dólares.
        """
        cleaned_data = super().clean()
        pago_pesos = cleaned_data.get('pago_pesos')
        pago_dolares = cleaned_data.get('pago_dolares')

        if pago_pesos is None or pago_pesos < 0:
            self.add_error('pago_pesos', "El pago en pesos debe ser mayor o igual a cero.")

        if pago_dolares is None or pago_dolares < 0:
            self.add_error('pago_dolares', "El pago en dólares debe ser mayor o igual a cero.")

        return cleaned_data

class NotaCreditoForm(forms.ModelForm):
    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Monto',
        min_value=0.01
    )
    motivo = forms.ChoiceField(
        choices=NotaCredito.MOTIVO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Motivo'
    )

    class Meta:
        model = NotaCredito
        fields = ['monto', 'motivo']

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto


class DetalleFacturaForm(forms.ModelForm):
    producto = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label='Producto'
    )
    cantidad = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label='Cantidad',
        min_value=1
    )
    precio_unitario = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        label='Precio Unitario',
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        model = DetalleFactura
        fields = ['producto', 'cantidad', 'precio_unitario']

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        return cantidad


