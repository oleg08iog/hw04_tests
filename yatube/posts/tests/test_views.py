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
            slug=SLUG2,
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
            context = self.guest_client.get(url).context
            with self.subTest(url):
                if expected_context == 'page_obj':
                    self.assertEqual(len(context['page_obj']), 1)
                    post = context['page_obj'][0]
                else:
                    post = context['post']
                    self.assertEqual(post.id, self.post.id)
                    self.assertEqual(post.text, self.post.text)
                    self.assertEqual(post.author, self.post.author)
                    self.assertEqual(post.group, self.post.group)

    def test_post_own_only_one_group(self):
        """Проверяем, что пост не появляется на странице второй группы"""
        response = self.client.get(GROUP2_LIST_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_author_on_profile_page(self):
        """Проверяем, что автор находится на своей странице профиля"""
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.context['author'], self.user)

    def test_group_details(self):
        """Проверяем, что все поля группы отображаются корректно"""
        response = self.client.get(GROUP_LIST_URL)
        self.assertEqual(
            response.context['group'].title, self.group.title
        )
        self.assertEqual(
            response.context['group'].description, self.group.description
        )
        self.assertEqual(
            response.context['group'].slug, self.group.slug
        )


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
        cls.post = Post.objects.bulk_create(
            Post(author=cls.user,
                 text=f'Тестовый пост {i}',
                 group=cls.group)
            for i in range(POSTS_PER_PAGE + PAGE_2_POSTS)
        )

    def setUp(self):
        self.guest_client = Client()

    def test_pagination_page_1_and_page_2(self):
        """Пагинатор работает правильно на 1 и 2 странице шаблона"""
        test_cases = [
            (HOME_URL, POSTS_PER_PAGE, PAGE_2_POSTS),
            (PROFILE_URL, POSTS_PER_PAGE, PAGE_2_POSTS),
            (GROUP_LIST_URL, POSTS_PER_PAGE, PAGE_2_POSTS),
        ]
        for url, page_1, page_2 in test_cases:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(len(response.context['page_obj']), page_1)
                response = self.guest_client.get(f"{url}?page=2")
                self.assertEqual(len(response.context['page_obj']), page_2)
