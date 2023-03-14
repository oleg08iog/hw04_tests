from django.test import TestCase
from django.urls import reverse

USERNAME = 'author'
SLUG = 'test-slug'
POST_ID = 1


class RouteTests(TestCase):
    def test_route_calculations(self):
        """Расчеты дают ожидаемые URL-адреса"""
        # Шаблоны по адресам
        test_cases = [
            ('/', 'posts:index', []),
            (f'/group/{SLUG}/', 'posts:group_list', [SLUG]),
            (f'/profile/{USERNAME}/', 'posts:profile', [USERNAME]),
            (f'/posts/{POST_ID}/', 'posts:post_detail', [POST_ID]),
            (f'/posts/{POST_ID}/edit/', 'posts:post_edit', [POST_ID]),
            ('/create/', 'posts:post_create', []),
        ]
        for address, routes, args in test_cases:
            with self.subTest(routes):
                self.assertEqual(address, reverse(routes, args=args))
