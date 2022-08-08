from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from api.models import (
    CountOfIngredient,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from users.serializers import UserDetailSerializer


TAGS_UNIQUE_ERROR = 'Теги не могут повторяться!'
INGREDIENTS_UNIQUE_ERROR = 'Ингредиенты не могут повторяться!'
INGREDIENT_DOES_NOT_EXIST = 'Ингредиента не существует!'
INGREDIENT_MIN_AMOUNT_ERROR = (
    'Количество ингредиента не может быть меньше {min_value}!'
)
INGREDIENT_MIN_AMOUNT = 1


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов, модели Ingredients """

    class Meta:
        model = Ingredient
        fields = (
                  'id',
                  'name',
                  'measurement_unit',
                  )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов, модели Tag. """

    class Meta:
        model = Tag
        fields = (
                  'id',
                  'name',
                  'color',
                  'slug',
                  )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления ингредиентов
    применяется в RecipeWriteSerializer для записи рецептов
    """
    class Meta:
        model = CountOfIngredient
        fields = ('id', 'amount',)
        extra_kwargs = {
            'id': {
                'read_only': False,
                'error_messages': {
                    'does_not_exist': INGREDIENT_DOES_NOT_EXIST,
                }
            },
            'amount': {
                'error_messages': {
                    'min_value': INGREDIENT_MIN_AMOUNT_ERROR.format(
                        min_value=INGREDIENT_MIN_AMOUNT
                    ),
                }
            }
        }


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения данных об ингредиентах, применяемых в рецепте
    """
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit.name'
    )
    id = serializers.ReadOnlyField(source='ingredient.id')

    class Meta:
        model = CountOfIngredient
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения рецептов
    """
    is_favorited = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserDetailSerializer()
    ingredients = RecipeIngredientReadSerializer(
        source='ingredient_amounts',
        many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'tags', 'author', 'ingredients', 'is_favorited',
            'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи рецептов
    """
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field='id', queryset=Tag.objects.all(),
            ),
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',
        )

    def validate(self, attrs):
        if len(attrs['tags']) > len(set(attrs['tags'])):
            raise serializers.ValidationError(TAGS_UNIQUE_ERROR)
        id_ingredients = []
        for ingredient in attrs['ingredients']:
            id_ingredients.append(ingredient['id'])
        if len(id_ingredients) > len(set(id_ingredients)):
            raise serializers.ValidationError(INGREDIENTS_UNIQUE_ERROR)
        return attrs

    def add_ingredients_and_tags(self, instance, validated_data):
        ingredients, tags = (
            validated_data.pop('ingredients'), validated_data.pop('tags')
        )
        new_ingredients = [
            CountOfIngredient(
                ingredient=get_object_or_404(Ingredient, pk=ingredient['id']),
                amount=ingredient['amount'],
                recipe=instance
            )
            for ingredient in ingredients
        ]
        CountOfIngredient.objects.bulk_create(new_ingredients)
        for tag in tags:
            instance.tags.add(tag)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def create(self, validated_data):
        saved = {}
        saved['ingredients'] = validated_data.pop('ingredients')
        saved['tags'] = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        return self.add_ingredients_and_tags(recipe, saved)

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        instance = self.add_ingredients_and_tags(instance, validated_data)
        return super().update(instance, validated_data)


class RecipeFollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения данных о рецепте
    """
    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time',
        )


class FavoriteSerializer(UserDetailSerializer):
    """
    Сериализатор для добавления рецепта в избранное
    """
    user = serializers.ReadOnlyField(source='user.id')
    recipe = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = self.context.get('request').parser_context['kwargs']['pk']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                        'Данный рецепт уже добавлен в избранное!')
        return Favorite.objects.create(user=user, recipe=recipe)


class ShoppingCartSerializer(UserDetailSerializer):
    """
    Сериализатор для добавления рецепта в избранное
    """
    user = serializers.ReadOnlyField(source='user.id')
    recipe = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = self.context.get('request').parser_context['kwargs']['pk']
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                        'Данный рецепт уже добавлен в список покупок!')
        return ShoppingCart.objects.create(user=user, recipe=recipe)
