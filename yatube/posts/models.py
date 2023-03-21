from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Group(models.Model):
    title = models.CharField(_("Название"), max_length=200)
    slug = models.SlugField(
        _("Идентификатор"),
        max_length=50,
        unique=True
    )
    description = models.TextField(_("Описание"))

    class Meta:
        verbose_name = _("Группа")
        verbose_name_plural = _("Группы")

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(_("Текст"))
    pub_date = models.DateTimeField(_("Дата публикации"), auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_("Автор")
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name=_("Группа")
    )
    image = models.ImageField(
        (_("Картинка")),
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = _("Пост")
        verbose_name_plural = _("Посты")

    def __str__(self) -> str:
        return self.text[0:30]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Пост")
    )
    author = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Автор")
    )
    text = models.TextField(max_length=200)
    created = models.DateTimeField(_("Дата публикации"), auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')

    def __str__(self) -> str:
        return self.text[0:30]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_("Подписчик")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_("Автор")
    )

    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
