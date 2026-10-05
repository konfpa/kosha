import json
from functools import cache
from pathlib import Path

from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()

LUCIDE = Path(__file__).resolve().parent.parent / "vendor" / "lucide-1.52.0.json"

DEFAULTS = {
    "xmlns": "http://www.w3.org/2000/svg",
    "width": 24,
    "height": 24,
    "viewBox": "0 0 24 24",
    "fill": "none",
    "stroke": "currentColor",
    "stroke-width": 2,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "aria-hidden": "true",
}


@cache
def _lucide():
    return json.loads(LUCIDE.read_text())


def _attrs(attrs):
    return format_html_join("", ' {}="{}"', attrs.items())


@register.simple_tag
def icon(name, **attrs):
    """Inline a Lucide icon: {% icon "eye" class="size-4" stroke_width=1.75 %}."""
    try:
        nodes = _lucide()[name]
    except KeyError:
        raise template.TemplateSyntaxError(f"Unknown Lucide icon {name!r}") from None
    attrs = DEFAULTS | {key.replace("_", "-"): value for key, value in attrs.items()}
    children = format_html_join("", "<{}{}/>", ((tag, _attrs(a)) for tag, a in nodes))
    return format_html("<svg{}>{}</svg>", _attrs(attrs), children)
