from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Student(models.Model):
    MEMBER_TYPE_CHOICES = [
        ('student', 'Student'),
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
        ('student_member', 'Student Member'),
    ]

    EXECUTIVE_POSITION_CHOICES = MEMBER_TYPE_CHOICES

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=100)
    school = models.CharField(max_length=100)
    department = models.CharField(max_length=50)
    level = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    age = models.PositiveIntegerField(null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)

    member_type = models.CharField(
        max_length=50,
        choices=MEMBER_TYPE_CHOICES,
        default='student_member'
    )

    executive_position = models.CharField(
        max_length=50,
        choices=EXECUTIVE_POSITION_CHOICES,
        null=True,
        blank=True
    )

    serial_number = models.CharField(max_length=20, unique=True, blank=True)

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )

    registration_date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):

        # sync email with auth user
        if self.user and self.user.email:
            self.email = self.user.email

        # auto assign executive position
        executive_roles = [
            'president', 'senate_president', 'deputy_senate_president',
            'social_director', 'welfare', 'organising_committee',
            'general_secretary', 'assistant_general_secretary',
            'pro', 'pro_ii', 'treasurer', 'financial_secretary'
        ]

        if self.member_type in executive_roles:
            self.executive_position = self.member_type
        else:
            self.executive_position = None

        # auto generate serial number
        if not self.serial_number:
            year = timezone.now().year

            last_student = Student.objects.filter(
                serial_number__startswith=f"NUSSNHQ/{year}/"
            ).order_by('id').last()

            if last_student and last_student.serial_number:
                try:
                    last_number = int(last_student.serial_number.split('/')[-1])
                except:
                    last_number = 0
            else:
                last_number = 0

            self.serial_number = f"NUSSNHQ/{year}/{last_number + 1:04d}"

        super().save(*args, **kwargs)

    # ✅ ADDED PERMANENT CLEAN LOGIC METHOD
    def is_executive(self):
        executive_roles = [
            'president',
            'treasurer',
            'financial_secretary'
        ]
        return self.member_type in executive_roles

    def __str__(self):
        return f"{self.full_name} ({self.serial_number})"


class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Fundraising(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    goal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.full_name} - {'Paid' if self.paid else 'Pending'}"