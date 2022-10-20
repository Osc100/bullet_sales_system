from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from api.models import Batch, BatchSale, Category, CompleteSale, Product, SaleHistory


class BatchSerializer(ModelSerializer):
    class Meta:
        model = Batch
        fields = "__all__"
        extra_kwargs = {
            "bought_by": {"read_only": True},
            "initial_quantity": {"read_only": True},
        }

    def to_representation(self, instance: Batch):
        obj = super().to_representation(instance)
        obj["product_name"] = instance.product.name
        return obj

    def create(self, validated_data):
        validated_data["bought_by"] = self.context.get("request").user
        validated_data["initial_quantity"] = validated_data["quantity"]
        return super().create(validated_data)


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(ModelSerializer):

    sale_price = serializers.IntegerField(min_value=0)
    alert_quantity = serializers.IntegerField(min_value=0)

    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance: Product, *args, **kwargs):
        obj = super().to_representation(instance)
        obj["category"] = instance.category.name
        # obj["is_inventory_low"] = instance.is_inventory_low
        obj["quantity"] = instance.quantity

        return obj


class BatchSaleSerializer(ModelSerializer):
    class Meta:
        model = BatchSale
        fields = "__all__"


class ProductValidatorSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "quantity", "unit_price"]


class SaleHistorySerializer(ModelSerializer):
    # batch_sales = BatchSaleSerializer(many=True, read_only=True)

    class Meta:
        model = SaleHistory
        fields = "__all__"

    def to_representation(self, instance: SaleHistory):
        obj = super().to_representation(instance)
        product = instance.batch_sales.first().batch.product
        obj["quantity_sold"] = instance.quantity_sold
        obj["total_sold"] = instance.total_sold
        obj["total_cost"] = instance.total_cost
        obj["total_renevue"] = instance.total_renevue
        obj["product_name"] = product.name
        obj["category_name"] = product.category.name
        return obj


class CompleteSaleSerializer(ModelSerializer):

    sales = SaleHistorySerializer(many=True, read_only=True)

    class Meta:
        model = CompleteSale
        fields = "__all__"

    def to_representation(self, instance: CompleteSale):
        obj = super().to_representation(instance)
        obj["sold_by_name"] = instance.sold_by.get_full_name()
        return obj


class UserSerializer(ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_superuser",
            "is_staff",
        ]
