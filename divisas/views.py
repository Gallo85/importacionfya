from django.shortcuts import render
from .utils import obtener_dolar

def conversion_divisas(request):
    dolar_blue = obtener_dolar("blue")
    dolar_oficial = obtener_dolar("oficial")
    return render(request, "divisas/conversion.html", {
        "dolar_blue": dolar_blue,
        "dolar_oficial": dolar_oficial,
    })
