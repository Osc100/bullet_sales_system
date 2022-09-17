from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import mixins, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.models import Category, Product, SalesHistory
from api.serializers import (CategorySerializer, ProductSerializer,
                             ProductValidatorSerializer,
                             SalesHistorySerializer, UserSerializer)


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


@api_view(['POST'])
@permission_classes([])
def login(request):
    token_serializer = AuthTokenSerializer(data=request.data)
    token_serializer.is_valid(raise_exception=True)
    user_instance = token_serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user_instance)

    return Response({'token': token.key})


@api_view(['POST'])
@permission_classes([IsSuperUser])
def register(request):
    data = dict(request.data)
    password1 = data.pop('password1')
    password2 = data.pop('password2')

    if password1 != password2:
        return Response({'password': 'Las contraseñas no coinciden'}, status=status.HTTP_400_BAD_REQUEST)

    password = password1

    user_serializer = UserSerializer(data=data)
    user_serializer.is_valid(raise_exception=True)

    user_instance = User(**user_serializer.validated_data)

    try:
        validate_password(password, user_instance)
    except ValidationError as e:
        return Response({'password': e})

    user_instance.save()
    return Response({'success': 'El usuario se ha creado correctamente'}, status=status.HTTP_201_CREATED)


class ProductView(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['post'])
    def vender(self, request):
        data: dict = request.data
        product_id: str = data.get('product_id')
        quantity = data.get('quantity')
        unit_price = data.get('unit_price')

        ProductValidatorSerializer(data={'id': product_id, 'quantity': quantity, 'unit_price': unit_price}).is_valid(
            raise_exception=True)

        product_instance = Product.objects.get(pk=product_id)

        quantity = int(quantity)

        if (quantity > product_instance.quantity):
            return Response({'quantity': 'No puede venderse más de lo que hay en el inventario'}, status=status.HTTP_400_BAD_REQUEST)

        sales_serializer = SalesHistorySerializer(
            data={'product': product_id, 'quantity_sold': quantity, 'unit_price': unit_price})
        sales_serializer.is_valid(raise_exception=True)
        sales_instance = SalesHistory(**sales_serializer.validated_data)
        sales_instance.save()

        product_instance.quantity -= quantity
        product_instance.save()

        return Response(SalesHistorySerializer(sales_instance).data, status=status.HTTP_201_CREATED)


class CategoryView(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SalesHistoryView(mixins.ListModelMixin, GenericViewSet):
    queryset = SalesHistory.objects.all()
    serializer_class = SalesHistorySerializer

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def calcular_ventas(self, request):
        data = dict(request.data)

        try:
            start_date = data.pop('start_date')
            end_date = data.pop('end_date')
        except KeyError as e:
            return Response({e.__str__(): "Por favor mande este campo correctamente"},
                            status=status.HTTP_400_BAD_REQUEST)

        sales_queryset = SalesHistory.objects.filter(
            date_sold__range=[start_date, end_date]).prefetch_related('product')

        try:
            product_instance = Product.objects.get(pk=data.get('product_id'))
            sales_queryset = sales_queryset.filter(product=product_instance)
        except Product.DoesNotExist:
            pass

        total_sales = sum(
            map(lambda i: i.quantity_sold * i.unit_price, sales_queryset))
        sales_cost = sum(
            map(lambda i: i.quantity_sold * i.product.unit_price, sales_queryset)
        )
        brute_utility = sum(map(lambda i: i.quantity_sold * i.unit_price -
                            i.quantity_sold * i.product.unit_price, sales_queryset))

        return Response({
            'total_sales': float('{:.2f}'.format(total_sales)),
            'brute_utility': float('{:.2f}'.format(brute_utility)),
            'sales_cost': float('{:.2f}'.format(sales_cost))
        })
