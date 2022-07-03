from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()


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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFormsTests.user)

    def test_authorized_can_post(self):
        """Проверка возможности создания поста авторизованным пользователем"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст из формы',
            'group': self.test_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'TestUser'}))
        self.assertEqual(Post.objects.count(), tasks_count + 1)

        response = self.client.get(reverse('posts:index'))
        new_post = response.context['page_obj'][0]

        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.title,
                         PostsFormsTests.test_group.title)
        self.assertEqual(new_post.author.username,
                         PostsFormsTests.user.username)

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
            follow=True
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
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_new_comment_in_post_detail(self):
        """"Проверка появления новых коментариев"""
        form_data = {
            'text': 'New comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists()
        )
