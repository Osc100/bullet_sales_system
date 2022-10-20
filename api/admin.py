from django.contrib import admin

from api.models import Category, CompleteSale, Product, SaleHistory

admin.site.register([Product, SaleHistory, Category, CompleteSale])
