from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='PostFormTests')
        super().setUpClass()
        Post.objects.create(
            text='first test post',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создаёт новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test post',
            'group': '',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        expected_redirect = reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        )
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='test post',
                author=PostFormTests.user
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
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        expected_redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        )
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=post.id,
                text='edited post'
            )
        )
