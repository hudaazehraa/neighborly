from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from .models import Resident

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        print("🔍 Adapter triggered!")  # Debugging log

        user = sociallogin.user

        # If already authenticated user → allow
        if user and user.id:
            print("✅ Existing user, proceed")
            return

        # If email exists in Resident model → allow
        if user.email and Resident.objects.filter(user__email=user.email).exists():
            print("✅ Resident with email exists, proceed")
            return

        # Otherwise → redirect to signup page WITH prefilled values
        print("🚨 Redirecting new Google user to signup page")
        signup_url = reverse("signup")
        signup_url += f"?email={user.email or ''}&first_name={user.first_name or ''}&last_name={user.last_name or ''}"

        raise ImmediateHttpResponse(redirect(signup_url))