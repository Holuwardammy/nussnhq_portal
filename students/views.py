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
    Tenure
)

from .forms import (
    StudentForm,
    EventForm,
    FundraisingForm
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
def home(request):
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

    return render(request, 'student_home.html', {
        'student': student,
        'payments': Payment.objects.filter(student=student),
        'events': Event.objects.all(),
        'fundraising': Fundraising.objects.all(),
    })


# =========================================================
# PAYMENT INSTRUCTIONS  ✅ FIX ADDED (WAS MISSING BEFORE)
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
# SCHOOL AUTOCOMPLETE  ✅ FIX ADDED (WAS MISSING BEFORE)
# =========================================================
def school_autocomplete(request):
    query = request.GET.get('term', '')
    schools = School.objects.filter(name__icontains=query)[:10]
    results = [school.name for school in schools]
    return JsonResponse(results, safe=False)


# =========================================================
# ADMIN DASHBOARD
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

    return render(request, 'admin_dashboard.html', {
        'students': Student.objects.all().select_related('user').prefetch_related('payments', 'executive_assignments'),
        'total_income': total_income,
        'unpaid_count': unpaid_count,
        'all_payments': all_payments,
        'events': Event.objects.all(),
        'fundraising': Fundraising.objects.all(),
        'executives': executives,
        'active_tenure': active_tenure,
        'admin_student': student
    })


# =========================================================
# APPROVE PAYMENT
# =========================================================
@login_required
def approve_payment(request, payment_id):

    student = get_active_student(request.user)

    if not (
        student and (
            student.is_president()
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

    # ==========================================
# TEMPORARY AUTO-DELETE FIX (Remove after deploy)
# ==========================================
from django.contrib.auth.models import User
try:
    # This finds the user connected to that specific school text and purges them
    bad_user = User.objects.filter(student__school__icontains="LADOKE").first()
    if bad_user:
        bad_user.delete()
        print("Success: Broken tester student deleted!")
except Exception as e:
    print(f"Auto-delete ran into an issue: {e}")
# ==========================================