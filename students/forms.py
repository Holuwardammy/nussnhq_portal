import re
import os
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import Student, Event, Fundraising, Payment

class StudentForm(forms.ModelForm):
    # 1. Single Password Field with both Styling and Help Text
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter a strong password', 'class': 'form-control'}),
        required=True,
        label="Password",
        help_text="Min. 8 chars, 1 uppercase, 1 number, 1 symbol"
    )

    class Meta:
        model = Student
        fields = [
            'full_name',
            'school',
            'department',
            'level',
            'phone',
            'email',
            'profile_picture',
            'age',
            'state',
            'nationality'
            # <-- 'member_type' REMOVED FROM HERE COMPLETELY!
        ]
        
        # 2. Corrected Widgets Placement (Inside Meta)
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter your full name', 'class': 'form-control'}),
            'school': forms.TextInput(attrs={'placeholder': 'Enter your school', 'class': 'form-control'}),
            'department': forms.TextInput(attrs={'placeholder': 'Enter your department', 'class': 'form-control'}),
            'level': forms.TextInput(attrs={'placeholder': 'Enter your level', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'placeholder': 'Enter your age', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter your state', 'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'placeholder': 'Enter your nationality', 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-file'})
        }

    # --- PASSWORD STRENGTH VALIDATION ---
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>+=\-_]', password):
            raise ValidationError("Password must contain at least one special character (symbol).")
        
        return password

    # --- EMAIL VALIDATION ---
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()

        # Check Student model
        if Student.objects.filter(email=email).exists():
            raise ValidationError("A student with this email already exists.")

        # Check Django User model (for login conflicts)
        if User.objects.filter(username=email).exists():
            raise ValidationError("This email is already registered as a user.")

        return email

    def save(self, commit=True):
        student = super().save(commit=False)
        email = self.cleaned_data.get('email').lower()
        password = self.cleaned_data.get('password')
        full_name = self.cleaned_data.get('full_name')

        # Create/Update the associated User
        user = User.objects.filter(username=email).first()
        if user is None:
            user = User.objects.create_user(
                username=email, 
                email=email,
                password=password
            )
        
        # Sync Profile names to the User account
        name_parts = full_name.strip().split()
        user.first_name = name_parts[0] if name_parts else ""
        user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # All web registrations default to standard non-staff access for structural safety
        user.is_staff = False
        user.save()

        student.user = user
        student.email = email
        
        if commit:
            student.save()
            
            # --- SEND WELCOME EMAIL ---
            try:
                send_mail(
                    subject="Congratulations on Your Registration!",
                    message=(
                        f"Hello {full_name},\n\n"
                        f"Welcome to the National Union of Saki Students (NUSS) Portal! "
                        f"Your registration was successful.\n\n"
                        f"You can now log in to pay your dues and access your dashboard.\n"
                        f"Login Email: {email}\n\n"
                        f"Best Regards,\nNUSS Executive Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Registration email failed: {e}")
                
        return student


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Event title', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'placeholder': 'Event description', 'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'Event location', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control-file'})
        }


class FundraisingForm(forms.ModelForm):
    class Meta:
        model = Fundraising
        fields = ['title', 'description', 'goal']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Fundraising title', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'placeholder': 'Fundraising description', 'class': 'form-control', 'rows': 3}),
            'goal': forms.NumberInput(attrs={'placeholder': 'Target amount', 'class': 'form-control'})
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'paid']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Payment amount', 'class': 'form-control'}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }