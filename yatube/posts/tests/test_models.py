from django.conf import settings
from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинный для проверки',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_tests = {
            self.group.title: str(self.group),
            self.post.text[:settings.POST_STR_LENGTH]: str(self.post),
        }
        for field, expected_value in str_tests.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
