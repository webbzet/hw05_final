import time
import tempfile
import shutil

from django import forms
from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

UPLOADED_GIF = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.author = User.objects.create_user(username='NoNameUser')
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.fake_group = Group.objects.create(
            title='Неправильная группа',
            slug='fake-slug',
            description='Неправильное описание'
        )
        for i in range(1, 12):
            time.sleep(0.001)
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
                image=UPLOADED_GIF,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostsPagesTest.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTest.user)

    def test_pages_template(self):
        """Проверка namespace:name"""
        pages_names = {
            reverse_lazy('posts:index'): 'posts/index.html',
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            ): ('posts/group_list.html'),
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.user.username}
            ): ('posts/profile.html'),
            reverse_lazy(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTest.post.id}
            ): ('posts/create_post.html'),
            reverse_lazy(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTest.post.id}
            ): ('posts/post_detail.html'),
            reverse_lazy('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context(self):
        """Проверяем переданный контекст"""
        pages_names = [
            reverse_lazy('posts:index'),
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            ),
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.user.username}
            )
        ]
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                first_object = response.context['page_obj'][0]
                text_page_obj = first_object.text
                author_page_obj = first_object.author.username
                group_page_obj = first_object.group.title
                image_page_obj = first_object.image
                self.assertEqual(text_page_obj, PostsPagesTest.post.text)
                self.assertEqual(image_page_obj, PostsPagesTest.post.image)
                self.assertEqual(author_page_obj, PostsPagesTest.user.username)
                self.assertEqual(group_page_obj, PostsPagesTest.group.title)
                self.assertEqual(first_object.id, PostsPagesTest.post.id)
                self.assertEqual(
                    first_object.author.id,
                    PostsPagesTest.user.id
                )
                self.assertEqual(
                    first_object.group.id,
                    PostsPagesTest.group.id
                )

    def test_profile_context(self):
        """post_detail context."""
        response = self.client.get(
            reverse_lazy(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTest.post.id}
            )
        )
        post = response.context['post']
        post_object = Post.objects.get(id=PostsPagesTest.post.id)
        self.assertEqual(post, post_object)
        self.assertEqual(post.image, post_object.image)

    def test_post_create_and_edit_context(self):
        """post create and edit form context."""
        pages_names = [
            reverse_lazy('posts:post_create'),
            reverse_lazy(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTest.post.id}
            )
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for adress in pages_names:
            response = self.authorized_client.get(adress)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_urls_first_page_contains_ten_posts(self):
        """Правильная работа первой страницы Paginator"""
        pages_names = [
            reverse_lazy('posts:index'),
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            ),
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.user.username}
            )
        ]
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.MAX_AMOUNT
                )

    def test_urls_second_page_contains_two_posts(self):
        """Правильная работа второй страницы Paginator"""
        pages_names = [
            reverse_lazy('posts:index'),
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            ),
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.user.username}
            )
        ]
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.client.get(adress + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    (Post.objects.count() % settings.MAX_AMOUNT)
                )

    def test_post_create_correct(self):
        """post is displayed on index, group, profile."""
        post = Post.objects.create(
            author=self.user,
            text='прост',
            group=self.group
        )
        pages_names = [
            reverse_lazy('posts:index'),
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            ),
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.user.username}
            )
        ]
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                last_post = response.context['page_obj'][0]
                self.assertEqual(last_post, post)
        response = self.client.get(
            reverse_lazy(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.fake_group.slug}
            ),
        )
        posts = response.context['page_obj'].object_list
        self.assertNotIn(post, posts)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться."""
        followers_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse_lazy(
                'posts:profile_follow',
                kwargs={'username': PostsPagesTest.author}
            )
        )
        self.assertRedirects(
            response,
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.author}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count + 1)

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться."""
        Follow.objects.create(
            user=PostsPagesTest.user,
            author=PostsPagesTest.author,
        )
        followers_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse_lazy(
                'posts:profile_unfollow',
                kwargs={'username': PostsPagesTest.author.username}
            )
        )
        self.assertRedirects(
            response,
            reverse_lazy(
                'posts:profile',
                kwargs={'username': PostsPagesTest.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count - 1)

    def test_new_post_appears(self):
        """Новая запись в ленте подписчиков."""
        posts_count = Post.objects.filter(
            author=PostsPagesTest.author
        ).count()
        Post.objects.create(
            author=PostsPagesTest.author,
            text='Новый пост',
            group=PostsPagesTest.group,
            image=UPLOADED_GIF,
        )
        Follow.objects.create(
            user=PostsPagesTest.user,
            author=PostsPagesTest.author,
        )
        response = self.authorized_client.get(
            reverse_lazy('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), posts_count + 1)

    def test_new_post_doesnt_appear(self):
        """Новая запись в ленте тех, кто не подписан."""
        posts_count = Post.objects.filter(
            author=PostsPagesTest.author
        ).count()
        Post.objects.create(
            author=PostsPagesTest.user,
            text='Тест пост',
            group=PostsPagesTest.group,
            image=UPLOADED_GIF,
        )
        response = self.authorized_client.get(
            reverse_lazy('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), posts_count)
