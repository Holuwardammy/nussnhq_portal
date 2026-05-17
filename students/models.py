from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# ---------------------------
# SCHOOL MODEL (Self-Learning List)
# ---------------------------
class School(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


# ---------------------------
# STUDENT MODEL 
# ---------------------------
class Student(models.Model):
    # Matches forms.py perfectly. Public dropdown cannot assign admin rights.
    MEMBER_TYPE_CHOICES = [
        ('student', 'Regular Student'),
        ('student_member', 'Financial Student Member'),
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

    serial_number = models.CharField(max_length=20, unique=True, blank=True)

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )

    registration_date = models.DateField(auto_now_add=True)

    # --- HIERARCHY HELPERS (Saves views.py from breaking) ---
    def is_executive(self):
        """Checks if this student has a record in the ExecutiveRole table."""
        return hasattr(self, 'executive_role')

    def is_president(self):
        return hasattr(self, 'executive_role') and self.executive_role.title == 'president'

    def is_treasurer(self):
        return hasattr(self, 'executive_role') and self.executive_role.title == 'treasurer'

    def is_financial_secretary(self):
        return hasattr(self, 'executive_role') and self.executive_role.title == 'financial_secretary'

    def save(self, *args, **kwargs):
        # Force email to lowercase for consistency
        if self.email:
            self.email = self.email.lower()

        # Sync email and username with the connected User model
        if self.user:
            update_user = False
            if self.email and (self.user.username != self.email or self.user.email != self.email):
                self.user.username = self.email
                self.user.email = self.email
                update_user = True
            
            if update_user:
                self.user.save()

        # Serial number generation logic (NUSSNHQ/YEAR/0001)
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
# EXECUTIVE ROLE MODEL (The Secure Vault)
# ---------------------------
class ExecutiveRole(models.Model):
    EXECUTIVE_CHOICES = [
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

    # Links 1-to-1 to an existing student profile. One student can only occupy one office.
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='executive_role')
    
    # unique=True guarantees you can never have two active officeholders at once
    title = models.CharField(max_length=50, choices=EXECUTIVE_CHOICES, unique=True)
    tenure = models.CharField(max_length=20, default="2026/2027")
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_title_display()} - {self.student.full_name}"


# ---------------------------
# EVENT MODEL
# ---------------------------
class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=100)
    image = models.ImageField(upload_to='event_flyers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

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
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Awaiting Verification'),
        ('paid', 'Paid'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status == 'paid':
            self.paid = True
            if not self.date_paid:
                self.date_paid = timezone.now()
        else:
            self.paid = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.get_status_display()}"