import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from posts.consts import ANOTHER_SLUG
from posts.consts import ANOTHER_USERNAME
from posts.consts import DESCRIPTION
from posts.consts import SLUG
from posts.consts import TEXT
from posts.consts import TITLE
from posts.consts import USERNAME
from posts.models import Comment
from posts.models import Group
from posts.models import Post
from posts.models import User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION
        )

        cls.group_2 = Group.objects.create(
            title=TITLE,
            slug=ANOTHER_SLUG,
            description=DESCRIPTION
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_CREATE = reverse(
            "posts:post_create"
        )
        cls.PROFILE = reverse(
            "posts:profile", kwargs={"username": cls.post.author}
        )
        cls.EDIT_POST = reverse(
            "posts:edit_post", kwargs={"post_id": cls.post.id}
        )
        cls.POST_DETAIL = reverse(
            "posts:post_detail", kwargs={"post_id": cls.post.id}
        )
        cls.ADD_COMMENT = reverse(
            "posts:add_comment", kwargs={"post_id": cls.post.id}
        )
        cls.GUEST_REDIRECT_CREATING_COMMENT = (
            f"/auth/login/?next=/posts/{cls.post.id}/comment/"
        )
        cls.GUEST_REDIRECT_EDIT_POST = (
            f"/auth/login/?next=/posts/{cls.post.id}/edit/"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Не авторизированный пользователь
        self.guest_client = Client()
        # Авторизированный пользователь
        self.authorized_client = Client()
        self.authorized_client.force_login(self.another_user)
        # Авторизированный автор
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

    def test_create_post(self):
        """Проверка валидации формы при создании поста"""
        post_count = Post.objects.count()

        form_data = {
            "text": "Текст поста в форме редактированный",
            "group": self.group.id,
            "image": self.post.image
        }

        response = self.authorized_author.post(
            self.POST_CREATE,
            data=form_data,
        )

        self.assertRedirects(
            response,
            self.PROFILE
        )

        self.assertEqual(
            Post.objects.count(),
            post_count + 1
        )

        post = Post.objects.first()
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(self.post.image, form_data["image"])

    def test_edit_post(self):
        """Проверка валидации формы при редактировании поста"""
        post_count = Post.objects.count()

        self.post = Post.objects.create(
            author=self.user,
            text=TEXT,
            group=self.group,
        )

        form_data = {
            "text": "Текст поста в форме",
            "group": self.group_2.id,
        }

        response = self.authorized_author.post(
            self.EDIT_POST,
            data=form_data
        )

        self.assertRedirects(
            response,
            self.POST_DETAIL
        )

        self.assertEqual(
            Post.objects.count(),
            post_count + 1
        )

        post = Post.objects.first()
        self.assertNotEqual(post.group.id, form_data["group"])
        self.assertNotEqual(post.text, form_data["text"])

    def test_edit_post_guest_client(self):
        """Проверка редактирование поста гостем"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Текст поста в форме",
            "group": self.group_2.id,
        }

        response = self.guest_client.post(
            self.EDIT_POST,
            data=form_data
        )

        self.assertRedirects(
            response,
            self.GUEST_REDIRECT_EDIT_POST
        )

        self.assertEqual(
            Post.objects.count(),
            post_count
        )
        post = Post.objects.first()
        self.assertNotEqual(post.text, form_data["text"])
        self.assertNotEqual(post.group.id, form_data["group"])

    def test_edit_post_authorized_client(self):
        """Проверка редактирование поста авторизированным пользователем"""
        post_count = Post.objects.count()

        form_data = {
            "text": "Текст поста в форме",
            "group": self.group_2.id,
        }

        response = self.authorized_client.post(
            self.EDIT_POST,
            data=form_data
        )

        self.assertRedirects(
            response,
            self.POST_DETAIL
        )

        self.assertEqual(
            Post.objects.count(),
            post_count
        )
        post = Post.objects.first()
        self.assertNotEqual(post.text, form_data["text"])
        self.assertNotEqual(post.group.id, form_data["group"])

    def test_comment_add(self):
        """Проверка создания комментария авторизированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "текст комментария"
        }

        response = self.authorized_author.post(
            self.ADD_COMMENT,
            data=form_data
        )

        self.assertRedirects(
            response,
            self.POST_DETAIL
        )

        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1
        )

    def test_comment_add_guest(self):
        """Проверка создания комментария гостевым пользователем
        и редиректа на страницу авторизации"""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "текст комментария"
        }

        response = self.guest_client.post(
            self.ADD_COMMENT,
            data=form_data
        )

        self.assertRedirects(
            response,
            self.GUEST_REDIRECT_CREATING_COMMENT
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count
        )
