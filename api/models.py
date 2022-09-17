
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    name = models.CharField(verbose_name=_('Nombre'), max_length=255)

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True


class Category(BaseModel):
    pass


class Product(BaseModel):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name=_("Categoría"))
    quantity = models.PositiveSmallIntegerField(verbose_name=_("Cantidad"))
    unit_price = models.FloatField(verbose_name=_("Precio Unitario"))
    date_created = models.DateField(auto_now=True)
    obsolete_date = models.DateField()
    alert_quantity = models.PositiveBigIntegerField()

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


class SalesHistory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name=_("Producto"))
    quantity_sold = models.PositiveSmallIntegerField(
        verbose_name=_("Cantidad"))
    unit_price = models.FloatField(verbose_name=_("Precio Unitario"))
    date_sold = models.DateField(verbose_name=_(
        "Fecha y hora"), help_text=_("Fecha y hora a la que se registró la transacción"), auto_created=True, auto_now=True)

    def __str__(self) -> str:
        return f'{self.product.name} - vendido: {self.quantity_sold} - a: {self.unit_price} - {self.date_sold}'

    @property
    def total_sold(self) -> float:
        return self.quantity_sold * self.unit_price
