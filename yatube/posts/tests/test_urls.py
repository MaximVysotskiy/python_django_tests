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
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_authorized(self):
        """Страница create доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """без авторизации приватные URL недоступны"""
        for adress in self.url_names:
            with self.subTest(adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_edit_post_list_url_exists_at_desired_location(self):
        """Страница /posts/1/edit/ доступна автору."""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.authorized_client.get('/qwerty12345/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
