from django.db import connection
from django.http import HttpResponse


def healthz_middleware(get_response):
    # Answered ahead of SecurityMiddleware and host validation, so container
    # probes over plain HTTP to 127.0.0.1 succeed whatever SECURE_SSL_REDIRECT
    # and ALLOWED_HOSTS say.
    def middleware(request):
        if request.path == "/healthz/":
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return HttpResponse("ok", content_type="text/plain")
        return get_response(request)

    return middleware
