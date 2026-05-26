import re

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Student,
    Event,
    Fundraising,
    Payment,
    Announcement
)

# =========================================================
# STUDENT FORM
# =========================================================
class StudentForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter a strong password',
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        required=True,
        label='Password'
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
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # =====================================================
    # PASSWORD VALIDATION
    # =====================================================
    def clean_password(self):
        password = self.cleaned_data.get('password')

        if not password:
            raise ValidationError("Password is required.")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")

        if not re.search(r'[A-Z]', password):
            raise ValidationError("Must contain uppercase letter.")

        if not re.search(r'[0-9]', password):
            raise ValidationError("Must contain number.")

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>+=\-_]', password):
            raise ValidationError("Must contain special character.")

        return password

    # =====================================================
    # EMAIL VALIDATION (SAFE FIX)
    # =====================================================
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        email = email.strip().lower()

        # If we are UPDATING an existing student profile
        if self.instance and self.instance.pk:
            # Check if ANY OTHER student is already using this email
            if Student.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise ValidationError("This email is already taken by another student.")
            return email

        # If we are REGISTERING a brand new student
        if Student.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")

        if User.objects.filter(email=email).exists():
            raise ValidationError("Account already exists with this email.")

        return email

    # =====================================================
    # SAVE METHOD (SAFE USER SYNC)
    # =====================================================
    def save(self, commit=True):

        student = super().save(commit=False)

        email = self.cleaned_data['email'].strip().lower()
        password = self.cleaned_data['password']
        full_name = self.cleaned_data['full_name'].strip()

        # Get or create user
        user = User.objects.filter(username=email).first()

        if user:
            user.username = email
            user.email = email
            user.set_password(password)
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

        # Split full name safely
        name_parts = full_name.split()
        user.first_name = name_parts[0] if name_parts else ""
        user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        user.is_staff = False
        user.is_superuser = False
        user.save()

        student.user = user
        student.email = email

        if commit:
            student.save()

            # Optional email (safe)
            try:
                send_mail(
                    subject="Welcome to NUSSNHQ Portal",
                    message=(
                        f"Hello {full_name},\n\n"
                        f"Registration successful.\n"
                        f"Email: {email}\n\n"
                        f"Welcome onboard."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                print("Email error:", e)

        return student


# =========================================================
# EVENT FORM
# =========================================================
class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'image']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


# =========================================================
# FUNDRAISING FORM
# =========================================================
class FundraisingForm(forms.ModelForm):

    class Meta:
        model = Fundraising
        fields = ['title', 'description', 'goal']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'goal': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# =========================================================
# PAYMENT FORM
# =========================================================
class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = ['student', 'amount', 'status']

        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# =========================================================
# ANNOUNCEMENT FORM
# =========================================================

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter announcement title'}),
            'content': forms.Textarea(attrs={'placeholder': 'Write your announcement content here...', 'rows': 4}),
        }