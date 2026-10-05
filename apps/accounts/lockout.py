from django.conf import settings

from .models import UserManager


def username(request, credentials):
    # Without this, each casing of one address gets its own failure count.
    data = credentials or getattr(request, "data", request.POST)
    return UserManager.normalize_email(data.get("username"))


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if settings.TRUST_X_FORWARDED_FOR and forwarded:
        # The proxy appends the address it saw; anything earlier came from the
        # client and can be forged.
        return forwarded.rsplit(",", 1)[-1].strip()
    return request.META.get("REMOTE_ADDR")
