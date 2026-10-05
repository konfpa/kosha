from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

from .choices import COLOURS, ICONS


def icon_choices():
    return ICONS


def colour_choices():
    return COLOURS


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=50)
    # Callables keep migrations from churning whenever the lists change.
    icon = models.CharField(max_length=50, choices=icon_choices)
    colour = models.CharField(max_length=20, choices=colour_choices)
    description = models.CharField(max_length=120, blank=True, default="")
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = [Lower("name")]
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                "user", Lower("name"), name="unique_category_name_per_user"
            ),
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=50)

    class Meta:
        ordering = [Lower("name")]
        constraints = [
            models.UniqueConstraint(
                "user", Lower("name"), name="unique_tag_name_per_user"
            ),
        ]

    def __str__(self):
        return self.name
