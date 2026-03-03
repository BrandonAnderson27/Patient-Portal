from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    PATIENT = 'patient'
    RECEPTIONIST = 'receptionist'
    PROVIDER = 'provider'
    ADMIN = 'admin'
    LAB_STAFF = 'lab_staff'

    ROLE_CHOICES = [
        (PATIENT, 'Patient'),
        (RECEPTIONIST, 'Receptionist'),
        (PROVIDER, 'Provider'),
        (ADMIN, 'Admin'),
        (LAB_STAFF, 'Lab Staff'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True)
    insurance_provider = models.CharField(max_length=255, blank=True)
    medical_record = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=False)

    def get_upcoming_appointments(self):
        from django.utils import timezone
        return self.appointments.filter(date__gte=timezone.now().date(), status='scheduled').order_by('date', 'time')

    def get_appointment_history(self):
        from django.utils import timezone
        return self.appointments.filter(date__lt=timezone.now().date()).order_by('-date', '-time')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class AccountApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Request for {self.patient.user.username} - {self.status}"

class Provider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=255, blank=True)

    def get_upcoming_appointments(self):
        from django.utils import timezone
        return self.appointments.filter(date__gte=timezone.now().date(), status='scheduled').order_by('date', 'time')

    def get_patient_list(self):
        return Patient.objects.filter(appointments__provider=self).distinct()

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, null=True, blank=True, on_delete=models.SET_NULL, related_name='receptionists')

class LabStaff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lab = models.CharField(max_length=255, blank=True)

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_level = models.CharField(max_length=255, blank=True)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.username} with Dr. {self.provider.user.last_name} on {self.date} at {self.time}"