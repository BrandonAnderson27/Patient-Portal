from django.contrib import admin
from .models import Lab, LabRequest, LabResult

admin.site.register(Lab)
admin.site.register(LabRequest)
admin.site.register(LabResult)