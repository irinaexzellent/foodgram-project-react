from djoser.views import TokenCreateView
from rest_framework import permissions, status, viewsets
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from users.models import Follow, User
from users.serializers import (FollowSerializer, FollowListSerializer,
                               UserCreateSerializer,
                               UserDetailSerializer)
from api.serializers import RecipeFollowSerializer

USER_BLOCKED = 'Данный аккаунт временно заблокирован!'


class TokenCreateWithCheckBlockStatusView(TokenCreateView):
    def _action(self, serializer):
        if serializer.user.is_blocked:
            return Response(
                {'error': USER_BLOCKED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super()._action(serializer)


class APIUser(APIView, PageNumberPagination):
    """
    View-класс для обработки эндпоинта /users/
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get(self, request, ):
        """
        Метод возвращает информацию о всех пользователях
        Доступно всем пользователям
        """
        page = self.paginate_queryset(self.queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Метод для регистрации пользователя
        """
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                                                self.request,
                                                view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


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


class FollowViewSet(APIView):
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
        user_id = self.kwargs.get('user_id')
        if user_id == request.user.id:
            return Response(
                {'error': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(
                user=request.user,
                author_id=user_id
        ).exists():
            return Response(
                {'error': 'Вы уже подписаны на пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, id=user_id)
        Follow.objects.create(user=request.user, author=author)
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


#class SubscriptionViewSet(viewsets.ModelViewSet):
#    permission_classes = [permissions.IsAuthenticated]
#
#    def get_queryset(self):
#        user = self.request.user
#       #return Follow.objects.filter(user=user).select_related('user')
#       return User.objects.filter(following__user=user)


class FollowListAPIView(ListAPIView):
    """
    ListAPIView для обработки эндпоинта /api/users/subscriptions/
    """
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь
        В выдаче добаляются рецепты
        """
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowListSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
