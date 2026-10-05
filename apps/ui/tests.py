from django.contrib.auth import get_user_model
from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.tests import plain_static


def render(source, **context):
    return Template("{% load icons %}" + source).render(Context(context))


class IconTests(SimpleTestCase):
    def test_renders_inline_svg(self):
        html = render('{% icon "check" %}')
        self.assertEqual(
            html,
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"'
            ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
            ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M20 6 9 17l-5-5"/></svg>',
        )

    def test_attributes_override_defaults_with_underscores_as_hyphens(self):
        html = render('{% icon "eye" class="size-4" stroke_width=1.75 data_eye="" %}')
        self.assertIn('class="size-4"', html)
        self.assertIn('stroke-width="1.75"', html)
        self.assertIn('data-eye=""', html)
        self.assertNotIn('stroke-width="2"', html)

    def test_escapes_attribute_values(self):
        html = render('{% icon "eye" class=value %}', value='">')
        self.assertIn('class="&quot;&gt;"', html)

    def test_unknown_icon_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            render('{% icon "no-such-icon" %}')


BOOSTED = {"HX-Request": "true", "HX-Boosted": "true"}
PRELOADED = {**BOOSTED, "HX-Preloaded": "true"}


@plain_static
class BoostTests(TestCase):
    def sign_in(self):
        user = get_user_model().objects.create_user(
            "ada@example.com", "Ada", "pw-12345!"
        )
        self.client.force_login(user)

    def test_signed_out_boosted_request_loads_the_full_page(self):
        url = reverse("category_list")
        response = self.client.get(url, headers=BOOSTED)
        self.assertEqual(response.headers["HX-Redirect"], url)

    def test_signed_in_boosted_request_renders_the_page(self):
        self.sign_in()
        response = self.client.get(reverse("category_list"), headers=BOOSTED)
        self.assertContains(response, '<main id="main"')
        self.assertNotIn("HX-Redirect", response.headers)

    def test_boosted_form_with_errors_stays_out_of_history(self):
        self.sign_in()
        response = self.client.post(
            reverse("category_create"), {"name": ""}, headers=BOOSTED
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Push-Url"], "false")

    def test_preloaded_page_is_briefly_cacheable_per_session(self):
        self.sign_in()
        response = self.client.get(reverse("category_list"), headers=PRELOADED)
        self.assertEqual(response.headers["Cache-Control"], "private, max-age=10")
        self.assertIn("Cookie", response.headers["Vary"])

    def test_only_preloaded_pages_are_cacheable(self):
        self.sign_in()
        response = self.client.get(reverse("category_list"), headers=BOOSTED)
        self.assertNotIn("Cache-Control", response.headers)

    def test_signed_out_preload_is_not_cacheable(self):
        response = self.client.get(reverse("category_list"), headers=PRELOADED)
        self.assertNotIn("Cache-Control", response.headers)

    def test_every_post_changes_the_data_version(self):
        self.sign_in()
        versions = set()
        for _ in range(2):
            self.client.post(reverse("category_create"), {"name": ""})
            versions.add(self.client.cookies["data_version"].value)
        self.assertEqual(len(versions), 2)
