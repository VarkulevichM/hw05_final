import shutil
import tempfile
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from posts.models import Follow
from posts.models import Group
from posts.models import Post
from posts.models import User
from posts.tests.consts import ANOTHER_USERNAME
from posts.tests.consts import DESCRIPTION
from posts.tests.consts import SLUG
from posts.tests.consts import TEXT
from posts.tests.consts import TITLE
from posts.tests.consts import USERNAME
from posts.utils import COUNT_POST_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower = User.objects.create_user(username=ANOTHER_USERNAME)

        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION
        )
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

        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
            group=cls.group,
            image=cls.uploaded
        )

        cls.url_address = {
            "index": reverse("posts:index"),
            "group_list": reverse(
                "posts:group_list", kwargs={"slug": cls.group.slug}
            ),
            "profile": reverse(
                "posts:profile", kwargs={"username": cls.post.author}
            ),
            "post_detail": reverse(
                "posts:post_detail", kwargs={"post_id": cls.post.id}
            ),
            "edit_post": reverse(
                "posts:edit_post", kwargs={"post_id": cls.post.id}
            ),
            "create_post": reverse("posts:post_create"),
            "follow_index": reverse("posts:follow_index")
        }

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
        # Подписчик на автора
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.create_follow = Follow.objects.create(
            author=self.post.author, user=self.follower)
        # Очистка кеша
        cache.clear()

    def assert_for_functions(self, post_object):
        """Вынесение проверок в отдельную функцию"""
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.image, self.post.image)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.author, self.post.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        template_page = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list", kwargs={"slug": self.group.slug}
                    ): "posts/group_list.html",
            reverse("posts:profile", kwargs={"username": self.post.author}
                    ): "posts/profile.html",
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}
                    ): "posts/post_detail.html",
            reverse("posts:edit_post", kwargs={"post_id": self.post.id}
                    ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

        for reverse_name, template in template_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address["index"]
        )
        post_object = response.context["page_obj"][0]

        self.assert_for_functions(post_object)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_group_posts_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address["group_list"]
        )
        post_object = response.context["page_obj"][0]

        self.assert_for_functions(post_object)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_profile_posts_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address["profile"]
        )
        post_object = response.context["page_obj"][0]

        self.assert_for_functions(post_object)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_detail_posts_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.url_address["post_detail"]
        )

        self.assertEqual(
            response.context["posts"], self.post
        )
        self.assertEqual(
            response.context["posts"].id, self.post.id
        )
        self.assertEqual(
            response.context["posts"].image, self.post.image
        )

    def test_create_posts_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            self.url_address["create_post"]
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_fields, expected)

    def test_edit_posts_correct_context(self):
        """Шаблон post_id сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            self.url_address["edit_post"]
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_fields, expected)

        response = self.authorized_client.get(
            self.url_address["edit_post"]
        )
        self.assertEqual(response.context['is_edit'], True)

    def test_post_appears_correctly(self):
        """Пост при создании добавлен корректно"""
        # проверка того, что пост попал в нужную группу - до
        post_group_count = Post.objects.filter(group=self.group).count()
        group = Post.objects.filter(group=self.group).count()
        self.assertEqual(group, post_group_count)

        post = Post.objects.create(
            author=self.user,
            text="Текст поста создание",
            group=self.group
        )

        response_index = self.authorized_client.get(
            self.url_address["index"]
        )
        response_group = self.authorized_client.get(
            self.url_address["group_list"]
        )
        response_profile = self.authorized_client.get(
            self.url_address["profile"]
        )

        index_post = response_index.context["page_obj"]
        group_post = response_group.context["page_obj"]
        profile_post = response_profile.context["page_obj"]
        # проверка того, что пост попал в нужную группу - после
        post_group_count = Post.objects.filter(group=self.group).count()
        group = Post.objects.filter(group=self.group).count()

        self.assertEqual(group, post_group_count)
        self.assertIn(post, index_post)
        self.assertIn(post, group_post)
        self.assertIn(post, profile_post)

    def test_cache_index(self):
        """Проверка работы кеша страницы index"""
        response = self.authorized_client.get(
            self.url_address["index"]
        ).content

        Post.objects.create(
            text="текст поста поста",
            author=self.user,
            group=self.group
        )
        response_old = self.authorized_client.get(
            self.url_address["index"]
        ).content
        self.assertEqual(response_old, response)

        cache.clear()

        response_new = self.authorized_client.get(
            self.url_address["index"]
        ).content
        self.assertNotEqual(response_old, response_new)

    def test_authorized_user_follow(self):
        """Проверка, что авторизированный пользователь
         может подписываться на других пользователей
         и удалять их из подписок"""
        follow_count = Follow.objects.count()
        response = self.follower_client.get(
            self.url_address["follow_index"]
        )
        self.assertEqual(len(
            response.context["page_obj"]), 1)
        self.assertEqual(follow_count, Follow.objects.count())

        self.create_follow.delete()

        follow_count_new = Follow.objects.count()
        self.assertEqual(follow_count_new, Follow.objects.count())

        response = self.follower_client.get(
            self.url_address["follow_index"]
        )
        self.assertEqual(len(
            response.context["page_obj"]), 0)

    def test_authorized_us(self):
        """ Проверка, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан. """
        response = self.follower_client.get(
            self.url_address["follow_index"]
        )
        self.assertEqual(len(
            response.context["page_obj"]), 1
        )

        response = self.authorized_client.get(
            self.url_address["follow_index"]
        )
        self.assertNotEqual(len(
            response.context["page_obj"]), 1
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Rick")
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION
        )

        for variable in range(COUNT_POST_PER_PAGE + 1):
            cls.post = Post.objects.create(
                text=TEXT + str({variable}),
                author=cls.user,
                group=cls.group,
            )

        cls.INDEX = reverse("posts:index")
        cls.GROUP_LIST = reverse(
            "posts:group_list", kwargs={"slug": "slug-test"}
        )
        cls.PROFILE = reverse(
            "posts:profile", kwargs={"username": cls.post.author}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_page(self):
        """Проверка страниц с пагинатором."""
        paginator_list = [
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE
        ]

        for reverse_name in paginator_list:
            with self.subTest(reverse_name=reverse_name):
                response_first_page = self.authorized_client.get(reverse_name)
                response_second_page = self.authorized_client.get(
                    reverse_name + "?page=2")

                self.assertEqual(len(
                    response_first_page.context["page_obj"]),
                    COUNT_POST_PER_PAGE)

                self.assertEqual(len(
                    response_second_page.context["page_obj"]), 1)
