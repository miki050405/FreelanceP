from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "example@mail.com"})}


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "avatar", "bio", "location", "skills", "qr_code"]
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+996 ..."}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Коротко о себе"}),
            "location": forms.TextInput(attrs={"placeholder": "Город"}),
            "skills": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Python, Django, SQL ..."}
            ),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class LoginForm(AuthenticationForm):
    pass
