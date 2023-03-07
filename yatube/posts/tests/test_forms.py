from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        # Авторизуем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись поста."""
        # Подсчитаем количество постов
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(text='Тестовый текст').exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись поста."""
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=(self.post.id,)))

        # Проверяем, что запись сохранилась с тем же id
        self.assertTrue(
            Post.objects.get(id=self.post.id, text='Тестовый текст'))

    def test_signup_create_new_user(self):
        """Валидная форма создает нового пользователя."""
        # регистрируем нового пользователя
        form_data = {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index',))
        # Проверяем, что появился новый пользователь
        self.assertTrue(
            User.objects.filter(username='testuser').exists()
        )

    def test_labels_and_help_text(self):
        """Проверяем labels и help_text формы"""
        field_tests = [
            ('text', 'Текст поста', 'Текст нового поста'),
            ('group', 'Группа', 'Группа, к которой будет относится новый пост')
        ]

        for field_name, expected_label, expected_help_text in field_tests:
            with self.subTest(field_name=field_name):
                field = PostFormTests.form.fields[field_name]
                self.assertEqual(field.label, expected_label)
                self.assertEqual(field.help_text, expected_help_text)
