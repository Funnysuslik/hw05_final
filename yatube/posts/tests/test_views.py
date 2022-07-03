from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.constants import MAX_POSTS_ON_PAGE

User = get_user_model()


class PostsTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.test_group = Group.objects.create(
            title='Test',
            slug='test_group',
            description='Test group',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.test_group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsTemplatesTests.user)

    def test_pages_uses_correct_template(self):
        """Тест на правильность использования html шаблонов"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_group'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'TestUser'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PostsContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.test_group = Group.objects.create(
            title='Test',
            slug='test_group',
            description='Test group',
        )
        cls.EXTRA_POSTS = 5
        for i in range(MAX_POSTS_ON_PAGE + PostsContextTests.EXTRA_POSTS):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.user,
                group=cls.test_group,
            )
        cls.last_post = Post.objects.get(pk=(cls.EXTRA_POSTS
                                             + MAX_POSTS_ON_PAGE))

    def setUp(self):
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsContextTests.user)

    def assert_context_check(self, object):
        self.assertEqual(object.text, PostsContextTests.last_post.text)
        self.assertEqual(object.author.username,
                         PostsContextTests.last_post.author.username)
        self.assertEqual(object.group.title,
                         PostsContextTests.last_post.group.title)

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_page_have_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': 1}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_have_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest.get(reverse('posts:post_detail',
                                          kwargs={'post_id': 15}))
        post = response.context.get('post')
        self.assert_context_check(post)

    def test_index_page_have_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.guest.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)

    def test_index_paginator_working(self):
        """Проверка работы пагинатора index"""
        cache.clear()
        response = self.guest.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.guest.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PostsContextTests.EXTRA_POSTS)

    def test_group_list_have_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest.get(reverse('posts:group_list',
                                          kwargs={'slug': 'test_group'}))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)
        group = response.context['group']
        self.assertEqual(group.title, PostsContextTests.test_group.title)
        self.assertEqual(group.description,
                         PostsContextTests.test_group.description)
        self.assertEqual(group.slug, PostsContextTests.test_group.slug)

    def test_group_list_paginator_working(self):
        """Проверка работы пагинатора group_list"""
        response = self.guest.get(reverse('posts:group_list',
                                          kwargs={'slug': 'test_group'}))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.guest.get(reverse('posts:group_list',
                                          kwargs={'slug': 'test_group'})
                                  + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PostsContextTests.EXTRA_POSTS)

    def test_profile_have_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'}))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)
        author = response.context['author']
        self.assertEqual(author.username, PostsContextTests.user.username)
        self.assertEqual(author.pk, PostsContextTests.user.pk)

    def test_profile_paginator_working(self):
        """Проверка работы пагинатора profile"""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'}))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'})
                                              + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PostsContextTests.EXTRA_POSTS)

    def test_work_of_cache(self):
        """Проверка работы кэширования.
        При удалении поста, он не пропадает со страницы
        до обновления кэша"""
        cache.clear()
        test_post = Post.objects.create(text='Тестовый текст для кэша',
                                        author=PostsContextTests.user,
                                        group=PostsContextTests.test_group,)
        response = self.guest.get(reverse('posts:index'))
        self.assertContains(response, test_post.text)
        Post.objects.filter(pk=15).delete()
        response = self.guest.get(reverse('posts:index'))
        self.assertContains(response, test_post.text)


class PostsNewPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.test_group = Group.objects.create(
            title='Test',
            slug='test_group',
            description='Test group',
        )
        cls.fake_group = Group.objects.create(
            title='Fake',
            slug='fake_group',
            description='Test fake group',
        )
        Post.objects.create(
            text='Фейковый пост текст',
            author=cls.user,
            group=cls.fake_group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsContextTests.user)

    def test_new_post_with_group(self):
        """Пост с группой появляется:
           на главной странице сайта,df
           на странице выбранной группы,
           в профайле пользователя,"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=PostsContextTests.user,
                                        group=PostsContextTests.test_group,)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_group'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'TestUser'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

    def test_new_post_dont_appear_in_other_group(self):
        """Пост с группой не появляется на странице другой группы"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=PostsContextTests.user,
                                        group=PostsContextTests.test_group,)
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'fake_group'}))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.pk, test_post.pk)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.fake_author = User.objects.create_user(username='FakeAuthor')
        Post.objects.create(
            text='Тестовый пост автора',
            author=cls.author,
        )
        Post.objects.create(
            text='Тестовый пост лишнего автора',
            author=cls.fake_author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTests.user)

    def test_user_can_follow(self):
        """Проверка на возможность подписаться и отписаться на авторов"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'TestAuthor'}))
        self.assertTrue(Follow.objects.filter(
            user=FollowTests.user, author=FollowTests.author).exists())
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': 'TestAuthor'}))
        self.assertFalse(Follow.objects.filter(
            user=FollowTests.user, author=FollowTests.author).exists())

    def test_user_cant_follow_himself(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'TestUser'}))
        self.assertFalse(Follow.objects.filter(
            user=FollowTests.user, author=FollowTests.author).exists())
