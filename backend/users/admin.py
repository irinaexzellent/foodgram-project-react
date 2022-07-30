from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from users.models import User


@register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name',
        'is_blocked', 'password', 'is_superuser',)
    list_filter = (
        'email', 'username', 'is_blocked', 'is_superuser',
    )
    fieldsets = (
        (None, {'fields': (
            'email', 'username', 'first_name', 'last_name', 'password',
        )}),
        ('Permissions', {'fields': ('is_blocked', 'is_superuser',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name', 'password1',
                'password2', 'is_blocked', 'is_superuser',
            )
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name',)
    ordering = ('id', 'email', 'username',)
