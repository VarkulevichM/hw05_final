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
import shutil
import tempfile

INCREASE_NUMBER_RECORDS = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Rick")
        cls.group = Group.objects.create(
            title="Название группы",
            slug="slug-test",
            description="Текстовое описание группы"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст поста",
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

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
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
        )

        self.assertRedirects(response, reverse(
            "posts:profile", kwargs={"username": self.post.author}))
        self.assertEqual(
            Post.objects.count(), post_count + INCREASE_NUMBER_RECORDS)

        post = Post.objects.first()
        self.assertEqual(post.text, "Текст поста в форме")
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.image, "posts/small.gif")

    def test_edit_post(self):
        """Проверка валидации формы при редактировании поста"""
        self.post = Post.objects.create(
            author=self.user,
            text="Текст поста",
            group=self.group,
        )

        post_for_edit = self.post

        form_data = {
            "text": "Текст поста в форме",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:edit_post", kwargs={"post_id": post_for_edit.id}),
            data=form_data
        )
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.id}))

        post = Post.objects.first()
        self.assertEqual(post.group.id, self.group.id)
        self.assertNotEqual(post_for_edit.text, form_data["text"])

    def test_comment_add(self):
        """Проверка создания комментария авторизированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
           "text": "текст комментария"
        }
        response = self.authorized_client.post(
           reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
           data=form_data
        )
        self.assertRedirects(response, reverse(
            "posts:post_detail", kwargs={"post_id": self.post.id}))
        self.assertEqual(
            Comment.objects.count(), comment_count + INCREASE_NUMBER_RECORDS)
