from django.contrib import admin

from api.models import Category, Product, SalesHistory

admin.site.register([Product, SalesHistory, Category])
