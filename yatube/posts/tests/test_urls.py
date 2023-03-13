from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User

USERNAME = 'author'
SLUG = 'test-slug'

HOME_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
POST_CREATE_URL = reverse('posts:post_create')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.user_not_author = User.objects.create(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)

    # Проверяем доступность страниц для разных пользователей
    def test_urls_exist_at_desired_locations(self):
        """Проверка доступности и использования правильных шаблонов
        для всех типов пользователей."""
        test_cases = [
            (HOME_URL, self.guest_client, HTTPStatus.OK),
            (GROUP_LIST_URL, self.guest_client, HTTPStatus.OK),
            (PROFILE_URL, self.guest_client, HTTPStatus.OK),
            (self.POST_DETAIL_URL, self.guest_client, HTTPStatus.OK),
            (POST_CREATE_URL, self.authorized_client, HTTPStatus.OK),
            (self.POST_EDIT_URL, self.authorized_client, HTTPStatus.OK),
            (self.POST_EDIT_URL, self.not_author_client, HTTPStatus.FOUND),
            ('/unexisting_page/', self.guest_client, HTTPStatus.NOT_FOUND),
        ]
        for url, client, expected_status_code in test_cases:
            with self.subTest(url=url):
                self.assertEqual(
                    client.get(url).status_code,
                    expected_status_code
                )

    # Проверяем редиректы для неавторизованного пользователя
    def test_redirect_anonymous_on_auth_login(self):
        """Страница перенаправит анонимного пользователя"""
        urls_redirect = [
            (POST_CREATE_URL, self.guest_client,
             reverse('users:login') + '?next=' + POST_CREATE_URL),
            (self.POST_EDIT_URL, self.guest_client,
             reverse('users:login') + '?next=' + self.POST_EDIT_URL),
            (self.POST_EDIT_URL, self.not_author_client,
             self.POST_DETAIL_URL)
        ]
        for url, client, expected_redirect in urls_redirect:
            with self.subTest(url=url):
                self.assertRedirects(
                    client.get(url, follow=True),
                    expected_redirect
                )

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
                self.assertTemplateUsed(
                    self.authorized_client.get(address),
                    template
                )
