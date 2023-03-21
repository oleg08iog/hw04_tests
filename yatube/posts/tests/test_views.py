import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

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
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_INDEX__URL_2_PAGE = f'{FOLLOW_INDEX_URL}?page=2'
FOLLOW_PROFILE_URL = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW_PROFILE_URL = reverse('posts:profile_unfollow', args=[USERNAME])

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для 1 группы',
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(self.user)
        self.another = Client()
        self.another.force_login(self.user_not_author)
        self.another.get(FOLLOW_PROFILE_URL)

    def test_cache_index_page(self):
        """Проверяем кеширования главной страницы"""
        response = self.client.get(HOME_URL)
        cache_check = response.content
        Post.objects.all().delete()
        response_old = self.client.get(HOME_URL)
        cache_old_check = response_old.content
        self.assertEqual(cache_old_check, cache_check)
        cache.clear()
        response_new = self.client.get(HOME_URL)
        cache_new_check = response_new.content
        self.assertNotEqual(cache_old_check, cache_new_check)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls = {
            HOME_URL: 'page_obj',
            FOLLOW_INDEX_URL: 'page_obj',
            GROUP_LIST_URL: 'page_obj',
            PROFILE_URL: 'page_obj',
            self.POST_DETAIL_URL: 'post',
        }

        for url, expected_context in urls.items():
            context = self.another.get(url).context
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
                self.assertEqual(post.image, self.post.image)

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
            FOLLOW_INDEX_URL: POSTS_PER_PAGE,
            FOLLOW_INDEX__URL_2_PAGE: PAGE_2_POSTS,
        }
        for url, page_posts in test_cases.items():
            with self.subTest(url):
                self.assertEqual(
                    len(self.another.get(url).context['page_obj']),
                    page_posts
                )

    def test_authorized_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других авторов и удалять их из подписок."""
        self.another.get(FOLLOW_PROFILE_URL)
        self.assertEqual(Follow.objects.count(), 1)
        self.another.get(UNFOLLOW_PROFILE_URL)
        self.assertEqual(Follow.objects.count(), 0)

    def test_post_not_in_follow_index_who_not_subscribe(self):
        """Проверяем, что пост автора не появляется
        в ленте тех, кто на него не подписан"""
        self.another.get(UNFOLLOW_PROFILE_URL)
        response = self.another.get(FOLLOW_INDEX_URL)
        self.assertNotIn(self.post, response.context['page_obj'])
