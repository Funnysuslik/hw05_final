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
        self.authorized_client.force_login(self.user)

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
        for i in range(MAX_POSTS_ON_PAGE + cls.EXTRA_POSTS):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.user,
                group=cls.test_group,
            )
        cls.last_post = Post.objects.first()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def assert_context_check(self, object):
        self.assertEqual(object.text, self.last_post.text)
        self.assertEqual(object.author,
                         self.last_post.author)
        self.assertEqual(object.group,
                         self.last_post.group)

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

    def test_post_edit_have_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': 1}))
        self.assertTrue(response.context['is_edit'])
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
        response = self.client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.last_post.pk}))
        post = response.context.get('post')
        self.assert_context_check(post)

    def test_index_page_have_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)

    def test_index_paginator_working(self):
        """Проверка работы пагинатора index"""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.EXTRA_POSTS)

    def test_group_list_have_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_group'}))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)
        group = response.context['group']
        self.assertEqual(group.title, self.test_group.title)
        self.assertEqual(group.description,
                         self.test_group.description)
        self.assertEqual(group.slug, self.test_group.slug)

    def test_group_list_paginator_working(self):
        """Проверка работы пагинатора group_list"""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_group'}))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_group'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.EXTRA_POSTS)

    def test_profile_have_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'}))
        first_object = response.context['page_obj'][0]
        self.assert_context_check(first_object)
        author = response.context['author']
        self.assertEqual(author, self.user)
        self.assertFalse(response.context['following'])

    def test_profile_paginator_working(self):
        """Проверка работы пагинатора profile"""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'}))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'TestUser'})
                                              + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.EXTRA_POSTS)

    def test_work_of_cache(self):
        """Проверка работы кэширования.
        При удалении поста, он не пропадает со страницы
        до обновления кэша"""
        cache.clear()
        test_post = Post.objects.create(text='Тестовый текст для кэша',
                                        author=self.user,
                                        group=self.test_group,)
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, test_post.text)
        Post.objects.first().delete()
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, test_post.text)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotContains(response, test_post.text)


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
        self.authorized_client.force_login(self.user)

    def test_new_post_with_group_in_index(self):
        """Пост с группой появляется на главной странице сайта"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.test_group,)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

    def test_new_post_with_group_in_profile(self):
        """Пост с группой появляется на странице профайла пользователя"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.test_group,)
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

    def test_new_post_with_group_in_group_list(self):
        """Пост с группой появляется на странице выбранной группы"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.test_group,)
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.test_group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, test_post.pk)

    def test_new_post_dont_appear_in_other_group(self):
        """Пост с группой не появляется на странице другой группы"""
        test_post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.test_group,)
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.fake_group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.pk, test_post.pk)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.author_1 = User.objects.create_user(username='TestAuthor_1')
        cls.author_2 = User.objects.create_user(username='TestAuthor_2')
        Post.objects.create(
            text='Тестовый пост автора 1',
            author=cls.author_1,
        )
        Post.objects.create(
            text='Тестовый пост автора 2',
            author=cls.author_2,
        )
        Follow.objects.create(
            author=FollowTests.author_1,
            user=FollowTests.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_user_can_follow(self):
        """Проверка на возможность подписаться на авторов 1 раз"""
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_2.username}))
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertEqual(Follow.objects.last().author, self.author_2)
        self.assertEqual(Follow.objects.last().user, self.user)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_2.username}))
        self.assertEqual(Follow.objects.count(), follows_count + 1)

    def test_user_can_unfollow(self):
        """Проверка на возможность отписаться от авторов"""
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author_1.username}))
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_user_cant_follow_himself(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user).exists())

    def test_following_authors_posts_in_feed(self):
        """Проверка появления постов авторов на странице подписок"""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertContains(
            response, Post.objects.get(author=self.author_1).text)

    def test_not_followed_author_posts_not_in_feed(self):
        """Проверка отсутствия постов, на которых пользователь не подписан"""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(
            response, Post.objects.get(author=self.author_2).text)
