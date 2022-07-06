from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post
from posts.constants import N_SYMBOLS_TO_SHOW

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, имеющий более 15'
                 'символов для корректной тестировки __str__',
        )

    def test_models_have_correct_object_attributes(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        post = self.post
        expected_objects = {
            group.title: str(group),
            post.text[:N_SYMBOLS_TO_SHOW]: str(post),
        }
        for obj_attribute, exp_attribute in expected_objects.items():
            with self.subTest(obj_attribute=obj_attribute):
                self.assertEqual(obj_attribute, exp_attribute)
