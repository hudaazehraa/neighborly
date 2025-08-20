from django.contrib import admin
from .models import Resident, Complaint, ContactMessage ,Testimonial


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ('user', 'apartment_number',)
    search_fields = ('user__username', 'apartment_number',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'timestamp')
    search_fields = ('name', 'email', 'message')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'resident', 'category', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description', 'resident__user__username')

admin.site.register(Testimonial)