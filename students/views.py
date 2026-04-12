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
# REGISTER STUDENT
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Registration Successful! Please login.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()

    return render(request, 'register_student.html', {'form': form})


# ---------------------------
# LOGIN VIEW (PERMANENT FIX)
# ---------------------------
def login_view(request):
    if request.method == "POST":
        username_input = request.POST.get("username")
        password = request.POST.get("password")

        user = None
        student_obj = None

        # 1. LOGIN VIA SERIAL NUMBER
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

        # 2. LOGIN VIA EMAIL
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

        # ---------------------------
        # LOGIN SUCCESS
        # ---------------------------
        if user is not None:
            login(request, user)

            student_obj = Student.objects.filter(user=user).first()

            # 🔥 CLEAN ROLE CHECK USING MODEL METHOD
            is_admin = (
                user.is_staff or
                user.is_superuser or
                (student_obj and student_obj.is_executive())
            )

            if is_admin:
                return redirect('admin_dashboard')

            return redirect('student_home')

        messages.error(request, "Invalid email, serial number, or password.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME
# ---------------------------
def student_home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    student = Student.objects.filter(user=request.user).first()

    if not student:
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

    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('student_home')

    admin_student = Student.objects.filter(user=request.user).first()

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "payments": Payment.objects.all(),
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": admin_student
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
# DELETE STUDENT
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