from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import HttpResponseBadRequest
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Complaint, Resident, Testimonial
from .forms import ComplaintForm, ResidentRegistrationForm, ContactForm, TestimonialForm
from fix.forms import CustomSetPasswordForm


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def is_admin(user):
    return user.is_staff or user.is_superuser


def send_resolution_email(complaint):
    """Send email notification to resident when complaint is resolved."""
    send_mail(
        subject='Your Complaint Has Been Resolved',
        message=(
            f'Dear {complaint.resident.user.first_name or complaint.resident.user.username},\n\n'
            f'Your complaint "{complaint.title}" has been marked as resolved.\n\n'
            'Thank you for your patience,\nYour Support Team'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[complaint.resident.user.email],
        fail_silently=False,
    )


def notify_admin_of_complaint(complaint):
    """Send email to admin when a new complaint is submitted."""
    send_mail(
        subject=f"New Complaint from {complaint.resident.user.username}",
        message=(
            f"User: {complaint.resident.user.username}\n"
            f"Apartment: {complaint.resident.apartment_number}\n"
            f"Title: {complaint.title}\n"
            f"Description: {complaint.description}\n"
            f"Status: {complaint.status}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
        fail_silently=False,
    )

# ---------------------------
# RESIDENT: SUBMIT COMPLAINT
# ---------------------------

@login_required(login_url='/signup/')
def complaint_page(request):
    resident, _ = Resident.objects.get_or_create(
        user=request.user,
        defaults={'apartment_number': 'N/A'}
    )

    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.resident = resident
            complaint.status = 'pending'
            complaint.save()

            # Email admin
            notify_admin_of_complaint(complaint)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('home')

        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {field: list(errors) for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)

    else:
        form = ComplaintForm()

    return render(request, 'complaint.html', {'form': form})


# ---------------------------
# TEMPLATE RENDERING VIEWS
# ---------------------------


def home_view(request):
    testimonials = Testimonial.objects.filter(approved=True).order_by('-created_at')[:5]

    # Get categories and statuses for the dropdowns
    categories = [choice[0] for choice in Complaint.CATEGORY_CHOICES]
    statuses = [choice[0] for choice in Complaint.STATUS_CHOICES]

    return render(request, 'index.html', {
        'testimonials': testimonials,
        'categories': categories,
        'statuses': statuses,
    })

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)
def community_guideline(request):
    return render(request, 'Community Guidelines.html')

def login_page(request):
    error = None
    if request.method == "POST":
        role = request.POST.get("role")  # 'admin' or 'user'
        username_or_email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=username_or_email, password=password)

        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            # ✅ Role validation
            if role == "admin" and not (user.is_staff or user.is_superuser):
                error = "You are not authorized for Admin Login."
            elif role == "user" and (user.is_staff or user.is_superuser):
                error = "Admins should use the Admin Login option."
            else:
                login(request, user)
                if role == "admin":
                    return redirect('admin_users_list')
                else:
                    return redirect('resident_dashboard')
        else:
            error = "Incorrect email or password. Please try again."

    return render(request, "login.html", {"error": error})


def sign_up_page(request):
    if request.method == "POST":
        form = ResidentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        # 👇 Prefill form from query params if available
        initial_data = {
            "email": request.GET.get("email", ""),
            "first_name": request.GET.get("first_name", ""),
            "last_name": request.GET.get("last_name", "")
        }
        form = ResidentRegistrationForm(initial=initial_data)

    return render(request, 'sign-up.html', {"form": form})

def contact_page(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # Send an email to admin
            subject = f"New Contact Message from {contact.name}"
            message = f"""
            Name: {contact.name}
            Email: {contact.email}

            Message:
            {contact.message}
            """
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,  # from
                    ["stemedge.edu@gmail.com"],   # to
                    fail_silently=False,
                )
            except Exception as e:
                return JsonResponse(
                    {"status": "error", "message": f"Failed to send email: {e}"},
                    status=500
                )

            return JsonResponse({"status": "success", "message": "Message sent successfully!"})
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    form = ContactForm()
    return render(request, 'contact.html', {"form": form})


def about_view(request):
    testimonials = Testimonial.objects.filter(approved=True).order_by('-created_at')[:5]
    return render(request, 'about.html', {
        'testimonials': testimonials,})

@login_required(login_url='/signup/')
def complaint_status_view(request):
    category = request.GET.get('category')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')

    complaints = Complaint.objects.filter(resident__user=request.user)

    if category and category != 'all':
        complaints = complaints.filter(category=category)
    if status_filter and status_filter != 'all':
        complaints = complaints.filter(status=status_filter)
    if search:
        complaints = complaints.filter(title__icontains=search)

    complaints = complaints.order_by('-created_at')
    no_results = not complaints.exists()

    # Get dynamic categories and statuses from model
    categories = [choice[0] for choice in Complaint.CATEGORY_CHOICES]
    statuses = [choice[0] for choice in Complaint.STATUS_CHOICES]

    context = {
        'complaints': complaints,
        'no_results': no_results,
        'categories': categories,
        'statuses': statuses,
        'filters': {
            'category': category or '',
            'status': status_filter or '',
            'search': search or ''
        }
    }
    return render(request, 'complaint_status.html', context)



@login_required(login_url='/signup/')
def feedback_page(request):
    resident, created = Resident.objects.get_or_create(
        user=request.user,
        defaults={'apartment_number': 'N/A'}
    )

    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.resident = resident
            testimonial.approved = False
            testimonial.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Thank you for your feedback!'})
            return redirect('home')

        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {field: list(errs) for field, errs in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)

    else:
        form = TestimonialForm()

    return render(request, 'feedback-form.html', {'form': form})
def test_email(request):
    subject = "Django Gmail Test"
    message = "This is a test email sent from Django using Gmail SMTP."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ["misbahzehra123@gmail.com"]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return HttpResponse("✅ Email sent successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send email: {e}")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('login')


# ---------------------------
# API VIEWS
# ---------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    apartment_number = request.data.get('apartment_number')
    phone_number = request.data.get('phone_number')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name
    )

    Resident.objects.create(
        user=user,
        apartment_number=apartment_number,
        phone_number=phone_number
    )

    send_mail(
        subject='Welcome to Neighborly!',
        message=f'Hi {first_name},\n\nThank you for registering at Neighborly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,
    )

    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'User registered successfully',
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



# -------------------
# RESIDENT DASHBOARD
# -------------------

@login_required
def resident_dashboard(request):
    resident = request.user.resident
    complaints = Complaint.objects.filter(resident=resident).order_by('-id')

    if request.method == "POST":
        # Create a new complaint
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category', 'other')

        complaint = Complaint.objects.create(
            resident=resident,
            title=title,
            description=description,
            category=category,
            status='pending'
        )

        # Send email to admin
        send_mail(
            subject='New Complaint Submitted',
            message=(
                f'A new complaint has been submitted by {request.user.username}:\n\n'
                f'Title: {complaint.title}\n\nDescription:\n{complaint.description}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=False,
        )

        # Send confirmation to resident
        send_mail(
            subject='Complaint Received',
            message=(
                f'Dear {request.user.username},\n\n'
                f'Your complaint "{complaint.title}" has been successfully submitted.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

    return render(request, 'resident_dashboard.html', {
        'complaints': complaints
    })

# -------------------
# ADMIN: UPDATE COMPLAINT STATUS (API)
# -------------------
@api_view(['POST'])
@user_passes_test(is_admin)
def update_complaint_status(request, complaint_id):
    """Handles both API (JSON) and HTML form status updates."""
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Get status from POST form or JSON
    new_status = request.data.get('status') or request.POST.get('status')
    if not new_status:
        return Response({'error': 'Status is required'}, status=400) \
            if request.content_type == 'application/json' else HttpResponseBadRequest("Status is required")

    complaint.status = new_status
    complaint.save()

    if new_status.lower() == 'resolved':
        send_resolution_email(complaint)

    # API client → JSON response
    if request.content_type == 'application/json':
        return Response({'message': f'Complaint status updated to {new_status}'}, status=200)

    # HTML form → redirect back to detail page
    return redirect('admin_user_detail', user_id=complaint.resident.id)


# -------------------
# ADMIN: USERS LIST (HTML page)
# -------------------
from django.db.models import Q
from django.db.models.functions import TruncMonth
from django.db.models import Count
@user_passes_test(is_admin)
def admin_users_list(request):
    query = request.GET.get('q', '')  
    users = Resident.objects.select_related('user').all()

    if query:
        users = users.filter(
            Q(user__username__icontains=query) |
            Q(apartment_number__icontains=query)
        )

    # Complaints
    pending_count = Complaint.objects.filter(status="pending").count()
    resolved_count = Complaint.objects.filter(status="resolved").count()

    # Residents over time
    residents_over_time = (
        Resident.objects.annotate(month=TruncMonth("user__date_joined"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    labels = [r["month"].strftime("%b %Y") for r in residents_over_time]
    data = [r["total"] for r in residents_over_time]

    return render(request, 'admin_users_list.html', {
        'users': users,
        'query': query,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'labels': labels,
        'data': data,
    })



# -------------------
# ADMIN: USER DETAIL + RESOLVE COMPLAINT (HTML form)
# -------------------

@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user_obj = get_object_or_404(Resident, id=user_id)
    complaints = Complaint.objects.filter(resident=user_obj)

    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        if complaint_id:
            complaint = get_object_or_404(Complaint, id=complaint_id, resident=user_obj)
            complaint.status = "resolved"
            complaint.save()

            # Email resident
            send_resolution_email(complaint)

            return redirect("admin_user_detail", user_id=user_id)

    return render(request, "admin_user_detail.html", {
        "user_obj": user_obj,
        "complaints": complaints
    })
# -------------------
# API: SUBMIT COMPLAINT (Resident)
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_complaint(request):
    """
    Allows logged-in resident to submit a complaint via API.
    """
    try:
        resident = request.user.resident
    except Resident.DoesNotExist:
        return Response({'error': 'Resident profile not found for this user.'}, status=400)

    title = request.data.get('title')
    description = request.data.get('description')
    category = request.data.get('category', 'other')

    if not title or not description:
        return Response({'error': 'Title and description are required'}, status=400)

    complaint = Complaint.objects.create(
        resident=resident,
        title=title,
        description=description,
        category=category,
        status='pending'
    )

    # Notify admin
    send_mail(
        subject='New Complaint Submitted',
        message=(
            f'A new complaint has been submitted by {request.user.username}:\n\n'
            f'Title: {complaint.title}\n\nDescription:\n{complaint.description}'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
        fail_silently=False,
    )

    # Notify resident
    send_mail(
        subject='Complaint Received',
        message=(
            f'Dear {request.user.username},\n\n'
            f'Your complaint "{complaint.title}" has been successfully submitted.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    return Response({'message': 'Complaint submitted successfully'}, status=200)
