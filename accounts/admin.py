from django.contrib import admin
from django.utils import timezone
from .models import Bill, Patient, AccountApprovalRequest, Appointment, SuccessStory  # add SuccessStory here

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
        
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'status', 'created_at']
    list_filter = ['status']
    actions = ['approve_stories', 'reject_stories']

    def approve_stories(self, request, queryset):
        queryset.update(
            status='approved',
            reviewed_by_id=request.user.id,  # use _id suffix for FK fields
            reviewed_at=timezone.now()
        )
        self.message_user(request, 'Selected stories have been approved.')  # also add this feedback

    def reject_stories(self, request, queryset):
        queryset.update(
            status='rejected',
            reviewed_by_id=request.user.id,
            reviewed_at=timezone.now()
        )
        self.message_user(request, 'Selected stories have been rejected.')  

admin.site.register(Patient)
admin.site.register(AccountApprovalRequest, AccountApprovalAdmin)
admin.site.register(Appointment)
admin.site.register(SuccessStory, SuccessStoryAdmin)  # add this line
admin.site.register(Bill)