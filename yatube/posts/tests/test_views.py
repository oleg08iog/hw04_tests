from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User

from yatube.settings import POSTS_PER_PAGE

PAGE_2_POSTS = 3
USERNAME = 'author'
SLUG = 'test-slug'
SLUG2 = 'test-slug-2'

HOME_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
GROUP2_LIST_URL = reverse('posts:group_list', args=[SLUG2])
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
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для 1 группы',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls = {
            HOME_URL: 'page_obj',
            GROUP_LIST_URL: 'page_obj',
            PROFILE_URL: 'page_obj',
            self.POST_DETAIL_URL: 'post',
        }

        for url, expected_context in urls.items():
            with self.subTest(url):
                if expected_context == 'page_obj':
                    self.assertEqual(
                        len(self.guest_client.get(url).context['page_obj']), 1
                    )
                    post = self.guest_client.get(url).context['page_obj'][0]
                else:
                    post = self.guest_client.get(url).context['post']
                    self.assertEqual(post.id, self.post.id)
                    self.assertEqual(post.text, self.post.text)
                    self.assertEqual(post.author, self.post.author)
                    self.assertEqual(post.group, self.post.group)

    def test_post_own_only_one_group(self):
        """Проверяем, что пост не появляется на странице второй группы"""
        response = self.client.get(GROUP2_LIST_URL)
        self.assertNotIn(Post.objects.get(id=self.post.id),
                         response.context['page_obj'])

    def test_author_and_group_on_self_pages(self):
        """Проверяем, что автор и группа находятся на своих страницах"""
        test_cases = [
            (PROFILE_URL, self.user.username),
            (GROUP_LIST_URL, self.group.title)
        ]
        for url, value in test_cases:
            with self.subTest(url):
                self.assertContains(self.client.get(url), value)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create(username='author')
        cls.post = Post.objects.bulk_create([
            Post(author=cls.user,
                 text=f'Тестовый пост {i}',
                 group=cls.group)
            for i in range(POSTS_PER_PAGE + PAGE_2_POSTS)
        ])

    def setUp(self):
        self.guest_client = Client()

    def test_pagination_page_1_and_page_2(self):
        """Пагинатор работает правильно на 1 и 2 странице шаблона"""
        test_cases = [
            {'url': HOME_URL,
             'page_1': POSTS_PER_PAGE,
             'page_2': PAGE_2_POSTS,
             },
            {'url': PROFILE_URL,
             'page_1': POSTS_PER_PAGE,
             'page_2': PAGE_2_POSTS,
             },
            {'url': GROUP_LIST_URL,
             'page_1': POSTS_PER_PAGE,
             'page_2': PAGE_2_POSTS,
             },
        ]

        for test_case in test_cases:
            with self.subTest():
                response = self.guest_client.get(test_case['url'])
                self.assertEqual(len(response.context['page_obj']),
                                 test_case['page_1'])
                response = self.guest_client.get(test_case['url'] + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 test_case['page_2'])
