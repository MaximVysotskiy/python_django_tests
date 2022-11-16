from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug')
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.user,
            group=cls.group,
        )
        cls.url_names = [
            "/",
            f"/group/{cls.group.slug}/",
            f"/profile/{cls.user}/",
            f"/posts/{cls.post.id}/",
        ]
        cls.templates_url_names = {
            "/": "posts/index.html",
            f"/group/{cls.group.slug}/": "posts/group_list.html",
            f"/profile/{cls.user.username}/": "posts/profile.html",
            f"/posts/{cls.post.id}/": "posts/post_detail.html",
            f"/posts/{cls.post.id}/edit/": "posts/post_create.html",
            "/create/": "posts/post_create.html",
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_quest_str(self):
        """страницы главная,группы,профайл и пост доступны всем"""
        for adress in self.url_names:
            with self.subTest(adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_edit_url_exists_at_author(self):
        """Страница /posts/post_id/edit/ доступна только автору."""
        self.user = User.objects.get(username=self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.authorized_client.get('/qwerty12345/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
