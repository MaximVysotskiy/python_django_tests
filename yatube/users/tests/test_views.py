from django.test import Client, TestCase
from django.urls import reverse


class ViewTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.templates_pages = {
            "users/signup.html": reverse("users:signup"),
            "users/login.html": reverse("users:login"),
            "users/logged_out.html": reverse("users:logout"),
            "users/password_reset_form.html": reverse("users:password_reset"),
            "users/password_reset_complete.html": reverse("users:password_reset_complete"),
            "users/password_reset_done.html": reverse("users:password_reset_done"),
        }

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
