# Generated by Django 4.1.1 on 2022-10-20 05:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="batchsale",
            name="sale_history",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="api.salehistory"
            ),
        ),
        migrations.AlterField(
            model_name="salehistory",
            name="complete_sale",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sales",
                to="api.completesale",
            ),
        ),
    ]
