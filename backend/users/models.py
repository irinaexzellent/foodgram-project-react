from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

ADMIN = 'admin'
USER = 'user'


class CustomUserManager(UserManager):

    def get_by_natural_key(self, username):
        return self.get(
            Q(**{self.model.USERNAME_FIELD: username}) |
            Q(**{self.model.EMAIL_FIELD: username})
        )


class User(AbstractUser):
    """
    Модель для хранения пользователей
    Ключевые аргументы:
    email -- электронная почта,
    password -- пароль
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        null=False)
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    password = models.TextField('password', max_length=150)
    first_name = models.CharField(
        'Имя пользователя', max_length=150, blank=True
    )
    last_name = models.CharField(
        'Фамилия пользователя', max_length=150, blank=True
    )
    is_superuser = models.BooleanField('Администратор', default=False)
    is_blocked = models.BooleanField('Заблокирован', default=False)

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.email


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Follow(models.Model):
    """Модель для хранения связей между авторами и
    подписчиками
    Ключевые аргументы:
    user -- ссылка на объект пользователя, который подписывается,
    author -- ссылка на объект пользователя, на которого подписываются
    """
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE)
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique follow',
            )
        ]

    def __str__(self):
        return f"Подписчик: '{self.user}', автор: '{self.author}'"
