from django.db import models


class Lab(models.Model):

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class LabRequest(models.Model):

    patient = models.ForeignKey("accounts.Patient", on_delete=models.CASCADE)
    provider = models.ForeignKey("accounts.Provider", on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)

    test_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient}"


class LabResult(models.Model):

    request = models.ForeignKey(LabRequest, on_delete=models.CASCADE)

    result = models.TextField()
    reference_range = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.request.test_name}"