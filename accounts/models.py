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
    appointment_history = models.TextField(blank=True)
    upcoming_appointments = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)  # new

class AccountApprovalRequest(models.Model):  # new
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
    appointment_schedule = models.TextField(blank=True)
    patient_list = models.TextField(blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=255, blank=True)

class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255, blank=True)
    
class LabStaff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lab = models.CharField(max_length=255, blank=True)

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_level = models.CharField(max_length=255, blank=True)