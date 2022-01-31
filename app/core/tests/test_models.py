import email
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = 'test@londonappdev.com'
        password = 'Password123'
        user = get_user_model().objects.create_user(
			email=email,
			password=password
		)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test to see if new users emails are normalized"""
        email = 'test@LONDONAPPDEV.com'
        password = 'Password123'
        user = get_user_model().objects.create_user(
			email=email,
			password=password
		)

        self.assertEqual(user.email, email.lower())


    def test_new_user_invalid_email(self):
            """Tests to see if an invalid email is used"""
            with self.assertRaises(ValueError):
                user = get_user_model().objects.create_user(
                    email=None,
                    password='test123'
                )

    def test_create_new_superuser(self):
        email = 'test@LONDONAPPDEV.com'
        password = 'Password123'
        user = get_user_model().objects.create_superuser(
			email=email,
			password=password
		)

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
