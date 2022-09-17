
from django.urls import include, path
from rest_framework import routers

from api.views import (CategoryView, ProductView, SalesHistoryView, login,
                       register)

router = routers.DefaultRouter()
router.register('products', ProductView, 'products')
router.register('categories', CategoryView, 'categories')
router.register('sales', SalesHistoryView, 'sales')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', login),
    path('register/', register)
]
