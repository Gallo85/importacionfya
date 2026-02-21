from django.shortcuts import render, redirect, get_object_or_404
from .models import Iphone, Mac, Accesorio, FotoProducto
from .forms import IphoneForm, MacForm, AccesorioForm, FotoProductoForm
from django.contrib.contenttypes.models import ContentType
from accounts.utils import role_required
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
import logging

# Cotización: preferir DolarHoy y, si falla, caer a Bluelytics (todo real)
from divisas.utils import obtener_dolar_venta_prefer

# Logger del módulo
logger = logging.getLogger(__name__)

# ---------------------------------
# Helpers
# ---------------------------------
def to_decimal_safe(value, default=Decimal("0")) -> Decimal:
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default

def get_dolar_blue_venta():
    """
    Devuelve Decimal(blue venta) o None si no hay dato.
    Preferimos DolarHoy; si falla, intentamos Bluelytics.
    """
    return obtener_dolar_venta_prefer(prefer="dolarhoy", backup="bluelytics")

# ---------------------------------
# Inventario
# ---------------------------------
@login_required
@role_required(['Gerente', 'Empleado', 'Vendedor'])
def inventario(request):
    modelo = request.GET.get('modelo', '')
    tipo = request.GET.get('tipo', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    imei = request.GET.get('imei', '')
    capacidad = request.GET.get('capacidad', '')
    ubicacion = request.GET.get('ubicacion', '')
    estado = request.GET.get('estado', '')
    color = request.GET.get('color', '')

    # Obtener tasa de cambio (Blue venta) con guardias
    dolar_venta_raw = get_dolar_blue_venta()
    if not dolar_venta_raw or dolar_venta_raw <= 0:
        logger.warning("No se pudo obtener una cotización válida del dólar blue. Valor: %r", dolar_venta_raw)
        messages.error(request, "No se pudo obtener la cotización del dólar. Se usará un valor por defecto para filtros/calculos.")
        dolar_venta = Decimal("1")
    else:
        dolar_venta = to_decimal_safe(dolar_venta_raw, default=Decimal("1"))
        if dolar_venta <= 0:
            messages.error(request, "Cotización inválida del dólar. Se usará un valor por defecto.")
            dolar_venta = Decimal("1")

    modelos = {'iphone': Iphone, 'mac': Mac, 'accesorio': Accesorio}

    # Filtro base: solo stock > 0
    filtros = Q(stock__gt=0)
    if modelo:
        filtros &= Q(modelo__icontains=modelo)

    # Filtros de precio en ARS => convertir a USD para comparar con campo 'precio' (USD)
    if precio_min:
        try:
            precio_min_usd = to_decimal_safe(precio_min) / (dolar_venta or Decimal("1"))
            filtros &= Q(precio__gte=precio_min_usd)
        except Exception as e:
            logger.warning("precio_min inválido (%r): %s", precio_min, e)

    if precio_max:
        try:
            precio_max_usd = to_decimal_safe(precio_max) / (dolar_venta or Decimal("1"))
            filtros &= Q(precio__lte=precio_max_usd)
        except Exception as e:
            logger.warning("precio_max inválido (%r): %s", precio_max, e)

    if ubicacion:
        filtros &= Q(ubicacion__icontains=ubicacion)
    if estado:
        filtros &= Q(estado__iexact=estado)
    if color:
        filtros &= Q(color__icontains=color)

    productos = []

    # Conversión USD -> ARS
    def convertir_ars(precio_usd):
        precio = to_decimal_safe(precio_usd, default=Decimal("0"))
        return round(precio * (dolar_venta or Decimal("1")), 2)

    # Filtrar por tipo si se selecciona
    if tipo and tipo.lower() in modelos:
        queryset = modelos[tipo.lower()].objects.filter(filtros).order_by('modelo')

        if tipo.lower() in ['iphone', 'mac'] and imei:
            queryset = queryset.filter(imei__icontains=imei)
        if tipo.lower() in ['iphone', 'mac'] and capacidad:
            queryset = queryset.filter(capacidad__icontains=capacidad)

        productos = [
            {
                'tipo': tipo.lower(),
                'obj': p,
                'pk': p.pk,
                'precio_pesos': convertir_ars(p.precio)
            }
            for p in queryset
        ]
    else:
        iphone_qs = Iphone.objects.filter(filtros)
        mac_qs = Mac.objects.filter(filtros)
        accesorio_qs = Accesorio.objects.filter(filtros)

        if imei:
            iphone_qs = iphone_qs.filter(imei__icontains=imei)
            mac_qs = mac_qs.filter(imei__icontains=imei)
        if capacidad:
            iphone_qs = iphone_qs.filter(capacidad__icontains=capacidad)
            mac_qs = mac_qs.filter(capacidad__icontains=capacidad)

        productos = (
            [
                {'tipo': 'iphone', 'obj': p, 'pk': p.pk, 'precio_pesos': convertir_ars(p.precio)}
                for p in iphone_qs
            ] + [
                {'tipo': 'mac', 'obj': p, 'pk': p.pk, 'precio_pesos': convertir_ars(p.precio)}
                for p in mac_qs
            ] + [
                {'tipo': 'accesorio', 'obj': p, 'pk': p.pk, 'precio_pesos': convertir_ars(p.precio)}
                for p in accesorio_qs
            ]
        )

    # Ordenar productos por modelo
    productos = sorted(productos, key=lambda x: (x['obj'].modelo or "").lower())

    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'productos/inventario.html', {
        'productos': page_obj,
        'dolar_venta': dolar_venta,
        'filtros': {
            'modelo': modelo,
            'tipo': tipo,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'imei': imei,
            'capacidad': capacidad,
            'ubicacion': ubicacion,
            'estado': estado,
            'color': color,
        },
    })

# ---------------------------------
# Crear / Editar / Eliminar
# ---------------------------------
@login_required
@role_required(['Gerente'])
def crear_producto(request, tipo):
    dolar_venta_raw = get_dolar_blue_venta()

    modelos = {'iphone': (Iphone, IphoneForm), 'mac': (Mac, MacForm), 'accesorio': (Accesorio, AccesorioForm)}
    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    Modelo, Formulario = modelos[tipo]
    form = Formulario(request.POST or None, request.FILES or None)

    # Si no hay cotización real, no mandamos 0 al template (evita “0 ARS/USD”)
    dolar_venta_ctx = float(dolar_venta_raw) if (dolar_venta_raw and dolar_venta_raw > 0) else None

    if request.method == 'POST':
        if form.is_valid():
            producto = form.save(commit=False)

            # Precio en USD -> ARS (solo si tenemos cotización)
            precio_dolares = (request.POST.get('precio_dolares', '') or '').strip()
            if not precio_dolares:
                messages.error(request, "Debes ingresar un precio en dólares.")
                return render(request, 'productos/crear_producto.html', {
                    'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
                })

            try:
                producto.precio = to_decimal_safe(precio_dolares, default=None)
                if producto.precio is None:
                    raise ValueError("Precio en dólares inválido")

                if dolar_venta_raw and dolar_venta_raw > 0:
                    producto.precio_pesos = producto.precio * to_decimal_safe(dolar_venta_raw, default=Decimal("1"))
                else:
                    # Si no hay cotización, guardamos solo el precio USD y dejamos pesos en 0
                    producto.precio_pesos = Decimal("0")

            except Exception as e:
                messages.error(request, f"Error en el cálculo del precio: {e}")
                return render(request, 'productos/crear_producto.html', {
                    'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
                })

            # Datos sensibles (solo Gerente)
            if request.user.groups.filter(name='Gerente').exists():
                nro_ord_str = (request.POST.get('numero_orden', '') or '').strip()
                if nro_ord_str:
                    try:
                        producto.numero_orden = datetime.strptime(nro_ord_str, '%d/%m/%Y').date()
                    except ValueError:
                        messages.error(request, "El formato de N° de Orden debe ser DD/MM/AAAA.")
                        return render(request, 'productos/crear_producto.html', {
                            'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
                        })

                proveedor = (request.POST.get('proveedor', '') or '').strip()
                if proveedor:
                    producto.proveedor = proveedor

                costo_str = (request.POST.get('costo', '') or '').strip()
                if costo_str:
                    costo_val = to_decimal_safe(costo_str, default=None)
                    if costo_val is None:
                        messages.error(request, "El costo ingresado no es válido.")
                        return render(request, 'productos/crear_producto.html', {
                            'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
                        })
                    producto.costo = costo_val

            # Cantidad para accesorio
            if tipo == "accesorio":
                cantidad = (request.POST.get('cantidad', '') or '').strip()
                if cantidad.isdigit() and int(cantidad) > 0:
                    producto.cantidad = int(cantidad)
                else:
                    messages.error(request, "La cantidad ingresada no es válida.")
                    return render(request, 'productos/crear_producto.html', {
                        'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
                    })

            producto.save()

            # Fotos asociadas
            fotos = request.FILES.getlist('fotos')
            if fotos:
                for i, foto in enumerate(fotos):
                    FotoProducto.objects.create(
                        content_type=ContentType.objects.get_for_model(producto),
                        object_id=producto.pk,
                        foto=foto,
                        es_principal=(i == 0)
                    )

            if dolar_venta_ctx:
                messages.success(request, f"Producto creado correctamente con precio en pesos: ${producto.precio_pesos:.2f} ARS.")
            else:
                messages.info(request, "Producto creado. No se pudo obtener la cotización; se guardó el precio en USD y ARS=0.")

            return redirect('inventario')

        # Form inválido
        return render(request, 'productos/crear_producto.html', {
            'form': form, 'dolar_venta': dolar_venta_ctx, 'tipo': tipo
        })

    # GET inicial
    return render(request, 'productos/crear_producto.html', {
        'form': form,
        'dolar_venta': dolar_venta_ctx,  # None si no hay cotización
        'tipo': tipo,
    })

# ---------------------------------
# Editar
# ---------------------------------
@login_required
@role_required(['Gerente'])
def editar_producto(request, tipo, pk):
    dolar_venta_raw = get_dolar_blue_venta()
    dolar_venta = to_decimal_safe(dolar_venta_raw, default=Decimal("1")) if dolar_venta_raw else Decimal("1")
    if dolar_venta <= 0:
        logger.warning("Cotización inválida en editar_producto. Valor: %r", dolar_venta_raw)
        dolar_venta = Decimal("1")

    modelos = {'iphone': (Iphone, IphoneForm), 'mac': (Mac, MacForm), 'accesorio': (Accesorio, AccesorioForm)}
    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    modelo, Formulario = modelos[tipo]
    producto = get_object_or_404(modelo, pk=pk)

    form = Formulario(request.POST or None, request.FILES or None, instance=producto, user=request.user)

    if request.method == 'POST' and form.is_valid():
        producto = form.save(commit=False)

        # Solo Gerentes pueden modificar sensibles
        if request.user.groups.filter(name='Gerente').exists():
            if 'numero_orden' in form.changed_data:
                producto.numero_orden = form.cleaned_data['numero_orden']
            if 'proveedor' in form.changed_data:
                producto.proveedor = form.cleaned_data['proveedor']
            if 'costo' in form.changed_data:
                costo_val = to_decimal_safe(form.cleaned_data['costo'], default=None)
                producto.costo = costo_val if costo_val is not None else Decimal("0")

        # Recalcular precio en pesos si cambia precio USD
        if 'precio' in form.changed_data:
            producto.precio_pesos = to_decimal_safe(producto.precio) * dolar_venta

        producto.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect('inventario')

    return render(request, 'productos/editar_producto.html', {
        'form': form,
        'tipo': tipo,
        'producto': producto,
        'dolar_venta': dolar_venta,
    })

# ---------------------------------
# Eliminar
# ---------------------------------
@login_required
@role_required(['Gerente'])
def eliminar_producto(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    producto.delete()
    return redirect('inventario')

# ---------------------------------
# Vistas auxiliares
# ---------------------------------
@login_required
def seleccionar_tipo_producto(request):
    return render(request, 'productos/seleccionar_tipo_producto.html')

@login_required
def ver_producto(request, tipo, pk):
    modelos = {'iphone': Iphone, 'mac': Mac, 'accesorio': Accesorio}

    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    producto = get_object_or_404(modelos[tipo], pk=pk)

    content_type = ContentType.objects.get_for_model(producto)
    fotos = FotoProducto.objects.filter(content_type=content_type, object_id=producto.pk)

    es_gerente = getattr(request.user, "role", "") == 'Gerente'

    # Cotización con guardia
    dolar_venta_raw = get_dolar_blue_venta()
    if not dolar_venta_raw or dolar_venta_raw <= 0:
        logger.warning("ver_producto: dolar_venta inválido: %r. Usando 1.", dolar_venta_raw)
        messages.error(request, "No se pudo obtener la cotización del dólar. Se mostrará solo en USD.")
        dolar_venta = Decimal("1")
    else:
        dolar_venta = to_decimal_safe(dolar_venta_raw, default=Decimal("1"))
        if dolar_venta <= 0:
            messages.error(request, "Cotización inválida del dólar. Se mostrará solo en USD.")
            dolar_venta = Decimal("1")

    # Precio ARS
    producto.precio_pesos = round(to_decimal_safe(producto.precio) * dolar_venta, 2)

    return render(request, 'productos/ver_producto.html', {
        'producto': producto,
        'tipo': tipo,
        'fotos': fotos,
        'es_gerente': es_gerente,
        'dolar_venta': dolar_venta,
    })

@login_required
def imprimir_qr(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    return render(request, 'productos/imprimir_qr.html', {'producto': producto})

@login_required
def imprimir_descripcion(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    content_type = ContentType.objects.get_for_model(producto)
    fotos = FotoProducto.objects.filter(content_type=content_type, object_id=producto.pk)

    return render(request, 'productos/imprimir_descripcion.html', {
        'producto': producto,
        'tipo': tipo,
        'fotos': fotos,
    })
