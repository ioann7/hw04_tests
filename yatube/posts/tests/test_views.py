from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django import forms

from ..models import Group, Post


User = get_user_model()


class PostPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='PostPagesTests')
        self.group = Group.objects.create(
            title='test group',
            slug='test-group',
            description='test-description'
        )
        self.group_without_posts = Group.objects.create(
            title='test group without posts',
            slug='test-group-without-posts',
            description='test description'
        )
        self.posts = [Post.objects.create(
            text='test post text with group',
            author=self.user,
            group=self.group
        ) for _ in range(5)]
        self.post = self.posts[0]
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_created_post_is_displayed(self):
        """
        Созданный пост отображается на шаблонах:
        index, group_posts, profile.
        """
        names_urls = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        }
        new_post = Post.objects.create(
            text='new post',
            author=self.user,
            group=self.group
        )
        self.assertNotIn(new_post, self.group_without_posts.posts.all())
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0], new_post)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in pages_names_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        group_title_0 = post_group_0.title
        group_slug_0 = post_group_0.slug
        group_description_0 = post_group_0.description
        self.assertEqual(post_text_0, 'test post text with group')
        self.assertEqual(post_pub_date_0, self.posts[-1].pub_date)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(group_title_0, 'test group')
        self.assertEqual(group_slug_0, 'test-group')
        self.assertEqual(group_description_0, 'test-description')

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        expected_group = self.group
        url = reverse(
            'posts:group_posts',
            kwargs={'slug': expected_group.slug}
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['group'], expected_group)
        for post in response.context['page_obj']:
            self.assertEqual(post.group, expected_group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        expected_author = self.user
        expected_posts_count = self.user.posts.count()
        url = reverse(
            'posts:profile',
            kwargs={'username': expected_author.username}
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['author'], expected_author)
        self.assertEqual(response.context['posts_count'], expected_posts_count)
        for post in response.context['page_obj']:
            self.assertEqual(post.author, expected_author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        expected_post = self.post
        expected_posts_count = self.post.author.posts.count()
        url = reverse(
            'posts:post_detail',
            kwargs={'post_id': expected_post.id}
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['post'], expected_post)
        self.assertEqual(response.context['posts_count'], expected_posts_count)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        expected_post_id = self.post.id
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': expected_post_id}
        )
        response = self.authorized_client.get(url)
        self.assertEqual(response.context['post_id'], expected_post_id)
        self.assertEqual(response.context['is_edit'], True)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test group',
            slug='test-group',
            description='test description group'
        )
        cls.user = User.objects.create_user(username='PaginatorViewsTest')
        cls.posts = []
        for i in range(15):
            cls.posts.append(Post.objects.create(
                text=f'test post{i}',
                author=cls.user,
                group=cls.group
            ))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_10_records(self):
        """
        Первая страница шаблонов:
        index, group_posts, profile отображает 10 постов.
        """
        group = PaginatorViewsTest.group
        user = PaginatorViewsTest.user
        names_urls = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': user.username}
            ),
        }
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_5_records(self):
        """
        Вторая страница шаблонов:
        index, group_posts, profile отображает 5 постов.
        """
        group = PaginatorViewsTest.group
        user = PaginatorViewsTest.user
        names_urls = {
            'index': reverse('posts:index') + '?page=2',
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': group.slug}
            ) + '?page=2',
            'profile': reverse(
                'posts:profile',
                kwargs={'username': user.username}
            ) + '?page=2',
        }
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 5)
