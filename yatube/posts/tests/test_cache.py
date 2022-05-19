from django.core.cache import cache
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy


from posts.models import Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def test_cache(self):
        request1 = self.client.get(reverse_lazy('posts:index'))
        PostTests.post.delete()
        request2 = self.client.get(reverse_lazy('posts:index'))
        self.assertHTMLEqual(
            str(request1.content),
            str(request2.content),
            'Ошибка кэширования'
        )
        cache.clear()
        request3 = self.client.get(reverse_lazy('posts:index'))
        self.assertHTMLNotEqual(
            str(request1.content),
            str(request3.content),
            'Ошибка кэширования'
        )
