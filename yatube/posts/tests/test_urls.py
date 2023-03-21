from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

USERNAME = 'author'
SLUG = 'test-slug'

HOME_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
REDIRECT_POST_CREATE = f"{LOGIN_URL}?next={POST_CREATE_URL}"
PAGE_404_URL = '/unexisting_page/'
FOLLOW_INDEX_URL = reverse('posts:follow_index')
REDIRECT_FOLLOW_INDEX_URL = f"{LOGIN_URL}?next={FOLLOW_INDEX_URL}"
PROFILE_URL = reverse('posts:profile', args=[USERNAME])


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
        cls.REDIRECT_POST_EDIT = f"{LOGIN_URL}?next={cls.POST_EDIT_URL}"
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=[cls.post.id])
        cls.REDIRECT_ADD_COMMENT = f"{LOGIN_URL}?next={cls.ADD_COMMENT_URL}"

    def setUp(self):
        cache.clear()
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.user)
        self.another = Client()
        self.another.force_login(self.user_not_author)

    # Проверяем доступность страниц для разных пользователей
    def test_urls_exist_at_desired_locations(self):
        """Проверка доступности и использования правильных шаблонов
        для всех типов пользователей."""
        test_cases = [
            (HOME_URL, self.guest, 200),
            (GROUP_LIST_URL, self.guest, 200),
            (PROFILE_URL, self.guest, 200),
            (self.POST_DETAIL_URL, self.guest, 200),
            (POST_CREATE_URL, self.author, 200),
            (self.POST_EDIT_URL, self.author, 200),
            (self.POST_EDIT_URL, self.another, 302),
            (POST_CREATE_URL, self.guest, 302),
            (self.POST_EDIT_URL, self.guest, 302),
            (self.ADD_COMMENT_URL, self.guest, 302),
            (PAGE_404_URL, self.guest, 404),
            (FOLLOW_INDEX_URL, self.another, 200),
            (FOLLOW_INDEX_URL, self.guest, 302),
        ]
        for url, client, code in test_cases:
            with self.subTest(url=url, code=code):
                self.assertEqual(client.get(url).status_code, code)

    # Проверяем редиректы для неавторизованного пользователя
    def test_redirect_anonymous_on_auth_login(self):
        """Страница перенаправит анонимного пользователя"""
        urls_redirect = [
            (POST_CREATE_URL, self.guest, REDIRECT_POST_CREATE),
            (self.POST_EDIT_URL, self.guest, self.REDIRECT_POST_EDIT),
            (self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL),
            (self.ADD_COMMENT_URL, self.guest, self.REDIRECT_ADD_COMMENT),
            (FOLLOW_INDEX_URL, self.guest, REDIRECT_FOLLOW_INDEX_URL)
        ]
        for url, client, redirect in urls_redirect:
            with self.subTest(url=url, redirect=redirect):
                self.assertRedirects(
                    client.get(url, follow=True), redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            HOME_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
            PAGE_404_URL: 'core/404.html',
            FOLLOW_INDEX_URL: 'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address),
                    template
                )
