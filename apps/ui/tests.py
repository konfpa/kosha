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


@plain_static
class BoostTests(TestCase):
    def test_signed_out_boosted_request_loads_the_full_page(self):
        url = reverse("category_list")
        response = self.client.get(
            url, headers={"HX-Request": "true", "HX-Boosted": "true"}
        )
        self.assertEqual(response.headers["HX-Redirect"], url)

    def test_signed_in_boosted_request_renders_the_page(self):
        user = get_user_model().objects.create_user(
            "ada@example.com", "Ada", "pw-12345!"
        )
        self.client.force_login(user)
        response = self.client.get(
            reverse("category_list"),
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        self.assertContains(response, '<main id="main"')
        self.assertNotIn("HX-Redirect", response.headers)

    def test_boosted_form_with_errors_stays_out_of_history(self):
        user = get_user_model().objects.create_user(
            "ada@example.com", "Ada", "pw-12345!"
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("category_create"),
            {"name": ""},
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Push-Url"], "false")
