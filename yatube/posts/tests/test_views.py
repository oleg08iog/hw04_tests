from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
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
        )

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name вызывается соответствующий HTML
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        test_object = response.context.get('page_obj').object_list
        expected = list(Post.objects.all())
        self.assertEqual(test_object, expected)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        test_object = response.context.get('page_obj').object_list
        expected = self.group.posts.all()
        self.assertQuerysetEqual(test_object, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        )
        test_object = response.context.get('page_obj').object_list
        expected = list(Post.objects.filter(author=self.user))
        self.assertEqual(test_object, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        test_object = response.context.get('post')
        expected = Post.objects.get(pk=self.post.id)
        self.assertEqual(test_object, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id})
        )
        form_instance = response.context.get('form').instance.id
        self.assertEqual(form_instance, self.post.id)
        self.assertEqual(response.context['post'], self.post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_instance = response.context.get('form')
        self.assertIsInstance(form_instance, PostForm)

    def test_post_create_with_group(self):
        """При создании поста указываем группу"""
        # Отправляем POST-запрос на создание поста
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={
                'text': 'Test post text',
                'group': self.group.id,
            }
        )

        # Проверяем, что пост создан успешно
        post = Post.objects.first()
        self.assertEqual(post.text, 'Test post text')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)

        # Проверяем, что пост появляется на главной странице
        response = self.client.get(reverse('posts:index'))
        self.assertIn(post, response.context['page_obj'])

        # Проверяем, что пост появляется на странице группы
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIn(post, response.context['page_obj'])

        # Проверяем, что пост появляется в профиле пользователя
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertIn(post, response.context['page_obj'])

        # Проверяем, что пост не появляется на странице второй группы
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug})
        )
        self.assertNotIn(post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
            )

    def setUp(self):
        # Создаем авторизованный клиент
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Первая страница отображает 10 постов."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Вторая страница отображает 3 поста."""
        response = self.guest_client.get(reverse('posts:index')
                                         + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
