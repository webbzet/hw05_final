import time

from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test')

    def test_cashe(self):
        request1 = self.client.get('/')
        Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        time.sleep(1)
        request2 = self.client.get('/')
        self.assertHTMLEqual(
            str(request1.content),
            str(request2.content),
            'Ошибка кэширования'
        )
