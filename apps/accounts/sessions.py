import time

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

LOGIN_AT_SESSION_KEY = "login_at"


@receiver(user_logged_in)
def record_login_time(*, request, **_):
    request.session[LOGIN_AT_SESSION_KEY] = time.time()


def max_age_middleware(get_response):
    # Sessions slide forward on every request, so without this cap a device
    # in daily use would stay signed in forever.
    def middleware(request):
        if request.user.is_authenticated:
            login_at = request.session.get(LOGIN_AT_SESSION_KEY, 0)
            if time.time() - login_at > settings.SESSION_MAX_AGE:
                logout(request)
        return get_response(request)

    return middleware
