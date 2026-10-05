from django_htmx.http import HttpResponseClientRedirect


def boost_middleware(get_response):
    def middleware(request):
        # Boosted navigation swaps only the shell's <main>, which pages for signed
        # out users, like sign-in after the session ends, don't fit into.
        if request.htmx.boosted and not request.user.is_authenticated:
            return HttpResponseClientRedirect(request.get_full_path())
        response = get_response(request)
        # A successful submit redirects, so the browser follows it with a GET. A
        # POST answered directly re-renders the form in place, and pushing its
        # URL would add a history entry that Back has to step through.
        if request.htmx.boosted and request.method == "POST":
            response["HX-Push-Url"] = "false"
        return response

    return middleware
