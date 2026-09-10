from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import (
    ACTIVITY_LEVEL_CHOICES, FITNESS_LEVEL_CHOICES, GENDER_CHOICES,
    GOAL_CHOICES, LOCATION_CHOICES,
)


class RegisterForm(forms.Form):
    fullName = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    mobile = forms.CharField(max_length=20)
    email = forms.EmailField()
    password = forms.CharField(min_length=8)
    confirmPassword = forms.CharField()
    agreeTerms = forms.BooleanField(required=True)

    def clean_username(self):
        value = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError("This username is already taken.")
        return value

    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("An account with this email already exists.")
        return value

    def clean_password(self):
        value = self.cleaned_data["password"]
        validate_password(value)
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("confirmPassword") and cleaned["password"] != cleaned["confirmPassword"]:
            self.add_error("confirmPassword", "Passwords do not match.")
        return cleaned


class LoginForm(forms.Form):
    loginId = forms.CharField()
    loginPassword = forms.CharField()


class ForgotPasswordForm(forms.Form):
    resetEmail = forms.EmailField()


class AdminLoginForm(forms.Form):
    adminUser = forms.CharField()
    adminPassword = forms.CharField()


class BodyDetailsForm(forms.Form):
    age = forms.IntegerField(min_value=13, max_value=90)
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    height = forms.FloatField()
    heightUnit = forms.CharField(required=False)
    weight = forms.FloatField()
    weightUnit = forms.CharField(required=False)
    targetWeight = forms.FloatField()
    targetWeightUnit = forms.CharField(required=False)
    fitnessLevel = forms.ChoiceField(choices=FITNESS_LEVEL_CHOICES)
    activityLevel = forms.ChoiceField(choices=ACTIVITY_LEVEL_CHOICES)
    measurements = forms.CharField(required=False)


class PreferencesForm(forms.Form):
    workoutLocation = forms.ChoiceField(choices=LOCATION_CHOICES)
    workoutDays = forms.IntegerField(min_value=1, max_value=7)
    workoutDuration = forms.CharField()
    workoutTime = forms.CharField()


class ProfileEditForm(forms.Form):
    fullName = forms.CharField(max_length=150)
    email = forms.EmailField()
    mobile = forms.CharField(max_length=20, required=False)
    age = forms.IntegerField(required=False, min_value=10, max_value=100)
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    height = forms.FloatField(required=False)


class FitnessPreferencesEditForm(forms.Form):
    weight = forms.FloatField()
    targetWeight = forms.FloatField()
    goal = forms.ChoiceField(choices=GOAL_CHOICES)
    fitnessLevel = forms.ChoiceField(choices=FITNESS_LEVEL_CHOICES)
    workoutDays = forms.IntegerField(min_value=1, max_value=7)
    workoutLocation = forms.ChoiceField(choices=LOCATION_CHOICES)


class ChangePasswordForm(forms.Form):
    currentPassword = forms.CharField()
    newPassword = forms.CharField(min_length=8)
    confirmNewPassword = forms.CharField()

    def clean_newPassword(self):
        value = self.cleaned_data["newPassword"]
        validate_password(value)
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("newPassword") and cleaned.get("confirmNewPassword") and cleaned["newPassword"] != cleaned["confirmNewPassword"]:
            self.add_error("confirmNewPassword", "Passwords do not match.")
        return cleaned
