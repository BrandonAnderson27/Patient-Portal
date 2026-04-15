from django.core.management.base import BaseCommand
from accounts.models import (
    User, Patient, Provider, Appointment, Prescription,
    ProviderAvailability, Receptionist, LabStaff, Admin,
    AccountApprovalRequest, SuccessStory
)
from django.utils import timezone
import datetime
from labs.models import Lab

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning up existing test data...')

        User.objects.filter(username__in=[
            'testpatient', 'testprovider', 'testreceptionist',
            'testadmin', 'testlabstaff'
        ]).delete()

        # ── Admin ─────────────────────────────────────────────
        self.stdout.write('Creating test admin...')
        admin_user = User.objects.create_user(
            username='testadmin', password='testpass123',
            first_name='Carol', last_name='White', role='admin'
        )
        admin_user.is_staff = True
        admin_user.save()
        Admin.objects.create(user=admin_user, admin_level='superadmin')

        # ── Provider ──────────────────────────────────────────
        self.stdout.write('Creating test provider...')
        provider_user = User.objects.create_user(
            username='testprovider', password='testpass123',
            first_name='Jane', last_name='Smith', role='provider'
        )
        provider = Provider.objects.create(
            user=provider_user,
            specialization='General Practice',
            license_number='LIC123456'
        )

        # ── Receptionist ──────────────────────────────────────
        self.stdout.write('Creating test receptionist...')
        receptionist_user = User.objects.create_user(
            username='testreceptionist', password='testpass123',
            first_name='Sarah', last_name='Jones', role='receptionist'
        )
        Receptionist.objects.create(user=receptionist_user, provider=provider)

        # ── Lab Staff ─────────────────────────────────────────────
        self.stdout.write('Creating test lab staff...')
        labstaff_user = User.objects.create_user(
            username='testlabstaff', password='testpass123',
            first_name='Mike', last_name='Brown', role='lab_staff'
        )
        lab, _ = Lab.objects.get_or_create(
            name='Main Diagnostics Lab',
            defaults={'location': '123 Lab Ave'}
        )
        LabStaff.objects.create(user=labstaff_user, lab=lab)

        # ── Patient ───────────────────────────────────────────
        self.stdout.write('Creating test patient...')
        patient_user = User.objects.create_user(
            username='testpatient', password='testpass123',
            first_name='John', last_name='Doe', role='patient'
        )
        patient = Patient.objects.create(
            user=patient_user,
            is_approved=True,
            address='123 Main St, Springfield',
            insurance_provider='BlueCross',
            medical_record='MR-00123'
        )
        AccountApprovalRequest.objects.create(
            patient=patient,
            status='approved',
            reviewed_at=timezone.now(),
            reviewed_by=admin_user
        )

        # ── Provider Availability (Mon–Fri) ───────────────────
        self.stdout.write('Creating provider availability...')
        ProviderAvailability.objects.filter(provider=provider).delete()
        for day in range(5):
            ProviderAvailability.objects.create(
                provider=provider,
                day_of_week=day,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(17, 0),
                slot_duration=30
            )

        # ── Appointments ──────────────────────────────────────
        self.stdout.write('Creating test appointments...')
        future_appointment = Appointment.objects.create(
            patient=patient,
            provider=provider,
            date=datetime.date.today() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            reason='Annual checkup',
            status='pending'
        )
        past_appointment = Appointment.objects.create(
            patient=patient,
            provider=provider,
            date=datetime.date.today() - datetime.timedelta(days=30),
            time=datetime.time(14, 0),
            reason='Follow-up visit',
            status='completed'
        )

        # ── Prescriptions ─────────────────────────────────────
        self.stdout.write('Creating test prescriptions...')
        Prescription.objects.create(
            patient=patient,
            provider=provider,
            appointment=past_appointment,
            medication_name='Amoxicillin',
            dosage='500mg',
            frequency='Twice daily',
            route='Oral',
            instructions='Take with food',
            prescribed_date=datetime.date.today() - datetime.timedelta(days=30),
            start_date=datetime.date.today() - datetime.timedelta(days=30),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            refills_allowed=2,
            refills_remaining=2,
            status='active'
        )
        Prescription.objects.create(
            patient=patient,
            provider=provider,
            appointment=past_appointment,
            medication_name='Lisinopril',
            dosage='10mg',
            frequency='Once daily',
            route='Oral',
            instructions='Take in the morning',
            prescribed_date=datetime.date.today() - datetime.timedelta(days=90),
            start_date=datetime.date.today() - datetime.timedelta(days=90),
            end_date=None,  # indefinite
            refills_allowed=5,
            refills_remaining=3,
            status='active'
        )

        # ── Success Stories ───────────────────────────────────
        self.stdout.write('Creating test success stories...')
        SuccessStory.objects.create(
            patient=patient,
            content='I came in feeling hopeless, but the team here changed everything. '
                    'Within weeks I was back on my feet. Cannot recommend this clinic enough!',
            status='approved',
            reviewed_by=admin_user,
            reviewed_at=timezone.now()
        )
        SuccessStory.objects.create(
            patient=patient,
            content='The care I received during my recovery was outstanding. '
                    'Dr. Smith was attentive and thorough at every step.',
            status='pending'
        )
        SuccessStory.objects.create(
            patient=patient,
            content='This is a test story that was rejected during review.',
            status='rejected',
            reviewed_by=admin_user,
            reviewed_at=timezone.now()
        )

        self.stdout.write(self.style.SUCCESS('\nDone! Test accounts:'))
        self.stdout.write('  Patient:      testpatient / testpass123')
        self.stdout.write('  Provider:     testprovider / testpass123')
        self.stdout.write('  Receptionist: testreceptionist / testpass123')
        self.stdout.write('  Lab Staff:    testlabstaff / testpass123')
        self.stdout.write('  Admin:        testadmin / testpass123')