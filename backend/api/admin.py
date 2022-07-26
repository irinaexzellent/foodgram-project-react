from django.contrib import admin
from import_export import resources
from import_export.admin import ImportMixin

from .models import Ingredient, Recipe, Tag


class IngredientImportMixin(ImportMixin):
    """
    Import mixin
    """
    from_encoding = 'utf-8'


class IngredientResource(resources.ModelResource):

    class Meta:
        model = Ingredient


class IngredientAdmin(IngredientImportMixin, admin.ModelAdmin):

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


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
