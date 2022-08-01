from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import include, path, re_path
from rest_framework.authtoken.models import Token
from rest_framework.routers import SimpleRouter

from api.views import (
    APIDownloadShoppingCart,
    APIFavorite,
    APIIngredients,
    APIIngredientsDetail,
    APIShoppingCart,
    RecipeViewSet,
    TagViewSet,
)
from users.views import (
    APIUser,
    APIUserDetail,
    FollowListAPIView,
    APIFollow,
    TokenCreateWithCheckBlockStatusView
)


app_name = 'api'

router_v1 = SimpleRouter()

router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/',
         APIUser.as_view()
         ),
    path('users/<int:pk>/',
         APIUserDetail.as_view()
         ),
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
        'recipes/<int:pk>/favorite/',
        APIFavorite.as_view(),
        name='favorite'
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
    path('', include('djoser.urls')),
    path(
        'auth/token/login/',
        TokenCreateWithCheckBlockStatusView.as_view(),
        name='login'
    ),
    re_path(r'^auth/',
            include('djoser.urls.authtoken')),
    path(
        'ingredients/',
        APIIngredients.as_view()
    ),
    path(
        'ingredients/<int:pk>/',
        APIIngredientsDetail.as_view()
    ),
    path('', include(router_v1.urls)),
]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
