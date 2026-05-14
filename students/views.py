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

from .models import Student, Payment, Event, Fundraising, School
from .forms import StudentForm, EventForm, FundraisingForm

def home(request):
    # This grabs EVERYTHING and puts the newest dates first
    events = Event.objects.all().order_by('-date') 
    return render(request, 'home.html', {'events': events})

# ---------------------------
# REGISTER (With Executive Role Lockout)
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        
        # form.is_valid() now automatically checks for:
        # 1. Real email format & uniqueness
        # 2. Strong password (Uppercase, Symbol, Number)
        if form.is_valid():
            
            # --- 1. EXECUTIVE ROLE LOCKOUT LOGIC ---
            selected_role = form.cleaned_data.get('member_type')
            restricted_roles = ['president', 'treasurer', 'financial_secretary']
            
            if selected_role in restricted_roles:
                # Check if this executive position is already taken in the database
                role_exists = Student.objects.filter(member_type=selected_role).exists()
                
                if role_exists:
                    display_role = selected_role.replace('_', ' ').title()
                    messages.error(request, f"Access Denied: The position of {display_role} is already occupied.")
                    # Return the form so they can change the role without losing data
                    return render(request, 'register_student.html', {'form': form})

            # --- 2. SCHOOL SELF-LEARNING LOGIC ---
            # We call form.save(commit=False) to get the student object 
            # so we can manually set the school before the final save.
            student = form.save(commit=False)
            
            school_name = request.POST.get('school', '').strip()
            if school_name:
                # Add to our School list if it's a new one
                School.objects.get_or_create(name=school_name)
                student.school = school_name
            
            # --- 3. FINAL SAVE ---
            # This triggers the StudentForm.save() method we just updated,
            # which handles User creation and Password hashing.
            student.save()
            
            messages.success(request, "Registration Successful! Please login with your email.")
            return redirect('login')
            
        else:
            # If email is taken or password is weak, Django shows the errors from forms.py
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

    # --- FINANCIAL DATA ---
    # Total income now only counts 'paid' status
    total_income = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # NEW LOGIC: This gets ALL payments but puts 'processing' at the top
    # Once you approve them, they stay in this list but move down
    all_payments = Payment.objects.annotate(
        priority=Case(
            When(status='processing', then=Value(1)), # New payments first
            When(status='paid', then=Value(2)),       # History second
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('priority', '-date') # Newest date within those groups

    unpaid_count = Student.objects.filter(payment__status='pending').count() + \
                   Student.objects.filter(payment__isnull=True).count()

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "total_income": total_income,
        "unpaid_count": unpaid_count,
        "all_payments": all_payments,  # Use this in your template loop
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": admin_student 
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
            # Create unique payment record
            payment = Payment.objects.create(
                student=student,
                amount=amount,
                payment_receipt=receipt,
                status='processing'
            )
            
            # EMAIL NOTIFICATION: Payment Received
            try:
                send_mail(
                    subject="Payment Received - Awaiting Verification",
                    message=(
                        f"Hello {student.full_name},\n\n"
                        f"Your payment of ₦{amount} has been received and is currently being "
                        "verified by the Financial Secretary.\n\n"
                        "You will receive another notification once your payment has been approved."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Payment submission email failed: {e}")

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

    # EMAIL NOTIFICATION: Payment Approved
    try:
        send_mail(
            subject="Payment Verified Successfully!",
            message=(
                f"Hello {payment.student.full_name},\n\n"
                f"Your payment of ₦{payment.amount} has been verified.\n\n"
                "You now have full access to your student portal features. "
                "Thank you for your commitment to NUSS!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.student.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Approval email failed: {e}")

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
    is_new_event = event is None  # Check if this is a fresh announcement

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            # 1. Save the event
            saved_event = form.save()
            
            # 2. Only send email blast if it's a NEW event
            if is_new_event:
                # Get all registered student emails
                recipient_emails = list(Student.objects.values_list('email', flat=True))
                
                if recipient_emails:
                    try:
                        send_mail(
                            subject=f"NUSS Announcement: {saved_event.title}",
                            message=(
                                f"Hello Students,\n\n"
                                f"A new event has been posted to the NUSS Portal: {saved_event.title}\n"
                                f"Date: {saved_event.date}\n\n"
                                f"Log in to the portal to see full details and location.\n\n"
                                f"Best Regards,\nNUSS Executive Team"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=recipient_emails,
                            fail_silently=True,
                        )
                    except Exception as e:
                        print(f"Event blast email failed: {e}")

            msg = "Event updated successfully!" if not is_new_event else "Event announced successfully and students notified!"
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