# Generated by Django 4.1 on 2022-08-31 23:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nombre')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nombre')),
                ('quantity', models.PositiveSmallIntegerField(verbose_name='Cantidad')),
                ('unit_price', models.FloatField(verbose_name='Precio Unitario')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.category', verbose_name='Categoría')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_sold', models.PositiveSmallIntegerField(verbose_name='Cantidad vendida')),
                ('unit_price', models.FloatField(verbose_name='Precio Unitario')),
                ('datetime', models.DateTimeField(help_text='Fecha y hora a la que se registró la transacción', verbose_name='Fecha y hora')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.product', verbose_name='Producto')),
            ],
        ),
    ]