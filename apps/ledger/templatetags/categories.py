from django import template

from apps.ledger.choices import PALETTE
from apps.ui.templatetags.icons import icon

register = template.Library()


@register.simple_tag
def category_icon(category, size="size-5"):
    """A category's icon drawn in its colour: {% category_icon category "size-4" %}."""
    return icon(
        category.icon, **{"class": f"{size} shrink-0 {PALETTE[category.colour]}"}
    )


@register.filter
def colour_classes(colour):
    return PALETTE[colour]
