from django.db import models
from django.contrib.auth.models import User

# 1. Resident Model (extends Django User)
class Resident(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    apartment_number = models.CharField(max_length=10)


    def __str__(self):
        return self.user.get_full_name() or self.user.username

# 2. Complaint Model
class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('water', 'Water Issue'),
        ('electricity', 'Electricity Issue'),
        ('noise', 'Noise Complaint'),
        ('security', 'Security Concern'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    ]

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='complaint_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# 3. ComplaintReply Model (admin or resident messages)
class ComplaintReply(models.Model):
    complaint = models.ForeignKey(Complaint, related_name='replies', on_delete=models.CASCADE)
    sender = models.CharField(max_length=100)  # e.g., 'Admin' or resident name
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.complaint.title} by {self.sender}"

# 4. Testimonial Model (optional user feedback)
class Testimonial(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(default=5)
    comments = models.TextField(blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Testimonial by {self.resident.user.username if self.resident else 'Anonymous'}"

# 5. ContactMessage Model (from public site form)
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message: {self.subject} by {self.name}"
