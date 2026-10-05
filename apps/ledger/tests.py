import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.tests import plain_static

from .choices import ICONS, PALETTE

User = get_user_model()


def make_user(email="ada@example.com"):
    return User.objects.create_user(email, "Ada Lovelace", "pw-12345!")


@plain_static
class SignedOutTests(TestCase):
    def test_every_category_url_redirects_to_login(self):
        category = make_user().categories.create(
            name="Rent", icon="house", colour="blue"
        )
        urls = [
            reverse("category_list"),
            reverse("category_create"),
            reverse("category_edit", args=[category.pk]),
            reverse("category_delete", args=[category.pk]),
        ]
        for url in urls:
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url)
                    self.assertRedirects(response, f"{reverse('login')}?next={url}")


@plain_static
class CategoryListTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_empty_state_offers_new_category(self):
        response = self.client.get(reverse("category_list"))
        self.assertContains(response, "No categories yet")
        self.assertContains(response, reverse("category_create"))

    def test_lists_own_categories_alphabetically_ignoring_case(self):
        for name in ("rent", "Groceries", "salary", "Bills"):
            self.user.categories.create(name=name, icon="tag", colour="red")
        make_user("bob@example.com").categories.create(
            name="Bob secret", icon="tag", colour="red"
        )

        response = self.client.get(reverse("category_list"))

        content = response.content.decode()
        positions = [
            content.index(f">{name}<")
            for name in ("Bills", "Groceries", "rent", "salary")
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertNotContains(response, "Bob secret")
        self.assertNotContains(response, "No categories yet")

    def test_shows_each_category_icon_in_its_colour(self):
        category = self.user.categories.create(
            name="Groceries", icon="shopping-cart", colour="emerald"
        )
        response = self.client.get(reverse("category_list"))
        self.assertContains(response, "text-emerald-600 dark:text-emerald-400")
        self.assertContains(response, reverse("category_edit", args=[category.pk]))

    def test_sidebar_marks_categories_active_on_every_categories_page(self):
        category = self.user.categories.create(name="Rent", icon="house", colour="blue")
        list_url = reverse("category_list")
        for url in (
            list_url,
            reverse("category_create"),
            reverse("category_edit", args=[category.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, f'href="{list_url}" aria-current="page"')


def checked_value(response, field):
    match = re.search(
        rf'name="{field}" value="([^"]+)"[^>]*\bchecked\b', response.content.decode()
    )
    return match and match[1]


@plain_static
class CreateCategoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def create(self, **data):
        return self.client.post(
            reverse("category_create"),
            {"name": "Groceries", "icon": "shopping-cart", "colour": "emerald"} | data,
        )

    def test_form_preselects_tag_and_a_palette_colour(self):
        response = self.client.get(reverse("category_create"))
        self.assertEqual(checked_value(response, "icon"), "bookmark")
        self.assertIn(checked_value(response, "colour"), PALETTE)

    def test_form_offers_every_curated_icon_and_colour(self):
        response = self.client.get(reverse("category_create"))
        for name, _ in ICONS:
            self.assertContains(response, f'name="icon" value="{name}"')
        for colour in PALETTE:
            self.assertContains(response, f'name="colour" value="{colour}"')

    def test_valid_create_saves_trimmed_name_and_redirects_to_list(self):
        response = self.create(name="  Groceries ")
        self.assertRedirects(response, reverse("category_list"))
        category = self.user.categories.get()
        self.assertEqual(
            (category.name, category.icon, category.colour),
            ("Groceries", "shopping-cart", "emerald"),
        )

    def test_rejects_duplicate_name_ignoring_case(self):
        self.user.categories.create(name="Groceries", icon="tag", colour="red")
        response = self.create(name="groceries")
        self.assertContains(response, "You already have a category called")
        self.assertEqual(self.user.categories.count(), 1)

    def test_other_users_names_do_not_clash(self):
        make_user("bob@example.com").categories.create(
            name="Groceries", icon="tag", colour="red"
        )
        response = self.create()
        self.assertRedirects(response, reverse("category_list"))

    def test_rejects_invalid_input(self):
        cases = {
            "blank name": ({"name": ""}, "This field is required."),
            "whitespace name": ({"name": "   "}, "This field is required."),
            "long name": ({"name": "x" * 51}, "at most 50 characters"),
            "unknown icon": ({"icon": "skull"}, "Select a valid choice."),
            "unknown colour": ({"colour": "black"}, "Select a valid choice."),
        }
        for label, (data, error) in cases.items():
            with self.subTest(label):
                response = self.create(**data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, error)
        self.assertFalse(self.user.categories.exists())


@plain_static
class EditCategoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.category = self.user.categories.create(
            name="Groceries", icon="shopping-cart", colour="emerald"
        )
        self.url = reverse("category_edit", args=[self.category.pk])

    def edit(self, **data):
        return self.client.post(
            self.url,
            {"name": "Groceries", "icon": "shopping-cart", "colour": "emerald"} | data,
        )

    def test_form_shows_current_values_and_delete_confirmation(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'value="Groceries"')
        self.assertEqual(checked_value(response, "icon"), "shopping-cart")
        self.assertEqual(checked_value(response, "colour"), "emerald")
        self.assertContains(response, "Delete <em>Groceries</em>?")
        self.assertContains(
            response, reverse("category_delete", args=[self.category.pk])
        )

    def test_rename_saves_trimmed_name_and_redirects_to_list(self):
        response = self.edit(name=" Food  ", icon="apple", colour="red")
        self.assertRedirects(response, reverse("category_list"))
        self.category.refresh_from_db()
        self.assertEqual(
            (self.category.name, self.category.icon, self.category.colour),
            ("Food", "apple", "red"),
        )

    def test_keeping_the_name_is_not_a_duplicate(self):
        response = self.edit(name="groceries", colour="red")
        self.assertRedirects(response, reverse("category_list"))
        self.category.refresh_from_db()
        self.assertEqual(
            (self.category.name, self.category.colour), ("groceries", "red")
        )

    def test_rename_rejects_duplicate_name_ignoring_case(self):
        self.user.categories.create(name="Rent", icon="house", colour="blue")
        response = self.edit(name="RENT")
        self.assertContains(response, "You already have a category called")
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Groceries")

    def test_rejects_invalid_input(self):
        response = self.edit(name="x" * 51)
        self.assertContains(response, "at most 50 characters")
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Groceries")


@plain_static
class DeleteCategoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.category = self.user.categories.create(
            name="Groceries", icon="shopping-cart", colour="emerald"
        )
        self.url = reverse("category_delete", args=[self.category.pk])

    def test_post_deletes_and_redirects_to_list(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("category_list"))
        self.assertFalse(self.user.categories.exists())

    def test_get_does_not_delete(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.user.categories.exists())


@plain_static
class OtherUsersCategoryTests(TestCase):
    def setUp(self):
        self.category = make_user("bob@example.com").categories.create(
            name="Bob secret", icon="tag", colour="red"
        )
        self.client.force_login(make_user())

    def test_edit_is_not_found(self):
        url = reverse("category_edit", args=[self.category.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(
            url, {"name": "Mine now", "icon": "tag", "colour": "red"}
        )
        self.assertEqual(response.status_code, 404)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Bob secret")

    def test_delete_is_not_found(self):
        response = self.client.post(reverse("category_delete", args=[self.category.pk]))
        self.assertEqual(response.status_code, 404)
        self.category.refresh_from_db()
