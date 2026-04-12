from django.contrib import admin
from .models import Student, Payment, Event, Fundraising


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'department', 'user')
    search_fields = ('full_name', 'user__email', 'department')
    list_filter = ('department',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'amount', 'paid', 'date_paid')
    search_fields = ('student__full_name',)
    list_filter = ('paid',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'date')
    search_fields = ('title',)


@admin.register(Fundraising)
class FundraisingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'goal')
    search_fields = ('title',)