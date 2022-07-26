from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

INGREDIENT_MIN_AMOUNT_ERROR = (
    'Количество ингредиентов не может быть меньше {min_value}!'
)
INGREDIENT_MIN_AMOUNT = 1


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField('название', max_length=250)
    measurement_unit = models.CharField('единица измерения', max_length=20)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тэгов"""
    name = models.CharField('Название', max_length=200)
    color = models.CharField('Цвет в HEX', max_length=7)
    slug = models.SlugField('Слаг', max_length=200)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    """Модель рецептов"""
    ingredients = models.ManyToManyField(
        'Ingredient',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    image = models.ImageField('Картинка')
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipes',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pk',)


class CountOfIngredient(models.Model):
    """Модель количества ингредиентов"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='count_in_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        'Количество', validators=(MinValueValidator(
            INGREDIENT_MIN_AMOUNT,
            message=INGREDIENT_MIN_AMOUNT_ERROR.format(
                min_value=INGREDIENT_MIN_AMOUNT)),
        )
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_amounts',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'


class Favorite(models.Model):
    """
    Модель для хранения связей между рецептами и
    авторми
    Ключевые аргументы:
    user -- ссылка на объект пользователя, который подписывается,
    recipe -- ссылка на объект рецепта, на который подписываются
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user',),
                name='unique_recipes_user',
            ),
        )

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    """
    Модель для хранения связей между рецептами в списке покупок и
    пользователями
    Ключевые аргументы:
    user -- ссылка на объект пользователя,
    recipe -- ссылка на объект рецепта
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping_carts', verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='shopping_carts', verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
