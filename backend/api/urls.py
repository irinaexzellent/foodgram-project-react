from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

from api.views import (
    APIDownloadShoppingCart,
    APIShoppingCart,
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
)
from users.views import (
    APIUserDetail,
    FollowListAPIView,
    APIFollow,
    TokenCreateWithCheckBlockStatusView,
    UserViewSet,
)


app_name = 'api'

router_v1 = SimpleRouter()

router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='tags')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path(
        'users/subscriptions/',
        FollowListAPIView.as_view(),
        name='subscriptions'
    ),
    path(
        'users/<int:user_id>/subscribe/',
        APIFollow.as_view(),
        name='subscribe'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        APIShoppingCart.as_view(),
        name='shopping_cart'
    ),
    path(
        'recipes/download_shopping_cart/',
        APIDownloadShoppingCart.as_view(),
        name='shopping_cart'
    ),
    path(
        'users/<int:pk>/',
        APIUserDetail.as_view(),
        name='user_detail'
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path(
        'auth/token/login/',
        TokenCreateWithCheckBlockStatusView.as_view(),
        name='login'
    ),
    re_path(r'^auth/',
            include('djoser.urls.authtoken')),
]
