from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PostFormTests.guest_client = Client()

    def test_signup_create_new_user(self):
        """Валидная форма создает нового пользователя."""
        # регистрируем нового пользователя
        form_data = {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, что появился новый пользователь
        self.assertTrue(
            User.objects.filter(username=form_data['username']).exists()
        )
