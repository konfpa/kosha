import secrets
from http import HTTPStatus

from django.conf import settings
from django.utils.cache import patch_cache_control, patch_vary_headers
from django_htmx.http import HttpResponseClientRedirect

PRELOAD_MAX_AGE = 10


def boost_middleware(get_response):
    def middleware(request):
        # Boosted navigation swaps only the shell's <main>, which pages for signed
        # out users, like sign-in after the session ends, don't fit into.
        if request.htmx.boosted and not request.user.is_authenticated:
            return HttpResponseClientRedirect(request.get_full_path())
        response = get_response(request)
        if request.method == "POST":
            # A successful submit redirects, so the browser follows it with a
            # GET. A POST answered directly re-renders the form in place, and
            # pushing its URL would add a history entry Back has to step through.
            if request.htmx.boosted:
                response["HX-Push-Url"] = "false"
            # Preloaded pages vary on cookies, so a new value here makes every
            # copy cached before the change miss, the redirect target included.
            if request.user.is_authenticated:
                response.set_cookie(
                    "data_version",
                    secrets.token_hex(4),
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=True,
                    samesite="Lax",
                )
        elif (
            request.headers.get("HX-Preloaded") == "true"
            and response.status_code == HTTPStatus.OK
            and request.user.is_authenticated
        ):
            # The preload extension hands a hovered page to the click through
            # the browser cache, so allow a brief copy that only this session
            # can reuse.
            patch_cache_control(response, private=True, max_age=PRELOAD_MAX_AGE)
            patch_vary_headers(response, ["Cookie"])
        return response

    return middleware
