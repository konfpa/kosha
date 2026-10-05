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

    def test_every_tag_url_redirects_to_login(self):
        tag = make_user().tags.create(name="gift")
        urls = [
            reverse("tag_list"),
            reverse("tag_create"),
            reverse("tag_edit", args=[tag.pk]),
            reverse("tag_delete", args=[tag.pk]),
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

    def test_shows_description_but_not_note(self):
        self.user.categories.create(
            name="Groceries",
            icon="tag",
            colour="red",
            description="Supermarket, not eating out",
            note="Budget 8k a month",
        )
        response = self.client.get(reverse("category_list"))
        self.assertContains(response, "Supermarket, not eating out")
        self.assertNotContains(response, "Budget 8k a month")

    def test_category_without_description_shows_only_its_name(self):
        self.user.categories.create(name="Rent", icon="house", colour="blue")
        response = self.client.get(reverse("category_list"))
        self.assertRegex(response.content.decode(), r">Rent</span>\s*</span>")

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

    def test_saves_trimmed_description_and_note(self):
        self.create(
            description="  Supermarket ", note="\n Budget 8k\r\n- no takeaway \n"
        )
        category = self.user.categories.get()
        self.assertEqual(
            (category.description, category.note),
            ("Supermarket", "Budget 8k\n- no takeaway"),
        )

    def test_description_and_note_are_optional(self):
        response = self.create(description="   ")
        self.assertRedirects(response, reverse("category_list"))
        category = self.user.categories.get()
        self.assertEqual((category.description, category.note), ("", ""))

    def test_note_line_breaks_count_as_one_character(self):
        response = self.create(note="x" * 499 + "\r\n" + "x" * 500)
        self.assertRedirects(response, reverse("category_list"))
        self.assertEqual(len(self.user.categories.get().note), 1000)

    def test_rejects_duplicate_name_ignoring_case(self):
        self.user.categories.create(name="Groceries", icon="tag", colour="red")
        response = self.create(name="groceries")
        self.assertContains(response, "You already have a category called")
        self.assertEqual(self.user.categories.count(), 1)

    def test_failed_save_keeps_description_and_note(self):
        self.user.categories.create(name="Groceries", icon="tag", colour="red")
        response = self.create(description="Supermarket", note="Line one\nLine two")
        self.assertContains(response, 'value="Supermarket"')
        self.assertContains(response, ">\nLine one\nLine two</textarea>")

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
            "long description": ({"description": "x" * 121}, "at most 120 characters"),
            "long note": ({"note": "x" * 1001}, "at most 1000 characters"),
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
            name="Groceries",
            icon="shopping-cart",
            colour="emerald",
            description="Supermarket",
            note="Line one\nLine two",
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
        self.assertContains(response, 'value="Supermarket"')
        self.assertContains(response, ">\nLine one\nLine two</textarea>")
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

    def test_changes_and_clears_description_and_note(self):
        cases = {
            "change": (
                {"description": "Food", "note": "New note"},
                ("Food", "New note"),
            ),
            "clear": ({"description": "", "note": ""}, ("", "")),
        }
        for label, (data, expected) in cases.items():
            with self.subTest(label):
                response = self.edit(**data)
                self.assertRedirects(response, reverse("category_list"))
                self.category.refresh_from_db()
                self.assertEqual(
                    (self.category.description, self.category.note), expected
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
        cases = {
            "long name": ({"name": "x" * 51}, "at most 50 characters"),
            "long description": ({"description": "x" * 121}, "at most 120 characters"),
            "long note": ({"note": "x" * 1001}, "at most 1000 characters"),
        }
        for label, (data, error) in cases.items():
            with self.subTest(label):
                response = self.edit(**data)
                self.assertContains(response, error)
        self.category.refresh_from_db()
        self.assertEqual(
            (self.category.name, self.category.description, self.category.note),
            ("Groceries", "Supermarket", "Line one\nLine two"),
        )


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


@plain_static
class TagListTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_empty_state_offers_new_tag(self):
        response = self.client.get(reverse("tag_list"))
        self.assertContains(response, "No tags yet")
        self.assertContains(response, reverse("tag_create"))

    def test_lists_own_tags_alphabetically_ignoring_case(self):
        for name in ("reimbursable", "Gift", "goa-trip-2026", "Bills"):
            self.user.tags.create(name=name)
        make_user("bob@example.com").tags.create(name="Bob secret")

        response = self.client.get(reverse("tag_list"))

        content = response.content.decode()
        positions = [
            content.index(f">{name}<")
            for name in ("Bills", "Gift", "goa-trip-2026", "reimbursable")
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertNotContains(response, "Bob secret")
        self.assertNotContains(response, "No tags yet")

    def test_links_each_tag_to_its_edit_page(self):
        tag = self.user.tags.create(name="gift")
        response = self.client.get(reverse("tag_list"))
        self.assertContains(response, reverse("tag_edit", args=[tag.pk]))

    def test_sidebar_marks_tags_active_on_every_tags_page(self):
        tag = self.user.tags.create(name="gift")
        list_url = reverse("tag_list")
        for url in (
            list_url,
            reverse("tag_create"),
            reverse("tag_edit", args=[tag.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, f'href="{list_url}" aria-current="page"')

    def test_sidebar_groups_categories_and_tags_under_classification(self):
        for url in (reverse("home"), reverse("tag_list")):
            with self.subTest(url=url):
                content = self.client.get(url).content.decode()
                positions = [
                    content.index(">Classification<"),
                    content.index(f'href="{reverse("category_list")}"'),
                    content.index(f'href="{reverse("tag_list")}"'),
                ]
                self.assertEqual(positions, sorted(positions))


@plain_static
class CreateTagTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def create(self, name):
        return self.client.post(reverse("tag_create"), {"name": name})

    def test_form_asks_only_for_a_name(self):
        response = self.client.get(reverse("tag_create"))
        self.assertContains(response, "New tag")
        self.assertContains(response, 'name="name"')
        self.assertNotContains(response, 'name="icon"')
        self.assertNotContains(response, 'name="colour"')

    def test_valid_create_saves_trimmed_name_as_typed_and_redirects_to_list(self):
        response = self.create("  Goa Trip-2026 ")
        self.assertRedirects(response, reverse("tag_list"))
        self.assertEqual(self.user.tags.get().name, "Goa Trip-2026")

    def test_rejects_duplicate_name_ignoring_case(self):
        self.user.tags.create(name="Gift")
        response = self.create("gift")
        self.assertContains(response, "You already have a tag called “gift”.")
        self.assertEqual(self.user.tags.count(), 1)

    def test_other_users_names_do_not_clash(self):
        make_user("bob@example.com").tags.create(name="gift")
        response = self.create("gift")
        self.assertRedirects(response, reverse("tag_list"))

    def test_may_share_a_name_with_a_category(self):
        self.user.categories.create(name="Gift", icon="gift", colour="red")
        response = self.create("Gift")
        self.assertRedirects(response, reverse("tag_list"))

    def test_rejects_invalid_input(self):
        cases = {
            "blank name": ("", "This field is required."),
            "whitespace name": ("   ", "This field is required."),
            "long name": ("x" * 51, "at most 50 characters"),
        }
        for label, (name, error) in cases.items():
            with self.subTest(label):
                response = self.create(name)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, error)
        self.assertFalse(self.user.tags.exists())


@plain_static
class EditTagTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.tag = self.user.tags.create(name="Gift")
        self.url = reverse("tag_edit", args=[self.tag.pk])

    def edit(self, name):
        return self.client.post(self.url, {"name": name})

    def test_form_shows_current_name_and_delete_confirmation(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Edit tag")
        self.assertContains(response, 'value="Gift"')
        self.assertContains(response, "Delete <em>Gift</em>?")
        self.assertContains(response, reverse("tag_delete", args=[self.tag.pk]))

    def test_rename_saves_trimmed_name_and_redirects_to_list(self):
        response = self.edit(" Present  ")
        self.assertRedirects(response, reverse("tag_list"))
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, "Present")

    def test_keeping_the_name_or_changing_its_case_is_not_a_duplicate(self):
        for name in ("Gift", "gift"):
            with self.subTest(name):
                response = self.edit(name)
                self.assertRedirects(response, reverse("tag_list"))
                self.tag.refresh_from_db()
                self.assertEqual(self.tag.name, name)

    def test_rename_rejects_duplicate_name_ignoring_case(self):
        self.user.tags.create(name="reimbursable")
        response = self.edit("REIMBURSABLE")
        self.assertContains(response, "You already have a tag called")
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, "Gift")

    def test_rejects_invalid_input(self):
        cases = {
            "blank name": ("", "This field is required."),
            "whitespace name": ("   ", "This field is required."),
            "long name": ("x" * 51, "at most 50 characters"),
        }
        for label, (name, error) in cases.items():
            with self.subTest(label):
                response = self.edit(name)
                self.assertContains(response, error)
                self.assertContains(response, "Delete <em>Gift</em>?")
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, "Gift")


@plain_static
class DeleteTagTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.tag = self.user.tags.create(name="Gift")
        self.url = reverse("tag_delete", args=[self.tag.pk])

    def test_post_deletes_and_redirects_to_list(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("tag_list"))
        self.assertFalse(self.user.tags.exists())

    def test_get_does_not_delete(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.user.tags.exists())


@plain_static
class OtherUsersTagTests(TestCase):
    def setUp(self):
        self.tag = make_user("bob@example.com").tags.create(name="Bob secret")
        self.client.force_login(make_user())

    def test_edit_is_not_found(self):
        url = reverse("tag_edit", args=[self.tag.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, {"name": "Mine now"})
        self.assertEqual(response.status_code, 404)
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, "Bob secret")

    def test_delete_is_not_found(self):
        response = self.client.post(reverse("tag_delete", args=[self.tag.pk]))
        self.assertEqual(response.status_code, 404)
        self.tag.refresh_from_db()
