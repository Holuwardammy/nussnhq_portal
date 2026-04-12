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

    EXECUTIVE_ROLES = [
        'president',
        'treasurer',
        'financial_secretary'
    ]

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

    # 🔥 FIX: Added the missing is_executive method
    def is_executive(self):
        """Checks if the student's member_type is in the executive roles list."""
        return self.member_type in self.EXECUTIVE_ROLES

    def save(self, *args, **kwargs):
        # Sync email and username with the User model
        if self.user:
            update_user = False
            if self.email and self.user.username != self.email:
                self.user.username = self.email
                self.user.email = self.email
                update_user = True
            
            if update_user:
                self.user.save()

        # Update executive_position based on member_type
        if self.is_executive():
            self.executive_position = self.member_type
        else:
            self.executive_position = None

        # Serial number generation logic
        if not self.serial_number:
            year = timezone.now().year
            last_student = Student.objects.filter(
                serial_number__startswith=f"NUSSNHQ/{year}/"
            ).order_by('id').last()

            last_number = 0
            if last_student and last_student.serial_number:
                try:
                    last_number = int(last_student.serial_number.split('/')[-1])
                except (IndexError, ValueError):
                    last_number = 0
            self.serial_number = f"NUSSNHQ/{year}/{last_number + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.serial_number})"


# ---------------------------
# EVENT MODEL
# ---------------------------
class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.title


# ---------------------------
# FUNDRAISING MODEL
# ---------------------------
class Fundraising(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    goal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


# ---------------------------
# PAYMENT MODEL
# ---------------------------
class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.full_name} - {'Paid' if self.paid else 'Pending'}"