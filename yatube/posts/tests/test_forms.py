from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from posts.models import Post


User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostFormTests')
        Post.objects.create(
            text='first test post',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создаёт новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test post',
            'group': '',
        }
        expected_redirect = reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        )

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostFormTests.user,
                group=None
            ).exists()
        )

    def test_guest_cant_create_post(self):
        """Не авторизованный пользователь не может создать новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test post',
            'group': '',
        }
        expected_redirect = f'{reverse(settings.LOGIN_URL)}?next=/create/'

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                author=PostFormTests.user,
                group=None
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет пост с тем же id."""
        posts_count = Post.objects.count()
        post = Post.objects.first()
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': post.id}
        )
        form_data = {'text': 'edited post'}
        expected_redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        )

        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=post.id,
                text=form_data['text'],
                group=None
            )
        )
