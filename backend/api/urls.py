from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

app_name = 'api'

router_v1 = SimpleRouter()

router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')

favorite = RecipeViewSet.as_view({'get': 'favorite', })
shopping_cart = RecipeViewSet.as_view({'get': 'shopping_cart', })

urlpatterns = [
    path('recipes/favorites/', favorite, name='favorite'),
    path('recipes/shopping_cart/', shopping_cart, name='shopping_cart'),
    path('', include(router_v1.urls)),
]
