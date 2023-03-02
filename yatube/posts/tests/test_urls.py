from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.public_pages = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.private_pages = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.all_pages = {**cls.public_pages, **cls.private_pages}

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_and_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.all_pages.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_for_not_authorized_user(self):
        """Страницы доступны неавторизованному пользователю."""
        for address in self.public_pages.keys():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_not_authorized_user(self):
        """Страницы доступны авторизованному пользователю."""
        for address in self.all_pages.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_not_authorized_user_redirect(self):
        """Страницы для неавторизованного пользователя перенаправляются."""
        for address in self.private_pages.keys():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    reverse('users:login') + '?next=' + address,
                )

    def test_for_authorized_user_redirect(self):
        """Страница редактирования поста для авторизованного пользователя
        перенаправляется."""
        user_not_author = User.objects.create_user(username='NotAuthor')
        authorized_client_not_author = Client()
        authorized_client_not_author.force_login(user_not_author)
        response = authorized_client_not_author.get(
            '/posts/1/edit/',
            follow=True,
        )
        self.assertRedirects(response, '/posts/1/')

    def test_for_not_existing_page(self):
        """Проверка несуществующей страницы."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
