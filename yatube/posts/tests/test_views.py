from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

from yatube.settings import POSTS_PER_PAGE

PAGE_2_POSTS = 3
USERNAME = 'author'
SLUG = 'test-slug'
SLUG2 = 'test-slug-2'

HOME_URL = reverse('posts:index')
HOME_URL_2_PAGE = f'{HOME_URL}?page=2'
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
GROUP_LIST_URL_2_PAGE = f'{GROUP_LIST_URL}?page=2'
GROUP2_LIST_URL = reverse('posts:group_list', args=[SLUG2])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
PROFILE_URL_2_PAGE = f'{PROFILE_URL}?page=2'
POST_CREATE_URL = reverse('posts:post_create')


class PostURLTests(TestCase):
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

    def test_post_not_in_another_group(self):
        """Проверяем, что пост не появляется на странице другой группы"""
        response = self.client.get(GROUP2_LIST_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_author_on_profile_page(self):
        """Проверяем, что автор находится на своей странице профиля"""
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.context['author'], self.user)

    def test_group_details(self):
        """Проверяем, что все поля группы отображаются корректно"""
        response = self.client.get(GROUP_LIST_URL)
        group = response.context['group']
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)

    def test_pagination_page_1_and_page_2(self):
        """Пагинатор работает правильно на 1 и 2 странице шаблона"""
        Post.objects.all().delete()
        self.post = Post.objects.bulk_create(
            Post(author=self.user,
                 text=f'Тестовый пост {i}',
                 group=self.group)
            for i in range(POSTS_PER_PAGE + PAGE_2_POSTS)
        )
        test_cases = {
            HOME_URL: POSTS_PER_PAGE,
            HOME_URL_2_PAGE: PAGE_2_POSTS,
            PROFILE_URL: POSTS_PER_PAGE,
            PROFILE_URL_2_PAGE: PAGE_2_POSTS,
            GROUP_LIST_URL: POSTS_PER_PAGE,
            GROUP_LIST_URL_2_PAGE: PAGE_2_POSTS,
        }
        for url, page_posts in test_cases.items():
            with self.subTest(url):
                self.assertEqual(
                    len(self.guest_client.get(url).context['page_obj']),
                    page_posts
                )
