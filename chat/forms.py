from django import forms
from .models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['name', 'mobile', 'password']

class LoginForm(forms.Form):
    mobile = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
