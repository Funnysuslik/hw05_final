from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake_user = User.objects.create_user(username='NotAuthor')
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
        self.fake_client = Client()
        self.fake_client.force_login(self.fake_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_correct_template_auth_author(self):
        """Тeст на использование правльного шаблна html"""
        templates_url_names = {
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{response.status_code}'
                )

    def test_correct_template_guest(self):
        """Тeст на использование правльного шаблна html"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_group/': 'posts/group_list.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        cache.clear()
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'{response.status_code}'
                )

    def test_non_exist_page(self):
        """Тест на ошибку 404"""
        unexisting_page = '/unexisting_page/'
        response = self.authorized_client.get(unexisting_page)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_not_auth_user_url_exists_at_desired_location(self):
        """Тест на доступность страниц неавторизованому клиенту"""
        templates_url_names_not_auth = [
            '/',
            '/group/test_group/',
            '/profile/TestUser/',
            '/posts/1/',
        ]
        for address in templates_url_names_not_auth:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_url_exists_at_desired_location(self):
        """Тест на доступность страниц авторизованому автору"""
        templates_url_names_auth = [
            '/create/',
            '/posts/1/edit/',
        ]
        for address in templates_url_names_auth:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_access(self):
        """Тест НЕдоступности страниц гостю"""
        templates_url_names_auth = [
            '/create/',
            '/posts/1/edit/',
            '/posts/1/comment/'
        ]
        for address in templates_url_names_auth:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code,
                                 HTTPStatus.FOUND)

    def test_guest_redirected_from_post_create_template(self):
        """Тест на перенаправление гостя на страницу
        авторизации из недоступных ему страниц"""
        templates_url_names_auth = [
            '/create/',
            '/posts/1/edit/',
        ]
        for address in templates_url_names_auth:
            with self.subTest(address=address):
                self.assertRedirects(self.client.get(address),
                                     '/auth/login/?next=' + address)

    def test_not_author_redirect_post_edit(self):
        """Тест перенаправления на другую страницу
        при попытке редактирования поста не автором"""
        self.assertRedirects(self.fake_client.get('/posts/1/edit/'),
                             '/posts/1/')
