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

from .models import Student, Payment, Event, Fundraising, School, ExecutiveRole
from .forms import StudentForm, EventForm, FundraisingForm


def home(request):
    # This grabs EVERYTHING and puts the newest dates first
    events = Event.objects.all().order_by('-date') 
    return render(request, 'home.html', {'events': events})


# ---------------------------
# REGISTER STUDENT (OPTIMIZED FOR AUTOMATIC STUDENT ROUTING)
# ---------------------------
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        
        if form.is_valid():
            # --- SCHOOL SELF-LEARNING LOGIC ---
            student = form.save(commit=False)
            
            # Enforce that all new web registrations default explicitly to a regular student status
            student.member_type = 'student'
            
            school_name = request.POST.get('school', '').strip()
            if school_name:
                # Add to our School list if it's a new one
                School.objects.get_or_create(name=school_name)
                student.school = school_name
            
            # --- FINAL SAVE ---
            # Triggers User model creation and custom lowercased username/email synchronization inside forms.py
            student.save()
            
            messages.success(request, "Registration Successful! Please login with your email.")
            return redirect('login')
            
        else:
            messages.error(request, "Please correct the errors below.")
            
    else:
        form = StudentForm()
        
    return render(request, 'register_student.html', {'form': form})


def school_autocomplete(request):
    query = request.GET.get('term', '')
    # This finds schools that contain the letters the student typed
    schools = School.objects.filter(name__icontains=query)[:10]
    results = [school.name for school in schools]
    return JsonResponse(results, safe=False)


# ---------------------------
# LOGIN (With Secure Executive Routing)
# ---------------------------
def login_view(request):
    if request.method == "POST":
        email_input = request.POST.get("username").lower() if request.POST.get("username") else ""
        password_input = request.POST.get("password")

        # Standard Django authentication matching the User model
        user = authenticate(request, username=email_input, password=password_input)

        if user:
            login(request, user)
            student = Student.objects.filter(user=user).first()
            
            # Simple, clean routing to your custom dashboards
            if user.is_superuser or user.is_staff or (student and student.is_executive()):
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

    # Access Control: Only users with assigned Executive Roles or Superusers
    if not (request.user.is_staff or (admin_student and admin_student.is_executive())):
        messages.error(request, "Access denied. Executives only.")
        return redirect('student_home')

    # --- FINANCIAL DATA ---
    total_income = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Priority sorting: 'processing' payments stay at the top of the stack
    all_payments = Payment.objects.annotate(
        priority=Case(
            When(status='processing', then=Value(1)), 
            When(status='paid', then=Value(2)),      
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('priority', '-date_paid')

    unpaid_count = Student.objects.filter(payment__status='pending').count() + \
                   Student.objects.filter(payment__isnull=True).count()

    return render(request, "admin_dashboard.html", {
        "students": Student.objects.all(),
        "total_income": total_income,
        "unpaid_count": unpaid_count,
        "all_payments": all_payments,  
        "events": Event.objects.all(),
        "fundraising": Fundraising.objects.all(),
        "admin_student": admin_student 
    })


# ---------------------------
# PAYMENT FLOW (Student Side)
# ---------------------------
@login_required
def payment_instructions(request):
    student = get_object_or_404(Student, user=request.user)
    return render(request, 'payment_instructions.html', {'student': student})


@login_required
def submit_payment(request):
    student = get_object_or_404(Student, user=request.user)

    if request.method == "POST":
        amount = request.POST.get('amount')
        receipt = request.FILES.get('payment_receipt')

        if receipt:
            payment = Payment.objects.create(
                student=student,
                amount=amount,
                payment_receipt=receipt,
                status='processing'
            )
            
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
                    timeout=10,  
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
    
    # Validation relying on safe table hierarchy lookups
    can_approve = request.user.is_staff or (admin_student and (admin_student.is_financial_secretary() or admin_student.is_president()))
    
    if not can_approve:
        messages.error(request, "Only the Financial Secretary or President can approve payments.")
        return redirect('admin_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'paid'
    payment.save()

    try:
        send_mail(
            subject="Payment Verified Successfully!",
            message=(
                f"Hello {payment.student.full_name},\n\n"
                f"Your payment of ₦{payment.amount} has been verified.\n\n"
                f"You now have full access to your student portal features. "
                "Thank you for your commitment to NUSS!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.student.email],
            fail_silently=True,
            timeout=10,  
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
    
    if not (request.user.is_staff or (admin_student and admin_student.is_president())):
        messages.error(request, "Only the President can manage events.")
        return redirect('admin_dashboard')

    event = get_object_or_404(Event, id=event_id) if event_id else None
    is_new_event = event is None  

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            saved_event = form.save()
            
            if is_new_event:
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
                            timeout=10,  
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