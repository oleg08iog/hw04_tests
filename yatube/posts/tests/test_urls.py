from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.user_not_author = User.objects.create(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)

    # Проверяем общедоступные страницы
    def test_urls_exist_at_desired_locations(self):
        """Проверка доступности и использования правильных шаблонов."""
        urls_status = {
            '/': HTTPStatus.OK,
            '/group/slug/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK
        }
        for url, expected_status in urls_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, expected_status)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_post_create_url_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страницы только для автора поста
    def test_post_edit_url_accessible_to_author(self):
        """Страница /posts/post_id/edit доступна автору поста."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_inaccessible_to_not_author(self):
        """Страница /posts/post_id/edit не доступна не автору поста."""
        response = self.not_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # Проверяем редиректы для неавторизованного пользователя
    def test_redirect_anonymous_on_auth_login(self):
        """Страница перенаправит анонимного пользователя
        на страницу логина.
        """
        urls_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/':
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
        }
        for url, expected_redirect in urls_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, expected_redirect)

    # Запрос к несуществующей странице
    def test_unexisting_page_url_not_existed(self):
        """Страница /unexisting_page/ вернет ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
