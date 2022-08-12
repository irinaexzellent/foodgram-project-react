from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

from users.views import (
    TokenCreateWithCheckBlockStatusView,
    UserSubscribeViewSet,
)

app_name = 'users'

router_v1 = SimpleRouter()

router_v1.register(r'users', UserSubscribeViewSet, basename='users')

subscriptions = UserSubscribeViewSet.as_view({'get': 'subscriptions', })


urlpatterns = [
    path('users/subscriptions/', subscriptions, name='subscriptions'),
    path('', include('djoser.urls')),
    path(
        'auth/token/login/',
        TokenCreateWithCheckBlockStatusView.as_view(),
        name='login'
    ),
    re_path(r'^auth/',
            include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
