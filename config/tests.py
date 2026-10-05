import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

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


@plain_static
class PwaTests(TestCase):
    def test_manifest_is_public_json(self):
        response = self.client.get(reverse("manifest"))
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        manifest = json.loads(response.content)
        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(manifest["display"], "standalone")

    def test_service_worker_is_served_from_root(self):
        response = self.client.get(reverse("service_worker"))
        self.assertEqual(response.request["PATH_INFO"], "/sw.js")
        self.assertEqual(response["Content-Type"], "text/javascript")
        self.assertContains(response, '"/offline/"')

    def test_offline_page_is_public(self):
        response = self.client.get(reverse("offline"))
        self.assertContains(response, "You're offline")

    def test_pages_link_manifest(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, "serviceWorker.register")
