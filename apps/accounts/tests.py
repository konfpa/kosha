import re

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .forms import UserCreationForm
from .lockout import client_ip
from .sessions import LOGIN_AT_SESSION_KEY

User = get_user_model()

# The test runner forces DEBUG off, so the manifest storage would demand a
# collectstatic run before any page with {% static %} could render.
plain_static = override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)


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
        user = authenticate(
            RequestFactory().post("/"), username="ADA@example.com", password="pw-12345!"
        )
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


@plain_static
class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "ada@example.com", "Ada Lovelace", "pw-12345!"
        )

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_login_redirects_home(self):
        response = self.client.post(
            reverse("login"), {"username": "ADA@example.com", "password": "pw-12345!"}
        )
        self.assertRedirects(response, reverse("home"))
        self.assertContains(self.client.get(reverse("home")), "Welcome, Ada")

    def test_remember_sets_long_session(self):
        credentials = {"username": "ada@example.com", "password": "pw-12345!"}
        self.client.post(reverse("login"), credentials)
        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_SHORT_AGE
        )

        self.client.post(reverse("logout"))
        self.client.post(reverse("login"), {**credentials, "remember": "on"})
        self.assertEqual(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE
        )

    def test_remember_is_checked_by_default(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'name="remember" checked')

    def test_session_ends_after_max_age(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

        session = self.client.session
        session[LOGIN_AT_SESSION_KEY] -= settings.SESSION_MAX_AGE + 1
        session.save()
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_wrong_password_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "ada@example.com", "password": "nope"}
        )
        self.assertContains(response, "don&#x27;t match an account")

    def test_signed_in_user_skips_login_page(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("login")), reverse("home"))

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


@plain_static
class PasswordResetTests(TestCase):
    def setUp(self):
        User.objects.create_user("ada@example.com", "Ada Lovelace", "pw-12345!")

    def request_reset(self, email="ada@example.com"):
        return self.client.post(reverse("password_reset"), {"email": email})

    def test_sends_text_and_html_email(self):
        response = self.request_reset()
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Reset your kosha password")
        self.assertIn("Hi Ada,", message.body)
        self.assertIn("/reset/", message.body)
        self.assertEqual(message.alternatives[0].mimetype, "text/html")

    def test_sent_page_names_the_address(self):
        self.request_reset()
        response = self.client.get(reverse("password_reset_done"))
        self.assertContains(response, "ada@example.com")

    def test_unknown_email_looks_the_same(self):
        response = self.request_reset("nobody@example.com")
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_link_sets_new_password_once(self):
        self.request_reset()
        link = re.search(r"https?://[^/]+(/reset/\S+)", mail.outbox[0].body)[1]

        response = self.client.get(link, follow=True)
        self.assertContains(response, "Choose a new password")
        response = self.client.post(
            response.redirect_chain[-1][0],
            {"new_password1": "a-Fresh-pass-42", "new_password2": "a-Fresh-pass-42"},
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        response = self.client.post(
            reverse("login"),
            {"username": "ada@example.com", "password": "a-Fresh-pass-42"},
        )
        self.assertRedirects(response, reverse("home"))

        self.client.post(reverse("logout"))
        response = self.client.get(link, follow=True)
        self.assertContains(response, "This link can't be used")


@plain_static
class LockoutTests(TestCase):
    def setUp(self):
        User.objects.create_user("ada@example.com", "Ada Lovelace", "pw-12345!")

    def fail(self, username="ada@example.com", ip="203.0.113.1"):
        return self.client.post(
            reverse("login"),
            {"username": username, "password": "nope"},
            REMOTE_ADDR=ip,
        )

    def test_locks_out_after_five_failures(self):
        for _ in range(4):
            self.assertEqual(self.fail().status_code, 200)
        response = self.fail()
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many sign-in attempts", status_code=429)

    def test_lockout_holds_for_the_right_password(self):
        for _ in range(5):
            self.fail()
        response = self.client.post(
            reverse("login"),
            {"username": "ada@example.com", "password": "pw-12345!"},
            REMOTE_ADDR="203.0.113.1",
        )
        self.assertEqual(response.status_code, 429)

    def test_casing_and_new_addresses_share_one_count(self):
        for i, username in enumerate(["ada@example.com", "ADA@example.com"] * 2):
            self.fail(username, ip=f"203.0.113.{i}")
        self.assertEqual(
            self.fail("Ada@Example.com", ip="198.51.100.9").status_code, 429
        )


class ClientIpTests(TestCase):
    def request(self, forwarded):
        return RequestFactory().get(
            "/", REMOTE_ADDR="172.17.0.1", HTTP_X_FORWARDED_FOR=forwarded
        )

    def test_ignores_forwarded_header_by_default(self):
        self.assertEqual(client_ip(self.request("198.51.100.7")), "172.17.0.1")

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_uses_address_the_proxy_appended(self):
        request = self.request("10.9.9.9, 198.51.100.7")
        self.assertEqual(client_ip(request), "198.51.100.7")
