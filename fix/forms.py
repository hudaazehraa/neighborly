from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import Resident, Complaint, ComplaintReply, Testimonial, ContactMessage
import re
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm


# ---------- Admin Registration ----------
# from django.contrib import admin
# admin.site.register(Complaint)
# admin.site.register(Resident)

# ---------- Registration Form ----------
class ResidentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    apartment_number = forms.CharField(max_length=10, required=True)
    # phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'apartment_number',  'password1', 'password2'
        ]

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.match(r"^[A-Za-z\s'-]+$", first_name):
            raise forms.ValidationError(
                "First name can only contain letters, spaces, apostrophes, and hyphens."
            )
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(r"^[A-Za-z\s'-]+$", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, apostrophes, and hyphens."
            )
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Resident.objects.create(
                user=user,
                apartment_number=self.cleaned_data.get('apartment_number', ''),
                # phone_number=self.cleaned_data.get('phone_number', '')
            )
        return user

# ---------- Login Form ----------
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# ---------- Complaint Submission Form ----------
class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter complaint title',
                'id': 'id_title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your complaint here...',
                'id': 'id_description'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'id': 'id_image'
            }),
        }

# ---------- Complaint Reply Form ----------
class ComplaintReplyForm(forms.ModelForm):
    class Meta:
        model = ComplaintReply
        fields = ['message']

# ---------- Testimonial Form ----------
class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['rating', 'comments'] 
        widgets = {
            'message': forms.Textarea(attrs={
                'placeholder': 'Enter your feedback here...',
                'rows': 5,
                'class': 'form-control',
            }),
        }
# ---------- Contact Form ----------
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your Full Name',
                'class': 'form-control',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address',
                'class': 'form-control',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Your Message',
                'class': 'form-control',
                'rows': 5,
                'required': True
            }),
        }

# class CustomSetPasswordForm(SetPasswordForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['new_password1'].widget.attrs.update({
#             'placeholder': 'Enter new password',
#             'id': 'id_new_password1'
#         })
#         self.fields['new_password2'].widget.attrs.update({
#             'placeholder': 'Confirm new password',
#             'id': 'id_new_password2'
#         })
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add placeholders
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': 'Enter new password',
            'class': 'form-control'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': 'Confirm new password',
            'class': 'form-control'
        })

    def clean(self):
        cleaned_data = super().clean()
        # Django will already add errors for mismatch & validation rules
        return cleaned_data


class CustomSocialSignupForm(SignupForm):
    username = forms.CharField(max_length=30, required=True, label="Username")
    apartment_number = forms.CharField(max_length=10, required=True, label="Apartment Number")

    def __init__(self, *args, **kwargs):
        # Pop sociallogin to avoid __init__ error but keep if needed later
        self.sociallogin = kwargs.pop('sociallogin', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def signup(self, request, user):
        # Set username and save user instance
        user.username = self.cleaned_data['username']
        user.save()

        # Create or update Resident profile with apartment number
        resident, created = Resident.objects.get_or_create(user=user)
        resident.apartment_number = self.cleaned_data['apartment_number']
        resident.save()

        return user

