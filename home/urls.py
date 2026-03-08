from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('portal/dashboard/', views.dashboard_view, name='dashboard'),
]