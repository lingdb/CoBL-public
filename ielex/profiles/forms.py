from django.contrib.auth.models import User
from django import forms

class UserAlterDetailsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]

class UserAlterPasswordForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["password"]
