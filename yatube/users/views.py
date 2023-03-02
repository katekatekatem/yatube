from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('posts:index')


class PasswordChange(PasswordChangeForm):
    form_class = PasswordChangeForm
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')


class PasswordReset(PasswordResetForm):
    form_class = PasswordChangeForm
    template_name = 'users/password_reset_form.html'
    success_url = reverse_lazy('users:password_reset_done')
