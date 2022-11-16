from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class URLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.templates_url = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        self.templates_pages = {
            "about/author.html": reverse('about:author'),
            "about/tech.html": reverse('about:tech'),
        }

    def test_quest_str(self):
        """страница про автора и навыки доступны всем"""
        for adress in self.templates_url:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
