from django.shortcuts import render, redirect
from accounts.utils import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.timezone import now
from facturacion.models import Factura, DetalleFactura
from productos.models import Iphone, Mac, Accesorio
from django.db import models
from django.db.models import Sum, Q, F, DecimalField, ExpressionWrapper
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.core.paginator import Paginator
from datetime import timedelta

# Vista general para redirigir según el rol
@login_required
def dashboard(request):
    if request.user.role == 'Gerente':
        return redirect('dashboard_gerente')
    elif request.user.role == 'Empleado':
        return redirect('dashboard_empleado')
    elif request.user.role == 'Vendedor':
        return redirect('dashboard_vendedor')
    else:
        messages.error(request, "No tienes acceso al dashboard.")
        return redirect('login')

@login_required
@role_required(['Gerente'])
def dashboard_gerente(request):
    # Inventario (estas queries son rápidas)
    total_iphones = Iphone.objects.filter(stock__gt=0).count()
    total_macs = Mac.objects.filter(stock__gt=0).count()
    total_fundas = Accesorio.objects.filter(stock__gt=0, tipo="Funda").count()
    total_protectores = Accesorio.objects.filter(stock__gt=0, tipo="Protec. Pantalla").count()
    total_cargadores = Accesorio.objects.filter(stock__gt=0, tipo="Cargador").count()
    total_auriculares = Accesorio.objects.filter(stock__gt=0, tipo="Auricular").count()
    total_accesorios = total_fundas + total_protectores + total_cargadores + total_auriculares
    total_productos = total_iphones + total_macs + total_accesorios

    # ✅ OPTIMIZACIÓN: Inversión usando agregaciones de la base de datos
    inversion_iphones = Iphone.objects.filter(stock__gt=0).aggregate(
        total=Sum(ExpressionWrapper(F('stock') * F('costo'), output_field=DecimalField()))
    )['total'] or 0
    
    inversion_macs = Mac.objects.filter(stock__gt=0).aggregate(
        total=Sum(ExpressionWrapper(F('stock') * F('costo'), output_field=DecimalField()))
    )['total'] or 0
    
    inversion_accesorios = Accesorio.objects.filter(stock__gt=0).aggregate(
        total=Sum(ExpressionWrapper(F('stock') * F('costo'), output_field=DecimalField()))
    )['total'] or 0

    # Filtro por rango de fechas
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    # ✅ OPTIMIZACIÓN: Prefetch y select_related para evitar N+1 queries
    facturas_validas = Factura.objects.filter(
        notacredito__isnull=True
    ).select_related(
        'cliente', 
        'cliente__vendedor'
    ).prefetch_related(
        'detalles__producto_iphone',
        'detalles__producto_mac',
        'detalles__producto_accesorio'
    )

    if fecha_inicio_str and fecha_fin_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            fecha_fin_inclusive = fecha_fin + timedelta(days=1)
            facturas_validas = facturas_validas.filter(fecha__gte=fecha_inicio, fecha__lt=fecha_fin_inclusive)
        except ValueError:
            messages.error(request, "Fechas inválidas. Por favor usá el formato correcto (YYYY-MM-DD).")

    facturas_validas = facturas_validas.order_by('-fecha')
    total_notas_credito = Factura.objects.filter(notacredito__isnull=False).count()

    # Total ventas en USD
    total_ventas_usd = sum(
        f.total / f.dolar_venta if f.dolar_venta else 0
        for f in facturas_validas
    )

    # Construcción de balance por factura
    balance_por_factura = []
    for factura in facturas_validas:
        detalles_balance = []
        balance_factura_total = 0

        # Los detalles ya están pre-cargados gracias a prefetch_related
        for detalle in factura.detalles.all():
            producto = detalle.producto_iphone or detalle.producto_mac or detalle.producto_accesorio
            if producto:
                precio_usd = detalle.precio_unitario / factura.dolar_venta if factura.dolar_venta else 0
                balance_unitario = precio_usd - (producto.costo or 0)
                total_balance = balance_unitario * detalle.cantidad
                balance_factura_total += total_balance

                detalles_balance.append({
                    'modelo': producto.modelo,
                    'precio': precio_usd,
                    'costo': producto.costo,
                    'cantidad': detalle.cantidad,
                    'balance': total_balance,
                    'imei': getattr(producto, 'imei', None),
                })

        balance_por_factura.append({
            'factura_id': factura.id,
            'cliente': factura.cliente.nombre,
            'balance_total': balance_factura_total,
            'detalles': detalles_balance,
            'vendedor': factura.cliente.vendedor.username if factura.cliente.vendedor else 'N/A',
            'fecha_venta': factura.fecha,
        })

    # Paginación
    paginator = Paginator(balance_por_factura, 10)
    page_number = request.GET.get('page')
    paged_balance_facturas = paginator.get_page(page_number)

    balance_total = sum(f['balance_total'] for f in balance_por_factura)

    context = {
        'total_iphones': total_iphones,
        'total_macs': total_macs,
        'total_accesorios': total_accesorios,
        'total_fundas': total_fundas,
        'total_protectores': total_protectores,
        'total_cargadores': total_cargadores,
        'total_auriculares': total_auriculares,
        'total_productos': total_productos,
        'total_facturas': facturas_validas.count(),
        'total_notas_credito': total_notas_credito,
        'total_ventas': float(total_ventas_usd),
        'balance_facturas': paged_balance_facturas,
        'balance_total': balance_total,
        'inversion_iphones': inversion_iphones,
        'inversion_macs': inversion_macs,
        'inversion_accesorios': inversion_accesorios,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
    }

    return render(request, 'core/dashboard_gerente.html', context)


# Vista específica para Empleado
@login_required
@role_required(['Empleado'])
def dashboard_empleado(request):
    return render(request, 'core/dashboard_empleado.html', {
        'data': 'Datos relevantes para empleados',
    })

@login_required
@role_required(['Vendedor'])
def dashboard_vendedor(request):
    # Obtener datos de inventario
    total_iphones = Iphone.objects.filter(stock__gt=0).count()
    total_macs = Mac.objects.filter(stock__gt=0).count()
    total_accesorios = Accesorio.objects.filter(stock__gt=0).count()
    total_productos = total_iphones + total_macs + total_accesorios

    # Pasar datos al template
    return render(request, 'core/dashboard_vendedor.html', {
        'data': 'Datos relevantes para vendedores',
        'total_iphones': total_iphones,
        'total_macs': total_macs,
        'total_accesorios': total_accesorios,
        'total_productos': total_productos,
    })

# Vista para que los usuarios puedan editar su perfil
@login_required
def editar_perfil(request):
    user = request.user

    # Permitir que solo los vendedores o empleados puedan editar su perfil
    if user.role not in ['Vendedor']:
        return HttpResponseForbidden("No tienes permiso para editar tu perfil.")

    if request.method == 'POST':
        # Procesar los datos enviados en el formulario
        user.first_name = request.POST.get('nombre', user.first_name)
        user.last_name = request.POST.get('apellido', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, "Perfil actualizado exitosamente.")
        return redirect('editar_perfil')

    return render(request, 'core/editar_perfil.html', {'user': user})

@login_required
@role_required(['Vendedor'])
def inventario_vendedor(request):
    return render(request, 'core/inventario_vendedor.html')