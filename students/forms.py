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
    Payment
)


# =========================================================
# STUDENT REGISTRATION FORM
# =========================================================
class StudentForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter a strong password',
                'class': 'form-control'
            }
        ),
        required=True,
        label='Password',
        help_text='Min. 8 chars, 1 uppercase, 1 number, 1 symbol'
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

            'full_name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your full name',
                    'class': 'form-control'
                }
            ),

            'school': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your school',
                    'class': 'form-control'
                }
            ),

            'department': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your department',
                    'class': 'form-control'
                }
            ),

            'level': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your level',
                    'class': 'form-control'
                }
            ),

            'phone': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your phone number',
                    'class': 'form-control'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'Enter your email',
                    'class': 'form-control'
                }
            ),

            'age': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter your age',
                    'class': 'form-control'
                }
            ),

            'state': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your state',
                    'class': 'form-control'
                }
            ),

            'nationality': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your nationality',
                    'class': 'form-control'
                }
            ),

            'profile_picture': forms.FileInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }

    # =====================================================
    # PASSWORD VALIDATION
    # =====================================================
    def clean_password(self):

        password = self.cleaned_data.get('password')

        if len(password) < 8:
            raise ValidationError(
                'Password must be at least 8 characters long.'
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'Password must contain at least one uppercase letter.'
            )

        if not re.search(r'[0-9]', password):
            raise ValidationError(
                'Password must contain at least one number.'
            )

        if not re.search(r'[!@#$%^&*(),.?":{}|<>+=\-_]', password):
            raise ValidationError(
                'Password must contain at least one special character.'
            )

        return password

    # =====================================================
    # EMAIL VALIDATION
    # =====================================================
    def clean_email(self):

        email = self.cleaned_data.get('email')

        if not email:
            raise ValidationError(
                'Email address is required.'
            )

        email = email.strip().lower()

        # Check Student model
        if Student.objects.filter(email=email).exists():
            raise ValidationError(
                'This email is already registered.'
            )

        return email

    # =====================================================
    # SAVE METHOD
    # =====================================================
    def save(self, commit=True):

        student = super().save(commit=False)

        email = self.cleaned_data.get('email').strip().lower()

        password = self.cleaned_data.get('password')

        full_name = self.cleaned_data.get('full_name').strip()

        # =================================================
        # CHECK EXISTING USER
        # =================================================
        existing_user = User.objects.filter(
            username=email
        ).first()

        if existing_user:

            # Prevent duplicate profile creation
            if hasattr(existing_user, 'student_profile'):
                raise ValidationError(
                    'A student with this email already exists.'
                )

            user = existing_user

            user.email = email
            user.set_password(password)

        else:

            # Create new user safely
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

        # =================================================
        # SPLIT FULL NAME
        # =================================================
        name_parts = full_name.split()

        user.first_name = (
            name_parts[0]
            if len(name_parts) > 0
            else ''
        )

        user.last_name = (
            ' '.join(name_parts[1:])
            if len(name_parts) > 1
            else ''
        )

        # Public registrations remain normal users
        user.is_staff = False
        user.is_superuser = False

        user.save()

        # =================================================
        # STUDENT PROFILE
        # =================================================
        student.user = user

        student.email = email

        if commit:
            student.save()

            # =============================================
            # WELCOME EMAIL
            # =============================================
            try:

                send_mail(
                    subject='Welcome to NUSSNHQ Portal',

                    message=(
                        f'Hello {full_name},\n\n'

                        f'Your registration on the '
                        f'NUSSNHQ Student Portal '
                        f'was successful.\n\n'

                        f'Login Email: {email}\n\n'

                        f'You can now access your '
                        f'dashboard and portal features.\n\n'

                        f'Best Regards,\n'
                        f'NUSSNHQ Executive Team'
                    ),

                    from_email=settings.DEFAULT_FROM_EMAIL,

                    recipient_list=[email],

                    fail_silently=True
                )

            except Exception as e:
                print(
                    f'Welcome email failed: {e}'
                )

        return student


# =========================================================
# EVENT FORM
# =========================================================
class EventForm(forms.ModelForm):

    class Meta:
        model = Event

        fields = [
            'title',
            'description',
            'date',
            'location',
            'image'
        ]

        widgets = {

            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Event title',
                    'class': 'form-control'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Event description',
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),

            'location': forms.TextInput(
                attrs={
                    'placeholder': 'Event location',
                    'class': 'form-control'
                }
            ),

            'image': forms.FileInput(
                attrs={
                    'accept': 'image/*',
                    'class': 'form-control'
                }
            ),
        }


# =========================================================
# FUNDRAISING FORM
# =========================================================
class FundraisingForm(forms.ModelForm):

    class Meta:
        model = Fundraising

        fields = [
            'title',
            'description',
            'goal'
        ]

        widgets = {

            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Fundraising title',
                    'class': 'form-control'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Fundraising description',
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'goal': forms.NumberInput(
                attrs={
                    'placeholder': 'Target amount',
                    'class': 'form-control'
                }
            ),
        }


# =========================================================
# PAYMENT FORM
# =========================================================
class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment

        fields = [
            'student',
            'amount',
            'status'
        ]

        widgets = {

            'student': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),

            'amount': forms.NumberInput(
                attrs={
                    'placeholder': 'Payment amount',
                    'class': 'form-control'
                }
            ),

            'status': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }