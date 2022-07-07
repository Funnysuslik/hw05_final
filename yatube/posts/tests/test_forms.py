import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.test_group = Group.objects.create(
            title='Test',
            slug='test_group',
            description='Test group',
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.test_group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_can_post(self):
        """Проверка возможности создания поста авторизованным пользователем"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст из формы',
            'group': self.test_group.pk,
            'image': uploaded,
        }
        self.assertTrue(PostForm(data=form_data).is_valid)
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

        response = self.client.get(reverse('posts:index'))
        new_post = Post.objects.first()
        post_data = {
            new_post.text: form_data['text'],
            new_post.group: self.test_group,
            new_post.author: self.user,
            new_post.image: 'posts/small.gif',
        }
        for data, exp_data in post_data.items():
            with self.subTest(data=data):
                self.assertEqual(data, exp_data)

    def test_guest_cant_post(self):
        """Проверка возможности создания поста гостевым пользователем"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст гостя из формы',
            'group': self.test_group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('users:login')
                             + '?next=/create/')
        self.assertEqual(Post.objects.count(), tasks_count)

    def test_author_can_edit_post(self):
        """При отправке автором валидной формы со страницы
           редактирования поста происходит изменение поста в базе данных"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы был изменён',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.test_post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post.pk}))
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertEqual(
            Post.objects.get(pk=1).text, form_data['text'])

    def test_new_comment_in_post_detail(self):
        """"Проверка появления новых коментариев
        авторизованных пользователей"""
        form_data = {
            'text': 'New comment',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.test_post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.test_post.pk}))
        self.assertEqual(
            Comment.objects.first().text, form_data['text']
        )

    def test_guests_cant_comment(self):
        """Проверка невозможности комментировать
        не авторизовавшись"""
        form_data = {
            'text': 'Shoudnt appear'
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.test_post.pk}),
            data=form_data,
        )
        self.assertIsNone(Comment.objects.first())
