from django.urls import include, path
from knox.views import LogoutView
from rest_framework import routers

from api.views import (
    BatchView,
    CategoryView,
    CompleteSaleView,
    LoginView,
    ProductView,
    SaleHistoryView,
    register,
)

router = routers.DefaultRouter()
router.register("products", ProductView, "products")
router.register("categories", CategoryView, "categories")
router.register("salehistory", SaleHistoryView, "salehistory")
router.register("sales", CompleteSaleView, "sales")
router.register("batchs", BatchView, "batchs")
urlpatterns = [
    path(r"", include(router.urls)),
    path(r"login/", LoginView.as_view(), name="knox_login"),
    path(r"logout/", LogoutView.as_view(), name="knox_logout"),
    path(r"register/", register),
]
