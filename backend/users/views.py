from djoser.views import TokenCreateView, UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer

from users.models import Follow, User
from users.serializers import (
    FollowSerializer,
    FollowPostSerializer,
    FollowListSerializer,
    UserCreateSerializer,
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


class UserViewSet(UserViewSet):
    """
    View-класс для обработки эндпоинта /users/
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

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

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        followed_list = User.objects.filter(following__user=user)
        paginator = PageNumberPagination()
        authors = paginator.paginate_queryset(
            followed_list,
            request=request
        )
        serializer = ListSerializer(
            child=FollowListSerializer(),
            context=self.get_serializer_context()
        )
        return paginator.get_paginated_response(
            serializer.to_representation(authors)
        )
