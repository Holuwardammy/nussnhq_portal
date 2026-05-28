from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Student,
    Payment,
    Event,
    Fundraising,
    School,
    ExecutiveAssignment,
    ExecutivePosition,
    Tenure,
    Announcement,
    Scholarship  # UPDATED: Imported the Scholarship Model
)

from .forms import (
    StudentForm,
    EventForm,
    FundraisingForm,
    AnnouncementForm,
    ScholarshipForm  # UPDATED: Imported the Scholarship Form
)

# =========================================================
# HELPERS
# =========================================================
def get_active_student(user):
    return Student.objects.filter(user=user).first()

def is_executive(user):
    student = get_active_student(user)
    return student and student.executive_assignments.filter(is_active=True).exists()

def is_president(user):
    student = get_active_student(user)
    return student and student.executive_assignments.filter(
        position__title='president',
        is_active=True
    ).exists()


# =========================================================
# HOME
# =========================================================
from django.http import HttpResponse

def home(request):
    # Quick intercept: If it's just an uptime bot checking if the server is breathing, 
    # give it a fast, clean 200 OK without running template rendering engine tasks.
    if request.method == 'HEAD':
        return HttpResponse()

    events = Event.objects.all().order_by('-date')
    return render(request, 'home.html', {'events': events})


# =========================================================
# REGISTER STUDENT
# =========================================================
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            student = form.save(commit=False)
            student.member_type = 'student'

            school_name = request.POST.get('school', '').strip()
            if school_name:
                # 1. Get or create the actual School database object row
                school_obj, created = School.objects.get_or_create(name=school_name)
                # 2. Assign the object directly to the foreign key relationship
                student.school = school_obj  

            student.save()

            messages.success(request, "Registration successful!")
            return redirect('login')

        messages.error(request, "Please correct errors.")
    else:
        form = StudentForm()

    return render(request, 'register_student.html', {'form': form})


# =========================================================
# LOGIN
# =========================================================
def login_view(request):

    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)

            if is_executive(user):
                return redirect('admin_dashboard')

            return redirect('student_home')

        messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


# =========================================================
# LOGOUT
# =========================================================
def logout_view(request):
    logout(request)
    return redirect('home')


# =========================================================
# STUDENT HOME
# =========================================================
@login_required
def student_home(request):
    student = get_object_or_404(Student, user=request.user)
    
    # Check the latest payment status for lockdown
    all_payments = Payment.objects.filter(student=student).order_by('-created_at')
    latest_payment = all_payments.first()
    is_paid_member = latest_payment and latest_payment.status == 'paid'

    if is_paid_member:
        # SECURE: Only query and pass data if dues are fully cleared
        announcements = Announcement.objects.all().order_by('-is_pinned', '-date_posted')
        scholarships = Scholarship.objects.filter(is_active=True).order_by('deadline')
        events = Event.objects.all()
        fundraising = Fundraising.objects.all()
    else:
        # BLOCK: Send completely empty data streams to unpaid profiles
        announcements = Announcement.objects.none()
        scholarships = Scholarship.objects.none()
        events = Event.objects.none()
        fundraising = Fundraising.objects.none()

    return render(request, 'student_home.html', {
        'student': student,
        'payments': all_payments,
        'events': events,
        'fundraising': fundraising,
        'announcements': announcements,
        'scholarships': scholarships,
        'is_paid_member': is_paid_member, # Passed helper boolean to control template layout layers
    })


# =========================================================
# PAYMENT INSTRUCTIONS  
# =========================================================
@login_required
def payment_instructions(request):
    student = get_object_or_404(Student, user=request.user)
    return render(request, 'payment_instructions.html', {'student': student})


# =========================================================
# SUBMIT PAYMENT
# =========================================================
@login_required
def submit_payment(request):

    student = get_object_or_404(Student, user=request.user)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        receipt = request.FILES.get('payment_receipt')

        if receipt:
            Payment.objects.create(
                student=student,
                amount=amount,
                payment_receipt=receipt,
                status='processing'
            )

            messages.success(request, "Payment submitted.")
            return redirect('student_home')

    return render(request, 'submit_payment.html', {'student': student})


# =========================================================
# SCHOOL AUTOCOMPLETE  
# =========================================================
def school_autocomplete(request):
    query = request.GET.get('term', '')
    schools = School.objects.filter(name__icontains=query)[:10]
    results = [school.name for school in schools]
    return JsonResponse(results, safe=False)


# =========================================================
# ADMIN DASHBOARD (UPDATED FOR SCHOLARSHIPS)
# =========================================================
@login_required
def admin_dashboard(request):
    student = get_active_student(request.user)

    if not is_executive(request.user):
        messages.error(request, "Executives only.")
        return redirect('student_home')

    active_tenure = Tenure.objects.filter(is_active=True).first()

    total_income = Payment.objects.filter(status='paid').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    all_payments = Payment.objects.annotate(
        priority=Case(
            When(status='processing', then=Value(1)),
            When(status='paid', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('priority', '-created_at')

    unpaid_count = Student.objects.filter(payments__isnull=True).count()

    executives = ExecutiveAssignment.objects.filter(
        is_active=True
    ).select_related('student', 'position', 'tenure')

    students_list = Student.objects.all().select_related('user').prefetch_related('payments', 'executive_assignments')
    for s in students_list:
        active_assignment = s.executive_assignments.filter(is_active=True).first()
        s.member_type = active_assignment.position.title.replace('_', ' ').title() if active_assignment else "Student Member"

    if student:
        student.is_president = student.executive_assignments.filter(position__title='president', is_active=True).exists()
        student.is_financial_secretary = student.executive_assignments.filter(position__title='financial_secretary', is_active=True).exists()
        student.is_treasurer = student.executive_assignments.filter(position__title='treasurer', is_active=True).exists()

    return render(request, 'admin_dashboard.html', {
        'students': students_list,
        'total_income': total_income,
        'unpaid_count': unpaid_count,
        'all_payments': all_payments,
        'events': Event.objects.all(),
        'fundraising': Fundraising.objects.all(),
        'executives': executives,
        'active_tenure': active_tenure,
        'admin_student': student,
        'announcements': Announcement.objects.all().order_by('-is_pinned', '-date_posted'),
        'announcement_form': AnnouncementForm(),
        
        # UPDATED: Added scholarship data configurations to the management hub
        'scholarships': Scholarship.objects.all().order_by('-date_posted'),
        'scholarship_form': ScholarshipForm()  # Empty form instance for the new popup modal
    })


# =========================================================
# CREATE / EDIT ANNOUNCEMENT
# =========================================================
@login_required
def create_announcement(request, announcement_id=None):
    if not is_executive(request.user):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    announcement = get_object_or_404(Announcement, id=announcement_id) if announcement_id else None

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement published successfully!")
            return redirect('admin_dashboard')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'create_announcement.html', {'form': form})


# =========================================================
# DELETE ANNOUNCEMENT
# =========================================================
@login_required
def delete_announcement(request, announcement_id):
    if not is_executive(request.user):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, "Announcement removed.")
    return redirect('admin_dashboard')


# =========================================================
# CREATE / EDIT SCHOLARSHIP (NEW)
# =========================================================
@login_required
def create_scholarship(request, scholarship_id=None):
    # Only allow active Executives to publish new scholarship opportunities
    if not is_executive(request.user):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    scholarship = get_object_or_404(Scholarship, id=scholarship_id) if scholarship_id else None

    if request.method == 'POST':
        form = ScholarshipForm(request.POST, instance=scholarship)
        if form.is_valid():
            form.save()
            messages.success(request, "Scholarship opportunity listed successfully!")
            return redirect('admin_dashboard')
    else:
        form = ScholarshipForm(instance=scholarship)

    return redirect('admin_dashboard')


# =========================================================
# DELETE SCHOLARSHIP (NEW)
# =========================================================
@login_required
def delete_scholarship(request, scholarship_id):
    if not is_executive(request.user):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    scholarship.delete()
    messages.success(request, "Scholarship record removed.")
    return redirect('admin_dashboard')


# =========================================================
# ASSIGN EXECUTIVE ROLE
# =========================================================
@login_required
def assign_executive_role(request, student_id):
    if not is_president(request.user) and not request.user.is_staff:
        messages.error(request, "Access denied. Only the President can modify executive assignments.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        position_title = request.POST.get('executive_position', '').strip().lower().replace(' ', '_')

        if not position_title:
            messages.error(request, "No position specified.")
            return redirect('admin_dashboard')

        # Clean out any old/existing executive assignments for this student to prevent overlapping conflicts
        ExecutiveAssignment.objects.filter(student=student, is_active=True).update(is_active=False)

        # If choice is 'member', we simply demote them by leaving active assignments turned off
        if position_title == 'member':
            messages.success(request, f"Successfully removed executive roles from {student.full_name}.")
            return redirect('admin_dashboard')

        # Locate the current active calendar tenure block
        active_tenure = Tenure.objects.filter(is_active=True).first()
        if not active_tenure:
            messages.error(request, "No active tenure track found. Please set an active tenure in django admin first.")
            return redirect('admin_dashboard')

        # Safely locate or provision the designated structural position row
        position_obj, _ = ExecutivePosition.objects.get_or_create(title=position_title)

        # Provision and bind the brand new leadership record assignments
        ExecutiveAssignment.objects.create(
            student=student,
            position=position_obj,
            get_active_student=active_tenure,
            tenure=active_tenure,
            is_active=True
        )

        display_title = position_title.replace('_', ' ').title()
        messages.success(request, f"Successfully appointed {student.full_name} as {display_title}!")
        
    return redirect('admin_dashboard')


# =========================================================
# APPROVE PAYMENT
# =========================================================
@login_required
def approve_payment(request, payment_id):

    student = get_active_student(request.user)

    if not (
        student and (
            student.executive_assignments.filter(position__title='president', is_active=True).exists()
            or student.executive_assignments.filter(
                position__title='financial_secretary',
                is_active=True
            ).exists()
        )
    ):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'paid'
    payment.save()

    messages.success(request, "Payment approved.")
    return redirect('admin_dashboard')


# =========================================================
# DELETE STUDENT
# =========================================================
@login_required
def delete_student(request, student_id):

    if not is_president(request.user):
        messages.error(request, "Only President can delete.")
        return redirect('admin_dashboard')

    student = get_object_or_404(Student, id=student_id)

    if student.user:
        student.user.delete()

    student.delete()

    messages.success(request, "Student deleted.")
    return redirect('admin_dashboard')


# =========================================================
# CREATE / EDIT EVENT
# =========================================================
@login_required
def create_event(request, event_id=None):

    if not is_president(request.user):
        messages.error(request, "Only President allowed.")
        return redirect('admin_dashboard')

    event = get_object_or_404(Event, id=event_id) if event_id else None

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            saved_event = form.save()

            emails = list(Student.objects.values_list('email', flat=True))

            if emails:
                send_mail(
                    subject=f"New Event: {saved_event.title}",
                    message=f"A new event has been posted: {saved_event.title}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=emails,
                    fail_silently=True
                )

            messages.success(request, "Event saved.")
            return redirect('admin_dashboard')

    else:
        form = EventForm(instance=event)

    return render(request, 'create_event.html', {'form': form})


# =========================================================
# DELETE EVENT
# =========================================================
@login_required
def delete_event(request, event_id):

    if not is_president(request.user):
        return redirect('admin_dashboard')

    event = get_object_or_404(Event, id=event_id)
    event.delete()

    messages.success(request, "Event deleted.")
    return redirect('admin_dashboard')


# =========================================================
# FUNDRAISING
# =========================================================
@login_required
def create_fundraising(request):

    if not is_president(request.user):
        return redirect('admin_dashboard')

    form = FundraisingForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Fundraising created.")
        return redirect('admin_dashboard')

    return render(request, 'create_fundraising.html', {'form': form})