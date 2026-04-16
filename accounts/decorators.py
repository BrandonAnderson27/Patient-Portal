from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def role_required(role):
    def check_role(user):
        return user.is_authenticated and user.role == role
    return user_passes_test(check_role, login_url='login')