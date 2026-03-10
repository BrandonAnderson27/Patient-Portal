from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import Appointment, User, Patient, AccountApprovalRequest, Provider, ProviderAvailability, Receptionist, Prescription
import datetime

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                patient = Patient.objects.get(user=user)
                if not patient.is_approved:
                    messages.error(request, 'Your account is pending admin approval.')
                    return render(request, 'accounts/login.html', {'form': form})
            except Patient.DoesNotExist:
                pass
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Login successful.')
            if user.role == 'provider':
                return redirect('provider_dashboard')
            if user.role == 'receptionist':
                return redirect('receptionist_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with that email already exists.')
            return render(request, 'accounts/register.html')
        phone_number = request.POST['phone_number']
        date_of_birth = request.POST['date_of_birth']

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            role='patient'
        )
        patient = Patient.objects.create(user=user, is_approved=False)
        AccountApprovalRequest.objects.create(patient=patient)
        messages.success(request, 'Registration submitted! Please wait for admin approval before logging in.')
        return redirect('login')
    
    return render(request, 'accounts/register.html')

@login_required
def dashboard_view(request):
    try:
        patient = Patient.objects.get(user=request.user)
        upcoming_appointments = patient.get_upcoming_appointments()
        appointment_history = patient.get_appointment_history()
        active_prescriptions = patient.get_active_prescriptions()
    except Patient.DoesNotExist:
        upcoming_appointments = []
        appointment_history = []
        active_prescriptions = []

    return render(request, 'accounts/dashboard.html', {
        'future_appointments': patient.get_upcoming_appointments(),   # renamed
        'past_appointments': patient.get_appointment_history(),       # renamed
        'prescriptions': active_prescriptions,
        'providers': Provider.objects.all(),
    })

@login_required
def schedule_appointment(request):
    if request.method == 'POST':
        patient = Patient.objects.get(user=request.user)
        provider = Provider.objects.get(id=request.POST['provider_id'])
        date = datetime.date.fromisoformat(request.POST['date'])
        time = datetime.time.fromisoformat(request.POST['time'])
        reason = request.POST['reason']

        Appointment.objects.create(
            patient=patient,
            provider=provider,
            date=date,
            time=time,
            reason=reason,
            status='pending'
        )
        messages.success(request, 'Appointment requested successfully.')
        return redirect('dashboard')
    
    return redirect('dashboard')

def get_available_slots(request):  # was missing entirely
    provider_id = request.GET.get('provider_id')
    date_str = request.GET.get('date')

    if not provider_id or not date_str:
        return JsonResponse({'slots': []})

    date = datetime.date.fromisoformat(date_str)
    day_of_week = date.weekday()

    try:
        availability = ProviderAvailability.objects.get(
            provider_id=provider_id,
            day_of_week=day_of_week
        )
    except ProviderAvailability.DoesNotExist:
        return JsonResponse({'slots': []})

    booked_times = Appointment.objects.filter(
        provider_id=provider_id,
        date=date,
        status='scheduled'
    ).values_list('time', flat=True)

    all_slots = availability.get_time_slots()
    available = [t.strftime('%H:%M') for t in all_slots if t not in booked_times]

    return JsonResponse({'slots': available})

def approve_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'scheduled'
    appointment.save()
    messages.success(request, 'Appointment approved.')
    return redirect('provider_dashboard')

def deny_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, 'Appointment denied.')
    return redirect('provider_dashboard')

@login_required
def provider_dashboard_view(request):
    try:
        provider = Provider.objects.get(user=request.user)
        pending_appointments = Appointment.objects.filter(
            provider=provider,
            status='pending'
        ).order_by('date', 'time')
        upcoming_appointments = Appointment.objects.filter(
            provider=provider,
            status='scheduled',
            date__gte=datetime.date.today()
        ).order_by('date', 'time')
        prescription_count = Prescription.objects.filter(provider=provider).count()
        patient_count = Patient.objects.filter(appointments__provider=provider).distinct().count()
        patients = Patient.objects.filter(appointments__provider=provider).distinct()
    except Provider.DoesNotExist:
        pending_appointments = []
        upcoming_appointments = []
        prescription_count = 0
        patient_count = 0
        patients = []

    return render(request, 'accounts/provider_dashboard.html', {
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'prescription_count': prescription_count,
        'patient_count': patient_count,
        'patients': patients,
    })
    
@login_required
def receptionist_dashboard_view(request):
    try:
        receptionist = Receptionist.objects.get(user=request.user)
        provider = receptionist.provider
        if provider:
            pending_appointments = Appointment.objects.filter(
                provider=provider,
                status='pending'
            ).order_by('date', 'time')
            upcoming_appointments = Appointment.objects.filter(
                provider=provider,
                status='scheduled',
                date__gte=datetime.date.today()
            ).order_by('date', 'time')
        else:
            pending_appointments = []
            upcoming_appointments = []
    except Receptionist.DoesNotExist:
        pending_appointments = []
        upcoming_appointments = []
        provider = None

    return render(request, 'accounts/receptionist_dashboard.html', {
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'provider': provider,
    })
    
@login_required
def add_prescription(request):
    if request.method == 'POST':
        provider = Provider.objects.get(user=request.user)
        patient = Patient.objects.get(id=request.POST['patient_id'])
        appointment_id = request.POST.get('appointment_id')
        appointment = Appointment.objects.get(id=appointment_id) if appointment_id else None

        import datetime
        Prescription.objects.create(
            patient=patient,
            provider=provider,
            appointment=appointment,
            medication_name=request.POST['medication_name'],
            dosage=request.POST['dosage'],
            frequency=request.POST['frequency'],
            route=request.POST.get('route', ''),
            instructions=request.POST.get('instructions', ''),
            prescribed_date=request.POST.get('prescribed_date') or datetime.date.today(),
            start_date=request.POST['start_date'],
            end_date=request.POST.get('end_date') or None,
            refills_allowed=int(request.POST.get('refills_allowed', 0)),
            refills_remaining=int(request.POST.get('refills_allowed', 0)),
            status='active',
        )
        messages.success(request, 'Prescription saved successfully.')
        return redirect('provider_dashboard')
    return redirect('provider_dashboard')