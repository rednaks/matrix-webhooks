from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField()
    invitation_code = forms.CharField(required=False)


class AuthForm(forms.Form):
    token = forms.CharField()
