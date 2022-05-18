from http import HTTPStatus
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


class CreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            group=cls.group,
            author=User.objects.create(username='author'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CreateFormTest.post.author)

    def test_create_post(self):
        """Форма создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
            'group': CreateFormTest.group.id,
            'image': UPLOADED
        }
        response = self.authorized_client.post(
            reverse_lazy('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = response.context['page_obj'][0]
        self.assertRedirects(
            response,
            reverse_lazy(
                'posts:profile',
                kwargs={'username': CreateFormTest.post.author}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertIsNotNone(last_post.image, form_data['image'])

    def test_edit_post_changed(self):
        """Пост меняется"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': CreateFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse_lazy(
                'posts:post_edit',
                kwargs={'post_id': CreateFormTest.post.id}
            ),
            data=form_data,
            follow=True,
        )
        post = response.context['post']
        self.assertRedirects(
            response,
            reverse_lazy(
                'posts:post_detail',
                kwargs={'post_id': CreateFormTest.post.id}
            )
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post(self):
        """Форма создает комментарий."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'ого, классный пост!',
            'author': CreateFormTest.user.username,
            'post': CreateFormTest.post.id
        }
        response = self.authorized_client.post(
            reverse_lazy(
                'posts:add_comment',
                kwargs={'post_id': CreateFormTest.post.id}
            ),
            data=form_data,
            follow=True
        )
        last_comment = response.context['comments'].order_by('-pub_date')[0]
        self.assertRedirects(
            response,
            reverse_lazy(
                'posts:post_detail',
                kwargs={'post_id': CreateFormTest.post.pk}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.post.id, form_data['post'])
        self.assertIsNotNone(last_comment.author, form_data['author'])

    def test_guest_client_cant_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'ого-гооо',
            'author': CreateFormTest.user.username
        }
        self.client.post(
            reverse_lazy(
                'posts:add_comment',
                kwargs={'post_id': CreateFormTest.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
