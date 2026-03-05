from django.core.management.base import BaseCommand
from accounts.models import User, Patient, Provider, Appointment, Prescription, ProviderAvailability, Receptionist
import datetime

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning up existing test data...')

        User.objects.filter(username__in=[
            'testpatient', 'testprovider', 'testreceptionist'
        ]).delete()

        # Create patient
        self.stdout.write('Creating test patient...')
        patient_user = User.objects.create_user(
            username='testpatient', password='testpass123',
            first_name='John', last_name='Doe', role='patient'
        )
        patient = Patient.objects.create(user=patient_user, is_approved=True)

        # Create provider
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

        # Create receptionist assigned to provider
        self.stdout.write('Creating test receptionist...')
        receptionist_user = User.objects.create_user(
            username='testreceptionist', password='testpass123',
            first_name='Sarah', last_name='Jones', role='receptionist'
        )
        Receptionist.objects.create(user=receptionist_user, provider=provider)

        # Create provider availability Monday through Friday
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

        # Create a pending appointment
        self.stdout.write('Creating test appointment...')
        appointment = Appointment.objects.create(
            patient=patient,
            provider=provider,
            date=datetime.date.today() + datetime.timedelta(days=7),
            time=datetime.time(10, 0),
            reason='Annual checkup',
            status='pending'
        )

        # Create a prescription
        self.stdout.write('Creating test prescription...')
        Prescription.objects.create(
            patient=patient,
            provider=provider,
            appointment=appointment,
            medication_name='Amoxicillin',
            dosage='500mg',
            frequency='Twice daily',
            route='Oral',
            instructions='Take with food',
            prescribed_date=datetime.date.today(),
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            refills_allowed=2,
            refills_remaining=2,
            status='active'
        )

        self.stdout.write(self.style.SUCCESS('\nDone! Test accounts:'))
        self.stdout.write('  Patient:      testpatient / testpass123')
        self.stdout.write('  Provider:     testprovider / testpass123')
        self.stdout.write('  Receptionist: testreceptionist / testpass123')