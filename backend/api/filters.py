from django.db.models import IntegerField, Value
from django_filters.rest_framework import (
    AllValuesMultipleFilter,
    BooleanFilter,
    CharFilter,
    FilterSet
)

from api.models import Ingredient, Recipe


class IngredientSearchFilter(FilterSet):
    name = CharFilter(method='search_by_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def search_by_name(self, queryset, name, value):
        if not value:
            return queryset
        start_with_queryset = (
            queryset.filter(name__istartswith=value).annotate(
                order=Value(0, IntegerField())
            )
        )
        contain_queryset = (
            queryset.filter(name__icontains=value).exclude(
                pk__in=(ingredient.pk for ingredient in start_with_queryset)
            ).annotate(
                order=Value(1, IntegerField())
            )
        )
        return start_with_queryset.union(contain_queryset).order_by('order')


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    author = CharFilter(lookup_expr='exact')
    is_in_shopping_cart = BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = BooleanFilter(method='get_is_favorited')

    def get_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        favorites = self.request.user.favorites.all()
        return queryset.filter(
            pk__in=(favorite.recipe.pk for favorite in favorites)
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset.all()

    class Meta:
        model = Recipe
        fields = ['author', 'is_in_shopping_cart']
