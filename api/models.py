from datetime import date
from functools import lru_cache

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class Category(models.Model):
    name = models.CharField(max_length=255)


class Product(models.Model):
    name = models.CharField(max_length=254, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    sale_price = models.DecimalField(max_digits=6, decimal_places=2)
    alert_quantity = models.PositiveBigIntegerField(null=True)

    @property
    def total_value(self) -> float:
        return self.quantity * self.sale_price

    @property
    def quantity(self) -> int:
        quantity = self.batch_set.filter(product__name=self.name).aggregate(
            Sum("quantity")
        )["quantity__sum"]

        return quantity if quantity else 0

    @property
    def is_inventory_low(self) -> bool:
        quantity = self.quantity

        return quantity < self.alert_quantity


class Batch(models.Model):
    quantity = models.PositiveIntegerField()
    initial_quantity = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    buy_price = models.DecimalField(max_digits=6, decimal_places=2)
    bought_by = models.ForeignKey(User, on_delete=models.PROTECT)
    date_created = models.DateField(auto_now=True)
    obsolete_date = models.DateField(null=True)

    @property
    def total_price(self) -> float:
        return self.initial_quantity * self.buy_price

    class Meta:
        ordering = ("-date_created", "id")

    @property
    def days_until_obsolete(self):
        if not self.obsolete_date:
            return
        return (date.today() - self.obsolete_date).days

    @property
    def is_obsolete(self) -> bool:
        return self.obsolete_date and date.today() < self.obsolete_date


class CompleteSale(models.Model):
    date_sold = models.DateField(auto_now=True)
    reverted = models.BooleanField(default=False)
    sold_by = models.ForeignKey(User, on_delete=models.PROTECT)

    # @property
    # def quantity_sold(self) -> float:
    #     return self.salehistory_set.all().aggregate(Sum("quantity_sold"))[
    #         "quantity_sold__sum"
    #     ]

    # @property
    # def total_sold(self) -> float:
    #     return self.salehistory_set.all().aggregate(Sum("total_sold"))[
    #         "total_sold__sum"
    #     ]


class SaleHistory(models.Model):
    unit_price = models.FloatField()
    complete_sale = models.ForeignKey(
        CompleteSale, on_delete=models.CASCADE, null=True, related_name="sales"
    )

    @property
    @lru_cache(maxsize=10)
    def quantity_sold(self) -> int:
        return self.batch_sales.all().aggregate(Sum("quantity"))["quantity__sum"]

    @property
    def total_sold(self) -> float:
        return self.quantity_sold * self.unit_price

    @property
    def total_cost(self) -> float:
        return sum([float(bs.total_cost) for bs in self.batch_sales.all()])

    @property
    def total_renevue(self) -> float:
        return self.total_sold - self.total_cost


class BatchSale(models.Model):
    quantity = models.PositiveIntegerField()
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    sale_history = models.ForeignKey(
        SaleHistory, on_delete=models.CASCADE, related_name="batch_sales"
    )

    @property
    @lru_cache(maxsize=10)
    def total_cost(self) -> int:
        return self.batch.buy_price * self.quantity
