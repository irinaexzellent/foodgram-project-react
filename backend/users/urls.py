from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FollowListView, FollowViewSet

app_name = 'users'

router = DefaultRouter()


urlpatterns = [
    path(
        'users/subscriptions/',
        FollowListView.as_view(),
        name='subscriptions'
    ),
    path(
        'users/<int:user_id>/subscribe/',
        FollowViewSet.as_view(),
        name='subscribe'
    ),
    path('', include(router.urls)),
]
