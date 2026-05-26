from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


# =========================================================
# SCHOOL MODEL
# =========================================================
class School(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# =========================================================
# TENURE / SESSION MODEL
# =========================================================
class Tenure(models.Model):
    session = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.is_active:
            Tenure.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.session


# =========================================================
# STUDENT MODEL
# =========================================================
class Student(models.Model):

    MEMBER_TYPE_CHOICES = [
        ('student', 'Regular Student'),
        ('student_member', 'Financial Student Member'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=150)
    school = models.ForeignKey(
        'School', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='students'
    )
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)

    email = models.EmailField(unique=True)

    age = models.PositiveIntegerField(null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)

    member_type = models.CharField(
        max_length=30,
        choices=MEMBER_TYPE_CHOICES,
        default='student'
    )

    serial_number = models.CharField(max_length=30, unique=True, blank=True)

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )

    is_verified = models.BooleanField(default=False)

    registration_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # HELPERS
    # =====================================================
    def is_executive(self):
        return self.executive_assignments.filter(is_active=True).exists()

    def is_president(self):
        return self.executive_assignments.filter(
            position__title__iexact='president',  
            is_active=True
        ).exists()

    def get_active_roles(self):
        return self.executive_assignments.filter(is_active=True)

    # =====================================================
    # SAVE METHOD
    # =====================================================
    def save(self, *args, **kwargs):

        if self.email:
            self.email = self.email.lower().strip()

        # Sync user
        if self.user:
            self.user.username = self.email
            self.user.email = self.email
            self.user.save()

        # Prevent duplicate email (extra safety)
        if Student.objects.exclude(id=self.id).filter(email=self.email).exists():
            raise ValueError("Duplicate email detected.")

        # Generate serial number
        if not self.serial_number:
            year = timezone.now().year

            last_student = Student.objects.filter(
                serial_number__startswith=f"NUSSNHQ/{year}/"
            ).order_by('id').last()

            last_number = 0
            if last_student and last_student.serial_number:
                try:
                    last_number = int(last_student.serial_number.split('/')[-1])
                except:
                    last_number = 0

            self.serial_number = f"NUSSNHQ/{year}/{last_number + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.serial_number})"


# =========================================================
# EXECUTIVE POSITION
# =========================================================
class ExecutivePosition(models.Model):

    POSITION_CHOICES = [
        ('president', 'President'),
        ('vice_president', 'Vice President'),
        ('senate_president', 'Senate President'),
        ('deputy_senate_president', 'Deputy Senate President'),
        ('general_secretary', 'General Secretary'),
        ('assistant_general_secretary', 'Assistant General Secretary'),
        ('treasurer', 'Treasurer'),
        ('financial_secretary', 'Financial Secretary'),
        ('pro', 'PRO'),
        ('pro_ii', 'PRO II'),
        ('social_director', 'Social Director'),
        ('welfare', 'Welfare'),
        ('organising_committee', 'Organising Committee'),
    ]

    title = models.CharField(
        max_length=100,
        choices=POSITION_CHOICES,
        unique=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.get_title_display()


# =========================================================
# EXECUTIVE ASSIGNMENT
# =========================================================
class ExecutiveAssignment(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='executive_assignments'
    )

    position = models.ForeignKey(ExecutivePosition, on_delete=models.CASCADE)
    tenure = models.ForeignKey(Tenure, on_delete=models.CASCADE)

    appointed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments_made'
    )

    is_active = models.BooleanField(default=True)

    assigned_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['position', 'tenure']

    def save(self, *args, **kwargs):

        if self.is_active:

            # Only one active per position per tenure
            ExecutiveAssignment.objects.filter(
                position=self.position,
                tenure=self.tenure,
                is_active=True
            ).exclude(id=self.id).update(
                is_active=False,
                removed_at=timezone.now()
            )

            # Extra safety for president (global uniqueness per tenure)
            if self.position.title == 'president':
                ExecutiveAssignment.objects.filter(
                    position__title='president',
                    tenure=self.tenure,
                    is_active=True
                ).exclude(id=self.id).update(
                    is_active=False,
                    removed_at=timezone.now()
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.position.get_title_display()} ({self.tenure.session})"


# =========================================================
# EVENT
# =========================================================
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_flyers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title


# =========================================================
# FUNDRAISING
# =========================================================
class Fundraising(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =========================================================
# PAYMENT
# =========================================================
class Payment(models.Model):

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Awaiting Verification'),
        ('paid', 'Paid'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    payment_receipt = models.ImageField(
        upload_to='receipts/',
        null=True,
        blank=True
    )

    paid = models.BooleanField(default=False)
    date_paid = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

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


# =========================================================
# ANNOUNCEMENT MODEL (ADDED)
# =========================================================
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-date_posted']

    def __str__(self):
        return f"{'📌 ' if self.is_pinned else ''}{self.title}"