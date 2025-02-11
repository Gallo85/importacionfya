from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiplica dos valores. Utiliza este filtro en las plantillas.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
