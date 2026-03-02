from django.contrib import admin
from .models import Patient, AccountApprovalRequest
from django.utils import timezone

class AccountApprovalAdmin(admin.ModelAdmin):
    list_display = ['patient', 'status', 'requested_at']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for approval in queryset:
            approval.status = 'approved'
            approval.reviewed_at = timezone.now()
            approval.reviewed_by = request.user
            approval.save()
            approval.patient.is_approved = True
            approval.patient.save()
        self.message_user(request, 'Selected requests have been approved.')

    def reject_requests(self, request, queryset):
        for approval in queryset:
            approval.status = 'rejected'
            approval.reviewed_at = timezone.now()
            approval.reviewed_by = request.user
            approval.save()
        self.message_user(request, 'Selected requests have been rejected.')

admin.site.register(Patient)
admin.site.register(AccountApprovalRequest, AccountApprovalAdmin)