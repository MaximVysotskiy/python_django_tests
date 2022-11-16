import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comments, Follow, Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="agent 007")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
            group=cls.group,
        )
        cls.templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": cls.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": cls.post.author}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": cls.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": cls.post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/post_create.html",
            reverse("posts:post_create"): "posts/post_create.html",
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        response = self.authorized_client.get(reverse("posts:index"))
        expected = list(Post.objects.all())
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={'slug': self.group.slug}))
        first_object = response.context["group"]
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, self.group.title)
        self.assertEqual(group_slug_0, self.group.slug)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.authorized_client.get(
            reverse("posts:profile", args=(self.post.author,))
        )
        expected = list(Post.objects.filter(author_id="1"))
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.context.get("post").text, self.post.text)
        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(response.context.get("post").group, self.post.group)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Форма Комментария создает запись в Post"""
        comments_count = Comments.objects.count()
        form_data = {"text": "Тестовый комментарий"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Comments.objects.count(), comments_count + 1)
        self.assertTrue(Comments.objects.filter(text="Тестовый комментарий").exists())

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.post.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_follow_page(self):
        '''Авторизованный пользователь может подписываться на других пользователей и удалять их.'''
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        post_1 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(post_1.context["page_obj"]), 1)
        self.assertIn(self.post, post_1.context["page_obj"])

        # Проверка что пост не появился в избранных у юзера-обычного
        outsider = User.objects.create(username="NoName")
        self.authorized_client.force_login(outsider)
        post_1 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertNotIn(self.post, post_1.context["page_obj"])

        # Проверка отписки от автора поста
        Follow.objects.all().delete()
        post_2 = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(post_2.context["page_obj"]), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list",
                    kwargs={"slug": "test_slug"}): "posts/group_list.html",
            reverse("posts:profile",
                    kwargs={"username": "test_name"}): "posts/profile.html",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse("posts:index") + "?page=2": "posts/index.html",
            reverse("posts:group_list",
                    kwargs={"slug": "test_slug"}) + "?page=2":
            "posts/group_list.html",
            reverse("posts:profile",
                    kwargs={"username": "test_name"}) + "?page=2":
            "posts/profile.html",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 3)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TaskPagesTests, cls).setUpClass()
        cls.user = User.objects.create_user(username="agent007")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group_slug",
            description="Test group description",
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
            text="Тестовый текст",
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницу index_and_profile."""
        templates = (
            reverse("posts:index"),
            reverse("posts:profile", kwargs={"username": self.post.author}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context["page_obj"][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        obj = response.context["post"]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что при создании поста с картинкой создается запись в БД"""
        self.assertTrue(
            Post.objects.filter(
            text='Тестовый текст', image='posts/small.gif').exists()
        )
