from django.db import models
from django.contrib.auth import get_user_model

from posts.constants import N_SYMBOLS_TO_SHOW

User = get_user_model()


class Post(models.Model):
    """Модель поста сайта."""

    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:

        ordering = ('-pub_date',)
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.text[:N_SYMBOLS_TO_SHOW]


class Comment(models.Model):
    """Модель коментариев к постам"""

    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ('-created',)
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'


class Group(models.Model):
    """Модель группы на сайте."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:

        verbose_name = 'Group'
        verbose_name_plural = 'Groups'

    def __str__(self):
        return self.title


class Follow(models.Model):
    """Модель подписок на авторов"""

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:

        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'
