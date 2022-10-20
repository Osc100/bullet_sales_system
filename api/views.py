from typing import List

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from knox.views import LoginView as KnoxLoginView
from rest_framework import mixins, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.models import Batch, BatchSale, Category, CompleteSale, Product, SaleHistory
from api.serializers import (
    BatchSerializer,
    CategorySerializer,
    CompleteSaleSerializer,
    ProductSerializer,
    SaleHistorySerializer,
    UserSerializer,
)
from api.utils import ResponseBadRequest, key_error_as_response_bad_request


class IsSuperUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user:
            return False
        return bool(request.user.is_superuser)


class LoginView(KnoxLoginView):
    authentication_classes = []
    permission_classes = []

    def get_user_serializer_class(self):
        return UserSerializer

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(LoginView, self).post(request, format=None)


@api_view(["POST"])
@permission_classes([IsSuperUser])
@key_error_as_response_bad_request
def register(request):
    data = dict(request.data)
    password1 = data.pop("password1")
    password2 = data.pop("password2")

    if password1 != password2:
        return ResponseBadRequest({"password2": "Las contraseñas no coinciden"})

    password = password1

    if data.get("is_superuser"):
        data["is_superuser"] = True
        data["is_staff"] = True
    else:
        data["is_superuser"] = False
        data["is_staff"] = False

    user_serializer = UserSerializer(data=data)
    user_serializer.is_valid(raise_exception=True)

    user_instance = User(**user_serializer.validated_data)
    try:
        validate_password(password, user_instance)
    except ValidationError as e:
        return ResponseBadRequest({"password1": e})

    user_instance.set_password(password)
    user_instance.save()
    return Response(
        UserSerializer(user_instance).data,
        status=status.HTTP_201_CREATED,
    )


class BatchView(ModelViewSet):
    queryset = Batch.objects.all().prefetch_related("product")
    serializer_class = BatchSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return ResponseBadRequest(
                {"non_field_errors": "No se puede borrar un lote con ventas asociadas."}
            )


class ProductView(ModelViewSet):
    queryset = Product.objects.prefetch_related("category").order_by(
        "category__name", "name"
    )
    serializer_class = ProductSerializer

    @permission_classes([IsSuperUser])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @permission_classes([IsSuperUser])
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return ResponseBadRequest(
                {
                    "non_field_errors": "No se puede borrar un producto que tenga lotes asociados"
                }
            )


class CategoryView(ModelViewSet):
    permission_classes = [IsSuperUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SaleHistoryView(mixins.ListModelMixin, GenericViewSet):
    queryset = SaleHistory.objects.all()
    serializer_class = SaleHistorySerializer


class CompleteSaleView(ModelViewSet):
    queryset = CompleteSale.objects.prefetch_related(
        "sales",
        "sales__batch_sales",
        "sales__batch_sales__batch",
        "sales__batch_sales__batch__product",
        "sales__batch_sales__batch__product__category",
    ).order_by("-id")
    serializer_class = CompleteSaleSerializer

    @action(detail=False, methods=["post"])
    @key_error_as_response_bad_request
    def sell(self, request):
        data = request.data

        print(data)
        if not isinstance(data, list):
            data = [data]

        complete_sale_instance = CompleteSale.objects.create(sold_by=request.user)

        for index, product_dict in enumerate(data):
            product_id: str = product_dict.pop("product")

            try:
                product_instance: Product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                return ResponseBadRequest(
                    {index: {"product": "Este campo es requerido"}}
                )

            quantity = int(product_dict.pop("quantity"))

            if quantity <= 0:
                return ResponseBadRequest(
                    {index: {"quantity": "No puedes vender una cantidad negativa"}}
                )

            if product_instance.quantity < quantity:
                return ResponseBadRequest(
                    {index: {"quantity": "No hay suficiente cantidad en el inventario"}}
                )

            sale_history_instance = SaleHistory.objects.create(
                unit_price=product_instance.sale_price,
                complete_sale=complete_sale_instance,
            )
            batch_sales_instances: List[BatchSale] = []

            try:
                batch_queryset: List[Batch] = product_instance.batch_set.filter(
                    quantity__gt=0
                )
                for batch in batch_queryset:
                    sell_quantity = min(batch.quantity, quantity)
                    quantity -= sell_quantity
                    batch.quantity -= sell_quantity
                    batch_sales_instances.append(
                        BatchSale(
                            batch=batch,
                            quantity=sell_quantity,
                            sale_history=sale_history_instance,
                        )
                    )

                    if quantity == 0:
                        break

                Batch.objects.bulk_update(batch_queryset, ["quantity"])
                BatchSale.objects.bulk_create(batch_sales_instances)
            except Exception as e:
                complete_sale_instance.delete()
                return ResponseBadRequest({index: e})

        return Response({"success": "La venta se ha efectuado satisfactoriamente"})

    def revert_batch_sale(self, complete_sale: CompleteSale):
        batches_to_update: List[Batch] = []
        if complete_sale.reverted is True:
            return
        for sale_history in complete_sale.sales.all():
            print(sale_history)
            for batch_sale in sale_history.batch_sales.all():
                batch: Batch = batch_sale.batch
                matching_batch = list(
                    filter(lambda b: b.id == batch.id, batches_to_update)
                )

                if matching_batch:
                    batch = matching_batch[0]
                    batch.quantity += batch_sale.quantity
                    continue

                batch.quantity += batch_sale.quantity
                batches_to_update.append(batch)

        complete_sale.reverted = True
        print(batches_to_update)
        Batch.objects.bulk_update(batches_to_update, ["quantity"])
        complete_sale.save()

    @action(detail=False, methods=["post"])
    @key_error_as_response_bad_request
    def revert_sale(self, request):
        complete_sale_id = request.data.pop("sale_id")

        complete_sale = CompleteSale.objects.prefetch_related(
            "sales", "sales__batch_sales", "sales__batch_sales__batch"
        ).get(pk=complete_sale_id)

        try:
            self.revert_batch_sale(complete_sale)
        except Exception as e:
            return ResponseBadRequest({"non_field_errors": e})

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        self.revert_batch_sale(instance)
        super().perform_destroy(instance)
