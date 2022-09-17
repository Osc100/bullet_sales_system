from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from api.models import Category, Product, SalesHistory


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance: Product):
        obj = super().to_representation(instance)
        obj['category'] = instance.category.name
        obj['total_price'] = instance.total_price
        return obj

    def validate(self, attrs):
        if float(attrs.get('quantity')) < 0:
            raise ValidationError(
                {'quantity': 'La cantidad no puede ser menor que 0'})

        if float(attrs.get('unit_price')) < 0:
            raise ValidationError(
                {'unit_price': 'El precio no peude ser menor que 0'})

        return super().validate(attrs)


class ProductValidatorSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'quantity', 'unit_price']


class SalesHistorySerializer(ModelSerializer):
    class Meta:
        model = SalesHistory
        fields = "__all__"

    def to_representation(self, instance):
        obj = super().to_representation(instance)
        obj['product'] = Product.objects.get(pk=obj['product']).name
        return obj


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']
