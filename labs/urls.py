from django.urls import path
from . import views

urlpatterns = [

    path("create/", views.create_lab_request, name="create_lab_request"),

    path("dashboard/", views.lab_dashboard, name="lab_dashboard"),

    path("upload/<int:request_id>/", views.upload_result, name="upload_result"),

    path("results/", views.patient_results, name="patient_results"),

    
]