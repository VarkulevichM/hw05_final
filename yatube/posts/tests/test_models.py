from django.test import TestCase

from posts.consts import DESCRIPTION
from posts.consts import SLUG
from posts.consts import TEXT
from posts.consts import TITLE
from posts.consts import USERNAME
from posts.models import Group
from posts.models import Post
from posts.models import User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT
        )

    def test_models_have_correct_object_post(self):
        """Проверяем, что у моделей Post корректно работает __str__."""
        expected_object_text = self.post.text
        self.assertEqual(expected_object_text, str(self.post))

    def test_models_have_correct_object_group(self):
        """Проверяем, что у моделей Group корректно работает __str__."""
        expected_object_title = self.group.title
        self.assertEqual(expected_object_title, str(self.group))

    def test_verbose_name(self):
        """Verbose_name в полях совпадает с ожидаемым."""
        field_verbose = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа"
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(
                        field).verbose_name, expected_value)

    def test_help_text(self):
        """Help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            "text": "Введите текст поста",
            "group": "Группа, к которой будет относиться пост"
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(
                        field).help_text, expected_value)
