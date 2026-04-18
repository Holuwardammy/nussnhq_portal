from django.contrib import admin
from .models import Student, Payment, Event, Fundraising

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'department', 'level', 'user', 'serial_number')
    search_fields = ('full_name', 'user__email', 'department', 'serial_number')
    list_filter = ('department', 'level', 'school')
    ordering = ('id',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Added 'status' and 'payment_receipt' to list_display
    list_display = ('id', 'student', 'amount', 'status', 'paid', 'date_paid')
    
    # Allows you to filter by the new status (Pending, Processing, Paid)
    list_filter = ('status', 'paid', 'date_paid')
    
    # Search by student name or serial number
    search_fields = ('student__full_name', 'student__serial_number')
    
    # Optional: adds a clickable link to the receipt in the admin list
    readonly_fields = ('date_paid',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'date', 'location')
    search_fields = ('title', 'location')
    list_filter = ('date',)

@admin.register(Fundraising)
class FundraisingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'goal', 'description')
    search_fields = ('title',)