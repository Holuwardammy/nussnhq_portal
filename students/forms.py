from django import forms
from django.contrib.auth.models import User
from .models import Student, Event, Fundraising, Payment


class StudentForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        required=True,
        label="Password"
    )

    MEMBERSHIP_CHOICES = [
        ('student', 'Student'),
        ('student_member', 'Student Member'),
        ('president', 'President'),
        ('senate_president', 'Senate President'),
        ('deputy_senate_president', 'Deputy Senate President'),
        ('social_director', 'Social Director'),
        ('welfare', 'Welfare'),
        ('organising_committee', 'Organising Committee'),
        ('general_secretary', 'General Secretary'),
        ('assistant_general_secretary', 'Assistant General Secretary'),
        ('pro', 'PRO'),
        ('pro_ii', 'PRO II'),
        ('treasurer', 'Treasurer'),
        ('financial_secretary', 'Financial Secretary'),
    ]

    member_type = forms.ChoiceField(
        choices=MEMBERSHIP_CHOICES,
        widget=forms.Select(),
        label="Membership Type"
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
            'nationality',
            'member_type'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'school': forms.HiddenInput(),  # keep your original logic (IMPORTANT)
            'department': forms.TextInput(attrs={'placeholder': 'Enter your department'}),
            'level': forms.TextInput(attrs={'placeholder': 'Enter your level'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'age': forms.NumberInput(attrs={'placeholder': 'Enter your age'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter your state'}),
            'nationality': forms.TextInput(attrs={'placeholder': 'Enter your nationality'}),
            'profile_picture': forms.FileInput()
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # FIXED SAFE CHECKS
        if Student.objects.filter(email=email).exists():
            raise forms.ValidationError("A student with this email already exists.")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered with another account.")

        return email

    def save(self, commit=True):
        student = super().save(commit=False)

        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        full_name = self.cleaned_data.get('full_name')
        member_type = self.cleaned_data.get('member_type')

        admin_executives = ["president", "treasurer", "financial_secretary"]
        is_admin = member_type in admin_executives

        user, created = User.objects.get_or_create(username=email, email=email)

        if created:
            user.set_password(password)
            user.first_name = full_name.split()[0]
            user.last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''

            if is_admin:
                user.is_staff = True

            user.save()

        student.user = user
        student.member_type = member_type

        if is_admin:
            student.executive_position = member_type
        else:
            student.executive_position = None

        if commit:
            student.save()

        return student


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Event title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Event description'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'placeholder': 'Event location'})
        }


class FundraisingForm(forms.ModelForm):
    class Meta:
        model = Fundraising
        fields = ['title', 'description', 'goal']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Fundraising title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Fundraising description'}),
            'goal': forms.NumberInput(attrs={'placeholder': 'Target amount'})
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'paid']
        widgets = {
            'student': forms.Select(),
            'amount': forms.NumberInput(attrs={'placeholder': 'Payment amount'}),
            'paid': forms.CheckboxInput()
        }