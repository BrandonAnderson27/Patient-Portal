from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User, Patient, AccountApprovalRequest

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # check if patient needs approval
            try:
                patient = Patient.objects.get(user=user)
                if not patient.is_approved:
                    messages.error(request, 'Your account is pending admin approval.')
                    return render(request, 'accounts/login.html', {'form': form})
            except Patient.DoesNotExist:
                pass  # admins/providers won't have a patient profile
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Login successful.')
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
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
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
    return render(request, 'accounts/dashboard.html')