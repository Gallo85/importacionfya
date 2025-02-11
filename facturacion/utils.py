from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO
from django.http import HttpResponse
from django.contrib.humanize.templatetags.humanize import intcomma

def generar_factura_pdf(factura):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 50, "IMPORTACION FyA")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 65, "Av. Siempre Viva 123, Buenos Aires, Argentina")
    p.drawString(50, height - 80, "Tel: +54 9 11 1234-5678 | Email: contacto@importacionesfya.com")

    # Línea separadora
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.line(50, height - 90, width - 50, height - 90)

    # Datos del Cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 120, f"Factura N° {factura.id}")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 140, f"Fecha: {factura.fecha.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(50, height - 155, f"Cliente: {factura.cliente.nombre} {factura.cliente.apellido}")
    p.drawString(50, height - 170, f"Email: {factura.cliente.email}")

    # Tabla con detalles de productos
    table_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
    
    for item in factura.detalles.all():
        # Determinar el nombre correcto del producto
        if item.producto_iphone:
            nombre_producto = f"{item.producto_iphone.modelo} (IMEI: {item.producto_iphone.imei})"
        elif item.producto_mac:
            nombre_producto = f"{item.producto_mac.modelo} (IMEI: {item.producto_mac.imei})"
        elif item.producto_accesorio:
            nombre_producto = item.producto_accesorio.modelo
        else:
            nombre_producto = "Producto desconocido"

        table_data.append([
            nombre_producto,
            item.cantidad,
            f"${intcomma(item.precio_unitario)}",
            f"${intcomma(item.subtotal)}"
        ])

    # Agregar Total
    table_data.append(["", "", "Total:", f"${intcomma(factura.total)}"])

    table = Table(table_data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 250)

    # Firma y mensaje final
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, height - 350, "Gracias por su compra. Esperamos verlo nuevamente.")

    # Guardar y devolver el PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer



