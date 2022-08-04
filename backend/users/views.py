from djoser.views import TokenCreateView
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from users.models import Follow, User
from users.serializers import (FollowSerializer, FollowListSerializer,
                               UserCreateSerializer,
                               UserDetailSerializer)


USER_BLOCKED = 'Данный аккаунт временно заблокирован!'


class TokenCreateWithCheckBlockStatusView(TokenCreateView):
    def _action(self, serializer):
        if serializer.user.is_blocked:
            return Response(
                {'error': USER_BLOCKED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super()._action(serializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    View-класс для обработки эндпоинта /users/
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    http_method_names = ('get', 'post')


class APIUserDetail(APIView):
    """
    View-класс для получения данных о пользователе по pk
    Доступно аутентифицированному пользователю
    """
    def get(self, request, pk):
        "Возвращает информацию о пользователе по pk"
        try:
            user = User.objects.get(pk=pk)
            serializer = UserDetailSerializer(
                user,
                context={'request': request})
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class APIFollow(APIView):
    """
    APIView для добавления и удаления подписки на автора
    Доступно аутентифицированному поользователю
    """
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Возвращает информацию об авторе, после подписки на него
        авторизированного пользователя
        """
        """
        serializer_for_subscribing = self.serializer_class(data=request.data)
        serializer_for_subscribing.is_valid(raise_exception=True)
        serializer_for_subscribing.save()
        не нужен сериализатор, чтобы подписаться на пользователя
        """
        user_id = self.kwargs.get('user_id')
        if user_id == request.user.id:
            return Response(
                {'error': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            Follow.objects.create(user=request.user, author_id=user_id)
        except:
            return Response(
                {'errors': 'Вы уже подписаны на пользователя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        author = get_object_or_404(User, id=user_id)
        serializer = FollowSerializer(
                    author, context={'request': request}
                )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        """
        Возвращает HTTP_204_NO_CONTENT после удаления
        подписки на автора рецепта
        """
        user_id = self.kwargs.get('user_id')
        follow = Follow.objects.filter(
                user=request.user,
                author_id=user_id)
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на пользователя!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class FollowListAPIView(ListAPIView):
    """
    ListAPIView для обработки эндпоинта /api/users/subscriptions/
    """
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь
        В выдачу добаляются рецепты
        """
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowListSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
