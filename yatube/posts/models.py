from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Group(models.Model):
    title = models.CharField(_("Название"), max_length=200)
    slug = models.SlugField(_("Слаг"), max_length=100, unique=True)
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

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = _("Пост")
        verbose_name_plural = _("Посты")

    def __str__(self) -> str:
        return self.text[0:30]
