# Generated by Django 5.1.4 on 2025-02-09 23:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detallefactura',
            name='producto',
        ),
        migrations.RemoveField(
            model_name='detallefactura',
            name='producto_id',
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='producto_accesorio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='productos.accesorio'),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='producto_iphone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='productos.iphone'),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='producto_mac',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='productos.mac'),
        ),
    ]
