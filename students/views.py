from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Student, Payment, Event, Fundraising, School
from .forms import StudentForm, EventForm, FundraisingForm


def home(request):
    # This grabs EVERYTHING and puts the newest dates first
    events = Event.objects.all().order_by('-date') 
    return render(request, 'home.html', {'events': events})


# ---------------------------
# REGISTER
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            
            # --- SELF-LEARNING LOGIC ---
            # Get the school name from the hidden input in your HTML
            school_name = request.POST.get('school', '').strip()
            if school_name:
                # This saves the school to the database if it doesn't exist yet
                School.objects.get_or_create(name=school_name)
                student.school = school_name
            
            student.save()
            messages.success(request, "Registration Successful! Please login with your email.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()
    return render(request, 'register_student.html', {'form': form})

# ADD THIS NEW VIEW HERE:
def school_autocomplete(request):
    query = request.GET.get('term', '')
    # This finds schools that contain the letters the student typed
    schools = School.objects.filter(name__icontains=query)[:10]
    results = [school.name for school in schools]
    return JsonResponse(results, safe=False)


# ---------------------------
# LOGIN
# ---------------------------
def login_view(request):
    if request.method == "POST":
        email_input = request.POST.get("username").lower() if request.POST.get("username") else ""
        password_input = request.POST.get("password")

        user = authenticate(request, username=email_input, password=password_input)

        if user:
            login(request, user)
            student = Student.objects.filter(user=user).first()
            
            # Redirect logic based on specific Executive Roles
            if student and student.is_executive():
                return redirect('admin_dashboard')
            
            return redirect('student_home')
        else:
            messages.error(request, "Invalid login details.")

    return render(request, 'login.html')


# ---------------------------
# STUDENT HOME
# ---------------------------
@login_required
def student_home(request):
    # We find the student profile linked to the logged-in user
    student = get_object_or_404(Student, user=request.user)
    return render(request, "student_home.html", {
        "student": student,
        "payments": Payment.objects.filter(student=student),
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
    })


# ---------------------------
# ADMIN DASHBOARD (PRESIDENT, TREASURER, FIN SEC)
# ---------------------------
@login_required
def admin_dashboard(request):
    admin_student = Student.objects.filter(user=request.user).first()

    # Access Control: Only President, Treasurer, Fin Sec, or Superuser
    if not (request.user.is_staff or (admin_student and admin_student.is_executive())):
        messages.error(request, "Access denied. Executives only.")
        return redirect('student_home')

    # --- FINANCIAL DATA (Optimized for Treasurer) ---
    total_income = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    awaiting_verification = Payment.objects.filter(status='processing')
    unpaid_count = Student.objects.filter(payment__status='pending').count() + Student.objects.filter(payment__isnull=True).count()

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "total_income": total_income,
        "unpaid_count": unpaid_count,
        "awaiting_verification": awaiting_verification,
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": admin_student # Used in template to check roles
    })


# ---------------------------
# PAYMENT FLOW (Student Side)
# ---------------------------

@login_required
def payment_instructions(request):
    """Step 1: Show the student where to send the money"""
    student = get_object_or_404(Student, user=request.user)
    return render(request, 'payment_instructions.html', {'student': student})

@login_required
def submit_payment(request):
    """Step 2: Student uploads the screenshot of the transfer"""
    student = get_object_or_404(Student, user=request.user)

    if request.method == "POST":
        amount = request.POST.get('amount')
        receipt = request.FILES.get('payment_receipt')

        if receipt:
            # CHANGE: Use .create() instead of .get_or_create()
            # This ensures every payment is a unique record in the database
            Payment.objects.create(
                student=student,
                amount=amount,
                payment_receipt=receipt,
                status='processing'
            )
            
            messages.success(request, "Payment submitted! The Financial Secretary will verify it shortly.")
            return redirect('student_home')
        
    return render(request, 'submit_payment.html', {'student': student})


# ---------------------------
# APPROVE PAYMENT (Financial Secretary / President Only)
# ---------------------------
@login_required
def approve_payment(request, payment_id):
    admin_student = Student.objects.filter(user=request.user).first()
    
    # Strictly for Fin Sec or President (Full Access)
    can_approve = request.user.is_staff or (admin_student and (admin_student.is_financial_secretary() or admin_student.is_president()))
    
    if not can_approve:
        messages.error(request, "Only the Financial Secretary or President can approve payments.")
        return redirect('admin_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'paid'
    payment.save()

    messages.success(request, f"Successfully verified payment for {payment.student.full_name}.")
    return redirect('admin_dashboard')


# ---------------------------
# DELETE STUDENT (President / Staff Only)
# ---------------------------
@login_required
def delete_student(request, student_id):
    admin_student = Student.objects.filter(user=request.user).first()
    
    # Strictly for President or Superuser
    if not (request.user.is_staff or (admin_student and admin_student.is_president())):
        messages.error(request, "Only the President has authority to delete records.")
        return redirect('admin_dashboard')

    student = get_object_or_404(Student, id=student_id)
    if student.user:
        student.user.delete()
    student.delete()
    messages.success(request, "Student record deleted successfully.")
    return redirect('admin_dashboard')


# ---------------------------
# EVENTS & FUNDRAISING (President / Staff Only)
# ---------------------------

@login_required
def create_event(request, event_id=None):
    admin_student = Student.objects.filter(user=request.user).first()
    
    # Permission Check
    if not (request.user.is_staff or (admin_student and admin_student.is_president())):
        messages.error(request, "Only the President can manage events.")
        return redirect('admin_dashboard')

    # If event_id is provided, we are EDITING; otherwise, we are CREATING
    event = get_object_or_404(Event, id=event_id) if event_id else None

    if request.method == 'POST':
        # Added instance=event to update the existing record if it exists
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            msg = "Event updated successfully!" if event else "Event announced successfully!"
            messages.success(request, msg)
            return redirect('admin_dashboard')
    else:
        form = EventForm(instance=event)
        
    return render(request, 'create_event.html', {
        'form': form, 
        'edit_mode': bool(event)
    })

@login_required
def delete_event(request, event_id):
    admin_student = Student.objects.filter(user=request.user).first()
    
    if not (request.user.is_staff or (admin_student and admin_student.is_president())):
        messages.error(request, "Permission denied.")
        return redirect('admin_dashboard')

    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, "Event deleted successfully.")
    return redirect('admin_dashboard')

@login_required
def create_fundraising(request):
    admin_student = Student.objects.filter(user=request.user).first()
    if not (request.user.is_staff or (admin_student and admin_student.is_president())):
        messages.error(request, "Only the President can create fundraising campaigns.")
        return redirect('admin_dashboard')

    form = FundraisingForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'create_fundraising.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')