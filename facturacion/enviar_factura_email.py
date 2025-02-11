from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .utils import generar_factura_pdf  # ✅ Importa la función mejorada

def enviar_factura_email(factura):
    pdf_file = generar_factura_pdf(factura)

    email_subject = f'Factura N° {factura.id} - Importaciones FyA'
    email_body = render_to_string('facturacion/email_factura.html', {'factura': factura})
    email = EmailMessage(
        email_subject,
        email_body,
        settings.EMAIL_HOST_USER,
        [factura.cliente.email],
    )
    email.attach(f'factura_{factura.id}.pdf', pdf_file.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    email.send()
