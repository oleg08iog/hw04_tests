from django.test import TestCase
from django.urls import reverse

USERNAME = 'author'
SLUG = 'test-slug'
POST_ID = 1
ROUTE_URLS = [
    ('/', 'index', []),
    (f'/group/{SLUG}/', 'group_list', [SLUG]),
    (f'/profile/{USERNAME}/', 'profile', [USERNAME]),
    (f'/posts/{POST_ID}/', 'post_detail', [POST_ID]),
    (f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]),
    ('/create/', 'post_create', []),
]


class RouteTests(TestCase):
    def test_route_calculations(self):
        """Расчеты дают ожидаемые URL-адреса"""
        for address, route, args in ROUTE_URLS:
            with self.subTest(route):
                self.assertEqual(
                    address,
                    reverse(f'posts:{route}', args=args)
                )
