from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='me')
        cls.user2 = User.objects.create(username='authorized')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='lol',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user2)

    def test_templates(self):
        """Проверяем вызываемые шаблоны"""
        url_template_list = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for url, template in url_template_list.items():
            with self.subTest(template=template):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Проверяем несуществующую страницу"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_pages(self):
        """Проверяем незарегистрированного пользователя"""
        pages_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        ]
        for page in pages_list:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page(self):
        """Проверяем автора"""
        pages_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/'
        ]
        for page in pages_list:
            with self.subTest(page=page):
                response = self.author_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page(self):
        """Проверяем авторизованного пользователя"""
        pages_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            '/create/'
        ]
        for page in pages_list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)
