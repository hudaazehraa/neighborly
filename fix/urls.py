from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from fix.views import CustomPasswordResetConfirmView
from django.contrib import admin

urlpatterns = [
    # ---------- Template Rendering Views ----------
    path('', views.home_view, name='home'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.sign_up_page, name='signup'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('complaint/', views.complaint_page, name='complaints'),
    path('complaints/status/', views.complaint_status_view, name='complaint_status'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('404/', views.custom_404_view, name='404'),
    path('admin-dashboard/users/', views.admin_users_list, name='admin_users_list'),
    path('admin-dashboard/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('resident/dashboard/', views.resident_dashboard, name='resident_dashboard'),
    path('community/',views.community_guideline, name='guideline'),
    path('feedback/', views.feedback_page, name='feedback'),
    path('forgot_password/',auth_views.PasswordResetView.as_view(template_name='forgot.html'),name='forgot_password'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),
    path("test-email/", views.test_email, name="test_email"),
      # normal Django admin site
    path('admin/', admin.site.urls),
    # ---------- API Endpoints ----------
    path('api/signup/', views.signup_api, name='api_signup'),
    path('api/login/', views.login_api, name='api_login'),
    path('api/complaints/submit/', views.submit_complaint, name='submit_complaint'),

    # ---------- Authentication / Social Login ----------
    path('auth/', include('dj_rest_auth.urls')),  # login/logout/password reset
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # sign up
    path('auth/social/', include('allauth.socialaccount.urls')),  # for Google login
    path('accounts/', include('allauth.urls')),  # needed for Google OAuth flow
    
]
