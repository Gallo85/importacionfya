from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Agrega una clase CSS al widget del campo del formulario."""
    return field.as_widget(attrs={"class": css_class})


