from django.shortcuts import render, redirect
from accounts.utils import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.timezone import now
from facturacion.models import Factura
from productos.models import Iphone, Mac, Accesorio
from django.db import models
from django.db.models import Sum
from datetime import datetime, timedelta
import json

# Vista general para redirigir según el rol
@login_required
def dashboard(request):
    if request.user.role == 'Gerente':
        return redirect('dashboard_gerente')  # Asegúrate de usar el namespace si lo configuraste
    elif request.user.role == 'Empleado':
        return redirect('dashboard_empleado')
    elif request.user.role == 'Vendedor':
        return redirect('dashboard_vendedor')
    else:
        messages.error(request, "No tienes acceso al dashboard.")
        return redirect('login')  # Si no tiene rol válido, redirigir al login

# Vista específica para Gerente
@login_required
@role_required(['Gerente'])
def dashboard_gerente(request):
    total_iphones = Iphone.objects.filter(stock__gt=0).count()
    total_macs = Mac.objects.filter(stock__gt=0).count()
    total_accesorios = Accesorio.objects.filter(stock__gt=0).count()
    total_productos = total_iphones + total_macs + total_accesorios

    total_facturas = Factura.objects.count()
    total_ventas = Factura.objects.aggregate(total=Sum('total'))['total'] or 0

    # Ventas últimos 6 meses
    meses = []
    ventas = []
    for i in range(6):
        mes = datetime.now() - timedelta(days=i*30)
        mes_str = mes.strftime("%b %Y")
        total_mes = Factura.objects.filter(fecha__month=mes.month, fecha__year=mes.year).aggregate(total=Sum('total'))['total'] or 0
        
        meses.append(mes_str)
        ventas.append(float(total_mes))  # Convertir a float para evitar errores con JSON

    contexto = {
        'total_productos': total_productos,
        'total_iphones': total_iphones,
        'total_macs': total_macs,
        'total_accesorios': total_accesorios,
        'total_facturas': total_facturas,
        'total_ventas': float(total_ventas),  # Convertir a float
        'ultimas_facturas': Factura.objects.order_by('-fecha')[:5],
        'meses': json.dumps(meses[::-1]),  # Asegurar orden correcto
        'ventas': json.dumps(ventas[::-1])  # Ahora sin error de Decimal
    }
    
    return render(request, 'core/dashboard_gerente.html', contexto)


# Vista específica para Empleado
@login_required
@role_required(['Empleado'])
def dashboard_empleado(request):
    return render(request, 'core/dashboard_empleado.html', {
        'data': 'Datos relevantes para empleados',  # Pasa datos adicionales si es necesario
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
    return render(request, 'core/inventario_vendedor.html')  # Asegúrate de que esta plantilla existe