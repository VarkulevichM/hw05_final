import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from posts.models import Comment
from posts.models import Group
from posts.models import Post
from posts.models import User
from posts.consts import USERNAME
from posts.consts import TITLE
from posts.consts import SLUG
from posts.consts import DESCRIPTION
from posts.consts import TEXT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

URL_TEMPLATES = {
    "post_create": reverse("posts:post_create")
}


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
            text=TEXT,
            group=cls.group,
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
        self.authorized_client.force_login(self.user)
        # Авторизированный автор
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

    def test_create_post(self):
        """Проверка валидации формы при создании поста"""
        post_count = Post.objects.count()

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
            "text": "Текст поста в форме",
            "group": self.group.id,
            "image": uploaded
        }
        response = self.authorized_author.post(
            reverse("posts:post_create"),
            data=form_data,
        )

        self.assertRedirects(response, reverse(
            "posts:profile", kwargs={"username": self.post.author}))
        self.assertEqual(
            Post.objects.count(), post_count + 1)

        post = Post.objects.first()
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(str(post.image), "posts/small.gif")

    def test_edit_post(self):
        """Проверка валидации формы при редактировании поста"""
        self.post = Post.objects.create(
            author=self.user,
            text=TEXT,
            group=self.group,
        )

        form_data = {
            "text": "Текст поста в форме",
            "group": self.group.id,
        }
        response = self.authorized_author.post(
            reverse("posts:edit_post", kwargs={"post_id": self.post.id}),
            data=form_data
        )
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.id}))

        post = Post.objects.first()
        self.assertEqual(post.group.id, form_data["group"])
        self.assertNotEqual(self.post.text, form_data["text"])
        print("2")

    def test_comment_add(self):
        """Проверка создания комментария авторизированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {"text": "текст комментария"}
        response = self.authorized_author.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data)
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.id}))
        self.assertEqual(
            Comment.objects.count(), comment_count + 1)

    def test_comment_add_guest(self):
        """Проверка создания комментария гостевым пользователем
        и редиректа на страницу авторизации"""
        comment_count = Comment.objects.count()
        form_data = {"text": "текст комментария"}
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data)
        self.assertRedirects(response, f"/auth/login/?next=/posts/{self.post.id}/comment/")
        self.assertEqual(
            Comment.objects.count(), comment_count)
