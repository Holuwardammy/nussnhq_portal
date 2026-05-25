from django.contrib import admin
from .models import (
    Student,
    Payment,
    Event,
    Fundraising,
    School,
    Tenure,
    ExecutivePosition,
    ExecutiveAssignment
)


# =========================================================
# STUDENT ADMIN
# =========================================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'full_name',
        'email',
        'school',
        'department',
        'level',
        'serial_number',
        'member_type',
        'is_verified',
        'registration_date'
    )

    search_fields = (
        'full_name',
        'email',
        'department',
        'school',
        'serial_number'
    )

    list_filter = (
        'school',
        'department',
        'level',
        'member_type',
        'is_verified'
    )

    readonly_fields = (
        'serial_number',
        'registration_date',
        'updated_at'
    )

    ordering = ('-registration_date',)


# =========================================================
# PAYMENT ADMIN
# =========================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'student',
        'amount',
        'status',
        'paid',
        'date_paid',
        'created_at'
    )

    list_filter = (
        'status',
        'paid',
        'created_at'
    )

    search_fields = (
        'student__full_name',
        'student__email',
        'student__serial_number'
    )

    readonly_fields = (
        'date_paid',
        'created_at'
    )

    ordering = ('-created_at',)


# =========================================================
# EVENT ADMIN
# =========================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'date',
        'location',
        'created_at'
    )

    search_fields = ('title', 'location')

    list_filter = ('date',)

    ordering = ('-date',)


# =========================================================
# FUNDRAISING ADMIN
# =========================================================
@admin.register(Fundraising)
class FundraisingAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'goal',
        'created_at'
    )

    search_fields = ('title',)

    ordering = ('-created_at',)


# =========================================================
# SCHOOL ADMIN
# =========================================================
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):

    list_display = ('id', 'name')

    search_fields = ('name',)

    ordering = ('name',)


# =========================================================
# TENURE ADMIN
# =========================================================
@admin.register(Tenure)
class TenureAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'session',
        'is_active',
        'created_at'
    )

    list_filter = ('is_active',)

    search_fields = ('session',)

    ordering = ('-created_at',)


# =========================================================
# EXECUTIVE POSITION ADMIN
# =========================================================
@admin.register(ExecutivePosition)
class ExecutivePositionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'created_at'
    )

    search_fields = ('title',)

    ordering = ('title',)


# =========================================================
# EXECUTIVE ASSIGNMENT ADMIN (FULLY MATCHED SYSTEM)
# =========================================================
@admin.register(ExecutiveAssignment)
class ExecutiveAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'student',
        'position',
        'tenure',
        'is_active',
        'assigned_at',
        'removed_at'
    )

    list_filter = (
        'position',
        'tenure',
        'is_active'
    )

    search_fields = (
        'student__full_name',
        'student__email',
        'position__title',
        'tenure__session'
    )

    readonly_fields = (
        'assigned_at',
        'removed_at'
    )

    ordering = ('-assigned_at',)

    actions = [
        'activate_executive',
        'deactivate_executive'
    ]

    # =====================================================
    # SAFE ACTION: ACTIVATE EXECUTIVE
    # =====================================================
    def activate_executive(self, request, queryset):
        for obj in queryset:
            obj.is_active = True
            obj.save()

    activate_executive.short_description = "Activate selected executives"

    # =====================================================
    # SAFE ACTION: DEACTIVATE EXECUTIVE
    # =====================================================
    def deactivate_executive(self, request, queryset):
        for obj in queryset:
            obj.is_active = False
            obj.save()

    deactivate_executive.short_description = "Deactivate selected executives"