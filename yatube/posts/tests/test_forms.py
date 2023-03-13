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
        cls.form = PostForm()
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        # Авторизуем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись поста."""
        # Подсчитаем количество постов
        test_posts = set(Post.objects.all())
        form_data = {
            'text': 'Текст для теста 1',
            'group': self.group.id,
            'author': self.user
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        created_post = list(set(Post.objects.all()) - test_posts)
        post = created_post[-1]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, form_data['author'])
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(len(created_post), 1)

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
        update_post = Post.objects.get(id=self.post.id)
        self.assertEqual(update_post.text, form_data['text'])
        self.assertEqual(update_post.group.id, form_data['group'])

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

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL)
        form_instance = response.context.get('form')
        self.assertIsInstance(form_instance, PostForm)
