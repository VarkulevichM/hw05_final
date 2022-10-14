from django.core.cache import cache
from django.test import Client
from django.test import TestCase
from http import HTTPStatus

from posts.consts import DESCRIPTION
from posts.consts import SLUG
from posts.consts import TEXT
from posts.consts import TITLE
from posts.consts import USERNAME
from posts.models import Group
from posts.models import Post
from posts.models import User


class PostURLTests(TestCase):
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

        cls.urls_with_user_access_rights = {
            "/": "all",
            "/group/slug-test/": "all",
            f"/profile/{cls.user.username}/": "all",
            f"/posts/{cls.post.id}/": "all",
            "/create/": "authorized",
            "/follow/": "authorized",
            f"/posts/{cls.post.id}/edit/": "author",
            "/unexisting_page/": "non-existent"
        }

        cls.url_with_templates = {
            "/": "posts/index.html",
            "/group/slug-test/": "posts/group_list.html",
            "/create/": "posts/create_post.html",
            f"/profile/{cls.user.username}/": "posts/profile.html",
            f"/posts/{cls.post.id}/": "posts/post_detail.html",
            f"/posts/{cls.post.id}/edit/": "posts/create_post.html",
            "/follow/": "posts/follow.html",
            "/unexisting_page/": "core/404.html"
        }

    def setUp(self):
        # Не авторизированный пользователь
        self.guest_client = Client()
        # Авторизированный пользователь
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Авторизированный автор
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)
        # Очистка кеша, без него проверка не проходилась
        cache.clear()

    def test_urls_redirect_guest_client(self):
        """Проверка редиректа пользователя, который не авторизовался."""
        url_name = {
            "/create/": "/auth/login/?next=/create/",
            f"/posts/{self.post.id}/edit/":
            f"/auth/login/?next=/posts/{self.post.id}/edit/"
        }
        for url, address_redirect in url_name.items():
            response = self.guest_client.get(url)
            self.assertRedirects(response, address_redirect)

    def test_available_to_authorized(self):
        """Проверка доступности страниц в соответствие с status code
        с авторизированным пользователем."""
        for url, access in self.urls_with_user_access_rights.items():
            if access == "authorized":
                with self.subTest(url=url):
                    response = self.authorized_author.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_available_to_guest_client(self):
        """Проверка доступности страниц в соответствие с status code
        с не авторизированным пользователем."""
        for url, access in self.urls_with_user_access_rights.items():
            if access == "all":
                with self.subTest(url=url):
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_available_to_authorized_author(self):
        """Проверка доступности страниц в соответствие с status code
        с автором."""
        for url, access in self.urls_with_user_access_rights.items():
            if access == "author":
                with self.subTest(url=url):
                    response = self.authorized_author.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_authorized_users(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.url_with_templates.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_non_existent_page(self):
        """Проверка не существующей страницы в соответствие с status code."""
        for url, access in self.urls_with_user_access_rights.items():
            if access == "non-existent":
                with self.subTest(url=url):
                    response = self.authorized_author.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
