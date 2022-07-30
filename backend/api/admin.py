from django.contrib import admin

from .models import Ingredients, Recipe, Tag


class IngredientAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'color',
        'slug',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'author',
    )
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'

    def count_favorites(self, obj):
        return obj.favorites.count()


admin.site.register(Ingredients, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
