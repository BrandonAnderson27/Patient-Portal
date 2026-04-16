from django.core.management.base import BaseCommand
from accounts.models import (
    User, Patient, Provider, Appointment, Prescription,
    ProviderAvailability, Receptionist, LabStaff, Admin,
    AccountApprovalRequest, SuccessStory, MessageAccess, Message, Bill
)
from django.utils import timezone
import datetime
from labs.models import Lab, LabRequest, LabResult

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning up existing test data...')

        User.objects.filter(username__in=[
            'testpatient', 'testprovider', 'testreceptionist',
            'testadmin', 'testlabstaff'
        ]).delete()

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
            gender='Male',
            contact_number='555-123-4567',
            emergency_contact='555-987-6543',
            insurance_name='BlueCross',
            insurance_member_id='MR-00123',
            insurance_group='GRP-001',
            insurance_contact='555-111-2222',
            previous_clinic='Springfield General',
            previous_doctor='Dr. Adams',
            weight='180 lbs',
            height='5\'11"',
            blood_pressure='120/80',
            temperature='98.6',
            preconditions='None'
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
        # ── Messages ──────────────────────────────────────────
        self.stdout.write('Creating test messages...')
        MessageAccess.objects.create(provider=provider, patient=patient)

        Message.objects.create(
            sender=patient_user,
            recipient=provider_user,
            body='Hello Dr. Smith, I have been experiencing some side effects from the Amoxicillin. Should I be concerned?',
            is_read=True
        )
        Message.objects.create(
            sender=provider_user,
            recipient=patient_user,
            body='Hi John, some mild side effects are normal. If you experience severe symptoms please contact us immediately.',
            is_read=True
        )
        Message.objects.create(
            sender=patient_user,
            recipient=provider_user,
            body='Thank you doctor. One more question — can I take this with ibuprofen?',
            is_read=False
        )

        # ── Lab Requests & Results ────────────────────────────
        self.stdout.write('Creating test lab requests and results...')
        lab_request_completed = LabRequest.objects.create(
            patient=patient,
            provider=provider,
            lab=lab,
            test_name='Complete Blood Count (CBC)',
            notes='Routine checkup panel',
            status='COMPLETED'
        )
        LabResult.objects.create(
            request=lab_request_completed,
            result='WBC: 6.5, RBC: 4.8, Hemoglobin: 14.2, Hematocrit: 42%, Platelets: 250 — all within normal range.',
            reference_range='WBC: 4.5–11.0, RBC: 4.5–5.5, Hemoglobin: 13.5–17.5'
        )

        lab_request_pending = LabRequest.objects.create(
            patient=patient,
            provider=provider,
            lab=lab,
            test_name='Lipid Panel',
            notes='Check cholesterol levels',
            status='PENDING'
        )

        # ── Bills ─────────────────────────────────────────────
        self.stdout.write('Creating test bills...')
        Bill.objects.create(
            patient=patient,
            description='Office Visit - Dr. Smith',
            amount=150.00,
            status='paid',
            paid_at=datetime.date.today() - datetime.timedelta(days=28)
        )
        Bill.objects.create(
            patient=patient,
            description='Lab Work - Complete Blood Count',
            amount=75.50,
            status='paid',
            paid_at=datetime.date.today() - datetime.timedelta(days=28)
        )
        Bill.objects.create(
            patient=patient,
            description='Follow-up Visit - Dr. Smith',
            amount=100.00,
            status='unpaid'
        )
        Bill.objects.create(
            patient=patient,
            description='Prescription - Amoxicillin',
            amount=25.00,
            status='unpaid'
        )
        # ── Admin ─────────────────────────────────────────────
        self.stdout.write('Creating test admin...')
        admin_user = User.objects.create_user(
            username='testadmin', password='testpass123',
            first_name='Carol', last_name='White', role='admin'
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        Admin.objects.create(user=admin_user, admin_level='superadmin')

        self.stdout.write(self.style.SUCCESS('\nDone! Test accounts:'))
        self.stdout.write('  Patient:      testpatient / testpass123')
        self.stdout.write('  Provider:     testprovider / testpass123')
        self.stdout.write('  Receptionist: testreceptionist / testpass123')
        self.stdout.write('  Lab Staff:    testlabstaff / testpass123')
        self.stdout.write('  Admin:        testadmin / testpass123')