from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.models import (
    CountOfIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
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


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для получения данных о всех ингредиентах
    Доступно всем пользователям
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ['name']
    http_method_names = ('get', )


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для получения данных о всех тэгах
    Доступно всем пользователям
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get',)


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

    def add_to_favorite(self, request):
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        #не нужен сериализатор, чтобы добавлять рецепты в избранное
        try:
            Favorite.objects.create(user=request.user, recipes=recipe)
        except:
            return Response(
                {'errors': 'Вы уже подписаны на данный рецепт!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FavoriteSerializer(
            recipe, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete_from_favorite(self, request):
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

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.add_to_favorite(request)
        return self.delete_from_favorite(request)


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
            {'error': 'Данного рецепта нет в списке покупок!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class APIDownloadShoppingCart(APIView):
    """
    APIView для скачивания списка покупок
    """
    def get(self, request):
        ingredients = CountOfIngredient.objects.filter(
                recipes__shopping_carts__user=request.user).values(
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
