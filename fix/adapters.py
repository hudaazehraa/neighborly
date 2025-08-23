from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login
from .models import Resident

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user

        # Already logged in → allow
        if user and user.id:
            return

        # If this Google user matches a Resident
        try:
            resident = Resident.objects.get(user__email=user.email)
            user = resident.user
            user.is_active = True
            user.save()

            # Explicit backend (important when multiple backends exist)
            user.backend = 'allauth.account.auth_backends.AuthenticationBackend'
            login(request, user)

            # 🚨 Stop allauth from continuing → redirect to dashboard/home
            raise ImmediateHttpResponse(redirect("/"))

        except Resident.DoesNotExist:
            # 🚨 Instead of allauth’s form → redirect to your signup page
            signup_url = reverse("signup")
            signup_url += f"?email={user.email or ''}&first_name={user.first_name or ''}&last_name={user.last_name or ''}"
            raise ImmediateHttpResponse(redirect(signup_url))
