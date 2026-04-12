from django.shortcuts import render, redirect, get_object_or_404
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

        messages.error(request, "Please correct the errors below.")

    else:
        form = StudentForm()

    return render(request, 'register_student.html', {'form': form})


# ---------------------------
# LOGIN VIEW (FIXED)
# ---------------------------
def login_view(request):

    if request.method == "POST":

        username_input = request.POST.get("username")
        password = request.POST.get("password")

        # Convert serial number → email if needed
        try:
            student_obj = Student.objects.get(serial_number=username_input)
            username_input = student_obj.email
        except Student.DoesNotExist:
            pass

        user = authenticate(request, username=username_input, password=password)

        if user is not None:
            login(request, user)

            # 🔥 GUARANTEE STUDENT PROFILE EXISTS
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": user.username,
                    "email": user.email,
                    "school": "Not set",
                    "department": "Not set",
                    "level": "Not set",
                    "phone": "Not set",
                    "member_type": "student_member"
                }
            )

            # Redirect based on role
            if student.is_executive():
                return redirect('admin_dashboard')

            return redirect('student_home')

        messages.error(request, "Invalid email, serial number, or password.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME (FIXED)
# ---------------------------
def student_home(request):

    if not request.user.is_authenticated:
        return redirect('login')

    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.username,
            "email": request.user.email,
            "school": "Not set",
            "department": "Not set",
            "level": "Not set",
            "phone": "Not set",
            "member_type": "student_member"
        }
    )

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
# ADMIN DASHBOARD (FIXED SAFETY)
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

    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')

    student = get_object_or_404(Student, id=student_id)

    user = student.user

    student.delete()

    if user:
        user.delete()

    messages.success(request, "Student and associated user deleted successfully.")

    return redirect('admin_dashboard')