from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User

USERNAME = 'author'
SLUG = 'test-slug'

HOME_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
POST_CREATE_URL = reverse('posts:post_create')


class RouteTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
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
        self.client = Client()

    def test_route_calculations(self):
        """Расчеты дают ожидаемые URL-адреса"""
        # Шаблоны по адресам
        test_cases = {
            '/': HOME_URL,
            f'/group/{self.group.slug}/': GROUP_LIST_URL,
            f'/profile/{self.user.username}/': PROFILE_URL,
            f'/posts/{self.post.id}/': self.POST_DETAIL_URL,
            f'/posts/{self.post.id}/edit/': self.POST_EDIT_URL,
            '/create/': POST_CREATE_URL,
        }
        for address, expected_url in test_cases.items():
            with self.subTest(address=address):
                self.assertEqual(address, expected_url)
