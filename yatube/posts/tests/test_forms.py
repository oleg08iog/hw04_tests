from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

USERNAME = 'author'
SLUG = 'test-slug'

HOME_URL = reverse('posts:index')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
POST_CREATE_URL = reverse('posts:post_create')


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        # Авторизуем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись поста."""
        test_posts = set(Post.objects.all())
        form_data = {
            'text': 'Текст для теста 1',
            'group': self.group.id,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        created_post = set(Post.objects.all()) - test_posts
        self.assertEqual(len(created_post), 1)
        post = created_post.pop()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertRedirects(response, PROFILE_URL)

    def test_post_edit(self):
        """Валидная форма редактирует запись поста."""
        form_data = {
            'text': 'Другой текст для теста 2',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)

    def test_labels_and_help_text(self):
        """Проверяем labels и help_text формы"""
        form = PostForm()
        field_tests = [
            ('text', 'Текст поста', 'Текст нового поста', forms.CharField),
            ('group', 'Группа', 'Группа, к которой будет относится новый пост',
             forms.ModelChoiceField)
        ]

        for field_name, label, help_text, form_type in field_tests:
            with self.subTest(field_name=field_name):
                field = form.fields[field_name]
                self.assertEqual(field.label, label)
                self.assertEqual(field.help_text, help_text)
                self.assertEqual(type(field), form_type)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL)
        form_instance = response.context.get('form')
        self.assertIsInstance(form_instance, PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_EDIT_URL)
        form_instance = response.context.get('form').instance.id
        self.assertEqual(form_instance, self.post.id)
        self.assertIsInstance(response.context['post'], Post)
