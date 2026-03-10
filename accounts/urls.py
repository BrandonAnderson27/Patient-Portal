from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('appointment/<int:appointment_id>/approve/', views.approve_appointment, name='approve_appointment'),
    path('appointment/<int:appointment_id>/deny/', views.deny_appointment, name='deny_appointment'),
    path('provider-dashboard/', views.provider_dashboard_view, name='provider_dashboard'),
    path('schedule/', views.schedule_appointment, name='schedule_appointment'),
    path('available-slots/', views.get_available_slots, name='available_slots'),
    path('receptionist-dashboard/', views.receptionist_dashboard_view, name='receptionist_dashboard'),
    path('prescription/add/', views.add_prescription, name='add_prescription'),
    path('success-story/submit/', views.submit_success_story, name='submit_success_story'),
    path('success-story/<int:story_id>/approve/', views.approve_story, name='approve_story'),
    path('success-story/<int:story_id>/reject/', views.reject_story, name='reject_story'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
]