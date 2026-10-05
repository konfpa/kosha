from django.conf import settings
from django.contrib.auth import views as auth_views

from .forms import LoginForm

RESET_EMAIL_SESSION_KEY = "password_reset_email"


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data["remember"]:
            # Not 0 (browser close): an installed PWA "closes" whenever the OS
            # kills it.
            self.request.session.set_expiry(settings.SESSION_SHORT_AGE)
        return response


class PasswordResetView(auth_views.PasswordResetView):
    email_template_name = "registration/password_reset_email.txt"
    html_email_template_name = "registration/password_reset_email.html"

    def form_valid(self, form):
        # Lets the "sent" page name the address and offer to send again.
        self.request.session[RESET_EMAIL_SESSION_KEY] = form.cleaned_data["email"]
        return super().form_valid(form)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get(RESET_EMAIL_SESSION_KEY)
        return context
