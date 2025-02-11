from django import template

register = template.Library()

@register.filter
def formato_precio(value):
    """
    Formatea un número como precio con separadores de miles y dos decimales.
    Ejemplo: 9500000.50 -> $9.500.000,50
    """
    try:
        return f"${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value  # Devuelve el valor original si hay un error