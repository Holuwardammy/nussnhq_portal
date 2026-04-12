from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Student, Payment, Event, Fundraising
from .forms import StudentForm, EventForm, FundraisingForm, PaymentForm


def home(request):
    return render(request, 'home.html')


# ---------------------------
# REGISTER STUDENT (FIXED)
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            email = form.cleaned_data.get('email')

            # FIX: prevent duplicate email
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")
                return redirect('register_student')

            student = form.save()

            messages.success(request, "Registration Successful! Please login.")
            return redirect('login')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = StudentForm()

    return render(request, 'register_student.html', {'form': form})


# ---------------------------
# LOGIN VIEW (FULLY FIXED)
# ---------------------------
def login_view(request):
    if request.method == "POST":
        username_input = request.POST.get("username")
        password = request.POST.get("password")

        user = None
        student_obj = None

        # 1. Try login via serial number
        try:
            student_obj = Student.objects.get(serial_number=username_input)

            if student_obj.user:
                user = authenticate(
                    request,
                    username=student_obj.user.username,
                    password=password
                )
        except Student.DoesNotExist:
            student_obj = None

        # 2. Try login via email (FIXED)
        if user is None:
            try:
                user_obj = User.objects.get(email=username_input)

                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                user = None

        # 3. Login success
        if user is not None:
            login(request, user)

            # Get related student safely
            if student_obj is None:
                try:
                    student_obj = Student.objects.get(user=user)
                except Student.DoesNotExist:
                    student_obj = None

            admin_roles = [
                "president",
                "treasurer",
                "financial_secretary"
            ]

            if user.is_staff or (student_obj and student_obj.member_type in admin_roles):
                return redirect('admin_dashboard')
            else:
                return redirect('student_home')

        else:
            messages.error(request, "Invalid email, serial number, or password.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME
# ---------------------------
def student_home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found. Please contact admin.")
        return redirect('home')

    payments = Payment.objects.filter(student=student)
    events = Event.objects.all()
    fundraising = Fundraising.objects.all()

    return render(request, "student_home.html", {
        "student": student,
        "payments": payments,
        "events": events,
        "fundraising": fundraising
    })


# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if not request.user.is_staff:
        return redirect('student_home')

    try:
        admin_student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        admin_student = None

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "payments": Payment.objects.all(),
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": admin_student
    })


# ---------------------------
# GENERAL DASHBOARD (OPTIONAL)
# ---------------------------
def dashboard(request):
    return render(request, 'dashboard.html', {
        'students': Student.objects.all(),
        'payments': Payment.objects.all(),
        'events': Event.objects.all(),
        'fundraising': Fundraising.objects.all()
    })


# ---------------------------
# CREATE EVENT
# ---------------------------
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = EventForm()

    return render(request, 'create_event.html', {'form': form})


# ---------------------------
# CREATE FUNDRAISING
# ---------------------------
def create_fundraising(request):
    if request.method == 'POST':
        form = FundraisingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = FundraisingForm()

    return render(request, 'create_fundraising.html', {'form': form})


# ---------------------------
# MARK PAYMENT
# ---------------------------
def mark_payment(request, student_id):
    student = Student.objects.get(id=student_id)

    payment, created = Payment.objects.get_or_create(student=student)
    payment.paid = True
    payment.date_paid = timezone.now()
    payment.save()

    return redirect('admin_dashboard')


# ---------------------------
# LOGOUT
# ---------------------------
def logout_view(request):
    logout(request)
    return redirect('home')


# ---------------------------
# DELETE STUDENT (SAFE)
# ---------------------------
def delete_student(request, student_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    try:
        student = Student.objects.get(id=student_id)

        user = student.user
        student.delete()

        if user:
            user.delete()

        messages.success(request, "Student and associated user deleted successfully.")

    except Student.DoesNotExist:
        messages.error(request, "Student not found.")

    return redirect('admin_dashboard')