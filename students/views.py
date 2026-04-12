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
# REGISTER (SAFE)
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

def login_view(request):
    if request.method == "POST":
        email_input = request.POST.get("username") # The email typed in the box
        password_input = request.POST.get("password")

        # Authenticate using the email as the username
        user = authenticate(request, username=email_input, password=password_input)

        if user:
            login(request, user)
            # Fetch the student profile to check for executive status
            student = Student.objects.filter(user=user).first()
            
            if student and student.is_executive():
                return redirect('admin_dashboard')
            return redirect('student_home')
        else:
            messages.error(request, "Invalid login details. Use your registered email.")

    return render(request, 'login.html')


def login_view(request):
    if request.method == "POST":
        email_input = request.POST.get("username") # This is the 'email' from your form
        password = request.POST.get("password")

        # We authenticate using the email_input as the 'username' 
        # because we synced them during registration above.
        user = authenticate(request, username=email_input, password=password)

        if user:
            login(request, user)
            
            # Check for student profile
            student = Student.objects.filter(user=user).first()
            
            if student and student.is_executive():
                return redirect('admin_dashboard')
            
            return redirect('student_home')
        else:
            messages.error(request, "Invalid login details. Please use your registered email.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME (SAFE)
# ---------------------------
def student_home(request):

    if not request.user.is_authenticated:
        return redirect('login')

    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.username,
            "email": request.user.email or "",
            "school": "Not set",
            "department": "Not set",
            "level": "Not set",
            "phone": "Not set",
            "member_type": "student_member"
        }
    )

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

    is_admin = request.user.is_staff or request.user.is_superuser or (
        student.is_executive() if student else False
    )

    if not is_admin:
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
    form = EventForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'create_event.html', {'form': form})


# ---------------------------
# FUNDRAISING
# ---------------------------
def create_fundraising(request):
    form = FundraisingForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'create_fundraising.html', {'form': form})


# ---------------------------
# PAYMENT
# ---------------------------
def mark_payment(request, student_id):

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