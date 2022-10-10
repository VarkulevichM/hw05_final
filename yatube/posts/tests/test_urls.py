from django.test import Client
from django.test import TestCase
from http import HTTPStatus
from posts.models import Group
from posts.models import Post
from posts.models import User


URL_CONSISTING_KNOWN_VALUES = {
    "/": "posts/index.html",
    "/group/test-slug/": "posts/group_list.html",
    "/create/": "posts/create_post.html"
}


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Rick")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="текстовое описание сообщества"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост"
        )
        cls.url_consisting_unknown_values = {
            f"/profile/{cls.user.username}/": "posts/profile.html",
            f"/posts/{cls.post.id}/": "posts/post_detail.html",
            f"/posts/{cls.post.id}/edit/": "posts/create_post.html",
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

    def test_urls_redirect_guest_client(self):
        """Проверка редиректа пользователя, который не авторизовался."""
        url_name = {
            "/create/": "/auth/login/?next=/create/",
            f"/posts/{self.post.id}/edit/":
            f"/auth/login/?next=/posts/{self.post.id}/edit/"}
        for url, address_redirect in url_name.items():
            response = self.guest_client.get(url)
            self.assertRedirects(response, address_redirect)

    def test_available_to_authorized(self):
        """Проверка доступности страниц в соответствие с status code."""
        new_dict = {**URL_CONSISTING_KNOWN_VALUES,
                    **self.url_consisting_unknown_values}
        for url in new_dict:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_existent_page(self):
        """Проверка не существующей страницы в соответствие с status code."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template_authorized_users(self):
        """URL-адрес использует соответствующий шаблон."""
        new_dict = {**URL_CONSISTING_KNOWN_VALUES,
                    **self.url_consisting_unknown_values}
        for url, template in new_dict.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_404_page_uses_custom_template(self):
        """Cтраница 404 использует кастомный шаблон."""
        response = self.authorized_client.get("/unexisting_page/")
        self.assertTemplateUsed(response, "core/404.html")
