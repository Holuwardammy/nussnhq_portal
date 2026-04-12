from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Student, Payment, Event, Fundraising
from .forms import StudentForm, EventForm, FundraisingForm


def home(request):
    return render(request, 'home.html')


# ---------------------------
# REGISTER
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() # The form handles user creation and hashing
            messages.success(request, "Registration Successful! Please login with your email.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()
    return render(request, 'register_student.html', {'form': form})


# ---------------------------
# LOGIN
# ---------------------------
def login_view(request):
    if request.method == "POST":
        # Normalize email to lowercase to match the registration data
        email_input = request.POST.get("username").lower() if request.POST.get("username") else ""
        password_input = request.POST.get("password")

        # Authenticate using email as username
        user = authenticate(request, username=email_input, password=password_input)

        if user:
            login(request, user)
            
            # Fetch student profile
            student = Student.objects.filter(user=user).first()
            
            # Safety check: is_executive() only returns True for President, Treasurer, and Fin Sec
            if student and hasattr(student, 'is_executive') and student.is_executive():
                return redirect('admin_dashboard')
            
            # Everyone else (Senate, PRO, Students) goes to student_home
            return redirect('student_home')
        else:
            messages.error(request, "Invalid login details. Please use your registered email.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME
# ---------------------------
def student_home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    student = Student.objects.filter(user=request.user).first()
    
    # If no profile exists for some reason, we avoid a crash
    if not student:
        messages.error(request, "Student profile not found.")
        return redirect('home')

    return render(request, "student_home.html", {
        "student": student,
        "payments": Payment.objects.filter(student=student),
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
    })


# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    student = Student.objects.filter(user=request.user).first()

    # Safety check for admin access based on the 3 roles defined in Models
    is_exec = False
    if student and hasattr(student, 'is_executive'):
        is_exec = student.is_executive()

    # Admin access requires superuser status OR being one of the 3 specific roles
    is_admin = request.user.is_staff or request.user.is_superuser or is_exec

    if not is_admin:
        messages.error(request, "Access denied. Admins only.")
        return redirect('student_home')

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "payments": Payment.objects.all(),
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": student
    })


# ---------------------------
# EVENT
# ---------------------------
def create_event(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can create events.")
        return redirect('login')
    form = EventForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'create_event.html', {'form': form})


# ---------------------------
# FUNDRAISING
# ---------------------------
def create_fundraising(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can create fundraising.")
        return redirect('login')
    form = FundraisingForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'create_fundraising.html', {'form': form})


# ---------------------------
# PAYMENT
# ---------------------------
def mark_payment(request, student_id):
    if not request.user.is_staff:
        return redirect('login')
        
    student = get_object_or_404(Student, id=student_id)
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
    if not request.user.is_staff:
        return redirect('login')

    student = get_object_or_404(Student, id=student_id)

    if student.user:
        student.user.delete()

    student.delete()

    messages.success(request, "Deleted successfully.")
    return redirect('admin_dashboard')