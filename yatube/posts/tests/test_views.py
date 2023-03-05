import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_two = User.objects.create_user(username='User 2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.index = (reverse('posts:index'), 'posts/index.html')
        cls.group_list = (
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            'posts/group_list.html',
        )
        cls.profile = (
            reverse('posts:profile', kwargs={'username': cls.user.username}),
            'posts/profile.html',
        )
        cls.post_edit = (
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}),
            'posts/create_post.html',
        )
        cls.post_detail = (
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}),
            'posts/post_detail.html',
        )
        cls.create = (
            reverse('posts:post_create'),
            'posts/create_post.html',
        )
        cls.follow = (
            reverse('posts:follow_index'),
            'posts/follow.html',
        )
        cls.profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_two.username},
        )
        cls.profile_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_two.username}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in (
            self.index,
            self.group_list,
            self.profile,
            self.post_edit,
            self.post_detail,
            self.create,
            self.follow,
        ):
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_for_check(self, response):
        """Функция для проверки правильности контекста."""
        if 'page_obj' in response:
            post_for_check = response['page_obj'][0]
        else:
            post_for_check = response.get('post')
        self.assertIsInstance(post_for_check, Post)
        post_text = {
            post_for_check.text: self.post.text,
            post_for_check.group: self.group,
            post_for_check.author: self.user,
            post_for_check.image: self.post.image,
        }
        for value, expected in post_text.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        address, _ = self.index
        response = self.client.get(address).context
        self.context_for_check(response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        address, _ = self.group_list
        response = self.client.get(address).context
        self.context_for_check(response)

        group_for_check = response.get('group')
        group_context = {
            group_for_check.title: self.group.title,
            group_for_check.slug: self.group.slug,
            group_for_check.description: self.group.description,
        }
        for value, expected in group_context.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        authorized_client = Client()
        authorized_client.force_login(self.user_two)
        Follow.objects.get_or_create(user=self.user_two, author=self.user)

        address, _ = self.profile
        response = authorized_client.get(address).context
        self.context_for_check(response)

        user_for_check = response.get('author')
        following_for_check = response.get('following')
        user_context = {
            user_for_check.username: self.user.username,
            following_for_check: self.post.author.following.exists(),
        }
        for value, expected in user_context.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        address, _ = self.post_detail
        comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=self.post,
            author=self.user,
        )
        response = self.authorized_client.get(address).context
        self.context_for_check(response)
        self.assertIn(comment, response['comments'])

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        address, _ = self.post_edit
        response = self.authorized_client.get(address)
        self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)

        post_for_check = response.context.get('form').instance
        post_context = {
            post_for_check.text: self.post.text,
            post_for_check.group: self.group,
        }
        for value, expected in post_context.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        address, _ = self.create
        response = self.authorized_client.get(address)
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)

    def test_pajinator(self):
        """Проверка паджинатора."""
        Post.objects.all().delete()
        POST_ON_PAGE_2 = 3
        Post.objects.bulk_create([Post(
            text=f'Post {i}',
            group=self.group,
            author=self.user,
        ) for i in range(settings.POST_ON_PAGE + POST_ON_PAGE_2)])
        address_index, _ = self.index
        address_group_list, _ = self.group_list
        address_profile, _ = self.profile
        reverse_pages = [
            address_index,
            address_group_list,
            address_profile,
        ]
        for page in reverse_pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POST_ON_PAGE,
                )
                response = self.client.get(page + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    POST_ON_PAGE_2,
                )

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно."""
        Post.objects.all().delete()
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )
        address_index, _ = self.index
        address_group_list, _ = self.group_list
        address_profile, _ = self.profile
        reverse_pages = [
            address_index,
            address_group_list,
            address_profile,
        ]
        for page in reverse_pages:
            with self.subTest(page=page):
                response = self.client.get(page).context['page_obj']
                self.assertIn(post, response)

    def test_post_not_added_to_another_group(self):
        """Пост при создании добавлен в нужную группу."""
        Post.objects.all().delete()
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )
        group_two = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-2'
        )
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': group_two.slug})
        ).context['page_obj']
        self.assertNotIn(post, response)

    def test_check_cache(self):
        """Проверка кеширования главной страницы."""
        address, _ = self.index
        response = self.client.get(address).content
        Post.objects.all().delete()
        response_post_deleted = self.client.get(address).content
        self.assertEqual(response, response_post_deleted)
        cache.clear()
        response_cache_deleted = self.client.get(address).content
        self.assertNotEqual(response, response_cache_deleted)

    def test_add_follow(self):
        """Проверка подписки на автора."""
        self.authorized_client.get(self.profile_follow)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_two).exists()
        )

    def test_delete_follow(self):
        """Проверка отписки от автора."""
        Follow.objects.create(user=self.user, author=self.user_two)
        self.authorized_client.get(self.profile_unfollow)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_two).exists()
        )

    def test_new_post_for_followers(self):
        """Пост появляется на странице избранного у подписчика."""
        address, _ = self.follow
        Follow.objects.get_or_create(user=self.user, author=self.user_two)
        post_by_user_two = Post.objects.create(
            author=self.user_two,
            text='Тестовый пост от второго автора',
        )
        response = self.authorized_client.get(address)
        self.assertIn(post_by_user_two, response.context["page_obj"])

    def test_new_post_not_shown_for_not_followers(self):
        """Пост не появляется на странице у не подписчика."""
        address, _ = self.follow
        post_by_user_two = Post.objects.create(
            author=self.user_two,
            text='Тестовый пост от второго автора',
        )
        response = self.authorized_client.get(address)
        self.assertNotIn(
            post_by_user_two,
            response.context["page_obj"]
        )
