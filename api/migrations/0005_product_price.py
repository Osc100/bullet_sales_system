# Generated by Django 4.1.1 on 2022-09-09 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_saleshistory_date_sold'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.FloatField(default=100, verbose_name='Precio Unitario'),
            preserve_default=False,
        ),
    ]