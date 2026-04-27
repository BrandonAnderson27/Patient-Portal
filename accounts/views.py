import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import Appointment, Bill, SuccessStory, User, Patient, AccountApprovalRequest, Provider, ProviderAvailability, Receptionist, Prescription, Message, MessageAccess
from labs.models import Lab, LabRequest, LabResult
from accounts.decorators import role_required
from django.views.decorators.http import require_POST
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
            if user.role == 'lab_staff':
                return redirect('lab_dashboard')
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
        print("POST received:", request.POST)
        try:
            username = request.POST['username']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
                return render(request, 'accounts/register.html')
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            if User.objects.filter(email=email).exists():
                messages.error(request, 'An account with that email already exists.')
                return render(request, 'accounts/register.html')
            password = request.POST['password1']
            password2 = request.POST['password2']
            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/register.html')

            print("Creating user...")
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role='patient'
            )
            print("User created:", user)
            patient = Patient.objects.create(user=user, is_approved=False)
            print("Patient created:", patient)
            AccountApprovalRequest.objects.create(patient=patient)
            print("Approval request created")
            messages.success(request, 'Registration submitted! Please wait for admin approval before logging in.')
            return redirect('login')
        except Exception as e:
            print("ERROR:", e)
            messages.error(request, f'Registration failed: {e}')
            return render(request, 'accounts/register.html')

    return render(request, 'accounts/register.html')

@login_required
@role_required('patient')
def dashboard_view(request):
    try:
        patient = Patient.objects.get(user=request.user)
        active_prescriptions = patient.get_active_prescriptions()
        pending_requests = LabRequest.objects.filter(patient=patient, status='PENDING')
        completed_results = LabResult.objects.filter(request__patient=patient).select_related('request')
    except Patient.DoesNotExist:
        patient = None
        active_prescriptions = []
        pending_requests = []
        completed_results = []

    approved_stories = SuccessStory.objects.filter(status='approved').order_by('-created_at')

    # Messaging
    inbox = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = inbox.filter(is_read=False).count()

    # Which providers has this patient been granted access to message?
    if patient:
        accessible_providers = Provider.objects.filter(
            message_access_grants__patient=patient
        )
    else:
        accessible_providers = []
        
    unpaid_bills = Bill.objects.filter(patient=patient, status='unpaid').order_by('-created_at') if patient else []
    paid_bills = Bill.objects.filter(patient=patient, status='paid').order_by('-paid_at') if patient else []


    return render(request, 'accounts/dashboard.html', {
        'future_appointments': patient.get_upcoming_appointments() if patient else [],
        'past_appointments': patient.get_appointment_history() if patient else [],
        'prescriptions': active_prescriptions,
        'providers': Provider.objects.all(),
        'approved_stories': approved_stories,
        'pending_requests': pending_requests,
        'completed_results': completed_results,
        'messages_inbox': inbox,
        'unread_count': unread_count,
        'accessible_providers': accessible_providers,
        'patient': patient,
        'unpaid_bills': unpaid_bills,   
        'paid_bills': paid_bills,
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
    
    Bill.objects.create(
        patient=appointment.patient,
        description=f"Office Visit — Dr. {appointment.provider.user.last_name} on {appointment.date}",
        amount=100.00,
        status='unpaid'
    )    
    
    messages.success(request, 'Appointment approved.')
    if request.user.role == 'receptionist':
        return redirect('receptionist_dashboard')
    return redirect('provider_dashboard')

def deny_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, 'Appointment denied.')
    if request.user.role == 'receptionist':
        return redirect('receptionist_dashboard')
    return redirect('provider_dashboard')

@login_required
@role_required('provider')
def provider_dashboard_view(request):
    try:
        provider = Provider.objects.get(user=request.user)
        pending_appointments = Appointment.objects.filter(provider=provider, status='pending').order_by('date', 'time')
        upcoming_appointments = Appointment.objects.filter(provider=provider, status='scheduled', date__gte=datetime.date.today()).order_by('date', 'time')
        prescription_count = Prescription.objects.filter(provider=provider).count()
        patient_count = Patient.objects.filter(appointments__provider=provider).distinct().count()
        patients = Patient.objects.filter(appointments__provider=provider).distinct()
        labs = Lab.objects.all()
        pending_lab_count = LabRequest.objects.filter(provider=provider, status='PENDING').count()

        # Messaging
        inbox = Message.objects.filter(recipient=request.user).order_by('-sent_at')
        unread_count = inbox.filter(is_read=False).count()
        granted_patient_ids = MessageAccess.objects.filter(provider=provider).values_list('patient_id', flat=True)

    except Provider.DoesNotExist:
        pending_appointments = []
        upcoming_appointments = []
        prescription_count = 0
        patient_count = 0
        patients = []
        labs = []
        pending_lab_count = 0
        inbox = []
        unread_count = 0
        granted_patient_ids = []

    return render(request, 'accounts/provider_dashboard.html', {
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'prescription_count': prescription_count,
        'patient_count': patient_count,
        'patients': patients,
        'labs': labs,
        'pending_lab_count': pending_lab_count,
        'messages_inbox': inbox,
        'unread_count': unread_count,
        'granted_patient_ids': granted_patient_ids,
    })
    
@login_required
@role_required('receptionist')
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
        
        Bill.objects.create(
            patient=patient,
            description=f"Prescription — {Prescription.medication_name} ({Prescription.dosage})",
            amount=25.00,
            status='unpaid'
        )

        messages.success(request, 'Prescription saved successfully.')
        return redirect('provider_dashboard')
    return redirect('provider_dashboard')

@login_required
def submit_success_story(request):
    if request.method == 'POST':
        patient = Patient.objects.get(user=request.user)
        content = request.POST.get('content', '').strip()
        if content:
            SuccessStory.objects.create(patient=patient, content=content)
            messages.success(request, 'Your story has been submitted for review!')
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
def approve_story(request, story_id):
    from django.utils import timezone
    story = SuccessStory.objects.get(id=story_id)
    story.status = 'approved'
    story.reviewed_by = request.user
    story.reviewed_at = timezone.now()
    story.save()
    messages.success(request, 'Story approved.')
    return redirect('admin_dashboard')

@login_required
def reject_story(request, story_id):
    from django.utils import timezone
    story = SuccessStory.objects.get(id=story_id)
    story.status = 'rejected'
    story.reviewed_by = request.user
    story.reviewed_at = timezone.now()
    story.save()
    messages.success(request, 'Story rejected.')
    return redirect('admin_dashboard')

@login_required
def admin_dashboard_view(request):
    pending_stories = SuccessStory.objects.filter(status='pending').order_by('created_at')
    return render(request, 'accounts/admin_dashboard.html', {
        'pending_stories': pending_stories,
    })
    
@login_required
@role_required('patient')
def send_message(request):
    if request.method == 'POST':
        patient = Patient.objects.get(user=request.user)
        provider_id = request.POST.get('provider_id')

        # Make sure this patient actually has access to message this provider
        has_access = MessageAccess.objects.filter(
            patient=patient,
            provider_id=provider_id
        ).exists()

        if not has_access:
            messages.error(request, 'You do not have permission to message this provider.')
            return redirect('dashboard')

        provider = Provider.objects.get(id=provider_id)
        body = request.POST.get('body', '').strip()

        if body:
            Message.objects.create(
                sender=request.user,
                recipient=provider.user,
                body=body
            )
            messages.success(request, 'Message sent.')

    next_url = request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)

@login_required
@role_required('provider')
def send_message_provider(request):
    if request.method == 'POST':
        provider = Provider.objects.get(user=request.user)
        patient_id = request.POST.get('patient_id')

        # Make sure this provider has granted access to this patient (they're in their patient list)
        patient = Patient.objects.get(id=patient_id)
        has_access = MessageAccess.objects.filter(
            patient=patient,
            provider=provider
        ).exists()

        if not has_access:
            messages.error(request, 'You do not have permission to message this patient.')
            return redirect('dashboard')

        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                sender=request.user,
                recipient=patient.user,
                body=body
            )
            messages.success(request, 'Message sent.')

    next_url = request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)


@login_required
@role_required('provider')
def grant_message_access(request, patient_id):
    provider = Provider.objects.get(user=request.user)
    patient = Patient.objects.get(id=patient_id)
    MessageAccess.objects.get_or_create(provider=provider, patient=patient)
    messages.success(request, f'Message access granted to {patient}.')
    return redirect('provider_dashboard')


@login_required
@role_required('provider')
def revoke_message_access(request, patient_id):
    provider = Provider.objects.get(user=request.user)
    MessageAccess.objects.filter(provider=provider, patient_id=patient_id).delete()
    messages.success(request, 'Message access revoked.')
    return redirect('provider_dashboard')


@login_required
def mark_message_read(request, message_id):
    msg = Message.objects.get(id=message_id, recipient=request.user)
    msg.is_read = True
    msg.save()
    next_url = request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)


@login_required
@role_required('patient')
def update_profile(request):
    if request.method == 'POST':
        patient = Patient.objects.get(user=request.user)
        update_type = request.POST.get('update_type')

        if update_type == 'personal':
            patient.date_of_birth = request.POST.get('date_of_birth') or None
            patient.gender = request.POST.get('gender', '')
            patient.contact_number = request.POST.get('contact_number', '')
            patient.emergency_contact = request.POST.get('emergency_contact', '')
            patient.address = request.POST.get('address', '')
            patient.save()

            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            if new_password:
                if new_password == confirm_password:
                    from django.contrib.auth import update_session_auth_hash
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Password updated successfully.')
                else:
                    messages.error(request, 'Passwords do not match.')
                    return redirect('dashboard')

            messages.success(request, 'Personal information updated.')

        elif update_type == 'insurance':
            patient.insurance_name = request.POST.get('insurance_name', '')
            patient.insurance_member_id = request.POST.get('insurance_member_id', '')
            patient.insurance_group = request.POST.get('insurance_group', '')
            patient.insurance_coverage_date = request.POST.get('insurance_coverage_date') or None
            patient.insurance_contact = request.POST.get('insurance_contact', '')
            patient.insurance_address = request.POST.get('insurance_address', '')
            patient.save()
            messages.success(request, 'Insurance information updated.')

        elif update_type == 'medical':
            patient.previous_clinic = request.POST.get('previous_clinic', '')
            patient.previous_doctor = request.POST.get('previous_doctor', '')
            patient.weight = request.POST.get('weight', '')
            patient.height = request.POST.get('height', '')
            patient.blood_pressure = request.POST.get('blood_pressure', '')
            patient.temperature = request.POST.get('temperature', '')
            patient.preconditions = request.POST.get('preconditions', '')
            patient.save()
            messages.success(request, 'Medical information updated.')

    return redirect('dashboard')

@login_required
@role_required('patient')
def mark_bill_paid(request, bill_id):
    import datetime
    bill = Bill.objects.get(id=bill_id, patient__user=request.user)
    bill.status = 'paid'
    bill.paid_at = datetime.date.today()
    bill.save()
    messages.success(request, 'Bill marked as paid.')
    next_url = request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)

@require_POST
def fp_send_code(request):
    data = json.loads(request.body)
    username = data.get('username', '').strip()

    # We always respond OK to avoid exposing whether a username exists
    # But only store session data if the user actually exists
    try:
        User.objects.get(username=username)
        code = str(random.randint(100000, 999999))
        request.session['fp_code'] = code
        request.session['fp_username'] = username
    except User.DoesNotExist:
        # Still generate a fake code so the response looks identical
        code = str(random.randint(100000, 999999))

    # ⚠️ In production: email/SMS the code instead of returning it here
    return JsonResponse({'ok': True, 'code': code})


@require_POST
def fp_verify_code(request):
    data = json.loads(request.body)
    entered = data.get('code', '').strip()

    stored = request.session.get('fp_code')
    if not stored or entered != stored:
        return JsonResponse({'ok': False, 'error': 'Incorrect code. Please try again.'}, status=400)

    return JsonResponse({'ok': True})


@require_POST
def fp_reset_password(request):
    data = json.loads(request.body)
    new_password = data.get('password', '').strip()

    username = request.session.get('fp_username')
    code = request.session.get('fp_code')

    if not username or not code:
        return JsonResponse({'ok': False, 'error': 'Session expired. Please start over.'}, status=400)

    if len(new_password) < 6:
        return JsonResponse({'ok': False, 'error': 'Password must be at least 6 characters.'}, status=400)

    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)  # Uses Django's hasher, same as your register_view
        user.save()
        # Clean up session
        request.session.pop('fp_code', None)
        request.session.pop('fp_username', None)
        return JsonResponse({'ok': True})
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'User not found.'}, status=404)