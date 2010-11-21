from django.contrib.auth.models import User
from django import forms
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth.forms
# from django.contrib.auth.forms import 

class UserAlterDetailsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]

class UserAlterPasswordForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["password"]
