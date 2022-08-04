from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.models import Recipe
from users.models import Follow, User


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей """
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )


class UserDetailSerializer(UserSerializer):
    """Сериализатор для пользователя """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            )

    def get_is_subscribed(self, obj):
        """
        Метод получения поля 'is_subscribed'
        'is_subscribed' = True, если авторизированный пользователь
        подписан на текущего
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        else:
            user = request.user
            return Follow.objects.filter(user=user, author=obj).exists()


class FollowSerializer(UserDetailSerializer):
    """
    Сериализатор подписок на авторов
    """

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            )
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message=('Вы уже подписаны на данного пользователя!')
            )
        ]
    """
    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя!')
        return data
    не получается вынести логику валидации в сериалайзер
    """


class RecipeFollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обработки данных о рецепете
    применяется в FollowListSerializer
    """
    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time',
        )


class FollowListSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для обработки данных о пользователях,
    на которых подписан текущий пользователь
    В выдачу добавлены рецепты и общее количество рецептов пользователей
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = RecipeFollowSerializer(many=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()
