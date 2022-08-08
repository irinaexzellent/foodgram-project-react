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

urlpatterns = [
    path('', include(router_v1.urls)),
]
