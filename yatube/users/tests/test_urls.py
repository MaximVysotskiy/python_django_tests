from http import HTTPStatus

from django.test import Client, TestCase


class URLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.templates_url = {
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/logout/": "users/logged_out.html",
            "/auth/password_reset/": "users/password_reset_form.html",
            "/auth/reset/done/": "users/password_reset_complete.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
        }

    def test_quest_str(self):
        """страницы пользователя доступны всем"""
        for adress in self.templates_url:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
