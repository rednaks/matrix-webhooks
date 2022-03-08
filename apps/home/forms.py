from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField()


class AuthForm(forms.Form):
    token = forms.CharField()
