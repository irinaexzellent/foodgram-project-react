from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from api.models import Recipe
from users.models import Follow, User

SUBSCRIBE_ON_AUTHOR_EXIST = 'Вы уже подписаны на данного автора!'


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


class FollowSerializer(UserDetailSerializer):
    """
    Сериализатор подписок на авторов
    """
    recipes = RecipeFollowSerializer(many=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


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
    Сериализатор для обработки данных о пользователях,
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


class FollowPostSerializer(UserDetailSerializer):
    """
    Сериализатор для создания подписки на автора
    """
    user = serializers.ReadOnlyField(source='user.id')
    author = serializers.ReadOnlyField(source='author.id')

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def create(self, validated_data):
        user =  self.context['request'].user
        author_id = self.context.get('request').parser_context['kwargs']['pk']
        author = get_object_or_404(User, id=author_id)
        if Follow.objects.filter(user=user, author=author).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                    SUBSCRIBE_ON_AUTHOR_EXIST)
        return Follow.objects.create(user=user, author=author)

