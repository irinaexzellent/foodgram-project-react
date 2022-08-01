from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import filters, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet


from api.mixins import ListRetrieveViewSet
from api.models import (
    Favorite,
    Ingredients,
    Recipe,
    ShoppingCart,
    Tag,
    IngredientQuantity
)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    IngredientsSerializer,
    TagSerializer
)


User = get_user_model()


class APIIngredients(APIView):
    """View-класс для отбражения всех ингредиентов.
    Доступно всем пользователям.
    """
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ['name']

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_queryset(self):
        return Ingredients.objects.all()

    def get(self, request):
        "Возвращает список всех ингредиентов"
        the_filtered_qs = self.filter_queryset(self.get_queryset())
        ingredients = the_filtered_qs
        serializer = IngredientsSerializer(ingredients, many=True)
        return Response(serializer.data)


class APIIngredientsDetail(APIView):
    """View-класс для отбражения ингредиента по id.
    Доступно всем пользователям.
    """
    def get(self, request, pk):
        "Возвращает информацию об ингредиенте"
        try:
            ingredient = Ingredients.objects.get(pk=pk)
            serializer = IngredientsSerializer(ingredient)
            return Response(serializer.data)
        except Ingredients.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TagViewSet(ListRetrieveViewSet):
    """
    ViewSet для обработки эндпоинта 'api/tags/'
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    http_method_names = ('get',)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(
            queryset,
            self.request,
            view=self
        )

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для обработки эндпоинта 'api/recipes/'
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self):
        """
        Метод получения сериалайзера
        """
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """
        Метод создания рецепта
        """
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class APIFavorite(APIView):
    """
    APIView для добавления и удаления рецепта в избранное
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        if Favorite.objects.filter(
                user=request.user,
                recipes_id=recipe_id
        ).exists():
            return Response(
                {'error': 'Вы уже подписаны на данный рецепт!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(user=request.user, recipes=recipe)
        serializer = FavoriteSerializer(
                    recipe, context={'request': request}
                )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        favorite = Favorite.objects.filter(
                user=request.user,
                recipes_id=recipe_id)
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'error': 'Данный рецепт не в избранном!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class APIShoppingCart(APIView):
    """
    APIView для добавления и удаления рецепта в список покупок
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        if ShoppingCart.objects.filter(
                user=request.user,
                recipe_id=recipe_id
        ).exists():
            return Response(
                {'error': 'Вы уже добавли данный рецепт в список покупок!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteSerializer(
                    recipe, context={'request': request}
                )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        object_shopping_card = ShoppingCart.objects.filter(
                user=request.user,
                recipe_id=recipe_id)
        if object_shopping_card:
            object_shopping_card.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'error': 'Данный рецепт уже добавлен в список покупок!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class APIDownloadShoppingCart(APIView):
    """
    APIView для скачивания списка покупок
    """
    def get(self, request):
        ingredients = IngredientQuantity.objects.filter(
                recipe__shopping_carts__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit', 'amount'
            )
        shopping_cart = '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["amount"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_cart)
        response['Content-Type'] = 'text/plain'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
