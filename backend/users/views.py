from djoser.views import TokenCreateView, UserViewSet
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from foodgram.pagination import LimitPageNumberPagination
from users.models import Follow, User
from users.serializers import (
    FollowSerializer,
    FollowPostSerializer,
    FollowListSerializer,
    )

USER_BLOCKED = 'Данный аккаунт временно заблокирован!'


class TokenCreateWithCheckBlockStatusView(TokenCreateView):
    def _action(self, serializer):
        if serializer.user.is_blocked:
            return Response(
                {'error': USER_BLOCKED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super()._action(serializer)


class UserSubscribeViewSet(UserViewSet):
    """
    View-класс для обработки эндпоинта /users/
    """
    pagination_class = LimitPageNumberPagination
    lookup_url_kwarg = 'id'

    def subscribe_to_author(self, request):
        user_id = self.kwargs.get('id')
        serializer = FollowPostSerializer(
            context={'request': request},
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author = get_object_or_404(User, id=user_id)
        serializer_data = FollowSerializer(
            author,
            context={'request': request},
            )
        return Response(
            serializer_data.data,
            status=status.HTTP_201_CREATED
            )

    def unsubscribe_from_author(self, request):
        user_id = self.kwargs.get('id')
        subscribe = Follow.objects.filter(
                user=request.user,
                author_id=user_id)
        if subscribe:
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'error': 'Вы не подписаны на пользователя!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.subscribe_to_author(request)
        return self.unsubscribe_from_author(request)

    def get_subscribtion_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())
        return FollowListSerializer(*args, **kwargs)

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions'
    )
    @permission_classes([IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        followed_list = User.objects.filter(following__user=user)
        page = self.paginate_queryset(followed_list)
        if page is not None:
            serializer = self.get_subscribtion_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_subscribtion_serializer(followed_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
