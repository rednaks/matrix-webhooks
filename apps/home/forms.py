from constance import config
from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField()
    invitation_code = forms.CharField(required=False)
    captcha_solution = forms.CharField(required=config.FRIENDLY_CAPTCHA_ENABLED)


class AuthForm(forms.Form):
    token = forms.CharField()
