import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

USERNAME = 'author'
SLUG = 'test-slug'

HOME_URL = reverse('posts:index')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
POST_CREATE_URL = reverse('posts:post_create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись поста."""
        test_posts = set(Post.objects.all())
        form_data = {
            'text': 'Текст для теста 1',
            'group': self.group.id,
            'image': self.uploaded,
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
        self.assertEqual(post.image, f"posts/{form_data['image']}")
        self.assertEqual(post.author, self.post.author)
        self.assertRedirects(response, PROFILE_URL)

    def test_post_edit(self):
        """Валидная форма редактирует запись поста."""
        form_data = {
            'text': 'Другой текст для теста 2',
            'group': self.group2.id,
            'image': SimpleUploadedFile(
                name='big.gif',
                content=self.small_gif,
                content_type='image/gif'
            )
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
        self.assertEqual(post.image, f"posts/{form_data['image']}")
        self.assertEqual(post.author, self.user)

    def test_add_comment_on_post_detail_page(self):
        """Валидная форма создает запись комментария."""
        form_data = {
            'text': 'Комментарий под постом',
            'post': self.post.id
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comment = Comment.objects.get(post=self.post.id)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post.id, self.post.id)
        self.assertEqual(comment.author, self.user)

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
