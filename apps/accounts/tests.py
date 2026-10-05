from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

from .forms import UserCreationForm

User = get_user_model()


class UserTests(TestCase):
    def test_create_user_lowercases_email(self):
        user = User.objects.create_user("Ada@Example.COM", "Ada Lovelace", "pw-12345!")
        self.assertEqual(user.email, "ada@example.com")
        self.assertFalse(user.is_staff)

    def test_create_superuser_is_staff_and_superuser(self):
        user = User.objects.create_superuser("root@example.com", "Root", "pw-12345!")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_authenticate_ignores_email_case(self):
        User.objects.create_user("ada@example.com", "Ada Lovelace", "pw-12345!")
        user = authenticate(username="ADA@example.com", password="pw-12345!")
        self.assertIsNotNone(user)

    def test_creation_form_rejects_email_differing_only_in_case(self):
        User.objects.create_user("ada@example.com", "Ada Lovelace", "pw-12345!")
        form = UserCreationForm(
            data={
                "email": "Ada@Example.com",
                "full_name": "Ada Again",
                "usable_password": "true",
                "password1": "a-Long-pass-123",
                "password2": "a-Long-pass-123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_names(self):
        user = User(email="ada@example.com", full_name="Ada King Lovelace")
        self.assertEqual(user.get_full_name(), "Ada King Lovelace")
        self.assertEqual(user.get_short_name(), "Ada")
