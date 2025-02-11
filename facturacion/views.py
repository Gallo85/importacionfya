from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Value, BooleanField, When, Case, F
from django.utils.dateparse import parse_date
from decimal import Decimal
import requests

from .models import Factura, NotaCredito, DetalleFactura
from .forms import FacturaForm, NotaCreditoForm, DetalleFacturaForm
from productos.models import Iphone, Mac, Accesorio
from productos.forms import IphoneForm, MacForm, AccesorioForm
from accounts.models import Cliente
from accounts.utils import role_required

from .utils import generar_factura_pdf
from .enviar_factura_email import enviar_factura_email


def listar_facturas(request):
    num_factura = request.GET.get('num_factura', '').strip()
    nombre_cliente = request.GET.get('nombre_cliente', '').strip()
    fecha_factura = request.GET.get('fecha_factura', '').strip()

    facturas_list = Factura.objects.all().order_by('-fecha')

    # 🔹 Filtros separados
    if num_factura:
        facturas_list = facturas_list.filter(id__icontains=num_factura)
    if nombre_cliente:
        facturas_list = facturas_list.filter(
            Q(cliente__nombre__icontains=nombre_cliente) | Q(cliente__apellido__icontains=nombre_cliente)
        )
    if fecha_factura:
        facturas_list = facturas_list.filter(fecha__date=fecha_factura)  # YYYY-MM-DD

    # Paginación (10 facturas por página)
    paginator = Paginator(facturas_list, 10)
    page_number = request.GET.get('page')
    facturas = paginator.get_page(page_number)

    es_gerente = request.user.groups.filter(name="Gerente").exists() or request.user.is_superuser

    return render(request, 'facturacion/listar_facturas.html', {
        'facturas': facturas,
        'es_gerente': es_gerente,
        'num_factura': num_factura,
        'nombre_cliente': nombre_cliente,
        'fecha_factura': fecha_factura,
    })

def obtener_dolar_venta():
    """
    Obtiene el valor del dólar venta desde la API configurada.
    """
    try:
        response = requests.get(settings.DOLAR_API_ENDPOINT, timeout=5)
        response.raise_for_status()
        datos = response.json()
        if isinstance(datos, list):
            for item in datos:
                if item.get("casa") == "blue":
                    return float(item.get("venta", 0))
        return float(datos.get("blue", {}).get("venta", 0))
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a la API: {e}")
        return 0

def obtener_dolar_compra():
    """
    Obtiene el valor del dólar compra desde la API configurada.
    """
    try:
        response = requests.get(settings.DOLAR_API_ENDPOINT, timeout=5)
        response.raise_for_status()
        datos = response.json()
        if isinstance(datos, list):
            for item in datos:
                if item.get("casa") == "blue":
                    return float(item.get("compra", 0))
        return float(datos.get("blue", {}).get("compra", 0))
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a la API: {e}")
        return 0

def crear_factura(request):
    productos = list(Iphone.objects.filter(stock__gt=0)) + list(Mac.objects.filter(stock__gt=0)) + list(Accesorio.objects.filter(stock__gt=0))
    dolar_venta = obtener_dolar_venta()
    dolar_compra = obtener_dolar_compra()

    if dolar_venta <= 0 or dolar_compra <= 0:
        messages.error(request, "No se pudo obtener la cotización del dólar. Intenta nuevamente más tarde.")
        return redirect('facturacion:crear_factura')

    if request.method == 'POST':
        factura_form = FacturaForm(request.POST)
        if factura_form.is_valid():
            try:
                with transaction.atomic():
                    productos_ids = request.POST.getlist('productos_ids[]')
                    cantidades = request.POST.getlist('cantidades[]')
                    pago_pesos = Decimal(request.POST.get('pago_pesos', 0))
                    pago_dolares = Decimal(request.POST.get('pago_dolares', 0)) * Decimal(dolar_compra)
                    vuelto_entregado = request.POST.get('vuelto_entregado') == 'on'  # ✅ Checkbox para el vuelto

                    errores_stock = []
                    productos_seleccionados = {}

                    # Validación de productos y stock
                    for producto_id, cantidad in zip(productos_ids, cantidades):
                        try:
                            producto_id = int(producto_id)
                            cantidad = int(cantidad)
                        except ValueError:
                            errores_stock.append(f"ID de producto inválido: {producto_id}")
                            continue

                        producto = (
                            Iphone.objects.filter(id=producto_id, stock__gt=0).first() or
                            Mac.objects.filter(id=producto_id, stock__gt=0).first() or
                            Accesorio.objects.filter(id=producto_id, stock__gt=0).first()
                        )

                        if not producto:
                            errores_stock.append(f"El producto con ID {producto_id} no existe o no tiene stock disponible.")
                        elif producto.stock < cantidad:
                            errores_stock.append(f"No hay suficiente stock para {producto.modelo} (Stock actual: {producto.stock}).")
                        else:
                            productos_seleccionados[producto_id] = producto

                    if errores_stock:
                        for error in errores_stock:
                            messages.error(request, error)
                        return redirect('facturacion:crear_factura')

                    # Crear la factura
                    factura = factura_form.save(commit=False)
                    factura.dolar_venta = Decimal(dolar_venta)
                    factura.dolar_compra = Decimal(dolar_compra)
                    factura.vuelto_entregado = vuelto_entregado
                    factura.save()

                    total_factura = Decimal(0)

                    # Crear los detalles de la factura
                    for producto_id, cantidad in zip(productos_ids, cantidades):
                        cantidad_int = int(cantidad)
                        producto = productos_seleccionados.get(int(producto_id))

                        if producto:
                            precio_dolares = producto.precio
                            precio_pesos = precio_dolares * Decimal(dolar_venta)
                            subtotal = precio_pesos * cantidad_int

                            # Reducir stock del producto
                            producto.stock -= cantidad_int
                            producto.save()

                            # Crear el detalle de la factura
                            detalle_factura_data = {
                                "factura": factura,
                                "precio_unitario": precio_pesos,
                                "cantidad": cantidad_int,
                                "subtotal": subtotal,
                            }

                            # Asignar el producto al campo correcto
                            if isinstance(producto, Iphone):
                                detalle_factura_data["producto_iphone"] = producto
                            elif isinstance(producto, Mac):
                                detalle_factura_data["producto_mac"] = producto
                            elif isinstance(producto, Accesorio):
                                detalle_factura_data["producto_accesorio"] = producto

                            DetalleFactura.objects.create(**detalle_factura_data)
                            total_factura += subtotal

                    # Actualizar totales de la factura
                    factura.total = total_factura
                    total_pagado = pago_pesos + pago_dolares
                    vuelto = max(Decimal(0), total_pagado - total_factura)

                    factura.total_pagado = total_pagado
                    factura.vuelto = vuelto
                    factura.save()

                    messages.success(request, f"Factura creada con total de ${factura.total:.2f} ARS. Vuelto: ${vuelto:.2f} ARS. {'Vuelto entregado' if vuelto_entregado else 'Vuelto pendiente'}")
                    return redirect('facturacion:listar_facturas')

            except Exception as e:
                messages.error(request, f"Error al crear la factura: {e}")
                return redirect('facturacion:crear_factura')

        else:
            messages.error(request, "Errores en el formulario.")
    else:
        factura_form = FacturaForm()

    return render(request, 'facturacion/crear_factura.html', {
        'factura_form': factura_form,
        'productos': productos,
        'dolar_venta': dolar_venta,
        'dolar_compra': dolar_compra,
    })



def detalle_factura(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    detalles = factura.detalles.all()

    print(f"Factura ID: {factura.id}, Total: {factura.total}")
    print(f"Vuelto: {factura.vuelto}")
    print("Detalles asociados:")

    # Ajustamos para obtener el nombre correcto del producto
    detalles_con_nombre = []
    for detalle in detalles:
        if detalle.producto_iphone:
            nombre_producto = f"{detalle.producto_iphone.modelo} - IMEI: {detalle.producto_iphone.imei}"
        elif detalle.producto_mac:
            nombre_producto = f"{detalle.producto_mac.modelo} - IMEI: {detalle.producto_mac.imei}"
        elif detalle.producto_accesorio:
            nombre_producto = detalle.producto_accesorio.modelo
        else:
            nombre_producto = "Producto Desconocido"

        print(f"- Producto: {nombre_producto}, Cantidad: {detalle.cantidad}, Subtotal: {detalle.subtotal}")

        detalles_con_nombre.append({
            "nombre": nombre_producto,
            "precio_unitario": detalle.precio_unitario,
            "cantidad": detalle.cantidad,
            "subtotal": detalle.subtotal
        })

    return render(request, 'facturacion/detalle_factura.html', {
        'factura': factura,
        'detalles': detalles_con_nombre,
        'vuelto': factura.vuelto,  # ✅ Agregar el vuelto
        'vuelto_entregado': factura.vuelto_entregado,  # ✅ Estado del vuelto
    })



def agregar_detalle_factura(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    if request.method == 'POST':
        form = DetalleFacturaForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.factura = factura
            detalle.save()
            return redirect('facturacion:detalle_factura', factura_id=factura.id)
    else:
        form = DetalleFacturaForm()
    return render(request, 'facturacion/agregar_detalle_factura.html', {'form': form, 'factura': factura})


def listar_notas_credito(request):
    notas_credito = NotaCredito.objects.all().order_by('-fecha')
    return render(request, 'facturacion/listar_notas_credito.html', {'notas_credito': notas_credito})

@login_required
@role_required(['Gerente'])
def eliminar_factura(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    factura.delete()
    return redirect('facturacion:listar_facturas')


def total_ventas(request):
    page_number = request.GET.get('page', 1)  # Página actual, por defecto 1

    # Obtener todas las facturas con sus Notas de Crédito asociadas
    facturas_query = Factura.objects.annotate(
        tiene_nc=Case(
            When(notacredito__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        ),
        monto_nc=Sum('notacredito__monto', default=0)
    ).order_by('-fecha')

    # Determinar el método de pago correctamente
    for factura in facturas_query:
        if factura.pago_pesos > 0 and factura.pago_dolares > 0:
            factura.metodo_pago = "Mixto"
        elif factura.pago_dolares > 0:
            factura.metodo_pago = "Dólares"
        else:
            factura.metodo_pago = "Pesos"

    # Paginación: 10 facturas por página
    paginator = Paginator(facturas_query, 10)  
    facturas_paginadas = paginator.get_page(page_number)

    # Calcular el Total de Ventas Ajustado (Ventas - Notas de Crédito)
    total_ventas_ajustado = Factura.objects.aggregate(
        total_ventas=Sum('total', default=0),
        total_nc=Sum('notacredito__monto', default=0)
    )

    total_ventas = total_ventas_ajustado["total_ventas"] - total_ventas_ajustado["total_nc"]

    return render(request, "facturacion/total_ventas.html", {
        "facturas": facturas_paginadas,  # 🔹 Ahora es un objeto paginado
        "total_ventas": total_ventas,
    })


def buscar_productos(request):
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET.get('q', '').strip()
        productos = []

        if query:
            filtros_iphone = Q(modelo__icontains=query) | Q(imei__icontains=query)
            filtros_mac = Q(modelo__icontains=query) | Q(imei__icontains=query)
            filtros_accesorio = Q(tipo__icontains=query) | Q(modelo__icontains=query)

            # Buscar productos con stock disponible
            iphones = Iphone.objects.filter(filtros_iphone, stock__gt=0).values('id', 'modelo', 'precio', 'imei', 'stock')
            macs = Mac.objects.filter(filtros_mac, stock__gt=0).values('id', 'modelo', 'precio', 'imei', 'stock')
            accesorios = Accesorio.objects.filter(filtros_accesorio, stock__gt=0).values('id', 'tipo', 'modelo', 'precio', 'stock')

            # Agregar productos
            productos.extend([
                {'id': iphone['id'], 'nombre': f'Iphone {iphone["modelo"]}', 'precio': str(iphone['precio']),
                 'imei': iphone['imei'], 'stock': iphone['stock']}
                for iphone in iphones
            ])

            productos.extend([
                {'id': mac['id'], 'nombre': f'Mac {mac["modelo"]}', 'precio': str(mac['precio']),
                 'imei': mac['imei'], 'stock': mac['stock']}
                for mac in macs
            ])

            productos.extend([
                {'id': accesorio['id'], 'nombre': f'Accesorio {accesorio["tipo"]} - {accesorio["modelo"]}', 
                 'precio': str(accesorio['precio']), 'imei': 'N/A', 'stock': accesorio['stock']}
                for accesorio in accesorios
            ])

        return JsonResponse({'productos': productos}, safe=False)

    return JsonResponse({'error': 'Método no permitido'}, status=400)


def listar_notas_credito(request):
    notas = NotaCredito.objects.all()
    return render(request, 'facturacion/listar_notas_credito.html', {'notas': notas})

def crear_nota_credito(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    detalles = factura.detalles.all()  # Obtener los detalles de la factura

    if request.method == 'POST':
        form = NotaCreditoForm(request.POST)
        if form.is_valid():
            # Guardar la nota de crédito asociada a la factura
            nota_credito = form.save(commit=False)
            nota_credito.factura = factura
            nota_credito.cliente = factura.cliente  # Asigna automáticamente el cliente
            nota_credito.usuario_creador = request.user.username  # Asigna el usuario creador
            nota_credito.save()
            messages.success(request, f"Nota de Crédito #{nota_credito.id} creada exitosamente.")
            return redirect('facturacion:listar_notas_credito')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = NotaCreditoForm()

    # Calcular el total de la factura
    total_factura = detalles.aggregate(total=Sum('subtotal'))['total'] or 0

    return render(request, 'facturacion/crear_nota_credito.html', {
        'form': form,
        'factura': factura,
        'detalles': detalles,  # Pasar los detalles al contexto
        'total_factura': total_factura,  # Pasar el total de la factura al contexto
    })


def procesar_nota_credito(request, nota_id):
    nota = get_object_or_404(NotaCredito, id=nota_id)
    try:
        if nota.estado == 'pendiente':
            print(f"Procesando Nota de Crédito #{nota.id} para Factura #{nota.factura.id}")
            
            # Verificar los detalles de la factura antes de procesar
            detalles_factura = nota.factura.detalles.all()
            for detalle in detalles_factura:
                producto = detalle.producto_iphone or detalle.producto_mac or detalle.producto_accesorio
                print(f"Detalle: {detalle.id} - Producto: {producto.modelo if producto else 'No encontrado'} - Cantidad: {detalle.cantidad}")

            nota.procesar()  # Llama al método de procesamiento
            messages.success(request, f"Nota de Crédito #{nota.id} procesada correctamente. Productos devueltos al inventario.")
        else:
            messages.warning(request, "La nota de crédito ya fue procesada o anulada.")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
    
    return redirect('facturacion:listar_notas_credito')




def anular_nota_credito(request, nota_id):
    """
    Cambia el estado de una nota de crédito a 'anulada'.
    Si la nota estaba en estado 'procesada', se revierte el impacto en el inventario.
    """
    nota = get_object_or_404(NotaCredito, id=nota_id)
    try:
        # Llamar al método anular que maneja la lógica del inventario
        nota.anular()
        messages.success(request, f"La Nota de Crédito #{nota.id} ha sido anulada correctamente. Cambios revertidos en el inventario.")
    except ValueError as e:
        # Manejar errores, como si la nota ya estaba anulada
        messages.error(request, str(e))
    return redirect('facturacion:listar_notas_credito')


def listar_facturas_para_nota_credito(request):
    facturas = Factura.objects.all()  # Ajusta el filtro si es necesario
    return render(request, 'facturacion/listar_facturas_para_nota_credito.html', {'facturas': facturas})


def detalle_nota_credito(request, nota_id):
    """
    Muestra el detalle de una Nota de Crédito junto con su factura asociada.
    """
    nota = get_object_or_404(NotaCredito, id=nota_id)
    factura = nota.factura  # Obtener la factura asociada a la nota de crédito
    detalles = factura.detalles.all()  # Obtener los productos en la factura

    return render(request, 'facturacion/detalle_nota_credito.html', {
        'nota': nota,
        'factura': factura,
        'detalles': detalles,
    })

@login_required
@role_required(['Gerente'])
def eliminar_nota_credito(request, nota_id):
    nota = get_object_or_404(NotaCredito, id=nota_id)
    nota.delete()
    messages.success(request, "Nota de crédito eliminada correctamente.")
    return redirect('facturacion:listar_notas_credito')  # Asegurate de tener esta URL configurada


@login_required
@role_required(['Gerente'])
def caja_diaria(request):
    fecha_inicio = request.GET.get('fecha_inicio', '')  # Asegura que no sea None
    fecha_fin = request.GET.get('fecha_fin', '')        # Asegura que no sea None
    page_number = request.GET.get('page', 1)  # Página actual, por defecto 1

    # Filtrar facturas por rango de fechas si se proporcionan fechas válidas
    facturas_query = Factura.objects.all().order_by('-fecha')

    if fecha_inicio and fecha_inicio != 'None':  # Validar que no sea None o vacío
        facturas_query = facturas_query.filter(fecha__date__gte=parse_date(fecha_inicio))
    if fecha_fin and fecha_fin != 'None':  # Validar que no sea None o vacío
        facturas_query = facturas_query.filter(fecha__date__lte=parse_date(fecha_fin))

    # Paginación: 10 facturas por página
    paginator = Paginator(facturas_query, 10)  
    facturas_paginadas = paginator.get_page(page_number)

    # Calcular total de pesos y dólares
    total_pesos = facturas_query.aggregate(total=Sum('pago_pesos'))['total'] or 0
    total_dolares = facturas_query.aggregate(total=Sum('pago_dolares'))['total'] or 0

    return render(request, "facturacion/caja_diaria.html", {
        "caja_diaria": facturas_paginadas,  
        "total_pesos": total_pesos,
        "total_dolares": total_dolares,
        "fecha_inicio": fecha_inicio if fecha_inicio and fecha_inicio != 'None' else '',
        "fecha_fin": fecha_fin if fecha_fin and fecha_fin != 'None' else '',
    })


# Vista para generar el PDF
def imprimir_factura(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    pdf_file = generar_factura_pdf(factura)

    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura.id}.pdf"'  # ✅ Mantiene el PDF en una pestaña nueva
    return response

# Vista para enviar el email
def enviar_factura_email_view(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)

    if request.method == 'POST':
        enviar_factura_email(factura)
        messages.success(request, f'Factura {factura.id} enviada correctamente.')
        return redirect('facturacion:listar_facturas')  # 🔹 Ahora redirige a la lista de facturas

    messages.error(request, 'No se pudo enviar el correo.')
    return redirect('facturacion:listar_facturas')