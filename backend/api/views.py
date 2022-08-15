from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from foodgram.pagination import LimitPageNumberPagination
from api.filters import IngredientSearchFilter, RecipeFilter
from api.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    IngredientsSerializer,
    FavoriteSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    ShoppingCartSerializer
)

User = get_user_model()


RECIPE_NOT_EXIST = 'Данный рецепт не добавлен!'


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для получения данных о всех ингредиентах
    Доступно всем пользователям
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    search_fields = ['name']
    http_method_names = ('get', )
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для получения данных о всех тэгах
    Доступно всем пользователям
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get',)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для обработки эндпоинта 'api/recipes/'
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        """
        Метод получения сериалайзера
        """
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_to(self, request, serializer):
        serializer = serializer(
            context={'request': request},
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, request, type_object):
        recipe_id = self.kwargs.get('pk')
        favorite = type_object.objects.filter(
            user=request.user,
            recipe_id=recipe_id)
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': RECIPE_NOT_EXIST},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
        )
    def favorite(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.add_to(
                request,
                serializer=FavoriteSerializer,)
        return self.delete_from(request, type_object=Favorite)

    @action(
        detail=True,
        methods=['post', 'get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=None)
    def shopping_cart(self, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_cart = get_object_or_404(
            ShoppingCart, user=user, recipe=recipe
        )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
        )
    def download_shopping_cart(self, request, pk=None):
        annotated_result = Ingredient.objects.filter(
            count_in_recipes__recipe__shopping_carts__user=request.user).annotate(
                quantity=Sum(F'{"count_in_recipes__amount"}'))

        shopping_cart = '\n'.join([
            f'{ingredient.name} - {ingredient.quantity} '
            f'{ingredient.measurement_unit}'
            for ingredient in annotated_result
        ])

        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_cart)
        response['Content-Type'] = 'text/plain'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
